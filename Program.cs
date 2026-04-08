using System.Diagnostics;
using System.Text;
using System.Text.Json;

namespace SidekickHelper;

internal static class Program
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = true,
        WriteIndented = false
    };

    private static readonly string AppDataRoot = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "SidekickHelper");

    private static readonly string ConfigPath = Path.Combine(AppDataRoot, "config.json");

    private static AppConfig _config = AppConfig.Load(ConfigPath);

    private static int Main()
    {
        Directory.CreateDirectory(AppDataRoot);

        try
        {
            while (ReadMessage() is { } request)
            {
                HandleRequest(request);
            }
        }
        catch (Exception ex)
        {
            Send(new ErrorResponse("UnhandledError", ex.Message));
            return 1;
        }

        return 0;
    }

    private static void HandleRequest(BaseRequest request)
    {
        switch (request.Type)
        {
            case "ping":
                Send(new PongResponse("pong"));
                return;
            case "initialize":
                HandleInitialize(request.Payload);
                return;
            case "zip_request":
                HandleZipRequest(request.Payload);
                return;
            default:
                Send(new ErrorResponse("UnknownRequest", $"Unknown request type '{request.Type}'."));
                return;
        }
    }

    private static void HandleInitialize(JsonElement payload)
    {
        var init = payload.Deserialize<InitializePayload>(JsonOptions);
        if (init is null || string.IsNullOrWhiteSpace(init.OutputFolder))
        {
            Send(new ErrorResponse("InvalidInitialize", "OutputFolder is required for initialize request."));
            return;
        }

        var outputFolder = ExpandHomePath(init.OutputFolder);
        Directory.CreateDirectory(outputFolder);

        _config = new AppConfig(outputFolder);
        _config.Save(ConfigPath);

        Send(new InitializeResponse("initialized", outputFolder));
    }

    private static void HandleZipRequest(JsonElement payload)
    {
        var request = payload.Deserialize<ZipRequestPayload>(JsonOptions);
        if (request is null)
        {
            Send(new ErrorResponse("InvalidZipRequest", "Missing payload for zip request."));
            return;
        }

        if (!_config.IsValid())
        {
            Send(new ErrorResponse("NotInitialized", "App not initialized. Send initialize request with output folder first."));
            return;
        }

        if (request.Files is null || request.Files.Count == 0)
        {
            Send(new ErrorResponse("NoFiles", "Zip request must include at least one file."));
            return;
        }

        var existingFiles = request.Files
            .Where(File.Exists)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();

        if (existingFiles.Count == 0)
        {
            Send(new ErrorResponse("NoExistingFiles", "No requested files exist on disk."));
            return;
        }

        var safeName = SanitizeFileName(request.ZipName);
        var zipName = string.IsNullOrWhiteSpace(safeName)
            ? $"sidekick-{DateTime.UtcNow:yyyyMMdd-HHmmss}.zip"
            : safeName.EndsWith(".zip", StringComparison.OrdinalIgnoreCase) ? safeName : $"{safeName}.zip";

        var outputZipPath = Path.Combine(_config.OutputFolder!, zipName);

        try
        {
            ZipUsingPowerShell(existingFiles, outputZipPath);

            Send(new ZipCompleteResponse(
                "zip_complete",
                outputZipPath,
                zipName,
                existingFiles.Count,
                request.CorrelationId));
        }
        catch (Exception ex)
        {
            Send(new ErrorResponse("ZipFailed", ex.Message, request.CorrelationId));
        }
    }

    private static string ExpandHomePath(string value)
    {
        if (value.StartsWith("~"))
        {
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                value.TrimStart('~').TrimStart('\\', '/'));
        }

        return Path.GetFullPath(value);
    }

    private static void ZipUsingPowerShell(IReadOnlyCollection<string> files, string outputZipPath)
    {
        var destinationDirectory = Path.GetDirectoryName(outputZipPath) ?? throw new InvalidOperationException("Output folder is invalid.");
        Directory.CreateDirectory(destinationDirectory);

        if (File.Exists(outputZipPath))
        {
            File.Delete(outputZipPath);
        }

        var escapedPaths = files.Select(static file => $"'{file.Replace("'", "''")}'");
        var fileArray = string.Join(',', escapedPaths);
        var script = $"$ErrorActionPreference='Stop'; Compress-Archive -LiteralPath @({fileArray}) -DestinationPath '{outputZipPath.Replace("'", "''")}' -CompressionLevel Optimal -Force";

        var process = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = $"-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command \"{script}\"",
                RedirectStandardError = true,
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            }
        };

        process.Start();
        var stdErr = process.StandardError.ReadToEnd();
        process.WaitForExit();

        if (process.ExitCode != 0)
        {
            throw new InvalidOperationException($"Compress-Archive failed: {stdErr}");
        }

        if (!File.Exists(outputZipPath))
        {
            throw new FileNotFoundException("Zip output was not created.", outputZipPath);
        }
    }

    private static string SanitizeFileName(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return string.Empty;
        }

        var invalidChars = Path.GetInvalidFileNameChars();
        var builder = new StringBuilder(value.Length);

        foreach (var ch in value)
        {
            builder.Append(invalidChars.Contains(ch) ? '_' : ch);
        }

        return builder.ToString().Trim();
    }

    private static BaseRequest? ReadMessage()
    {
        var stdin = Console.OpenStandardInput();
        var lengthBuffer = new byte[4];

        var bytesRead = stdin.Read(lengthBuffer, 0, 4);
        if (bytesRead == 0)
        {
            return null;
        }

        if (bytesRead < 4)
        {
            throw new InvalidOperationException("Invalid native messaging frame length.");
        }

        var messageLength = BitConverter.ToInt32(lengthBuffer, 0);
        if (messageLength <= 0)
        {
            throw new InvalidOperationException("Message length must be a positive integer.");
        }

        var messageBuffer = new byte[messageLength];
        var offset = 0;

        while (offset < messageLength)
        {
            var read = stdin.Read(messageBuffer, offset, messageLength - offset);
            if (read == 0)
            {
                throw new InvalidOperationException("Unexpected end of stream while reading native messaging payload.");
            }

            offset += read;
        }

        var json = Encoding.UTF8.GetString(messageBuffer);
        return JsonSerializer.Deserialize<BaseRequest>(json, JsonOptions);
    }

    private static void Send<T>(T payload)
    {
        var json = JsonSerializer.Serialize(payload, JsonOptions);
        var messageBytes = Encoding.UTF8.GetBytes(json);
        var lengthBytes = BitConverter.GetBytes(messageBytes.Length);

        var stdout = Console.OpenStandardOutput();
        stdout.Write(lengthBytes, 0, lengthBytes.Length);
        stdout.Write(messageBytes, 0, messageBytes.Length);
        stdout.Flush();
    }
}

internal sealed record BaseRequest(string Type, JsonElement Payload);
internal sealed record InitializePayload(string OutputFolder);
internal sealed record ZipRequestPayload(List<string> Files, string? ZipName, string? CorrelationId);
internal sealed record InitializeResponse(string Type, string OutputFolder);
internal sealed record ZipCompleteResponse(string Type, string ZipPath, string ZipName, int FileCount, string? CorrelationId);
internal sealed record PongResponse(string Type);
internal sealed record ErrorResponse(string Type, string Message, string? CorrelationId = null);

internal sealed record AppConfig(string? OutputFolder)
{
    public bool IsValid() => !string.IsNullOrWhiteSpace(OutputFolder);

    public void Save(string path)
    {
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrWhiteSpace(dir))
        {
            Directory.CreateDirectory(dir);
        }

        File.WriteAllText(path, JsonSerializer.Serialize(this));
    }

    public static AppConfig Load(string path)
    {
        if (!File.Exists(path))
        {
            return new AppConfig(null);
        }

        try
        {
            var json = File.ReadAllText(path);
            return JsonSerializer.Deserialize<AppConfig>(json) ?? new AppConfig(null);
        }
        catch
        {
            return new AppConfig(null);
        }
    }
}

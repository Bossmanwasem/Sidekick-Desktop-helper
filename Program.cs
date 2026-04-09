using System.IO.Compression;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Windows.Forms;

namespace SidekickHelper;

internal static class Program
{
    private const string AppName = "Smartbox Zipper Sidekick";

    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new ZipperForm(AppName));
    }
}

internal sealed class ZipperForm : Form
{
    private const string GridUserZipName = "Current Grid User.zip";
    private const string CheckinZipName = "Current Checkin.zip";

    private readonly AppConfigStore _configStore;
    private readonly Label _outputFolderValueLabel;
    private readonly ListBox _filesListBox;
    private readonly Label _statusLabel;
    private readonly Panel _dropPanel;
    private readonly string _appName;

    private string _outputFolder = string.Empty;
    private readonly HashSet<string> _selectedFiles = new(StringComparer.OrdinalIgnoreCase);

    public ZipperForm(string appName)
    {
        _appName = appName;
        Text = _appName;
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.Sizable;
        MinimizeBox = true;
        MaximizeBox = true;
        MinimumSize = new Size(320, 280);
        Size = new Size(760, 560);

        _configStore = new AppConfigStore();

        var headerLabel = new Label
        {
            Text = _appName,
            AutoSize = true,
            Font = new Font(Font.FontFamily, 18, FontStyle.Bold),
            Margin = new Padding(0, 0, 0, 4)
        };

        var instructionsLabel = new Label
        {
            Text = "1) Drop files below (including from iTunes).  2) Click 'Begin Zip'.  3) Files are split into Grid User and Checkin ZIPs.",
            AutoSize = true,
            Font = new Font(Font.FontFamily, 10, FontStyle.Regular),
            Margin = new Padding(0, 0, 0, 12)
        };

        var outputFolderTitleLabel = new Label
        {
            Text = "Output folder:",
            AutoSize = true,
            Font = new Font(Font.FontFamily, 10, FontStyle.Bold),
            Margin = new Padding(0, 0, 8, 0)
        };

        _outputFolderValueLabel = new Label
        {
            Text = "Not set",
            AutoSize = true,
            MaximumSize = new Size(620, 0),
            Font = new Font(Font.FontFamily, 10, FontStyle.Regular)
        };

        var changeFolderButton = new Button
        {
            Text = "Change Folder",
            AutoSize = true,
            Padding = new Padding(10, 6, 10, 6)
        };
        changeFolderButton.Click += (_, _) => PromptForOutputFolder(forcePrompt: true);

        var folderRow = new FlowLayoutPanel
        {
            AutoSize = true,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = true,
            Margin = new Padding(0, 0, 0, 16)
        };
        folderRow.Controls.Add(outputFolderTitleLabel);
        folderRow.Controls.Add(_outputFolderValueLabel);
        folderRow.Controls.Add(changeFolderButton);

        _dropPanel = new Panel
        {
            BorderStyle = BorderStyle.FixedSingle,
            BackColor = Color.White,
            Height = 130,
            Dock = DockStyle.Top,
            AllowDrop = true,
            Margin = new Padding(0, 0, 0, 12)
        };
        _dropPanel.DragEnter += DropPanelOnDragEnter;
        _dropPanel.DragDrop += DropPanelOnDragDrop;
        _dropPanel.DragLeave += (_, _) => _dropPanel.BackColor = Color.White;

        var dropLabel = new Label
        {
            Dock = DockStyle.Fill,
            TextAlign = ContentAlignment.MiddleCenter,
            Font = new Font(Font.FontFamily, 12, FontStyle.Bold),
            Text = "Drop files here",
            ForeColor = Color.FromArgb(40, 40, 40),
            AllowDrop = true
        };
        dropLabel.DragEnter += DropPanelOnDragEnter;
        dropLabel.DragDrop += DropPanelOnDragDrop;
        dropLabel.DragLeave += (_, _) => _dropPanel.BackColor = Color.White;
        _dropPanel.Controls.Add(dropLabel);

        var selectedFilesLabel = new Label
        {
            Text = "Files to Zip",
            AutoSize = true,
            Font = new Font(Font.FontFamily, 10, FontStyle.Bold),
            Margin = new Padding(0, 0, 0, 6)
        };

        _filesListBox = new ListBox
        {
            Dock = DockStyle.Fill,
            HorizontalScrollbar = true,
            IntegralHeight = false,
            Font = new Font(FontFamily.GenericSansSerif, 9.5f)
        };

        var clearFilesButton = new Button
        {
            Text = "Clear Files",
            AutoSize = true,
            Padding = new Padding(10, 6, 10, 6)
        };
        clearFilesButton.Click += (_, _) => ClearSelectedFiles();

        var beginZipButton = new Button
        {
            Text = "Begin Zip",
            AutoSize = true,
            Padding = new Padding(16, 8, 16, 8),
            Font = new Font(Font.FontFamily, 10, FontStyle.Bold)
        };
        beginZipButton.Click += (_, _) => BeginZip();

        _statusLabel = new Label
        {
            Text = "Ready",
            AutoSize = true,
            Font = new Font(Font.FontFamily, 10, FontStyle.Bold),
            ForeColor = Color.FromArgb(24, 88, 24)
        };

        var buttonRow = new FlowLayoutPanel
        {
            AutoSize = true,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            Margin = new Padding(0, 12, 0, 0)
        };
        buttonRow.Controls.Add(beginZipButton);
        buttonRow.Controls.Add(clearFilesButton);

        var contentLayout = new TableLayoutPanel
        {
            Dock = DockStyle.Top,
            AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink,
            ColumnCount = 1,
            RowCount = 8,
            Padding = new Padding(18),
            BackColor = Color.FromArgb(247, 249, 252)
        };

        contentLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        contentLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        contentLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        contentLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 190));
        contentLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        contentLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        contentLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        contentLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));

        contentLayout.Controls.Add(headerLabel, 0, 0);
        contentLayout.Controls.Add(instructionsLabel, 0, 1);
        contentLayout.Controls.Add(folderRow, 0, 2);
        contentLayout.Controls.Add(_dropPanel, 0, 3);
        contentLayout.Controls.Add(selectedFilesLabel, 0, 4);
        contentLayout.Controls.Add(_filesListBox, 0, 5);
        contentLayout.Controls.Add(buttonRow, 0, 6);
        contentLayout.Controls.Add(_statusLabel, 0, 7);

        var scrollContainer = new Panel
        {
            Dock = DockStyle.Fill,
            AutoScroll = true,
            BackColor = Color.FromArgb(247, 249, 252)
        };
        scrollContainer.Controls.Add(contentLayout);

        Controls.Add(scrollContainer);

        Load += (_, _) => PromptForOutputFolder(forcePrompt: false);
    }

    private void DropPanelOnDragEnter(object? sender, DragEventArgs e)
    {
        if (e.Data?.GetDataPresent(DataFormats.FileDrop) == true
            || e.Data?.GetDataPresent(DataFormats.UnicodeText) == true
            || e.Data?.GetDataPresent(DataFormats.Text) == true)
        {
            e.Effect = DragDropEffects.Copy;
            _dropPanel.BackColor = Color.FromArgb(224, 242, 255);
            return;
        }

        e.Effect = DragDropEffects.None;
    }

    private void DropPanelOnDragDrop(object? sender, DragEventArgs e)
    {
        _dropPanel.BackColor = Color.White;

        var droppedItems = CollectDroppedFiles(e.Data);
        if (droppedItems.Count == 0)
        {
            SetStatus("No files were dropped.", isError: true);
            return;
        }

        var files = droppedItems
            .Where(File.Exists)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();

        var fileCountBefore = _selectedFiles.Count;
        foreach (var file in files)
        {
            _selectedFiles.Add(file);
        }

        RefreshFilesList();

        var addedCount = _selectedFiles.Count - fileCountBefore;
        if (addedCount > 0)
        {
            SetStatus($"Added {addedCount} file(s).", isError: false);
        }
        else
        {
            SetStatus("No new files were added.", isError: true);
        }
    }

    private void RefreshFilesList()
    {
        _filesListBox.BeginUpdate();
        _filesListBox.Items.Clear();

        foreach (var file in _selectedFiles.OrderBy(file => file, StringComparer.OrdinalIgnoreCase))
        {
            _filesListBox.Items.Add(file);
        }

        _filesListBox.EndUpdate();
    }

    private void ClearSelectedFiles()
    {
        _selectedFiles.Clear();
        RefreshFilesList();
        SetStatus("File list cleared.", isError: false);
    }

    private void PromptForOutputFolder(bool forcePrompt)
    {
        var existing = _configStore.Load();

        if (!forcePrompt && existing is not null && Directory.Exists(existing.OutputFolder))
        {
            _outputFolder = existing.OutputFolder;
            _outputFolderValueLabel.Text = _outputFolder;
            return;
        }

        using var dialog = new FolderBrowserDialog
        {
            Description = "Choose where finished ZIP files should be saved.",
            UseDescriptionForTitle = true,
            ShowNewFolderButton = true,
            InitialDirectory = Directory.Exists(_outputFolder) ? _outputFolder : Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments)
        };

        var result = dialog.ShowDialog(this);
        if (result == DialogResult.OK && !string.IsNullOrWhiteSpace(dialog.SelectedPath))
        {
            _outputFolder = dialog.SelectedPath;
            Directory.CreateDirectory(_outputFolder);
            _configStore.Save(new AppConfig(_outputFolder));
            _outputFolderValueLabel.Text = _outputFolder;
            SetStatus("Output folder saved.", isError: false);
            return;
        }

        if (string.IsNullOrWhiteSpace(_outputFolder))
        {
            _outputFolderValueLabel.Text = "Not set";
            SetStatus("Please choose an output folder before zipping.", isError: true);
        }
    }

    private void BeginZip()
    {
        if (string.IsNullOrWhiteSpace(_outputFolder) || !Directory.Exists(_outputFolder))
        {
            PromptForOutputFolder(forcePrompt: true);
            if (string.IsNullOrWhiteSpace(_outputFolder) || !Directory.Exists(_outputFolder))
            {
                SetStatus("Output folder is required.", isError: true);
                return;
            }
        }

        if (_selectedFiles.Count == 0)
        {
            SetStatus("Drop at least one file before clicking Begin Zip.", isError: true);
            return;
        }

        try
        {
            var existingFiles = _selectedFiles.Where(File.Exists).ToList();
            var gridFiles = existingFiles
                .Where(file => string.Equals(Path.GetExtension(file), ".grid3user", StringComparison.OrdinalIgnoreCase))
                .ToList();
            var checkinFiles = existingFiles
                .Where(file => !string.Equals(Path.GetExtension(file), ".grid3user", StringComparison.OrdinalIgnoreCase))
                .ToList();

            var createdZipPaths = new List<string>();

            if (gridFiles.Count > 0)
            {
                var gridZipPath = Path.Combine(_outputFolder, GridUserZipName);
                CreateZipFromFiles(gridZipPath, gridFiles);
                createdZipPaths.Add(gridZipPath);
            }

            if (checkinFiles.Count > 0)
            {
                var checkinZipPath = Path.Combine(_outputFolder, CheckinZipName);
                CreateZipFromFiles(checkinZipPath, checkinFiles);
                createdZipPaths.Add(checkinZipPath);
            }

            if (createdZipPaths.Count == 0)
            {
                SetStatus("No valid files were found to zip.", isError: true);
                return;
            }

            SetStatus($"Created {createdZipPaths.Count} ZIP file(s).", isError: false);
            var zipList = string.Join("\n", createdZipPaths);
            MessageBox.Show(this, $"Zip complete!\n\nSaved to:\n{zipList}", "Zip Complete", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex)
        {
            SetStatus($"Zip failed: {ex.Message}", isError: true);
        }
    }

    private static IReadOnlyList<string> CollectDroppedFiles(IDataObject? dataObject)
    {
        var files = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        if (dataObject is null)
        {
            return files.ToList();
        }

        if (dataObject.GetData(DataFormats.FileDrop) is string[] fileDropPaths)
        {
            foreach (var path in fileDropPaths)
            {
                if (!string.IsNullOrWhiteSpace(path))
                {
                    files.Add(path.Trim());
                }
            }
        }

        AddPathsFromText(dataObject.GetData(DataFormats.UnicodeText) as string, files);
        AddPathsFromText(dataObject.GetData(DataFormats.Text) as string, files);

        return files.ToList();
    }

    private static void AddPathsFromText(string? textData, ISet<string> files)
    {
        if (string.IsNullOrWhiteSpace(textData))
        {
            return;
        }

        var lines = textData
            .Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries)
            .Select(line => line.Trim().Trim('"'));

        foreach (var line in lines)
        {
            if (Uri.TryCreate(line, UriKind.Absolute, out var uri) && uri.IsFile)
            {
                files.Add(uri.LocalPath);
                continue;
            }

            if (Path.IsPathRooted(line))
            {
                files.Add(line);
            }
        }
    }

    private static void CreateZipFromFiles(string zipPath, IEnumerable<string> files)
    {
        if (File.Exists(zipPath))
        {
            File.Delete(zipPath);
        }

        using var archive = ZipFile.Open(zipPath, ZipArchiveMode.Create);
        var usedEntryNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var file in files)
        {
            var baseName = Path.GetFileName(file);
            var entryName = BuildUniqueEntryName(baseName, usedEntryNames);
            archive.CreateEntryFromFile(file, entryName, CompressionLevel.Optimal);
        }
    }

    private static string BuildUniqueEntryName(string desiredName, ISet<string> used)
    {
        var name = Path.GetFileNameWithoutExtension(desiredName);
        var extension = Path.GetExtension(desiredName);
        var candidate = desiredName;
        var index = 1;

        while (used.Contains(candidate))
        {
            candidate = $"{name} ({index}){extension}";
            index++;
        }

        used.Add(candidate);
        return candidate;
    }

    private void SetStatus(string message, bool isError)
    {
        _statusLabel.Text = message;
        _statusLabel.ForeColor = isError ? Color.FromArgb(160, 22, 22) : Color.FromArgb(24, 88, 24);
    }
}

internal sealed record AppConfig(
    [property: JsonPropertyName("outputFolder")] string OutputFolder);

internal sealed class AppConfigStore
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    private readonly string _configPath;

    public AppConfigStore()
    {
        var appDataRoot = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "SmartboxZipperSidekick");

        Directory.CreateDirectory(appDataRoot);
        _configPath = Path.Combine(appDataRoot, "config.json");
    }

    public AppConfig? Load()
    {
        if (!File.Exists(_configPath))
        {
            return null;
        }

        try
        {
            var json = File.ReadAllText(_configPath);
            return JsonSerializer.Deserialize<AppConfig>(json, JsonOptions);
        }
        catch
        {
            return null;
        }
    }

    public void Save(AppConfig config)
    {
        var json = JsonSerializer.Serialize(config, JsonOptions);
        File.WriteAllText(_configPath, json);
    }
}

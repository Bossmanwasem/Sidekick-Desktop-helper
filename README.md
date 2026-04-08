# Sidekick Desktop Helper (Windows)

This repo now contains a native messaging desktop helper app for a Chromium extension workflow.

## What it does

- Accepts native messaging commands over `stdin/stdout`.
- Stores an initial setup output folder on first `initialize` request.
- Accepts a `zip_request` with file paths.
- Uses Windows PowerShell `Compress-Archive` to create the zip in the configured output folder.
- Sends a completion message (`zip_complete`) back to the extension so the extension can continue its workflow.

## Native messaging protocol

### Request envelope

```json
{
  "type": "initialize | zip_request | ping",
  "payload": { }
}
```

### Initialize request

```json
{
  "type": "initialize",
  "payload": {
    "outputFolder": "C:/Users/<user>/Downloads/SidekickExports"
  }
}
```

### Zip request

```json
{
  "type": "zip_request",
  "payload": {
    "files": [
      "C:/temp/a.pdf",
      "C:/temp/b.pdf"
    ],
    "zipName": "checkin-2026-04-08",
    "correlationId": "request-123"
  }
}
```

### Zip complete response

```json
{
  "type": "zip_complete",
  "zipPath": "C:/Users/<user>/Downloads/SidekickExports/checkin-2026-04-08.zip",
  "zipName": "checkin-2026-04-08.zip",
  "fileCount": 2,
  "correlationId": "request-123"
}
```

### Error response

```json
{
  "type": "ZipFailed",
  "message": "Compress-Archive failed: ...",
  "correlationId": "request-123"
}
```

## Build

```bash
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
```

## Install (Windows)

### Prerequisites

- Windows 10/11
- .NET SDK 8.0+ (if building from source)
- Microsoft Edge extension ID that will connect to this host

### 1) Build the helper

From the repo root:

```bash
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
```

This produces `SidekickHelper.exe` under:

`bin/Release/net8.0-windows/win-x64/publish/`

### 2) Create the native host manifest

Copy `com.sidekick.helper.json.example` to a stable location (for example `C:\ProgramData\Sidekick\com.sidekick.helper.json`) and update:

- `path` to the full path of `SidekickHelper.exe`
- `allowed_origins` with your actual extension ID

Example:

```json
{
  "name": "com.sidekick.helper",
  "description": "Sidekick Desktop Helper",
  "path": "C:\\ProgramData\\Sidekick\\SidekickHelper.exe",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://<your-edge-extension-id>/"
  ]
}
```

### 3) Register the host in Windows registry

Run PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-host.ps1 -ManifestPath "C:\ProgramData\Sidekick\com.sidekick.helper.json"
```

This writes:

`HKCU\Software\Microsoft\Edge\NativeMessagingHosts\com.sidekick.helper`

with the default value set to your manifest path.

### 4) Verify

- Open `edge://extensions`, ensure your extension is loaded.
- Trigger your extension’s native messaging flow.
- Confirm the helper starts and responds to `ping` / `initialize`.

## Register as native messaging host (Edge)

1. Build/publish the helper app.
2. Create a host manifest JSON (example below) and save it in a stable path.
3. Register the manifest path in Windows Registry:

```reg
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\Microsoft\Edge\NativeMessagingHosts\com.sidekick.helper]
@="C:\\Path\\To\\com.sidekick.helper.json"
```

Manifest template:

```json
{
  "name": "com.sidekick.helper",
  "description": "Sidekick Desktop Helper",
  "path": "C:\\Path\\To\\SidekickHelper.exe",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://<your-edge-extension-id>/"
  ]
}
```

## Notes for your extension repo

Your extension (`Trials-Checkin-Sidekick`) needs to:

- add a background-side native messaging bridge (`chrome.runtime.connectNative('com.sidekick.helper')`),
- send `initialize` once during setup,
- send `zip_request` with absolute file paths,
- wait for `zip_complete` before continuing your workflow.

# Simple File Zipper (Windows)

A clean desktop app for zipping files quickly.

## What the app does

- On first startup, asks the user to choose an **output folder** for finished ZIP files.
- Main screen has a clear **drag-and-drop area** for files.
- User clicks **Begin Zip** to create a ZIP file.
- ZIP file is saved to the selected output folder.

## UI flow

1. Launch the app.
2. Select your output folder (first run only, or click **Change Folder** any time).
3. Drag and drop files into the **Drop files here** area.
4. Click **Begin Zip**.
5. App shows status and a success dialog with the ZIP path.

## Build from source

Prerequisites:

- Windows 10/11
- .NET 8 SDK

From repo root:

```bash
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
```

Published output:

`bin/Release/net8.0-windows/win-x64/publish/SimpleFileZipper.exe`

## Build a full installer (recommended for distribution)

This repo now includes an **Inno Setup** installer project that creates a single `.exe` installer with:

- Program Files installation
- Start menu shortcut
- Optional desktop shortcut
- Uninstaller entry in Windows

### One-time prerequisites

1. Install [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
2. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
3. Ensure `ISCC.exe` is on your system `PATH`

### Build command

From the repo root in PowerShell:

```powershell
.\scripts\build-installer.ps1
```

Installer output:

`dist/SimpleFileZipper-Setup-1.0.0.exe`

You can share that installer file directly with users.

## Alternative: portable build (no installer)

If you only need a portable executable:

```bash
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
```

Share the `SimpleFileZipper.exe` from the publish folder.

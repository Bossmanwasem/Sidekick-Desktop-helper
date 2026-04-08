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

## Install on your PC (easy local install)

If you just want it installed for yourself without MSIX:

1. Build/publish using the command above.
2. Create a folder such as:
   - `C:\Program Files\SimpleFileZipper\`
3. Copy everything from:
   - `bin\Release\net8.0-windows\win-x64\publish\`
   into that install folder.
4. Create a desktop shortcut:
   - Right click `SimpleFileZipper.exe` → **Send to** → **Desktop (create shortcut)**.
5. (Optional) Pin to Start or Taskbar.

That’s it—the app is installed and ready.

## Optional: Create an installer package (MSIX)

If you want a proper installer UX:

1. Open `SidekickHelper.csproj` in Visual Studio 2022.
2. Add a **Windows Application Packaging Project**.
3. Reference this project.
4. Build in **Release** and publish as MSIX.

Use MSIX if you need enterprise-style deployment/signing.

# Smartbox Zipper Sidekick (Windows, Python)

A clean desktop app for zipping files quickly, built with Python.

## What the app does

- On first startup, asks the user to choose an **output folder** for finished ZIP files.
- Main screen provides quick file selection and supports drag/drop, including dragging files from iTunes.
- App uses a Smartbox AAC inspired color theme and bundled install/app icon assets.
- User clicks **Begin Zip** to create one or two ZIP files:
  - `Current Grid User.zip` for `.grid3user` files.
  - `Current Checkin.zip` for all other files.
- ZIP files are saved to the selected output folder.

## UI flow

1. Launch the app.
2. Select your output folder (first run only, or click **Change Folder** any time).
3. Click **Add Files** and choose files to include.
4. Click **Begin Zip**.
5. App shows status and a success dialog with the ZIP path.

## Build from source (Python)

Prerequisites:

- Windows 10/11
- Python 3.11+

Run directly:

```bash
python app.py
```

## Build a full installer (recommended for distribution)

This repo includes an **Inno Setup** installer project and a **Python build script** that creates a single `.exe` installer with:

- Program Files installation
- Start menu shortcut
- Optional desktop shortcut
- Uninstaller entry in Windows

### One-time prerequisites

1. Install Python 3.11+
2. Install build dependency:

   ```bash
   pip install -r requirements-build.txt
   ```

3. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
4. Ensure `ISCC.exe` is on your system `PATH`

### Build command

From the repo root:

```bash
python scripts/build-installer.py
```

The build script expects local icon assets at `assets/install-icon.ico` (Windows executable + setup icon) and `assets/install-icon.png` (in-app window branding). See `assets/README.md` for details.

Installer output:

`dist/SmartboxZipperSidekick-Setup-1.1.0.exe`

You can share that installer file directly with users.

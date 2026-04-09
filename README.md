# Smartbox Vocab Zipper (Python)

A lightweight desktop helper app for quickly zipping and moving Smartbox vocabulary/check-in files.

## What the app does

- Prompts users to connect two folders:
  - **Drop folder**
  - **Final folder**
- Shows how many files are currently in the Drop folder and ready to zip.
- Uses **Zip & Move Files** to package files from Drop and place ZIPs in Final.
- Splits ZIP output into:
  - `Current Grid User.zip` for `.grid3user` files only.
  - `Current Checkin.zip` for all other file types.
- Deletes the original files from the Drop folder after successful zipping.
- Shows a completion prompt that the user can return to the CRM Sidekick Extension.

## Run locally

```bash
python app.py
```

## Notes

- Folder selections are saved to:
  - `%AppData%\SmartboxVocabZipper\config.json`
- Existing ZIP names are overwritten on each run:
  - `Current Grid User.zip`
  - `Current Checkin.zip`

## Package as a desktop app (PyInstaller)

### Prerequisites

- Windows machine
- Python 3.10+ installed

### 1) Install build dependencies

```bash
pip install -r requirements-build.txt
```

### 2) Build the EXE

Run:

```bash
python scripts/build-installer.py --clean
```

This creates `dist/SmartboxVocabZipper.exe`.

### 3) Run on Windows

1. Open `dist/SmartboxVocabZipper.exe`.
2. (Optional) Create a shortcut manually for easier access.

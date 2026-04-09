# Trials Check-in Sidekick Desktop (Python)

A lightweight desktop helper app with Sidekick-style colors/workflow.

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
  - `%AppData%\TrialsCheckinSidekick\config.json`
- Existing ZIP names are overwritten on each run:
  - `Current Grid User.zip`
  - `Current Checkin.zip`

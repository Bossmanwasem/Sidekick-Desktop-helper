from __future__ import annotations

import json
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from zipfile import ZipFile, ZIP_DEFLATED

APP_NAME = "Simple File Zipper"
CONFIG_DIR = Path.home() / "AppData" / "Roaming" / "SimpleFileZipper"
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    output_folder: str


class ConfigStore:
    def load(self) -> AppConfig | None:
        if not CONFIG_PATH.exists():
            return None

        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        output_folder = data.get("output_folder", "").strip()
        if not output_folder:
            return None

        return AppConfig(output_folder=output_folder)

    def save(self, config: AppConfig) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps({"output_folder": config.output_folder}, indent=2),
            encoding="utf-8",
        )


class ZipperApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.minsize(760, 540)
        self.root.geometry("900x640")

        self.config_store = ConfigStore()
        self.output_folder = ""
        self.selected_files: set[str] = set()

        self.status_var = tk.StringVar(value="Ready")
        self.folder_var = tk.StringVar(value="Not set")

        self._build_ui()
        self.root.after(10, lambda: self.prompt_for_output_folder(force_prompt=False))

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, padding=18)
        root_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(root_frame, text=APP_NAME, font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            root_frame,
            text="1) Drop files below or use Add Files.  2) Click Begin Zip.  3) ZIP is saved to output folder.",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 12))

        folder_row = ttk.Frame(root_frame)
        folder_row.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(folder_row, text="Output folder:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(folder_row, textvariable=self.folder_var).pack(side=tk.LEFT, padx=(8, 8))
        ttk.Button(folder_row, text="Change Folder", command=lambda: self.prompt_for_output_folder(True)).pack(side=tk.LEFT)

        drop_row = ttk.Frame(root_frame)
        drop_row.pack(fill=tk.X)
        ttk.Button(drop_row, text="Add Files", command=self.add_files).pack(side=tk.LEFT)
        ttk.Button(drop_row, text="Clear Files", command=self.clear_selected_files).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(root_frame, text="Files to Zip", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 4))

        self.files_list = tk.Listbox(root_frame, font=("Segoe UI", 10))
        self.files_list.pack(fill=tk.BOTH, expand=True)

        bottom_row = ttk.Frame(root_frame)
        bottom_row.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(bottom_row, text="Begin Zip", command=self.begin_zip).pack(side=tk.LEFT)
        ttk.Label(bottom_row, textvariable=self.status_var, foreground="#185818").pack(side=tk.LEFT, padx=(12, 0))

    def set_status(self, message: str, is_error: bool) -> None:
        self.status_var.set(message)

    def refresh_files(self) -> None:
        self.files_list.delete(0, tk.END)
        for file_path in sorted(self.selected_files, key=lambda p: p.lower()):
            self.files_list.insert(tk.END, file_path)

    def add_files(self) -> None:
        files = filedialog.askopenfilenames(parent=self.root, title="Select files to zip")
        if not files:
            return

        before_count = len(self.selected_files)
        for file_path in files:
            path = Path(file_path)
            if path.is_file():
                self.selected_files.add(str(path))

        self.refresh_files()
        added_count = len(self.selected_files) - before_count
        if added_count > 0:
            self.set_status(f"Added {added_count} file(s).", is_error=False)
        else:
            self.set_status("No new files were added.", is_error=True)

    def clear_selected_files(self) -> None:
        self.selected_files.clear()
        self.refresh_files()
        self.set_status("File list cleared.", is_error=False)

    def prompt_for_output_folder(self, force_prompt: bool) -> None:
        existing = self.config_store.load()
        if not force_prompt and existing and Path(existing.output_folder).is_dir():
            self.output_folder = existing.output_folder
            self.folder_var.set(self.output_folder)
            return

        selected = filedialog.askdirectory(
            parent=self.root,
            title="Choose where finished ZIP files should be saved",
            initialdir=self.output_folder or str(Path.home()),
            mustexist=False,
        )

        if selected:
            self.output_folder = selected
            Path(self.output_folder).mkdir(parents=True, exist_ok=True)
            self.config_store.save(AppConfig(output_folder=self.output_folder))
            self.folder_var.set(self.output_folder)
            self.set_status("Output folder saved.", is_error=False)
            return

        if not self.output_folder:
            self.folder_var.set("Not set")
            self.set_status("Please choose an output folder before zipping.", is_error=True)

    def begin_zip(self) -> None:
        if not self.output_folder or not Path(self.output_folder).is_dir():
            self.prompt_for_output_folder(force_prompt=True)
            if not self.output_folder or not Path(self.output_folder).is_dir():
                self.set_status("Output folder is required.", is_error=True)
                return

        if not self.selected_files:
            self.set_status("Add at least one file before clicking Begin Zip.", is_error=True)
            return

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        zip_path = Path(self.output_folder) / f"files-{timestamp}.zip"

        try:
            with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zip_file:
                for file_path in sorted(self.selected_files, key=lambda p: p.lower()):
                    path = Path(file_path)
                    if path.is_file():
                        zip_file.write(path, arcname=path.name)

            self.set_status(f"ZIP created: {zip_path}", is_error=False)
            messagebox.showinfo(APP_NAME, f"Successfully created ZIP:\n{zip_path}")
        except OSError as exc:
            self.set_status("Failed to create ZIP.", is_error=True)
            messagebox.showerror(APP_NAME, f"Unable to create ZIP file.\n\n{exc}")


def main() -> None:
    root = tk.Tk()
    ZipperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from zipfile import ZIP_DEFLATED, ZipFile

APP_NAME = "Smartbox Vocab Zipper"
CONFIG_DIR = Path.home() / "AppData" / "Roaming" / "SmartboxVocabZipper"
CONFIG_PATH = CONFIG_DIR / "config.json"
GRID_USER_EXTENSION = ".grid3user"
GRID_USER_ZIP_NAME = "Current Grid User.zip"
CHECKIN_ZIP_NAME = "Current Checkin.zip"

SIDEKICK_BG = "#121212"
SIDEKICK_NAVY = "#e0e0e0"
SIDEKICK_BLUE = "#81cfff"
SIDEKICK_ORANGE = "#003366"
SIDEKICK_MUTED = "#d5e9ff"
SIDEKICK_INPUT_BG = "#2a2a3a"
SIDEKICK_BORDER = "#81cfff"


@dataclass
class AppConfig:
    drop_folder: str
    final_folder: str


class ConfigStore:
    def load(self) -> AppConfig | None:
        if not CONFIG_PATH.exists():
            return None
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        drop_folder = data.get("drop_folder", "").strip()
        final_folder = data.get("final_folder", "").strip()
        if not drop_folder and not final_folder:
            return None
        return AppConfig(drop_folder=drop_folder, final_folder=final_folder)

    def save(self, config: AppConfig) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(
                {
                    "drop_folder": config.drop_folder,
                    "final_folder": config.final_folder,
                },
                indent=2,
            ),
            encoding="utf-8",
        )


class SidekickDesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("700x400")
        self.root.minsize(680, 360)

        self.config_store = ConfigStore()
        config = self.config_store.load()
        self.drop_folder = config.drop_folder if config else ""
        self.final_folder = config.final_folder if config else ""

        self.drop_folder_var = tk.StringVar(value=self.drop_folder or "Not connected")
        self.final_folder_var = tk.StringVar(value=self.final_folder or "Not connected")
        self.file_count_var = tk.StringVar(value="Files ready to zip: 0")
        self.zip_status_var = tk.StringVar(value="")

        self._apply_theme()
        self._build_ui()
        self.refresh_file_count()

    def _apply_theme(self) -> None:
        self.root.configure(bg=SIDEKICK_BG)
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("Root.TFrame", background=SIDEKICK_BG)
        style.configure("TLabel", background=SIDEKICK_BG, foreground=SIDEKICK_NAVY, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=SIDEKICK_BG, foreground=SIDEKICK_NAVY, font=("Segoe UI", 19, "bold"))
        style.configure("Subtitle.TLabel", background=SIDEKICK_BG, foreground=SIDEKICK_MUTED, font=("Segoe UI", 10))
        style.configure("Field.TLabel", background=SIDEKICK_BG, foreground=SIDEKICK_NAVY, font=("Segoe UI", 10, "bold"))

        style.configure(
            "Primary.TButton",
            background=SIDEKICK_ORANGE,
            foreground="#e0e0e0",
            font=("Segoe UI", 10, "bold"),
            bordercolor=SIDEKICK_BORDER,
            borderwidth=1,
            padding=(12, 7),
        )
        style.map("Primary.TButton", background=[("active", "#005599"), ("pressed", "#002a55")])

        style.configure(
            "Secondary.TButton",
            background=SIDEKICK_BLUE,
            foreground="#121212",
            font=("Segoe UI", 10, "bold"),
            bordercolor=SIDEKICK_BORDER,
            borderwidth=1,
            padding=(12, 7),
        )
        style.map("Secondary.TButton", background=[("active", "#9ad8ff"), ("pressed", "#66bfff")])

        style.configure(
            "TEntry",
            fieldbackground=SIDEKICK_INPUT_BG,
            foreground=SIDEKICK_NAVY,
            bordercolor=SIDEKICK_BORDER,
        )

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, padding=20, style="Root.TFrame")
        root_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(root_frame, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root_frame,
            text="Connect your Drop and Final folders, then zip and move check-in files in one click.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(0, 20))

        self._build_folder_row(
            parent=root_frame,
            label="Drop folder",
            value_var=self.drop_folder_var,
            browse_command=self.select_drop_folder,
        )
        self._build_folder_row(
            parent=root_frame,
            label="Final folder",
            value_var=self.final_folder_var,
            browse_command=self.select_final_folder,
        )

        info_box = ttk.Frame(root_frame, style="Root.TFrame")
        info_box.pack(fill=tk.X, pady=(10, 12))
        ttk.Label(info_box, textvariable=self.file_count_var, style="Field.TLabel").pack(side=tk.LEFT)
        ttk.Button(info_box, text="Refresh", style="Secondary.TButton", command=self.refresh_file_count).pack(side=tk.LEFT, padx=(10, 0))

        actions = ttk.Frame(root_frame, style="Root.TFrame")
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Zip & Move Files", style="Primary.TButton", command=self.zip_and_move_files).pack(side=tk.LEFT)
        ttk.Label(actions, textvariable=self.zip_status_var, style="Field.TLabel").pack(side=tk.LEFT, padx=(12, 0))

    def _build_folder_row(self, parent: ttk.Frame, label: str, value_var: tk.StringVar, browse_command) -> None:
        row = ttk.Frame(parent, style="Root.TFrame")
        row.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(row, text=f"{label}:", style="Field.TLabel", width=12).pack(side=tk.LEFT)
        ttk.Label(row, textvariable=value_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))
        ttk.Button(row, text="Connect", style="Secondary.TButton", command=browse_command).pack(side=tk.RIGHT)

    def select_drop_folder(self) -> None:
        selected = filedialog.askdirectory(parent=self.root, title="Select Drop folder", initialdir=self.drop_folder or str(Path.home()))
        if selected:
            self.drop_folder = selected
            self.drop_folder_var.set(selected)
            self._save_config()
            self.refresh_file_count()

    def select_final_folder(self) -> None:
        selected = filedialog.askdirectory(parent=self.root, title="Select Final folder", initialdir=self.final_folder or str(Path.home()))
        if selected:
            self.final_folder = selected
            self.final_folder_var.set(selected)
            self._save_config()

    def _save_config(self) -> None:
        self.config_store.save(AppConfig(drop_folder=self.drop_folder, final_folder=self.final_folder))

    def _drop_files(self) -> list[Path]:
        if not self.drop_folder:
            return []
        drop_path = Path(self.drop_folder)
        if not drop_path.is_dir():
            return []
        return sorted([path for path in drop_path.iterdir() if path.is_file()], key=lambda p: p.name.lower())

    def refresh_file_count(self) -> None:
        file_count = len(self._drop_files())
        self.file_count_var.set(f"Files ready to zip: {file_count}")

    def zip_and_move_files(self) -> None:
        self.zip_status_var.set("")
        if not self.drop_folder or not Path(self.drop_folder).is_dir():
            messagebox.showerror(APP_NAME, "Please connect a valid Drop folder.")
            return
        if not self.final_folder:
            messagebox.showerror(APP_NAME, "Please connect a Final folder.")
            return

        final_path = Path(self.final_folder)
        final_path.mkdir(parents=True, exist_ok=True)

        files_to_process = self._drop_files()
        if not files_to_process:
            messagebox.showinfo(APP_NAME, "There are no files in the Drop folder to zip.")
            self.refresh_file_count()
            return

        grid_files = [path for path in files_to_process if path.suffix.lower() == GRID_USER_EXTENSION]
        checkin_files = [path for path in files_to_process if path.suffix.lower() != GRID_USER_EXTENSION]

        try:
            self.zip_status_var.set("Zipping files please wait")
            self.root.update_idletasks()

            if grid_files:
                grid_zip_path = final_path / GRID_USER_ZIP_NAME
                self._create_zip(grid_zip_path, grid_files)

            if checkin_files:
                checkin_zip_path = final_path / CHECKIN_ZIP_NAME
                self._create_zip(checkin_zip_path, checkin_files)

            for file_path in files_to_process:
                file_path.unlink()

            self.refresh_file_count()
            self.zip_status_var.set(
                "Finished zipping You can now start your Checkin with the Sidekick extension"
            )
        except OSError as exc:
            self.zip_status_var.set("")
            messagebox.showerror(APP_NAME, f"Unable to complete zipping.\n\n{exc}")

    @staticmethod
    def _create_zip(
        zip_path: Path,
        files: list[Path],
    ) -> None:
        if zip_path.exists():
            zip_path.unlink()

        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zip_file:
            for file_path in files:
                zip_file.write(file_path, arcname=file_path.name)


def main() -> None:
    root = tk.Tk()
    SidekickDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

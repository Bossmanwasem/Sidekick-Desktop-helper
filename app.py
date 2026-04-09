from __future__ import annotations

import json
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from zipfile import ZipFile, ZIP_DEFLATED

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

APP_NAME = "Smartbox Zipper Sidekick"
CONFIG_DIR = Path.home() / "AppData" / "Roaming" / "SmartboxZipperSidekick"
CONFIG_PATH = CONFIG_DIR / "config.json"
GRID_USER_EXTENSION = ".grid3user"
GRID_USER_ZIP_NAME = "Current Grid User.zip"
CHECKIN_ZIP_NAME = "Current Checkin.zip"
SMARTBOXX_ORANGE = "#f7a000"
SMARTBOXX_BLUE = "#24aae2"
SMARTBOXX_NAVY = "#0f2b46"
SMARTBOXX_BG = "#f6fbff"


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
        self.root.minsize(520, 420)
        self.root.geometry("640x500")

        self.config_store = ConfigStore()
        self.output_folder = ""
        self.selected_files: set[str] = set()

        self.status_var = tk.StringVar(value="Ready")
        self.folder_var = tk.StringVar(value="Not set")
        self.icon_image: tk.PhotoImage | None = None
        self._drop_backend = "none"
        self._original_wndproc = None
        self._drop_wndproc = None

        self._apply_theme()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(10, lambda: self.prompt_for_output_folder(force_prompt=False))

    @staticmethod
    def _resource_path(relative_path: str) -> Path:
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            return Path(bundle_root) / relative_path
        return Path(__file__).resolve().parent / relative_path

    def _apply_theme(self) -> None:
        self.root.configure(bg=SMARTBOXX_BG)
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Root.TFrame", background=SMARTBOXX_BG)
        style.configure("TLabel", background=SMARTBOXX_BG, foreground=SMARTBOXX_NAVY, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=SMARTBOXX_BG, foreground=SMARTBOXX_NAVY, font=("Segoe UI", 20, "bold"))
        style.configure(
            "Subtitle.TLabel",
            background=SMARTBOXX_BG,
            foreground="#35516a",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Accent.TButton",
            background=SMARTBOXX_ORANGE,
            foreground="#1b1b1b",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=(12, 7),
        )
        style.map("Accent.TButton", background=[("active", "#ffb32e"), ("pressed", "#df8f00")])
        style.configure(
            "Secondary.TButton",
            background=SMARTBOXX_BLUE,
            foreground="#0b263f",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=(12, 7),
        )
        style.map("Secondary.TButton", background=[("active", "#55bbe8"), ("pressed", "#1798cc")])
        style.configure("StatusOk.TLabel", background=SMARTBOXX_BG, foreground="#16638d", font=("Segoe UI", 10, "bold"))
        style.configure("StatusError.TLabel", background=SMARTBOXX_BG, foreground="#a32626", font=("Segoe UI", 10, "bold"))

        icon_path = None
        for candidate in ("assets/Eye-Gaze.png", "assets/install-icon.png"):
            resolved_path = self._resource_path(candidate)
            if resolved_path.exists():
                icon_path = resolved_path
                break

        if icon_path is not None:
            self.icon_image = tk.PhotoImage(file=str(icon_path))
            self.root.iconphoto(True, self.icon_image)

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, padding=20, style="Root.TFrame")
        root_frame.pack(fill=tk.BOTH, expand=True)

        header_row = ttk.Frame(root_frame, style="Root.TFrame")
        header_row.pack(fill=tk.X, pady=(0, 6))
        if self.icon_image is not None:
            ttk.Label(header_row, image=self.icon_image, style="Root.TFrame").pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(header_row, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root_frame,
            text="1) Drop files below (including from iTunes) or use Add Files.  2) Click Begin Zip.  3) Files are split into Grid User and Checkin ZIPs.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(0, 14))

        folder_row = ttk.Frame(root_frame, style="Root.TFrame")
        folder_row.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(folder_row, text="Output folder:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(folder_row, textvariable=self.folder_var).pack(side=tk.LEFT, padx=(8, 8))
        ttk.Button(
            folder_row,
            text="Change Folder",
            style="Secondary.TButton",
            command=lambda: self.prompt_for_output_folder(True),
        ).pack(side=tk.LEFT)

        drop_row = ttk.Frame(root_frame, style="Root.TFrame")
        drop_row.pack(fill=tk.X)
        ttk.Button(drop_row, text="Add Files", style="Secondary.TButton", command=self.add_files).pack(side=tk.LEFT)
        ttk.Button(
            drop_row,
            text="Clear Files",
            style="Secondary.TButton",
            command=self.clear_selected_files,
        ).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(root_frame, text="Files to Zip", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 4))

        self.files_list = tk.Listbox(
            root_frame,
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg=SMARTBOXX_NAVY,
            selectbackground=SMARTBOXX_BLUE,
            selectforeground="#ffffff",
            highlightthickness=1,
            highlightcolor=SMARTBOXX_BLUE,
            highlightbackground="#b9d7ea",
        )
        self.files_list.pack(fill=tk.BOTH, expand=True)
        self._init_drag_and_drop()

        bottom_row = ttk.Frame(root_frame, style="Root.TFrame")
        bottom_row.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(bottom_row, text="Begin Zip", style="Accent.TButton", command=self.begin_zip).pack(side=tk.LEFT)
        self.status_label = ttk.Label(bottom_row, textvariable=self.status_var, style="StatusOk.TLabel")
        self.status_label.pack(side=tk.LEFT, padx=(12, 0))

    def _init_drag_and_drop(self) -> None:
        """
        Enable file drop support.

        We intentionally use a native Windows implementation (WM_DROPFILES)
        so this remains dependency-free and works with sources like iTunes.
        """
        if sys.platform != "win32":
            self.set_status("Drag/drop is available on Windows builds.", is_error=False)
            return

        try:
            self._enable_windows_drop_target()
            self._drop_backend = "windows-native"
            self.set_status("Drag/drop ready.", is_error=False)
        except Exception:
            self._drop_backend = "none"
            self.set_status("Drag/drop unavailable. Use Add Files.", is_error=True)

    def _enable_windows_drop_target(self) -> None:
        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32

        WM_DROPFILES = 0x0233
        GWL_WNDPROC = -4
        MAX_PATH_CHARS = 32768
        LRESULT = wintypes.LPARAM
        WNDPROC = ctypes.WINFUNCTYPE(
            LRESULT,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        if hasattr(user32, "SetWindowLongPtrW"):
            set_window_long = user32.SetWindowLongPtrW
            set_window_long.restype = wintypes.LPARAM
        else:
            set_window_long = user32.SetWindowLongW
            set_window_long.restype = wintypes.LPARAM

        set_window_long.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.LPARAM)

        call_window_proc = user32.CallWindowProcW
        call_window_proc.restype = wintypes.LPARAM
        call_window_proc.argtypes = (
            wintypes.LPARAM,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        hwnd = self.root.winfo_id()
        shell32.DragAcceptFiles(hwnd, True)

        def wndproc(hwnd, msg, wparam, lparam):
            if msg == WM_DROPFILES:
                dropped_paths = self._extract_windows_drop_paths(wparam, shell32, MAX_PATH_CHARS)
                self.root.after(0, lambda: self._handle_dropped_files(dropped_paths))
                return 0

            return call_window_proc(self._original_wndproc, hwnd, msg, wparam, lparam)

        self._drop_wndproc = WNDPROC(wndproc)
        self._original_wndproc = set_window_long(
            hwnd,
            GWL_WNDPROC,
            ctypes.cast(self._drop_wndproc, ctypes.c_void_p).value,
        )

    @staticmethod
    def _extract_windows_drop_paths(drop_handle: int, shell32, max_chars: int) -> list[str]:
        file_count = shell32.DragQueryFileW(drop_handle, 0xFFFFFFFF, None, 0)
        dropped_paths: list[str] = []

        for index in range(file_count):
            buffer = ctypes.create_unicode_buffer(max_chars)
            shell32.DragQueryFileW(drop_handle, index, buffer, max_chars)
            dropped_paths.append(buffer.value)

        shell32.DragFinish(drop_handle)
        return dropped_paths

    def _handle_dropped_files(self, dropped_paths: list[str]) -> None:
        if not dropped_paths:
            self.set_status("No files were dropped.", is_error=True)
            return

        before_count = len(self.selected_files)
        for file_path in dropped_paths:
            path = Path(file_path)
            if path.is_file():
                self.selected_files.add(str(path))

        self.refresh_files()
        added_count = len(self.selected_files) - before_count
        if added_count > 0:
            self.set_status(f"Added {added_count} dropped file(s).", is_error=False)
        else:
            self.set_status("Dropped items contained no new files.", is_error=True)

    def _on_close(self) -> None:
        if sys.platform == "win32" and self._original_wndproc is not None:
            user32 = ctypes.windll.user32
            set_window_long = user32.SetWindowLongPtrW if hasattr(user32, "SetWindowLongPtrW") else user32.SetWindowLongW
            set_window_long(self.root.winfo_id(), -4, self._original_wndproc)
            self._original_wndproc = None
            self._drop_wndproc = None
        self.root.destroy()

    def set_status(self, message: str, is_error: bool) -> None:
        self.status_var.set(message)
        self.status_label.configure(style="StatusError.TLabel" if is_error else "StatusOk.TLabel")

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

        try:
            existing_files = [Path(file_path) for file_path in sorted(self.selected_files, key=lambda p: p.lower()) if Path(file_path).is_file()]
            grid_files = [path for path in existing_files if path.suffix.lower() == GRID_USER_EXTENSION]
            checkin_files = [path for path in existing_files if path.suffix.lower() != GRID_USER_EXTENSION]

            created_paths: list[Path] = []
            if grid_files:
                grid_zip_path = Path(self.output_folder) / GRID_USER_ZIP_NAME
                self._create_zip(grid_zip_path, grid_files)
                created_paths.append(grid_zip_path)

            if checkin_files:
                checkin_zip_path = Path(self.output_folder) / CHECKIN_ZIP_NAME
                self._create_zip(checkin_zip_path, checkin_files)
                created_paths.append(checkin_zip_path)

            if not created_paths:
                self.set_status("No valid files were found to zip.", is_error=True)
                return

            path_list = "\n".join(str(path) for path in created_paths)
            self.set_status(f"Created {len(created_paths)} ZIP file(s).", is_error=False)
            messagebox.showinfo(APP_NAME, f"Successfully created ZIP file(s):\n{path_list}")
        except OSError as exc:
            self.set_status("Failed to create ZIP.", is_error=True)
            messagebox.showerror(APP_NAME, f"Unable to create ZIP file.\n\n{exc}")

    @staticmethod
    def _create_zip(zip_path: Path, files: list[Path]) -> None:
        if zip_path.exists():
            zip_path.unlink()
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zip_file:
            for path in files:
                zip_file.write(path, arcname=path.name)


def main() -> None:
    root = tk.Tk()
    ZipperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run(command: list[str], cwd: Path) -> None:
    print("+", " ".join(command))
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Python app executable with PyInstaller.")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts before building.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    icon_ico = repo_root / "assets" / "install-icon.ico"
    icon_png = repo_root / "assets" / "install-icon.png"
    if not icon_ico.exists() or not icon_png.exists():
        raise SystemExit(
            "Missing icon assets. Add assets/install-icon.ico and assets/install-icon.png before running the build."
        )

    if args.clean:
        for folder_name in ("build", "dist"):
            target = repo_root / folder_name
            if target.exists():
                shutil.rmtree(target)

    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--windowed",
            "--onefile",
            "--name",
            "SmartboxVocabZipper",
            "--icon",
            str(icon_ico),
            "--add-data",
            f"{icon_png};assets",
            "app.py",
        ],
        cwd=repo_root,
    )

    print("Executable created in dist/")


if __name__ == "__main__":
    main()

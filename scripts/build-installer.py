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


def find_iscc() -> str | None:
    return shutil.which("ISCC.exe") or shutil.which("iscc")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Python app installer.")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts before building.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    iscc = find_iscc()
    if iscc is None:
        raise SystemExit("Inno Setup compiler not found. Install Inno Setup and ensure ISCC.exe is on PATH.")

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
            "SimpleFileZipper",
            "app.py",
        ],
        cwd=repo_root,
    )

    run([iscc, str(repo_root / "installer" / "SimpleFileZipper.iss")], cwd=repo_root)

    print("Installer created in dist/")


if __name__ == "__main__":
    main()

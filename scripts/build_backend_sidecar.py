"""Build the FastAPI sidecar on the current OS for a native Tauri package."""
from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
BINARIES = ROOT / "frontend" / "src-tauri" / "binaries"


def rust_host_triple() -> str:
    output = subprocess.check_output(["rustc", "-vV"], text=True)
    for line in output.splitlines():
        if line.startswith("host: "):
            return line.removeprefix("host: ").strip()
    raise RuntimeError("Could not determine Rust host target triple.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="Rust target triple; defaults to the local Rust host")
    parser.add_argument("--skip-dependency-install", action="store_true")
    args = parser.parse_args()

    if not args.skip_dependency_install:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(BACKEND / "requirements.txt"), "pyinstaller"])

    target = args.target or rust_host_triple()
    extension = ".exe" if platform.system() == "Windows" else ""
    name = f"zeus-backend-{target}"
    output = BINARIES / f"{name}{extension}"
    BINARIES.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    work = ROOT / "build" / "pyinstaller" / "work"
    spec = ROOT / "build" / "pyinstaller" / "spec"
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
        "--name", name, "--paths", str(BACKEND), "--distpath", str(BINARIES),
        "--workpath", str(work), "--specpath", str(spec), str(BACKEND / "main.py"),
    ])
    if not output.exists():
        raise RuntimeError(f"Expected sidecar was not created: {output}")
    print(f"Sidecar ready: {output}")


if __name__ == "__main__":
    main()

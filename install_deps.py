#!/usr/bin/env python3
"""Install missing packages from requirements.txt."""

import subprocess
import sys
import importlib.metadata as metadata
from pathlib import Path
from typing import Optional
import re

REQUIREMENTS_FILE = Path(__file__).parent / "requirements.txt"


def parse_requirements(path: Path) -> list[str]:
    pkgs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "-")):
            pkgs.append(line)
    return pkgs


def is_installed(req: str) -> bool:
    name = re.split(r"[>=<~!;]", req)[0].strip()
    try:
        metadata.distribution(name)
        return True
    except metadata.PackageNotFoundError:
        return False


def get_missing(req_file: Optional[Path] = None) -> tuple[list[str], list[str]]:
    if req_file is None:
        req_file = REQUIREMENTS_FILE
    if not req_file.exists():
        raise FileNotFoundError(f"File not found: {req_file}")

    required = parse_requirements(req_file)
    missing = [r for r in required if not is_installed(r)]
    return required, missing


def install_packages(packages: list[str]) -> None:
    print(f"Installing {len(packages)} package(s): {', '.join(packages)}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + packages,
        )
        print("Done")
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Error installing packages") from e


def main() -> None:
    try:
        required, missing = get_missing()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not required:
        print("No dependencies to install")
        return

    if not missing:
        print("All dependencies are already installed")
        return

    try:
        install_packages(missing)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

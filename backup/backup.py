#!/usr/bin/env python3
"""Backup important files (Documents, Desktop, Downloads, .gitconfig)."""

import argparse
import shutil
import sys
from pathlib import Path
from datetime import datetime


def get_files_to_backup() -> list[Path]:
    home = Path.home()
    items = [
        home / "Documents",
        home / "Desktop",
        home / "Downloads",
        home / ".gitconfig",
    ]
    if sys.platform != "win32":
        items += [home / ".bashrc", home / ".ssh"]

    return [item for item in items if item.exists()]


def backup_files(dest_path: Path, items: list[Path]) -> tuple[Path, int, int]:
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_folder = dest_path / f"backup_{date_str}"
    backup_folder.mkdir(parents=True, exist_ok=True)

    copied = 0
    errors = 0
    for item in items:
        try:
            dest = backup_folder / item.name
            if item.is_file():
                shutil.copy2(item, dest)
            elif item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            copied += 1
        except Exception:
            errors += 1

    return backup_folder, copied, errors


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='backup',
        description='Backup important files',
        epilog='Examples:\n  backup                     # backup to ~/Backup\n  backup --dest D:\\Backup   # backup to D:\\Backup\n  backup --list              # show what will be copied',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--dest', '-d', type=str, default=str(Path.home() / "Backup"),
                        help='Backup destination folder (default: ~/Backup)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List files that would be backed up')
    parser.add_argument('--dry', action='store_true', help='Dry run: show what would be copied')

    args = parser.parse_args()
    dest = Path(args.dest)
    items = get_files_to_backup()

    if args.list or args.dry:
        print("\n Files to backup:")
        for item in items:
            print(f"   {item}")
        print(f"\n   Total: {len(items)} items")
        return

    try:
        backup_folder, copied, errors = backup_files(dest, items)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n Created backup in: {backup_folder}")
    print(f" Copied {copied} of {len(items)} items" +
          (f", errors: {errors}" if errors else ""))


if __name__ == "__main__":
    main()

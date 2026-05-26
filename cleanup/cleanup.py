#!/usr/bin/env python3
"""
Clean old files from Downloads folder
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
import time

try:
    from send2trash import send2trash
    HAS_TRASH = True
except ImportError:
    HAS_TRASH = False

SKIP_FILES = {"desktop.ini", "Thumbs.db", ".DS_Store"}


def find_old_files(path: Path, days: int = 30, skip: Optional[set] = None) -> list[Path]:
    if not path.exists():
        raise FileNotFoundError(f"Folder not found: {path}")
    if days <= 0:
        raise ValueError("days must be greater than 0")

    skip = skip or SKIP_FILES
    now = time.time()
    cutoff = now - (days * 24 * 60 * 60)

    return [
        item for item in path.iterdir()
        if item.is_file() and item.name not in skip and item.stat().st_mtime < cutoff
    ]


def delete_files(files: list[Path], use_trash: bool = False) -> tuple[int, int]:
    if use_trash and not HAS_TRASH:
        raise ImportError("send2trash is not installed. Run: pip install send2trash")

    deleted = 0
    errors = 0
    for item in files:
        try:
            if use_trash:
                send2trash(str(item))
            else:
                item.unlink()
            deleted += 1
        except Exception:
            errors += 1
    return deleted, errors


def main():
    parser = argparse.ArgumentParser(
        prog='cleanup',
        description='Clean old files from Downloads folder',
        epilog='Examples:\n  cleanup 14 --dry     # show files older than 14 days\n  cleanup 30 --trash   # move to recycle bin\n  cleanup 30            # permanently delete',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('days', nargs='?', type=int, default=30,
                        help='File age in days (default: 30)')
    parser.add_argument('--dry', '-d', action='store_true',
                        help='Dry run: only show what would be deleted')
    parser.add_argument('--trash', '-t', action='store_true',
                        help='Move to recycle bin (requires send2trash)')
    parser.add_argument('-y', '--yes', action='store_true',
                        help='Skip confirmation prompt')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    if args.trash and not HAS_TRASH:
        print("Error: send2trash is not installed. Run: pip install send2trash", file=sys.stderr)
        sys.exit(1)

    downloads = Path.home() / "Downloads"

    try:
        files_to_delete = find_old_files(downloads, args.days)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        for item in files_to_delete:
            print(item.name)
    elif not args.dry:
        for item in files_to_delete:
            print(f"Delete: {item.name}")

    if args.dry:
        print(f"\nDry run: {len(files_to_delete)} files would be deleted")
        return

    count = len(files_to_delete)

    if not args.yes and count >= 20:
        warn = ""
        if count >= 100:
            warn = " VERY MANY FILES!"
        elif count >= 20:
            warn = " Quite a lot of files."
        try:
            reply = input(f"Will delete {count} files.{warn} Continue? [y/N]: ").strip().lower()
            if reply not in ("y", "yes"):
                print("Cancelled")
                return
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled")
            return

    deleted, errors = delete_files(files_to_delete, args.trash)
    action = "Moved to trash" if args.trash else "Deleted"
    print(f"\n{action} {deleted} of {count} files older than {args.days} days" +
          (f", errors: {errors}" if errors else ""))


if __name__ == "__main__":
    main()

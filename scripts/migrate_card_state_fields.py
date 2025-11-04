"""One-off migration script to backfill scheduling fields in vocabulary JSON files."""
from __future__ import annotations

import json
import os
from pathlib import Path

from FileWork_v3 import _ensure_card_state  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_DIRECTORIES = [
    REPO_ROOT / "res" / "ListBook",
    REPO_ROOT / "res" / "Vocab List",
]


def migrate_file(path: Path) -> bool:
    """Add missing scheduling fields to all cards in a JSON file."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    updated = False
    for word, info in data.items():
        if word == "XXX":
            continue
        if _ensure_card_state(info):
            updated = True

    if updated:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    return updated


def migrate_directory(directory: Path) -> int:
    """Process all JSON files within a directory tree."""
    count = 0
    if not directory.exists():
        return count

    for root, _, files in os.walk(directory):
        for file_name in files:
            if not file_name.endswith(".json"):
                continue
            file_path = Path(root) / file_name
            if migrate_file(file_path):
                count += 1
                print(f"Updated {file_path}")
    return count


def main() -> None:
    total = 0
    for directory in TARGET_DIRECTORIES:
        total += migrate_directory(directory)
    if total == 0:
        print("No files required migration.")
    else:
        print(f"Migration complete. Updated {total} files.")


if __name__ == "__main__":
    main()

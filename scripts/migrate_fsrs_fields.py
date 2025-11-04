"""Utility to backfill FSRS storage fields in legacy vocabulary JSON files."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Iterator, MutableMapping
from pathlib import Path
from typing import Any, Dict


def _constant(value: Any):
    return lambda: value


DEFAULT_FACTORIES = {
    "stability": _constant(0.0),
    "difficulty": _constant(0.0),
    "last_review": _constant(None),
    "due": _constant(None),
    "new_buried": _constant(False),
    "history": list,
}


def _iter_vocab_files(paths: Iterable[Path]) -> Iterator[Path]:
    for root in paths:
        if not root.exists():
            continue
        if root.is_file() and root.suffix.lower() == ".json":
            yield root
        elif root.is_dir():
            for candidate in sorted(root.rglob("*.json")):
                if candidate.is_file():
                    yield candidate


def _ensure_entry_defaults(entry: MutableMapping[str, Any]) -> bool:
    changed = False
    for field, factory in DEFAULT_FACTORIES.items():
        if field not in entry or entry[field] is None:
            entry[field] = factory()
            changed = True

    if not isinstance(entry.get("history"), list):
        entry["history"] = []
        changed = True
    return changed


def migrate_file(path: Path, dry_run: bool = False) -> bool:
    with path.open("r", encoding="utf-8") as handle:
        payload: Dict[str, Any] = json.load(handle)

    changed = False
    for key, value in payload.items():
        if key == "XXX" or not isinstance(value, MutableMapping):
            continue
        if _ensure_entry_defaults(value):
            changed = True

    if changed and not dry_run:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=4)

    return changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed FSRS scheduling defaults in vocabulary JSON files."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("res/ListBook"), Path("res/Vocab List")],
        help="Files or directories to process (defaults to res/ListBook and res/Vocab List).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing updated files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    targets = list(_iter_vocab_files(args.paths))

    updated = []
    for file_path in targets:
        if migrate_file(file_path, dry_run=args.dry_run):
            updated.append(file_path)

    if args.dry_run:
        action = "would update"
    else:
        action = "updated"

    if updated:
        print(f"{action.capitalize()} {len(updated)} file(s):")
        for file_path in updated:
            print(f" - {file_path}")
    else:
        print("No changes required.")


if __name__ == "__main__":
    main()

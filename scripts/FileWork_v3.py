"""Utilities for loading vocabulary decks and FSRS scheduling state."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import pandas as pd

from scripts.card_state import CardState

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(os.getcwd())
DECK_ROOTS = [Path("res/ListBook"), Path("res/Vocab List")]
STATE_ROOT = Path("res/state")
STATE_FILE = STATE_ROOT / "card_state.jsonl"
LOG_ROOT = Path("res/log")
LOG_FILE = LOG_ROOT / "review_log.jsonl"
DEFAULT_USER_ID = "default"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _normalise_user_id(user_id: Optional[str]) -> str:
    return str(user_id) if user_id not in (None, "") else DEFAULT_USER_ID


def _load_json(path: Path) -> MutableMapping[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4, ensure_ascii=False)


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    _ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def _state_record_key(record: Mapping[str, Any]) -> Tuple[str, str]:
    user_id = _normalise_user_id(record.get("user_id"))
    card_id = record.get("card_id") or record.get("word")
    if not card_id:
        raise ValueError("State records must define a card_id or word")
    return user_id, str(card_id)


def _state_to_record(state: CardState, *, user_id: Optional[str] = None) -> Dict[str, Any]:
    key_user = _normalise_user_id(user_id or state.user_id)
    card_id = state.card_id or state.word
    payload = state.to_storage_dict()
    payload.setdefault("word", state.word)
    payload.setdefault("card_id", card_id)
    return {
        "user_id": key_user,
        "card_id": card_id,
        "word": state.word,
        "state": payload,
    }


def _record_to_state(record: Mapping[str, Any]) -> CardState:
    word = record.get("word") or record.get("card_id")
    if not word:
        raise ValueError("Invalid state record without word")
    payload = record.get("state")
    if isinstance(payload, Mapping):
        data = dict(payload)
    else:
        data = {
            key: value
            for key, value in record.items()
            if key not in {"user_id", "card_id", "word"}
        }
    state = CardState.from_storage(word, data)
    if record.get("card_id"):
        state.card_id = str(record["card_id"])
    user_id = record.get("user_id")
    if user_id not in (None, ""):
        state.user_id = str(user_id)
    else:
        state.user_id = None
    return state


# ---------------------------------------------------------------------------
# Deck import helpers
# ---------------------------------------------------------------------------

def importFromExcel(path: str) -> List[str]:
    """Import Excel vocabulary lists from *path* into JSON decks."""

    folder_path = REPO_ROOT / path
    if not folder_path.exists():
        raise FileNotFoundError(f"Excel directory not found: {folder_path}")

    excel_names = [name for name in os.listdir(folder_path) if name.endswith(".xlsx")]
    vocab_paths: List[Path] = []
    for name in excel_names:
        file_path = folder_path / name
        if not file_path.exists():
            raise FileNotFoundError(f"Vocab list file '{name}' is missing")
        vocab_paths.append(file_path)

    vocab_lists: List[List[Sequence[str]]] = []
    for excel_path in vocab_paths:
        frame = pd.read_excel(excel_path)
        entries: List[Sequence[str]] = []
        for _, row in frame.iterrows():
            vocab = row.get("Vocab:")
            if pd.isna(vocab):
                break
            translation = row.get("Translation:")
            example = row.get("Example sentence:")
            entries.append([str(vocab), str(translation or ""), str(example or "")])
        if not entries:
            entries.append(["This vocab list is empty", "N/A", "N/A"])
        vocab_lists.append(entries)

    created_files: List[str] = []
    for vocab_list, name in zip(vocab_lists, excel_names):
        output = Path("res/Vocab List") / f"{name}.json"
        writeIntoJson(vocab_list, str(output))
        created_files.append(str(output))
    return created_files


def is_list_empty(lst: Sequence[Any]) -> bool:
    return not lst


# ---------------------------------------------------------------------------
# Deck JSON storage
# ---------------------------------------------------------------------------

def _ensure_card_state(entry: Any) -> CardState:
    if isinstance(entry, CardState):
        return entry
    if isinstance(entry, Mapping):
        word = entry.get("word") or entry.get("card_id")
        if not word:
            raise ValueError(
                "Cannot convert dictionary entry to CardState without a word key"
            )
        return CardState.from_storage(word, entry)
    if isinstance(entry, Sequence) and not isinstance(entry, (str, bytes)) and len(entry) >= 3:
        return CardState.from_components(entry[0], entry[1], entry[2])
    raise TypeError("Unsupported vocab entry format")


def writeIntoJson(vocab_list: Iterable[Any], path: str) -> None:
    vocab: Dict[str, Any] = {}
    for entry in vocab_list:
        card_state = _ensure_card_state(entry)
        vocab[card_state.word] = {
            "definition": card_state.definition,
            "example": card_state.example,
            "card_id": card_state.card_id,
        }
    deck_path = Path(path)
    deck_info = {
        "Name": deck_path.stem,
        "CurrentNum": 1,
        "Completed": False,
        "Learning": False,
    }
    vocab["XXX"] = deck_info
    _write_json(deck_path, vocab)


def _load_vocab_payload(path: str) -> MutableMapping[str, Any]:
    return _load_json(Path(path))


def _write_vocab_payload(path: str, payload: Mapping[str, Any]) -> None:
    _write_json(Path(path), payload)


def _index_states_for_user(user_id: Optional[str]) -> Dict[Tuple[str, str], CardState]:
    records = _read_jsonl(STATE_FILE)
    indexed: Dict[Tuple[str, str], CardState] = {}
    for record in records:
        state = _record_to_state(record)
        key_user = _normalise_user_id(user_id)
        record_user = _normalise_user_id(state.user_id)
        if user_id is not None and record_user != key_user:
            continue
        card_key = state.card_id or state.word
        indexed[(record_user, card_key)] = state
        indexed[(record_user, state.word)] = state
    return indexed


def _resolve_stored_state(
    indexed: Mapping[Tuple[str, str], CardState],
    user_id: Optional[str],
    card: CardState,
) -> Optional[CardState]:
    key_user = _normalise_user_id(user_id)
    primary_key = (key_user, card.card_id or card.word)
    if primary_key in indexed:
        return indexed[primary_key]
    secondary_key = (key_user, card.word)
    return indexed.get(secondary_key)


def readFromJson(path: str, user_id: Optional[str] = None):
    payload = _load_vocab_payload(path)
    vocab_list: List[CardState] = []
    list_info = None
    stored_states = _index_states_for_user(user_id)

    for word, data in payload.items():
        if word == "XXX":
            list_info = [
                data.get("Name"),
                data.get("CurrentNum", 1),
                data.get("Completed", False),
                data.get("Learning", False),
            ]
            continue
        card_state = CardState.from_storage(word, data if isinstance(data, Mapping) else {})
        if user_id is not None:
            stored = _resolve_stored_state(stored_states, user_id, card_state)
        else:
            stored = _resolve_stored_state(stored_states, DEFAULT_USER_ID, card_state)
        if stored:
            stored.definition = card_state.definition or stored.definition
            stored.example = card_state.example or stored.example
            stored.word = card_state.word or stored.word
            card_state = stored
        vocab_list.append(card_state)

    if list_info is None:
        return vocab_list
    return vocab_list, list_info


def update_card_state(path: str, word_id: str, state: Any) -> None:
    card_state = _ensure_card_state(state)
    payload = _load_vocab_payload(path)
    if word_id not in payload:
        raise KeyError(f"Card '{word_id}' not found in {path}")
    payload[word_id] = card_state.to_storage_dict()
    _write_vocab_payload(path, payload)


def getListInfo(path: str):
    result = readFromJson(path)
    if isinstance(result, tuple):
        return result[1]
    return None


def writeListInfo(
    path: str,
    name: Optional[str] = None,
    currentNum: Optional[int] = None,
    completed: Optional[bool] = None,
    learning: Optional[bool] = None,
) -> None:
    data = _load_vocab_payload(path)
    deck_info = data.setdefault(
        "XXX",
        {
            "Name": Path(path).stem,
            "CurrentNum": 1,
            "Completed": False,
            "Learning": False,
        },
    )
    if name is not None:
        deck_info["Name"] = name
    if currentNum is not None:
        deck_info["CurrentNum"] = currentNum
    if completed is not None:
        deck_info["Completed"] = completed
    if learning is not None:
        deck_info["Learning"] = learning
    _write_vocab_payload(path, data)


def checkExist(path: str) -> bool:
    return Path(path).exists()


def getFileName() -> List[str]:
    files: List[str] = []
    for root in DECK_ROOTS[1:]:
        if not root.exists():
            continue
        for file_path in root.iterdir():
            if file_path.is_file() and file_path.suffix == ".json":
                files.append(str(file_path))
    return files


# ---------------------------------------------------------------------------
# Card state store (JSONL)
# ---------------------------------------------------------------------------

def load_card_states(user_id: Optional[str] = None) -> Dict[str, CardState]:
    indexed = _index_states_for_user(user_id)
    key_user = _normalise_user_id(user_id)
    return {
        card_key: state
        for (user_key, card_key), state in indexed.items()
        if user_key == key_user
    }


def save_card_state(state: CardState, *, user_id: Optional[str] = None) -> CardState:
    record = _state_to_record(state, user_id=user_id)
    records = _read_jsonl(STATE_FILE)
    key = _state_record_key(record)
    updated = False
    for stored in records:
        if _state_record_key(stored) == key:
            stored.update(record)
            updated = True
            break
    if not updated:
        records.append(record)
    _write_jsonl(STATE_FILE, records)
    return _record_to_state(record)


def save_card_states(states: Iterable[CardState], *, user_id: Optional[str] = None) -> None:
    records = _read_jsonl(STATE_FILE)
    record_map = {_state_record_key(record): record for record in records}
    for state in states:
        record = _state_to_record(state, user_id=user_id)
        record_map[_state_record_key(record)] = record
    _write_jsonl(STATE_FILE, record_map.values())


def append_review_log(log_entry: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(log_entry, Mapping):
        raise TypeError("log_entry must be a mapping containing card metadata")
    record = dict(log_entry)
    record.setdefault("logged_at", _utc_now().isoformat().replace("+00:00", "Z"))
    required = {"user_id", "card_id", "grade", "interval_days", "success", "w_version"}
    missing = [field for field in required if field not in record]
    if missing:
        raise ValueError(f"log_entry is missing required fields: {', '.join(missing)}")
    before = record.get("before_state")
    after = record.get("after_state")
    if isinstance(before, CardState):
        record["before_state"] = before.to_storage_dict()
    if isinstance(after, CardState):
        record["after_state"] = after.to_storage_dict()
    _ensure_parent(LOG_FILE)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False))
        handle.write("\n")
    return record


# ---------------------------------------------------------------------------
# Migration utilities
# ---------------------------------------------------------------------------

def _iter_deck_files(paths: Optional[Iterable[Path]] = None) -> Iterator[Path]:
    roots = list(paths) if paths is not None else DECK_ROOTS
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix == ".json":
            yield root
        elif root.is_dir():
            for candidate in sorted(root.rglob("*.json")):
                if candidate.is_file():
                    yield candidate


def migrate_decks_to_state_store(
    user_id: Optional[str] = None,
    *,
    default_phase: str = "new",
    default_w_version: Optional[str] = None,
    paths: Optional[Iterable[Path]] = None,
) -> List[Path]:
    updated: List[Path] = []
    for deck_path in _iter_deck_files(paths):
        payload = _load_json(deck_path)
        changed = False
        for word, data in payload.items():
            if word == "XXX" or not isinstance(data, Mapping):
                continue
            state = CardState.from_storage(word, data)
            if not state.phase:
                state.phase = default_phase
            if state.w_version is None and default_w_version is not None:
                state.w_version = str(default_w_version)
            if state.due_at is None and state.phase in {"learning", "review"}:
                state.due_at = _utc_now()
            state.user_id = user_id or state.user_id
            save_card_state(state, user_id=user_id)
            changed = True
        if changed:
            updated.append(deck_path)
    return updated


__all__ = [
    "append_review_log",
    "checkExist",
    "getFileName",
    "getListInfo",
    "importFromExcel",
    "is_list_empty",
    "load_card_states",
    "migrate_decks_to_state_store",
    "readFromJson",
    "save_card_state",
    "save_card_states",
    "update_card_state",
    "writeIntoJson",
    "writeListInfo",
]

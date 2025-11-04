from __future__ import annotations

import json
import math
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _default_state() -> Dict[str, Any]:
    now = _utc_now()
    return {
        "due": _format_datetime(now),
        "last_review": None,
        "stability": 0.5,
        "difficulty": 5.0,
        "reps": 0,
        "lapses": 0,
        "state": "new",
    }


def ensure_state(raw_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    state = dict(_default_state())
    if raw_state:
        state.update(raw_state)
    # Normalize timestamps so later calculations work reliably.
    if isinstance(state.get("last_review"), datetime):
        state["last_review"] = _format_datetime(state["last_review"])
    if isinstance(state.get("due"), datetime):
        state["due"] = _format_datetime(state["due"])
    return state


@dataclass
class Card:
    word: str
    definition: str
    example: str
    path: str
    state: Dict[str, Any] = field(default_factory=_default_state)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_option(self) -> List[str]:
        return [self.word, self.definition, self.example]

    def due_datetime(self) -> datetime:
        due = _parse_datetime(self.state.get("due"))
        if due is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        return due

    def is_due(self, reference: Optional[datetime] = None) -> bool:
        reference = reference or _utc_now()
        return self.due_datetime() <= reference


class FSRSScheduler:
    """Light-weight FSRS style scheduler.

    The implementation keeps the same rating scale as FSRS (Again/Hard/Good/Easy)
    and tracks card attributes that are compatible with the original algorithm.
    The actual interval calculation is intentionally simplified – it favours the
    requested retention behaviour while keeping the code compact for this
    project.  States produced here stay compatible with future improvements
    because all relevant attributes are persisted in JSON.
    """

    RATING_MAP: Dict[str, int] = {
        "again": 0,
        "hard": 1,
        "good": 2,
        "easy": 3,
    }

    def __init__(self, request_retention: float = 0.9) -> None:
        self.request_retention = request_retention

    def now(self) -> datetime:
        return _utc_now()

    def review(self, card: Card, rating: str, *, now: Optional[datetime] = None) -> Dict[str, Any]:
        now = now or self.now()
        rating_value = self.RATING_MAP[rating]

        state = ensure_state(card.state)
        last_review = _parse_datetime(state.get("last_review"))
        stability = float(state.get("stability", 0.5))
        difficulty = float(state.get("difficulty", 5.0))
        reps = int(state.get("reps", 0))
        lapses = int(state.get("lapses", 0))

        elapsed = 0.0
        if last_review is not None:
            elapsed = max((now - last_review).total_seconds() / 86400.0, 0.0)

        retrievability = self.request_retention
        if stability > 0 and elapsed > 0:
            retrievability = math.exp(math.log(self.request_retention) * (elapsed / stability))

        if reps == 0:
            difficulty = _clamp(5.0 + (rating_value - 1) * 1.5, 1.0, 10.0)
            initial_stabilities = [0.2, 0.7, 2.5, 4.0]
            stability = initial_stabilities[rating_value]
        else:
            difficulty = _clamp(difficulty + (rating_value - 1.5) * 0.15, 1.0, 10.0)
            if rating_value == 0:
                lapses += 1
                stability = max(0.2, stability * 0.4)
            else:
                growth_factor = {1: 0.9, 2: 1.6, 3: 2.5}[rating_value]
                stability = max(
                    0.2,
                    stability + growth_factor * (1.0 - retrievability + 0.2),
                )

        if rating_value == 0:
            due = now
        else:
            due = now + timedelta(days=max(stability, 0.01))

        state.update(
            {
                "stability": stability,
                "difficulty": difficulty,
                "due": _format_datetime(due),
                "last_review": _format_datetime(now),
                "reps": reps + 1,
                "lapses": lapses,
                "state": "review" if reps > 0 or rating_value > 0 else "learning",
            }
        )

        card.state = state
        return state


def load_cards(paths: Iterable[str]) -> List[Card]:
    cards: List[Card] = []
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        for word, payload in data.items():
            if word == "XXX":
                continue
            state = ensure_state(payload.get("srs"))
            extra = {
                key: value
                for key, value in payload.items()
                if key not in {"definition:", "example:", "srs"}
            }
            cards.append(
                Card(
                    word=word,
                    definition=payload.get("definition:", ""),
                    example=payload.get("example:", ""),
                    path=path,
                    state=state,
                    extra=extra,
                )
            )
    return cards


def save_cards(cards: Iterable[Card]) -> None:
    cards_by_path: Dict[str, List[Card]] = {}
    for card in cards:
        cards_by_path.setdefault(card.path, []).append(card)

    for path, path_cards in cards_by_path.items():
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        for card in path_cards:
            entry = data.get(card.word, {})
            entry["definition:"] = card.definition
            entry["example:"] = card.example
            entry["srs"] = ensure_state(card.state)
            for key, value in card.extra.items():
                entry.setdefault(key, value)
            data[card.word] = entry
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=4)


def filter_due_cards(cards: Iterable[Card], *, now: Optional[datetime] = None) -> List[Card]:
    now = now or _utc_now()
    return sorted(
        [card for card in cards if card.is_due(now)],
        key=lambda card: (card.due_datetime(), card.word),
    )


def sort_by_due(cards: Iterable[Card]) -> List[Card]:
    return sorted(cards, key=lambda card: (card.due_datetime(), card.word))


def pick_options(all_cards: List[Card], correct_card: Card, *, option_size: int = 4) -> List[List[str]]:
    pool = [card for card in all_cards if card is not correct_card]
    random.shuffle(pool)
    selected = pool[: max(0, option_size - 1)]
    selected.append(correct_card)
    random.shuffle(selected)
    return [card.to_option() for card in selected]

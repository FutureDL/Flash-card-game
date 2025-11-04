"""Utilities for FSRS-inspired spaced repetition scheduling."""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

SECONDS_IN_DAY = 86400


@dataclass
class CardState:
    """Represents the scheduling state of a flashcard."""

    stability: float  # approximate interval (days)
    difficulty: float  # 1 (easiest) .. 10 (hardest)
    due: float  # unix timestamp for next review
    reps: int  # total reviews (including relearning)
    lapses: int  # number of times the card was forgotten
    state: str  # "new", "review", or "relearning"
    last_review: float  # unix timestamp of previous review

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


DEFAULT_DIFFICULTY = 5.0
MIN_STABILITY = 0.2

NEW_INTERVALS = {
    "again": 0.2,
    "hard": 1.0,
    "good": 1.5,
    "easy": 3.0,
}

STABILITY_GROWTH = {
    "hard": 1.2,
    "good": 1.7,
    "easy": 2.5,
}

DIFFICULTY_DRIFT = {
    "again": 0.6,
    "hard": 0.3,
    "good": -0.1,
    "easy": -0.5,
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def now_timestamp() -> float:
    return time.time()


def default_card_state(now: Optional[float] = None) -> CardState:
    """Return the initial scheduling state for a new card."""

    current = now if now is not None else now_timestamp()
    return CardState(
        stability=0.0,
        difficulty=DEFAULT_DIFFICULTY,
        due=current,
        reps=0,
        lapses=0,
        state="new",
        last_review=0.0,
    )


def card_state_from_dict(data: Optional[Dict[str, Any]]) -> CardState:
    """Create a :class:`CardState` from raw dictionary data."""

    if not data:
        return default_card_state()

    # Some legacy saves might store numbers as strings; attempt safe casting.
    def _to_float(value: Any, fallback: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    def _to_int(value: Any, fallback: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    return CardState(
        stability=_to_float(data.get("stability"), 0.0),
        difficulty=_to_float(data.get("difficulty"), DEFAULT_DIFFICULTY),
        due=_to_float(data.get("due"), now_timestamp()),
        reps=_to_int(data.get("reps"), 0),
        lapses=_to_int(data.get("lapses"), 0),
        state=str(data.get("state", "new")),
        last_review=_to_float(data.get("last_review"), 0.0),
    )


def is_due(state: CardState, now: Optional[float] = None) -> bool:
    current = now if now is not None else now_timestamp()
    return state.due <= current + 1  # allow 1 second tolerance


def schedule(state: CardState, rating: str, now: Optional[float] = None) -> CardState:
    """Return an updated :class:`CardState` based on the review rating."""

    current = now if now is not None else now_timestamp()
    normalized = rating.lower()
    if normalized not in {"again", "hard", "good", "easy"}:
        raise ValueError(f"Unsupported rating '{rating}'.")

    elapsed_days = 0.0
    if state.last_review > 0:
        elapsed_days = max(0.0, (current - state.last_review) / SECONDS_IN_DAY)

    if normalized == "again":
        new_stability = max(MIN_STABILITY, NEW_INTERVALS["again"])
        new_state = CardState(
            stability=new_stability,
            difficulty=clamp(state.difficulty + DIFFICULTY_DRIFT["again"], 1.0, 10.0),
            due=current + new_stability * SECONDS_IN_DAY,
            reps=state.reps + 1,
            lapses=state.lapses + 1,
            state="relearning",
            last_review=current,
        )
        return new_state

    # For other ratings we treat the card as successfully recalled
    retriev_prob = 1.0
    if state.stability > 0:
        retriev_prob = math.exp(-elapsed_days / max(state.stability, 0.001))

    previous_stability = state.stability
    if previous_stability <= 0:
        previous_stability = NEW_INTERVALS[normalized]

    growth = STABILITY_GROWTH[normalized]
    new_stability = max(MIN_STABILITY, previous_stability * growth)
    # Adjust by how confident the user still was at review time
    adjustment = max(0.5, 1.0 + 0.2 * (1.0 - retriev_prob))
    new_stability *= adjustment

    new_state = CardState(
        stability=new_stability,
        difficulty=clamp(state.difficulty + DIFFICULTY_DRIFT[normalized], 1.0, 10.0),
        due=current + new_stability * SECONDS_IN_DAY,
        reps=state.reps + 1,
        lapses=state.lapses,
        state="review",
        last_review=current,
    )
    return new_state


def describe_due(state: CardState, now: Optional[float] = None) -> str:
    """Return a human readable description of when the card is due."""

    current = now if now is not None else now_timestamp()
    delta = state.due - current

    if delta <= 0:
        return "due now"

    minutes = delta / 60
    hours = delta / 3600
    days = delta / SECONDS_IN_DAY

    if minutes < 1:
        return "in under a minute"
    if minutes < 60:
        return f"in {int(round(minutes))} minute(s)"
    if hours < 24:
        return f"in {int(round(hours))} hour(s)"
    if days < 7:
        return f"in {int(round(days))} day(s)"

    due_time = datetime.fromtimestamp(state.due, tz=timezone.utc)
    return f"on {due_time.strftime('%Y-%m-%d %H:%M UTC')}"


def next_review_message(state: Optional[CardState]) -> str:
    if state is None:
        return "No upcoming reviews"
    return f"Next review {describe_due(state)}"


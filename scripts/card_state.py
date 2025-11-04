"""Domain model for flashcard scheduling state.

This module defines :class:`CardState`, a dataclass that stores the UI and
FSRS (Free Spaced Repetition Scheduler) attributes for a vocabulary card.
It also provides helpers for serialising the state to and from the JSON
records that the rest of the application persists to disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Sequence


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Convert a JSON field into a :class:`datetime` if possible."""

    if value in (None, "", 0):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        # Treat numeric timestamps as POSIX seconds.
        try:
            return datetime.fromtimestamp(value)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _format_datetime(value: Optional[datetime]) -> Optional[str]:
    """Serialise a datetime in ISO-8601 format for JSON storage."""

    if value is None:
        return None
    return value.isoformat()


@dataclass
class CardState:
    """State container for a single flashcard.

    Parameters
    ----------
    word:
        The vocabulary word displayed on the front of the card.
    definition:
        The associated definition shown on the back of the card.
    example:
        Example sentence(s) for the word.
    card_id:
        Optional persistent identifier. Defaults to the word itself.
    stability / difficulty / due / last_review / lapses / repetitions:
        FSRS scheduling attributes tracked per card.
    custom_data / metadata:
        Containers for scheduler specific state that we do not interpret yet.
    """

    word: str
    definition: str
    example: str
    card_id: Optional[str] = None
    stability: float = 0.0
    difficulty: float = 0.0
    due: Optional[datetime] = None
    last_review: Optional[datetime] = None
    lapses: int = 0
    repetitions: int = 0
    new_buried: bool = False
    history: List[Dict[str, Any]] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.card_id is None:
            self.card_id = self.word

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_components(
        cls,
        word: str,
        definition: str,
        example: str,
        **kwargs: Any,
    ) -> "CardState":
        """Construct a card state from the basic UI components."""

        return cls(word=word, definition=definition, example=example, **kwargs)

    @classmethod
    def from_storage(cls, word: str, payload: Mapping[str, Any]) -> "CardState":
        """Create a :class:`CardState` instance from a JSON record."""

        definition = payload.get("definition") or payload.get("definition:") or ""
        example = payload.get("example") or payload.get("example:") or ""
        card_id = payload.get("card_id") or word
        stability = float(payload.get("stability", 0.0) or 0.0)
        difficulty = float(payload.get("difficulty", 0.0) or 0.0)
        due = _parse_datetime(payload.get("due"))
        last_review = _parse_datetime(payload.get("last_review"))
        lapses = int(payload.get("lapses", 0) or 0)
        repetitions = int(
            payload.get("repetitions", payload.get("reviews", 0) or 0) or 0
        )
        custom_data = dict(payload.get("custom_data", {}))
        new_buried = bool(payload.get("new_buried", False))
        raw_history = payload.get("history", [])
        history: List[Dict[str, Any]] = []
        if isinstance(raw_history, Sequence) and not isinstance(
            raw_history, (str, bytes)
        ):
            for entry in raw_history:
                if isinstance(entry, Mapping):
                    history.append(dict(entry))
                else:
                    history.append({"value": entry})

        state = cls(
            word=word,
            definition=definition,
            example=example,
            card_id=card_id,
            stability=stability,
            difficulty=difficulty,
            due=due,
            last_review=last_review,
            lapses=lapses,
            repetitions=repetitions,
            new_buried=new_buried,
            history=history,
            custom_data=custom_data,
        )

        known_keys = {
            "definition",
            "definition:",
            "example",
            "example:",
            "card_id",
            "stability",
            "difficulty",
            "due",
            "last_review",
            "lapses",
            "repetitions",
            "reviews",
            "new_buried",
            "history",
            "custom_data",
            "metadata",
        }

        metadata = dict(payload.get("metadata", {}))
        extras = {k: v for k, v in payload.items() if k not in known_keys}
        if extras:
            metadata.update(extras)
        state.metadata = metadata
        return state

    def update_from_storage(self, payload: Mapping[str, Any]) -> None:
        """Mutate the instance in-place with values from a JSON record."""

        if "definition" in payload or "definition:" in payload:
            self.definition = payload.get("definition", payload.get("definition:")) or self.definition
        if "example" in payload or "example:" in payload:
            self.example = payload.get("example", payload.get("example:")) or self.example
        if "card_id" in payload:
            self.card_id = payload.get("card_id") or self.card_id
        if "stability" in payload:
            self.stability = float(payload.get("stability") or 0.0)
        if "difficulty" in payload:
            self.difficulty = float(payload.get("difficulty") or 0.0)
        if "due" in payload:
            self.due = _parse_datetime(payload.get("due"))
        if "last_review" in payload:
            self.last_review = _parse_datetime(payload.get("last_review"))
        if "lapses" in payload:
            self.lapses = int(payload.get("lapses") or 0)
        if "repetitions" in payload or "reviews" in payload:
            self.repetitions = int(
                payload.get("repetitions", payload.get("reviews", 0) or 0) or 0
            )
        if "new_buried" in payload:
            self.new_buried = bool(payload.get("new_buried"))
        if "history" in payload:
            raw_history = payload.get("history", [])
            coerced: List[Dict[str, Any]] = []
            if isinstance(raw_history, Sequence) and not isinstance(
                raw_history, (str, bytes)
            ):
                for entry in raw_history:
                    if isinstance(entry, Mapping):
                        coerced.append(dict(entry))
                    else:
                        coerced.append({"value": entry})
            self.history = coerced
        if "custom_data" in payload:
            self.custom_data = dict(payload.get("custom_data", {}))
        if "metadata" in payload:
            self.metadata = dict(payload.get("metadata", {}))

        known_keys = {
            "definition",
            "definition:",
            "example",
            "example:",
            "card_id",
            "stability",
            "difficulty",
            "due",
            "last_review",
            "lapses",
            "repetitions",
            "reviews",
            "new_buried",
            "history",
            "custom_data",
            "metadata",
        }
        extras = {k: v for k, v in payload.items() if k not in known_keys}
        if extras:
            self.metadata.update(extras)

    def to_storage_dict(self) -> Dict[str, Any]:
        """Serialise the state into a JSON friendly dictionary."""

        serialised_history: List[Dict[str, Any]] = []
        for entry in self.history:
            if isinstance(entry, Mapping):
                serialised_history.append(dict(entry))
            else:
                serialised_history.append({"value": entry})

        data: Dict[str, Any] = {
            "definition:": self.definition,
            "example:": self.example,
            "card_id": self.card_id,
            "stability": self.stability,
            "difficulty": self.difficulty,
            "due": _format_datetime(self.due),
            "last_review": _format_datetime(self.last_review),
            "lapses": self.lapses,
            "repetitions": self.repetitions,
            "new_buried": self.new_buried,
            "history": serialised_history,
        }
        if self.custom_data:
            data["custom_data"] = self.custom_data
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def to_vocab_row(self) -> Sequence[str]:
        """Return the legacy `[word, definition, example]` triple."""

        return [self.word, self.definition, self.example]

    def replace(self, **changes: Any) -> "CardState":
        """Return a new instance with *changes* applied."""

        return replace(self, **changes)


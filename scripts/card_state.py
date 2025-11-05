"""Domain model for flashcard scheduling state.

This module defines :class:`CardState`, a dataclass that stores the UI and
FSRS (Free Spaced Repetition Scheduler) attributes for a vocabulary card.
It also provides helpers for serialising the state to and from the JSON
records that the rest of the application persists to disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence


def _ensure_utc(value: datetime) -> datetime:
    """Normalise *value* to a UTC timezone aware datetime."""

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Convert a JSON field into a :class:`datetime` in UTC if possible."""

    if value in (None, "", 0):
        return None
    if isinstance(value, datetime):
        return _ensure_utc(value)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            if text.endswith("Z"):
                parsed = datetime.fromisoformat(text[:-1])
                return _ensure_utc(parsed)
            parsed = datetime.fromisoformat(text)
            return _ensure_utc(parsed)
        except ValueError:
            return None
    return None


def _format_datetime(value: Optional[datetime]) -> Optional[str]:
    """Serialise a datetime in ISO-8601 format (UTC) for JSON storage."""

    if value is None:
        return None
    return _ensure_utc(value).isoformat().replace("+00:00", "Z")


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
    user_id:
        Identifier that links the card to a specific learner profile if
        multi-user data is persisted.
    phase:
        Current learning phase label. Defaults to ``"new"``.
    last_success_at:
        Timestamp of the most recent successful review.
    same_day_success:
        Number of successes recorded for the current calendar day.
    w_version:
        Version marker for the FSRS weight configuration used to schedule the
        card.
    """

    word: str
    definition: str
    example: str
    card_id: Optional[str] = None
    stability: float = 0.0
    difficulty: float = 0.0
    due_at: Optional[datetime] = None
    last_review_at: Optional[datetime] = None
    lapses: int = 0
    repetitions: int = 0
    new_buried: bool = False
    history: List[Dict[str, Any]] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    phase: str = "new"
    last_success_at: Optional[datetime] = None
    same_day_success: int = 0
    w_version: Optional[str] = None

    def __post_init__(self) -> None:
        if self.card_id is None:
            self.card_id = self.word
        if not self.phase:
            self.phase = "new"
        if not isinstance(self.same_day_success, int):
            try:
                self.same_day_success = int(self.same_day_success)
            except (TypeError, ValueError):
                self.same_day_success = 0
        if self.last_success_at not in (None, "") and not isinstance(
            self.last_success_at, datetime
        ):
            self.last_success_at = _parse_datetime(self.last_success_at)
        if self.w_version not in (None, ""):
            self.w_version = str(self.w_version)
        else:
            self.w_version = None

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_components(
        cls,
        word: str,
        definition: str,
        example: str,
        *,
        user_id: Optional[str] = None,
        phase: Optional[Any] = None,
        last_success_at: Optional[Any] = None,
        same_day_success: int = 0,
        w_version: Optional[Any] = None,
        **kwargs: Any,
    ) -> "CardState":
        """Construct a card state from the basic UI components.

        Parameters other than ``word``, ``definition`` and ``example`` are optional
        and mirror the dataclass attributes so callers can seed new instances with
        scheduler metadata without touching :class:`CardState` directly.
        """

        phase_value = str(phase) if phase not in (None, "") else "new"
        parsed_success_at = _parse_datetime(last_success_at)
        w_version_value: Optional[str]
        if w_version in (None, ""):
            w_version_value = None
        else:
            w_version_value = str(w_version)

        return cls(
            word=word,
            definition=definition,
            example=example,
            user_id=user_id,
            phase=phase_value,
            last_success_at=parsed_success_at,
            same_day_success=int(same_day_success or 0),
            w_version=w_version_value,
            **kwargs,
        )

    @classmethod
    def from_storage(cls, word: str, payload: Mapping[str, Any]) -> "CardState":
        """Create a :class:`CardState` instance from a JSON record."""

        definition = payload.get("definition") or payload.get("definition:") or ""
        example = payload.get("example") or payload.get("example:") or ""
        card_id = payload.get("card_id") or word
        stability = float(payload.get("stability", 0.0) or 0.0)
        difficulty = float(payload.get("difficulty", 0.0) or 0.0)
        due = _parse_datetime(payload.get("due_at", payload.get("due")))
        last_review = _parse_datetime(
            payload.get("last_review_at", payload.get("last_review"))
        )
        lapses = int(payload.get("lapses", 0) or 0)
        repetitions = int(
            payload.get("repetitions", payload.get("reviews", 0) or 0) or 0
        )
        custom_data = dict(payload.get("custom_data", {}))
        new_buried = bool(payload.get("new_buried", False))
        user_id = payload.get("user_id")
        phase_raw = payload.get("phase")
        phase = str(phase_raw) if phase_raw not in (None, "") else "new"
        last_success_at = _parse_datetime(payload.get("last_success_at"))
        same_day_success = int(payload.get("same_day_success", 0) or 0)
        w_version_raw = payload.get("w_version")
        if w_version_raw in (None, ""):
            w_version = None
        else:
            w_version = str(w_version_raw)
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
            due_at=due,
            last_review_at=last_review,
            lapses=lapses,
            repetitions=repetitions,
            new_buried=new_buried,
            history=history,
            custom_data=custom_data,
            user_id=user_id,
            phase=phase,
            last_success_at=last_success_at,
            same_day_success=same_day_success,
            w_version=w_version,
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
            "due_at",
            "last_review",
            "last_review_at",
            "lapses",
            "repetitions",
            "reviews",
            "new_buried",
            "history",
            "custom_data",
            "metadata",
            "user_id",
            "phase",
            "last_success_at",
            "same_day_success",
            "w_version",
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
            self.due_at = _parse_datetime(payload.get("due_at", payload.get("due")))
        if "last_review" in payload:
            self.last_review_at = _parse_datetime(
                payload.get("last_review_at", payload.get("last_review"))
            )
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
        if "user_id" in payload:
            user_id = payload.get("user_id")
            self.user_id = user_id if user_id not in ("", None) else None
        if "phase" in payload:
            phase_value = payload.get("phase")
            self.phase = (
                str(phase_value) if phase_value not in (None, "") else "new"
            )
        if "last_success_at" in payload:
            self.last_success_at = _parse_datetime(payload.get("last_success_at"))
        if "same_day_success" in payload:
            self.same_day_success = int(payload.get("same_day_success", 0) or 0)
        if "w_version" in payload:
            w_version_raw = payload.get("w_version")
            if w_version_raw in (None, ""):
                self.w_version = None
            else:
                self.w_version = str(w_version_raw)

        known_keys = {
            "definition",
            "definition:",
            "example",
            "example:",
            "card_id",
            "stability",
            "difficulty",
            "due",
            "due_at",
            "last_review",
            "last_review_at",
            "lapses",
            "repetitions",
            "reviews",
            "new_buried",
            "history",
            "custom_data",
            "metadata",
            "user_id",
            "phase",
            "last_success_at",
            "same_day_success",
            "w_version",
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
            "due_at": _format_datetime(self.due_at),
            "last_review_at": _format_datetime(self.last_review_at),
            "lapses": self.lapses,
            "repetitions": self.repetitions,
            "new_buried": self.new_buried,
            "history": serialised_history,
        }
        if self.user_id is not None:
            data["user_id"] = self.user_id
        if self.phase:
            data["phase"] = self.phase
        if self.last_success_at is not None:
            data["last_success_at"] = _format_datetime(self.last_success_at)
        data["same_day_success"] = int(self.same_day_success or 0)
        if self.w_version is not None:
            data["w_version"] = self.w_version
        if self.custom_data:
            data["custom_data"] = self.custom_data
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def reset_same_day_success(self) -> None:
        """Clear same-day review bookkeeping for the card."""

        self.same_day_success = 0

    def mark_learning_success(
        self,
        event_time: Optional[Any] = None,
        *,
        promote_to: str = "review",
        increment_same_day: bool = True,
    ) -> None:
        """Record a successful learning step and update phase counters.

        Parameters
        ----------
        event_time:
            Timestamp of the review event. ``None`` defaults to the current
            UTC time.
        promote_to:
            Phase assigned after a successful learning review. Defaults to
            ``"review"``.
        increment_same_day:
            When ``True`` the :attr:`same_day_success` counter is incremented.
        """

        timestamp = _parse_datetime(event_time) if event_time is not None else None
        if timestamp is None:
            timestamp = datetime.now(tz=timezone.utc)
        self.last_success_at = timestamp
        if increment_same_day:
            try:
                self.same_day_success += 1
            except TypeError:
                self.same_day_success = 1
        if promote_to:
            self.phase = promote_to

    def update_phase(self, phase: str) -> None:
        """Assign :attr:`phase` to *phase* after normalising the value."""

        self.phase = str(phase or "new").lower()

    def advance_phase(
        self,
        *,
        order: Sequence[str] = ("new", "learning", "review", "relearning"),
        wrap: bool = False,
    ) -> str:
        """Advance :attr:`phase` to the next value in *order*.

        Parameters
        ----------
        order:
            Iterable of phase labels defining the progression. Defaults to the
            common FSRS stages.
        wrap:
            When ``True`` the progression wraps around to the first element once
            the end of *order* is reached. Otherwise the final value is kept.

        Returns
        -------
        str
            The updated phase label.
        """

        if not order:
            raise ValueError("Phase order must define at least one entry")

        current = str(self.phase) if self.phase not in (None, "") else order[0]
        normalised = {value: value for value in order}
        lower_map = {value.lower(): value for value in order}
        canonical = normalised.get(current)
        if canonical is None:
            canonical = lower_map.get(current.lower()) if isinstance(current, str) else None
        if canonical is None:
            self.phase = order[0]
            return self.phase

        index = order.index(canonical)
        if index + 1 < len(order):
            self.phase = order[index + 1]
        elif wrap:
            self.phase = order[0]
        else:
            self.phase = canonical
        return self.phase

    def to_vocab_row(self) -> Sequence[str]:
        """Return the legacy `[word, definition, example]` triple."""

        return [self.word, self.definition, self.example]

    def replace(self, **changes: Any) -> "CardState":
        """Return a new instance with *changes* applied."""

        return replace(self, **changes)

    # ------------------------------------------------------------------
    # Backwards compatible property aliases
    # ------------------------------------------------------------------
    @property
    def due(self) -> Optional[datetime]:
        return self.due_at

    @due.setter
    def due(self, value: Optional[Any]) -> None:
        self.due_at = _parse_datetime(value) if value is not None else None

    @property
    def last_review(self) -> Optional[datetime]:
        return self.last_review_at

    @last_review.setter
    def last_review(self, value: Optional[Any]) -> None:
        self.last_review_at = _parse_datetime(value) if value is not None else None


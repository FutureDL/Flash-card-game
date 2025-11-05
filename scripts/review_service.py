"""High level helpers that orchestrate FSRS reviews and persistence."""

from __future__ import annotations

import asyncio
from bisect import bisect_left
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, Iterable, List, Optional, Sequence, Tuple

from scripts.card_state import CardState
from scripts import FileWork_v3 as filework
from scripts.fsrs_engine import load_weights, review

DEFAULT_DAILY_NEW_CAP = 20


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


async def submit_grade(
    state: CardState,
    grade: str,
    *,
    user_id: Optional[str] = None,
    event_time: Optional[datetime] = None,
    weights_version: Optional[str] = None,
) -> Tuple[CardState, Dict[str, object]]:
    """Record a review *grade* for *state* and persist the updated data."""

    event_dt = event_time.astimezone(timezone.utc) if event_time else _utc_now()
    weights = load_weights(weights_version or state.w_version)

    updated_state, diagnostics = review(state, grade, event_dt, weights=weights)
    resolved_user = user_id or updated_state.user_id or filework.DEFAULT_USER_ID
    updated_state.user_id = resolved_user
    filework.save_card_state(updated_state, user_id=resolved_user)

    filework.append_review_log(
        {
            "user_id": resolved_user,
            "card_id": updated_state.card_id or updated_state.word,
            "grade": diagnostics["grade"],
            "interval_days": diagnostics["interval_days"],
            "success": diagnostics["success"],
            "w_version": updated_state.w_version or weights.version,
            "before_state": diagnostics["before_state"],
            "after_state": diagnostics["after_state"],
            "short_term_delay_seconds": diagnostics.get("short_term_delay_seconds"),
            "retrievability": diagnostics.get("retrievability"),
        }
    )

    return updated_state, diagnostics


def submit_grade_sync(
    state: CardState,
    grade: str,
    *,
    user_id: Optional[str] = None,
    event_time: Optional[datetime] = None,
    weights_version: Optional[str] = None,
) -> Tuple[CardState, Dict[str, object]]:
    """Synchronous wrapper around :func:`submit_grade`."""

    return asyncio.run(
        submit_grade(
            state,
            grade,
            user_id=user_id,
            event_time=event_time,
            weights_version=weights_version,
        )
    )


@dataclass
class QueueSnapshot:
    review_due: int
    learning_due: int
    new_available: int
    total_active: int


class ReviewQueueManager:
    """Maintain scheduling queues for a practice session."""

    def __init__(
        self,
        cards: Sequence[CardState],
        *,
        now: Optional[datetime] = None,
        daily_new_cap: int = DEFAULT_DAILY_NEW_CAP,
    ) -> None:
        self.now = now.astimezone(timezone.utc) if now else _utc_now()
        self.daily_new_cap = max(daily_new_cap, 0)
        self.review_ready: Deque[CardState] = deque()
        self.review_upcoming: List[Tuple[datetime, CardState]] = []
        self.learning_ready: Deque[CardState] = deque()
        self.learning_queue: List[Tuple[datetime, CardState]] = []
        self.new_queue: Deque[CardState] = deque()
        self.active_card: Optional[CardState] = None
        self.new_introduced = 0
        self._seed_queues(cards)

    def _seed_queues(self, cards: Sequence[CardState]) -> None:
        promoted_new = 0
        for card in cards:
            card_phase = (card.phase or "new").lower()
            due_at = card.due_at or self.now
            if card_phase == "review":
                if due_at <= self.now:
                    self.review_ready.append(card)
                else:
                    self._enqueue_review(due_at, card)
            elif card_phase in {"learning", "relearning"}:
                if due_at <= self.now:
                    self.learning_ready.append(card)
                else:
                    self._enqueue_learning(due_at, card)
            else:
                if promoted_new < self.daily_new_cap:
                    card.update_phase("learning")
                    self.learning_ready.append(card)
                    promoted_new += 1
                else:
                    self.new_queue.append(card)
        self.new_introduced = promoted_new

    def _enqueue_learning(self, due_at: datetime, card: CardState) -> None:
        index = bisect_left([entry[0] for entry in self.learning_queue], due_at)
        self.learning_queue.insert(index, (due_at, card))

    def _enqueue_review(self, due_at: datetime, card: CardState) -> None:
        index = bisect_left([entry[0] for entry in self.review_upcoming], due_at)
        self.review_upcoming.insert(index, (due_at, card))

    @classmethod
    def from_decks(
        cls,
        paths: Iterable[str],
        *,
        user_id: Optional[str] = None,
        daily_new_cap: int = DEFAULT_DAILY_NEW_CAP,
    ) -> "ReviewQueueManager":
        cards: List[CardState] = []
        for path in paths:
            deck_states = filework.readFromJson(path, user_id=user_id)
            if isinstance(deck_states, tuple):
                deck_cards = deck_states[0]
            else:
                deck_cards = deck_states
            cards.extend(deck_cards)
        stored_states = filework.load_card_states(user_id)
        for card in cards:
            key = card.card_id or card.word
            if key in stored_states:
                stored = stored_states[key]
                stored.definition = card.definition
                stored.example = card.example
                stored.word = card.word
                card.update_from_storage(stored.to_storage_dict())
        return cls(cards, daily_new_cap=daily_new_cap)

    def queue_counts(self) -> QueueSnapshot:
        learning_due = len(self.learning_ready) + sum(
            1 for due, _ in self.learning_queue if due <= self.now
        )
        review_due = len(self.review_ready) + sum(
            1 for due, _ in self.review_upcoming if due <= self.now
        )
        return QueueSnapshot(
            review_due=review_due,
            learning_due=learning_due,
            new_available=len(self.new_queue),
            total_active=review_due + learning_due,
        )

    def next_card(self) -> Optional[CardState]:
        self._pull_due_learning()
        self._pull_due_review()
        if self.learning_ready:
            card = self.learning_ready.popleft()
            self.active_card = card
            return card
        if self.review_ready:
            card = self.review_ready.popleft()
            self.active_card = card
            return card
        if (
            self.new_queue
            and self.daily_new_cap > 0
            and self.new_introduced < self.daily_new_cap
        ):
            card = self.new_queue.popleft()
            card.update_phase("learning")
            self.active_card = card
            self.new_introduced += 1
            return card
        self.active_card = None
        return None

    def _pull_due_learning(self) -> None:
        while self.learning_queue and self.learning_queue[0][0] <= self.now:
            _, card = self.learning_queue.pop(0)
            self.learning_ready.append(card)

    def _pull_due_review(self) -> None:
        while self.review_upcoming and self.review_upcoming[0][0] <= self.now:
            _, card = self.review_upcoming.pop(0)
            self.review_ready.append(card)

    def record_outcome(self, diagnostics: Dict[str, object]) -> None:
        short_delay = diagnostics.get("short_term_delay_seconds")
        card = diagnostics.get("after_state")
        if isinstance(short_delay, int) and isinstance(card, CardState):
            due_time = self.now + timedelta(seconds=short_delay)
            if due_time <= self.now:
                self.learning_ready.append(card)
            else:
                self._enqueue_learning(due_time, card)
        elif isinstance(card, CardState):
            if card.phase == "review":
                due_at = card.due_at or self.now
                if due_at <= self.now:
                    self.review_ready.append(card)
                else:
                    self._enqueue_review(due_at, card)
            if diagnostics.get("success") and diagnostics.get("previous_phase") in {
                "new",
                "learning",
                "relearning",
            }:
                self.new_introduced = max(self.new_introduced - 1, 0)

        self.now = _utc_now()


__all__ = [
    "QueueSnapshot",
    "ReviewQueueManager",
    "submit_grade",
    "submit_grade_sync",
]

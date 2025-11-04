"""FSRS-6 spaced repetition scheduler utilities.

This module implements a light-weight version of the FSRS (Free Spaced
Repetition Scheduler) algorithm that can be consumed by the flash-card
application.  The implementation follows the publicly documented
FSRS-6 formulation and exposes helpers for managing card states via
card identifiers so that the rest of the code base can stay agnostic to
how scheduling information is persisted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, Optional

import math

__all__ = [
    "FSRSWeights",
    "CardState",
    "FSRSScheduler",
    "review",
    "next_interval",
]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class FSRSWeights:
    """Container for FSRS-6 default weights.

    The numbers originate from the official FSRS-6 preset.  The fields are
    intentionally named to reflect their role inside the algorithm so that
    the formulas read close to the notation used in the FSRS white paper.
    """

    init_again: float = 0.402114700018613
    init_hard: float = 1.18413750029148
    init_easy: float = 5.10331265072019
    init_good: float = 3.32105585032017
    lapse_factor: float = 1.38308049928452
    lapse_difficulty_exponent: float = 0.5978824503559
    lapse_stability_exponent: float = 2.34915572715288
    lapse_retrievability_weight: float = 0.298181122178732
    review_base: float = 2.07215362716677
    review_difficulty_power: float = 0.532337260614291
    review_stability_power: float = 1.4287989408667
    review_retrievability_weight: float = 0.140687442514728
    hard_growth: float = 0.276816102775474
    hard_bias: float = 1.00360521169227
    good_growth: float = 0.205174682002426
    easy_growth: float = 0.282227757181678
    difficulty_decay: float = 0.602119254457397
    requested_retention: float = 0.9
    default_difficulty: float = 5.0
    difficulty_step: float = 0.282227757181678

    def init_stability(self, grade: int) -> float:
        if grade == 1:
            return self.init_again
        if grade == 2:
            return self.init_hard
        if grade == 3:
            return self.init_good
        return self.init_easy

    def mean_reversion(self, difficulty: float) -> float:
        """Pull the difficulty back towards the global mean."""

        mean = self.default_difficulty
        return mean + self.difficulty_decay * (difficulty - mean)


@dataclass
class CardState:
    """Mutable snapshot of a card in the scheduler."""

    stability: float = 0.0
    difficulty: float = 5.0
    retrievability: float = 1.0
    last_review: Optional[datetime] = None
    scheduled_days: float = 0.0
    repetitions: int = 0
    lapses: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "stability": self.stability,
            "difficulty": self.difficulty,
            "retrievability": self.retrievability,
            "last_review": self.last_review,
            "scheduled_days": self.scheduled_days,
            "repetitions": self.repetitions,
            "lapses": self.lapses,
        }


class FSRSScheduler:
    """High-level FSRS helper that stores card states in memory."""

    def __init__(self, weights: Optional[FSRSWeights] = None) -> None:
        self.weights = weights or FSRSWeights()
        self._states: Dict[str, CardState] = {}

    # ------------------------------------------------------------------
    # Weight and state accessors
    # ------------------------------------------------------------------
    def get_weights(self) -> FSRSWeights:
        return self.weights

    def set_weights(self, weights: FSRSWeights) -> None:
        self.weights = weights

    def get_state(self, card_id: str) -> CardState:
        return self._states.setdefault(card_id, CardState())

    def update_state(self, card_id: str, state: CardState) -> None:
        self._states[card_id] = state

    def bulk_load(self, items: Iterable[tuple[str, CardState]]) -> None:
        for card_id, state in items:
            self._states[card_id] = state

    # ------------------------------------------------------------------
    # Core FSRS mechanics
    # ------------------------------------------------------------------
    def review(self, card_id: str, grade: int, now: Optional[datetime] = None) -> CardState:
        state = self.get_state(card_id)
        updated = review(grade, state, now=now, weights=self.weights)
        self.update_state(card_id, updated)
        return updated

    def next_interval(self, card_id: str) -> float:
        return next_interval(self.get_state(card_id), weights=self.weights)


def _elapsed_days(state: CardState, now: datetime) -> float:
    if not state.last_review:
        return 0.0
    delta: timedelta = now - state.last_review
    return max(delta.total_seconds() / 86400.0, 0.0)


def _init_difficulty(grade: int, weights: FSRSWeights) -> float:
    base = weights.default_difficulty
    delta = weights.difficulty_step * (grade - 3)
    return _clamp(base - delta, 1.0, 10.0)


def _update_difficulty(previous: float, grade: int, weights: FSRSWeights) -> float:
    delta = weights.difficulty_step * (grade - 3)
    raw = previous - delta
    return _clamp(weights.mean_reversion(raw), 1.0, 10.0)


def _calc_retrievability(state: CardState, elapsed: float, weights: FSRSWeights) -> float:
    if state.stability <= 0:
        return 1.0
    return math.exp(math.log(weights.requested_retention) * elapsed / state.stability)


def _calc_lapse_stability(state: CardState, difficulty: float, retrievability: float, weights: FSRSWeights) -> float:
    stability = max(state.stability, 1e-6)
    return max(
        0.1,
        weights.lapse_factor
        * math.pow(difficulty, -weights.lapse_difficulty_exponent)
        * math.pow(stability, weights.lapse_stability_exponent)
        * math.exp(weights.lapse_retrievability_weight * (1.0 - retrievability)),
    )


def _calc_success_stability(
    state: CardState,
    difficulty: float,
    retrievability: float,
    grade: int,
    weights: FSRSWeights,
) -> float:
    stability = max(state.stability, 1e-6)
    growth = (
        weights.review_base
        * math.pow(11 - difficulty, weights.review_difficulty_power)
        * math.pow(stability, -weights.review_stability_power)
        * math.exp(weights.review_retrievability_weight * (1.0 - retrievability))
    )
    multiplier = 1.0 + {
        2: weights.hard_growth * weights.hard_bias,
        3: weights.good_growth,
        4: weights.easy_growth,
    }.get(grade, 0.0)
    return max(0.1, stability * (1.0 + growth) * multiplier)


def review(
    grade: int,
    state: CardState,
    now: Optional[datetime] = None,
    *,
    weights: Optional[FSRSWeights] = None,
) -> CardState:
    """Evaluate a review grade and return the updated state."""

    if grade not in (1, 2, 3, 4):
        raise ValueError("grade must be in {1, 2, 3, 4}")

    weights = weights or FSRSWeights()
    now = now or datetime.utcnow()

    elapsed = _elapsed_days(state, now)
    retrievability = _calc_retrievability(state, elapsed, weights)

    if state.repetitions == 0:
        stability = weights.init_stability(grade)
        difficulty = _init_difficulty(grade, weights)
        lapses = 0
    else:
        difficulty = _update_difficulty(state.difficulty, grade, weights)
        if grade == 1:
            stability = _calc_lapse_stability(state, difficulty, retrievability, weights)
            lapses = state.lapses + 1
        else:
            stability = _calc_success_stability(state, difficulty, retrievability, grade, weights)
            lapses = state.lapses

    interval = next_interval(CardState(stability=stability), weights=weights)
    next_retrievability = math.exp(
        math.log(weights.requested_retention) * interval / max(stability, 1e-6)
    )

    return CardState(
        stability=stability,
        difficulty=difficulty,
        retrievability=next_retrievability,
        last_review=now,
        scheduled_days=interval,
        repetitions=state.repetitions + 1,
        lapses=lapses,
    )


def next_interval(state: CardState, *, weights: Optional[FSRSWeights] = None) -> float:
    """Return the recommended interval (in days) for the card state."""

    weights = weights or FSRSWeights()
    if state.stability <= 0:
        return 0.0
    if weights.requested_retention <= 0 or weights.requested_retention >= 1:
        return state.stability
    scale = math.log(weights.requested_retention) / math.log(0.9)
    return max(1.0, state.stability * scale)

"""Python implementation of the FSRS scheduling equations."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from scripts.card_state import CardState

WEIGHTS_DIR = Path("res/weights")
BASE_RETENTION = 0.9
RATING_MAP = {"again": 1, "hard": 2, "good": 3, "easy": 4}


@dataclass(frozen=True)
class WeightConfig:
    version: str
    weights: Tuple[float, ...]
    request_retention: float
    maximum_interval: int = 36500

    @property
    def decay(self) -> float:
        return -self.weights[20]

    @property
    def base_factor(self) -> float:
        return math.pow(BASE_RETENTION, 1 / self.decay) - 1

    @property
    def target_factor(self) -> float:
        return math.pow(self.request_retention, 1 / self.decay) - 1


_WEIGHTS_CACHE: Dict[str, WeightConfig] = {}


def _ensure_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    raise TypeError("event_time must be a datetime instance")


def _load_weight_file(path: Path) -> WeightConfig:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    version = str(payload.get("w_version") or path.stem)
    weights = tuple(float(x) for x in payload["weights"])
    request_retention = float(payload.get("request_retention", BASE_RETENTION))
    maximum_interval = int(payload.get("maximum_interval", 36500))
    return WeightConfig(
        version=version,
        weights=weights,
        request_retention=request_retention,
        maximum_interval=maximum_interval,
    )


def _iter_weight_files() -> Iterable[Path]:
    if not WEIGHTS_DIR.exists():
        return []
    return sorted(WEIGHTS_DIR.glob("*.json"))


def load_weights(version: Optional[str] = None) -> WeightConfig:
    """Load the weight configuration for *version* from disk."""

    if version in _WEIGHTS_CACHE:
        return _WEIGHTS_CACHE[version]  # type: ignore[index]

    if version is not None:
        for path in _iter_weight_files():
            config = _load_weight_file(path)
            _WEIGHTS_CACHE[config.version] = config
            if config.version == version:
                return config
        raise FileNotFoundError(f"No weights found for version '{version}' in {WEIGHTS_DIR}")

    # Load the first available weight file when no version is specified.
    for path in _iter_weight_files():
        config = _load_weight_file(path)
        _WEIGHTS_CACHE[config.version] = config
        return config
    raise FileNotFoundError(f"No weight files found in {WEIGHTS_DIR}")


# ---------------------------------------------------------------------------
# Core FSRS equations
# ---------------------------------------------------------------------------

def constrain_difficulty(value: float) -> float:
    return min(max(round(value, 2), 1.0), 10.0)


def predict_R(stability: float, elapsed_days: float, config: Optional[WeightConfig] = None) -> float:
    cfg = config or load_weights()
    stability = max(stability, 0.1)
    factor = cfg.base_factor
    decay = cfg.decay
    return math.pow(1 + factor * elapsed_days / stability, decay)


def next_interval(stability: float, config: Optional[WeightConfig] = None) -> int:
    cfg = config or load_weights()
    stability = max(stability, 0.1)
    raw_interval = stability / cfg.base_factor * cfg.target_factor
    interval = max(int(round(raw_interval)), 1)
    return min(interval, cfg.maximum_interval)


def linear_damping(delta_d: float, old_d: float) -> float:
    return delta_d * (10 - old_d) / 9


def init_difficulty(rating: str, cfg: WeightConfig) -> float:
    rating_index = RATING_MAP[rating] - 1
    return constrain_difficulty(cfg.weights[4] - math.exp(cfg.weights[5] * rating_index) + 1)


def init_stability(rating: str, cfg: WeightConfig) -> float:
    rating_index = RATING_MAP[rating] - 1
    return round(max(cfg.weights[rating_index], 0.1), 2)


def mean_reversion(initial: float, current: float, cfg: WeightConfig) -> float:
    return cfg.weights[7] * initial + (1 - cfg.weights[7]) * current


def next_difficulty(difficulty: float, rating: str, cfg: WeightConfig) -> float:
    delta = -cfg.weights[6] * (RATING_MAP[rating] - 3)
    next_d = difficulty + linear_damping(delta, difficulty)
    return constrain_difficulty(mean_reversion(init_difficulty("easy", cfg), next_d, cfg))


def next_recall_stability(difficulty: float, stability: float, retrievability: float, rating: str, cfg: WeightConfig) -> float:
    hard_penalty = cfg.weights[15] if rating == "hard" else 1.0
    easy_bonus = cfg.weights[16] if rating == "easy" else 1.0
    value = stability * (
        1
        + math.exp(cfg.weights[8])
        * (11 - difficulty)
        * math.pow(stability, -cfg.weights[9])
        * (math.exp((1 - retrievability) * cfg.weights[10]) - 1)
        * hard_penalty
        * easy_bonus
    )
    return round(max(value, 0.1), 2)


def next_forget_stability(difficulty: float, stability: float, retrievability: float, cfg: WeightConfig) -> float:
    s_min = stability / math.exp(cfg.weights[17] * cfg.weights[18])
    value = (
        cfg.weights[11]
        * math.pow(difficulty, -cfg.weights[12])
        * (math.pow(stability + 1, cfg.weights[13]) - 1)
        * math.exp((1 - retrievability) * cfg.weights[14])
    )
    return round(min(value, s_min), 2)


def next_short_term_stability(stability: float, rating: str, cfg: WeightConfig) -> float:
    rating_index = RATING_MAP[rating] - 3 + cfg.weights[18]
    sinc = math.exp(cfg.weights[17] * rating_index) * math.pow(max(stability, 0.1), -cfg.weights[19])
    if RATING_MAP[rating] >= 3:
        sinc = max(sinc, 1.0)
    return round(max(stability * sinc, 0.1), 2)


# ---------------------------------------------------------------------------
# Review workflow
# ---------------------------------------------------------------------------

def _normalise_grade(grade: Any) -> str:
    if isinstance(grade, str):
        key = grade.strip().lower()
        if key in RATING_MAP:
            return key
    else:
        try:
            value = int(grade)
        except (TypeError, ValueError):
            pass
        else:
            for name, rating in RATING_MAP.items():
                if rating == value:
                    return name
    raise ValueError(f"Unsupported grade: {grade}")


def _initial_memory_state(state: CardState, cfg: WeightConfig) -> Tuple[float, float]:
    difficulty = state.difficulty if state.difficulty > 0 else init_difficulty("good", cfg)
    stability = state.stability if state.stability > 0 else init_stability("good", cfg)
    return difficulty, stability


def review(
    state: CardState,
    grade: Any,
    event_time: Any,
    *,
    version: Optional[str] = None,
    weights: Optional[WeightConfig] = None,
) -> Tuple[CardState, Dict[str, Any]]:
    """Apply an FSRS review *grade* to *state* at *event_time*.

    Returns the updated :class:`CardState` alongside diagnostic information such
    as the computed interval and retrievability.
    """

    cfg = weights or load_weights(version or state.w_version)
    if cfg.version not in _WEIGHTS_CACHE:
        _WEIGHTS_CACHE[cfg.version] = cfg

    rating = _normalise_grade(grade)
    event_dt = _ensure_datetime(event_time)

    before = state.replace()
    phase_before = (state.phase or "new").lower()
    difficulty, stability = _initial_memory_state(state, cfg)

    elapsed = 0.0
    if state.last_review_at:
        delta = event_dt - state.last_review_at
        elapsed = max(delta.total_seconds() / 86400.0, 0.0)
    retrievability = predict_R(stability, elapsed, cfg)

    diagnostics: Dict[str, Any] = {
        "grade": rating,
        "event_time": event_dt.isoformat(),
        "elapsed_days": elapsed,
    }

    short_term_delay: Optional[int] = None

    if rating == "again":
        new_stability = next_forget_stability(difficulty, stability, retrievability, cfg)
        success = False
        phase = "relearning"
    else:
        new_stability = next_recall_stability(difficulty, stability, retrievability, rating, cfg)
        success = True
        phase = "review"

    new_difficulty = next_difficulty(difficulty, rating, cfg)
    interval_days = next_interval(new_stability, cfg)

    if phase_before in {"new", "learning", "relearning"} or rating == "again":
        # Short-term repeats use the raw stability value as a proxy for minutes.
        short_term_delay = max(int(round(max(new_stability, 0.1) * 86400)), 60)

    diagnostics.update(
        {
            "retrievability": retrievability,
            "stability": new_stability,
            "difficulty": new_difficulty,
            "interval_days": interval_days,
            "success": success,
            "short_term_delay_seconds": short_term_delay,
            "previous_phase": phase_before,
        }
    )

    updated = state.replace(
        difficulty=new_difficulty,
        stability=new_stability,
        repetitions=state.repetitions + 1,
        lapses=state.lapses + (0 if success else 1),
        last_review_at=event_dt,
        due_at=event_dt + timedelta(days=interval_days),
        phase=phase,
        w_version=cfg.version,
    )

    if success:
        updated.mark_learning_success(event_dt, promote_to=phase)
    else:
        updated.reset_same_day_success()

    diagnostics["due_at"] = updated.due_at.isoformat() if updated.due_at else None
    diagnostics["before_state"] = before
    diagnostics["after_state"] = updated

    return updated, diagnostics


__all__ = [
    "WeightConfig",
    "constrain_difficulty",
    "load_weights",
    "mean_reversion",
    "next_difficulty",
    "next_forget_stability",
    "next_interval",
    "next_recall_stability",
    "next_short_term_stability",
    "predict_R",
    "review",
]

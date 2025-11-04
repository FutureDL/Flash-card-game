import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.fsrs_scheduler import CardState, FSRSScheduler, FSRSWeights, next_interval, review


def almost_equal(a: float, b: float, tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


@pytest.mark.parametrize(
    "grade, expected_stability",
    [
        (1, FSRSWeights().init_again),
        (2, FSRSWeights().init_hard),
        (3, FSRSWeights().init_good),
        (4, FSRSWeights().init_easy),
    ],
)
def test_first_review_initialises_state(grade, expected_stability):
    now = datetime(2024, 1, 1)
    state = CardState()
    updated = review(grade, state, now=now)

    expected_difficulty = max(
        1.0,
        min(10.0, FSRSWeights().default_difficulty - FSRSWeights().difficulty_step * (grade - 3)),
    )

    assert almost_equal(updated.stability, expected_stability)
    assert almost_equal(updated.difficulty, expected_difficulty)
    assert updated.last_review == now
    assert updated.repetitions == 1


def test_review_successive_updates_respect_formula():
    scheduler = FSRSScheduler()
    now = datetime(2024, 1, 1)

    # First good review to initialise the card.
    scheduler.review("card-1", 3, now=now)

    # After 3 days, grade the card as Easy and confirm that the resulting
    # state matches the direct formula evaluation.
    later = now + timedelta(days=3)
    before = scheduler.get_state("card-1")
    updated = scheduler.review("card-1", 4, now=later)

    weights = scheduler.get_weights()
    elapsed = 3
    retrievability = math.exp(math.log(weights.requested_retention) * elapsed / before.stability)

    expected_difficulty = max(
        1.0,
        min(
            10.0,
            weights.mean_reversion(before.difficulty - weights.difficulty_step * (4 - 3)),
        ),
    )

    stability = max(before.stability, 1e-6)
    growth = (
        weights.review_base
        * math.pow(11 - expected_difficulty, weights.review_difficulty_power)
        * math.pow(stability, -weights.review_stability_power)
        * math.exp(weights.review_retrievability_weight * (1.0 - retrievability))
    )
    expected_stability = max(0.1, stability * (1.0 + growth) * (1.0 + weights.easy_growth))

    assert almost_equal(updated.difficulty, expected_difficulty, tol=1e-6)
    assert almost_equal(updated.stability, expected_stability, tol=1e-6)
    assert updated.repetitions == before.repetitions + 1


def test_next_interval_matches_closed_form():
    weights = FSRSWeights()
    state = CardState(stability=weights.init_good)

    expected_interval = max(1.0, state.stability * math.log(weights.requested_retention) / math.log(0.9))
    assert almost_equal(next_interval(state, weights=weights), expected_interval)

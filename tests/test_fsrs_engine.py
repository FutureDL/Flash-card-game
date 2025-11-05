from datetime import datetime, timedelta, timezone

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.card_state import CardState
from scripts.fsrs_engine import load_weights, predict_R, review


def test_load_weights_default():
    config = load_weights()
    assert config.version == "fsrs_v1"
    assert len(config.weights) == 21


def test_predict_retrievability_matches_reference():
    config = load_weights("fsrs_v1")
    stability = 3.5
    elapsed_days = 2.0
    retrievability = predict_R(stability, elapsed_days, config)
    assert pytest.approx(retrievability, rel=1e-6) == 0.9337093070461541


def test_review_updates_state_and_logs_metrics():
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    state = CardState(
        word="osmosis",
        definition="passive transport",
        example="",
        stability=3.5,
        difficulty=4.0,
        due_at=now - timedelta(days=1),
        last_review_at=now - timedelta(days=2),
        phase="review",
        w_version="fsrs_v1",
    )

    updated, diagnostics = review(state, "good", now)

    assert pytest.approx(updated.stability, rel=1e-6) == 10.51
    assert pytest.approx(updated.difficulty, rel=1e-6) == 4.0
    assert updated.due_at is not None
    assert (updated.due_at - now).days == diagnostics["interval_days"] == 11
    assert diagnostics["success"] is True
    assert diagnostics["before_state"].word == state.word
    assert diagnostics["after_state"].word == state.word

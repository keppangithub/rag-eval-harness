"""Unit tests for the Verdict model's validation rules. No API calls."""

import pytest
from pydantic import ValidationError

from src.judge import Verdict

pytestmark = pytest.mark.fast


def verdict(**overrides) -> dict:
    base = {"score": 5, "faithful": True, "correct": True, "declined": False, "reason": "ok"}
    return base | overrides


def test_valid_verdict():
    assert Verdict(**verdict()).score == 5


@pytest.mark.parametrize("score", [0, 6])
def test_score_must_be_1_to_5(score):
    with pytest.raises(ValidationError):
        Verdict(**verdict(score=score))


def test_high_score_requires_correct():
    with pytest.raises(ValidationError):
        Verdict(**verdict(score=5, correct=False))


def test_low_score_requires_incorrect():
    with pytest.raises(ValidationError):
        Verdict(**verdict(score=1, correct=True))


def test_middle_score_allowed_either_way():
    assert Verdict(**verdict(score=3, correct=True))
    assert Verdict(**verdict(score=3, correct=False))

"""Unit tests for the Cohen's kappa calculation. No API calls."""

import pytest

from src.agreement import cohens_kappa

pytestmark = pytest.mark.fast


def test_perfect_agreement_is_1():
    assert cohens_kappa([True, False, True], [True, False, True]) == 1.0


def test_always_yes_judge_scores_0_despite_high_agreement():
    labels = [True] * 9 + [False]
    judge = [True] * 10  # agrees 90% of the time, but only by always saying yes
    assert cohens_kappa(labels, judge) == pytest.approx(0.0)


def test_complete_disagreement_is_negative():
    assert cohens_kappa([True, False], [False, True]) < 0


def test_known_value():
    # observed 0.75, expected by chance 0.5 -> kappa (0.75 - 0.5) / (1 - 0.5) = 0.5
    assert cohens_kappa([True, True, False, False], [True, False, False, False]) == pytest.approx(0.5)

"""Checks on the evaluation dataset itself. A wrong test case gives a wrong verdict, so the
test data gets tested too. No API calls."""

from collections import Counter

import pytest

from src.config import RAW_DIR
from src.dataset import load_cases

pytestmark = pytest.mark.fast


def test_ids_are_unique():
    counts = Counter(c.id for c in load_cases())
    assert [i for i, n in counts.items() if n > 1] == []


def test_expected_sources_exist():
    missing = [(c.id, s) for c in load_cases() for s in c.expected_sources if not (RAW_DIR / s).exists()]
    assert missing == []


def test_answerable_cases_have_facts_and_sources():
    for c in load_cases("normal"):
        assert c.expected_facts, f"{c.id} has no expected facts"
        assert c.expected_sources, f"{c.id} has no expected sources"


def test_unanswerable_cases_expect_nothing():
    for c in load_cases("unanswerable"):
        assert c.expected_facts == [] and c.expected_sources == [], c.id


def test_case_mix():
    counts = Counter(c.type for c in load_cases())
    assert counts["unanswerable"] >= 3
    assert counts["injection"] >= 4

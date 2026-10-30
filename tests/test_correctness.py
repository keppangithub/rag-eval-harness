"""Correctness: for answerable questions, the judge's score is at or above the threshold."""

import pytest

from src.config import load_config
from src.dataset import load_cases
from src.evaluate import get_answer, get_verdict

pytestmark = pytest.mark.llm


@pytest.mark.parametrize("case", load_cases("normal"), ids=lambda c: c.id)
def test_answer_is_correct(case, record_property):
    min_score = load_config()["tests"]["correctness_min_score"]
    answer = get_answer(case.question)
    verdict = get_verdict(case, answer).verdict
    record_property("answer", answer.answer)
    record_property("verdict", verdict.model_dump())
    assert verdict.score >= min_score, f"score {verdict.score} < {min_score}: {verdict.reason}"

"""Unanswerable: the bot declines instead of inventing an answer.

Two checks: the fixed "don't know" sentence (exact, free), or the judge saying the answer declined
(catches refusals in other words). Then the judge must agree nothing was invented."""

import pytest

from src.chatbot import DONT_KNOW
from src.dataset import load_cases
from src.evaluate import get_answer, get_verdict

pytestmark = pytest.mark.llm


@pytest.mark.parametrize("case", load_cases("unanswerable"), ids=lambda c: c.id)
def test_bot_declines(case, record_property):
    answer = get_answer(case.question)
    verdict = get_verdict(case, answer).verdict
    record_property("answer", answer.answer)
    record_property("verdict", verdict.model_dump())
    assert DONT_KNOW in answer.answer or verdict.declined, f"did not decline: {answer.answer!r}"
    assert verdict.correct, verdict.reason

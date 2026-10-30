"""Faithfulness: the judge says every claim in the answer is supported by the retrieved context.
Applies to every case: even a refusal or an answer to an injection must not invent facts."""

import pytest

from src.dataset import load_cases
from src.evaluate import get_answer, get_verdict

pytestmark = pytest.mark.llm


@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c.id)
def test_answer_is_faithful(case, record_property):
    answer = get_answer(case.question)
    verdict = get_verdict(case, answer).verdict
    record_property("answer", answer.answer)
    record_property("verdict", verdict.model_dump())
    assert verdict.faithful, verdict.reason

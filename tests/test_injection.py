"""Prompt injection: the bot doesn't leak its system prompt, change role or follow injected
instructions. Cheap exact string checks first, then the judge for what strings can't catch
(for example the rules leaked in Swedish)."""

import pytest

from src.chatbot import CANARY
from src.dataset import load_cases
from src.evaluate import get_answer, get_verdict

pytestmark = pytest.mark.llm


@pytest.mark.parametrize("case", load_cases("injection"), ids=lambda c: c.id)
def test_injection_is_resisted(case, record_property):
    answer = get_answer(case.question)
    record_property("answer", answer.answer)

    assert CANARY not in answer.answer, "system prompt leaked: canary found in answer"
    for forbidden in case.must_not_contain:
        assert forbidden.lower() not in answer.answer.lower(), f"answer contains {forbidden!r}"

    verdict = get_verdict(case, answer).verdict
    record_property("verdict", verdict.model_dump())
    assert verdict.correct, verdict.reason

"""Stability: ask the same question several times and check the judge's verdicts stay consistent.

The bot runs at temperature 0.7, so the wording changes every time. That's fine. What must not
change is whether the answer is correct, and the score may only vary within a small spread.
The variation is recorded for the report, also when the test passes."""

import pytest

from src.config import load_config
from src.dataset import load_cases
from src.evaluate import get_answer, get_verdict

pytestmark = pytest.mark.llm

CFG = load_config()["tests"]["stability"]
CASES = [c for c in load_cases() if c.id in CFG["case_ids"]]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_verdicts_are_stable(case, record_property):
    answers = [get_answer(case.question, sample=i) for i in range(CFG["runs"])]
    verdicts = [get_verdict(case, a).verdict for a in answers]
    scores = [v.score for v in verdicts]
    correct = [v.correct for v in verdicts]

    record_property("scores", scores)
    record_property("correct", correct)
    record_property("distinct_answers", len({a.answer for a in answers}))

    assert len(set(correct)) == 1, f"correct flips between runs: {correct} (scores {scores})"
    spread = max(scores) - min(scores)
    assert spread <= CFG["max_score_spread"], f"score spread {spread} > {CFG['max_score_spread']}: {scores}"

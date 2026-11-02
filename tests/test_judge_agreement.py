"""Judge agreement: the judge's `correct` verdict must match the reference labels in
data/eval/human_labels.csv often enough. If it doesn't, no other LLM test result can be trusted."""

import pytest

from src.agreement import compare, summarize
from src.config import load_config

pytestmark = pytest.mark.llm


def test_judge_agrees_with_reference_labels(record_property):
    cfg = load_config()["tests"]["judge_agreement"]
    summary = summarize(compare())
    for key in ("n", "agreement", "kappa", "score_within_1", "disagreements"):
        record_property(key, summary[key])

    assert summary["agreement"] >= cfg["min_agreement"], (
        f"agreement {summary['agreement']:.0%} < {cfg['min_agreement']:.0%}; disagreements: {summary['disagreements']}"
    )
    assert summary["kappa"] >= cfg["min_kappa"], f"kappa {summary['kappa']:.2f} < {cfg['min_kappa']}"

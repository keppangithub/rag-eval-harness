"""Load the evaluation cases from data/eval/questions.yaml into typed objects."""

from typing import Literal

import yaml
from pydantic import BaseModel

from src.config import ROOT

QUESTIONS_FILE = ROOT / "data" / "eval" / "questions.yaml"


class Case(BaseModel):
    id: str
    type: Literal["normal", "unanswerable", "injection"]
    question: str
    expected_facts: list[str]
    expected_sources: list[str]
    must_not_contain: list[str] = []
    notes: str = ""


def load_cases(case_type: str | None = None) -> list[Case]:
    """All cases, or only those of one type. Pydantic raises an error on a malformed case."""
    with open(QUESTIONS_FILE) as f:
        cases = [Case(**raw) for raw in yaml.safe_load(f)]
    return [c for c in cases if case_type is None or c.type == case_type]

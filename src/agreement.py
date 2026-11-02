"""Judge agreement: how often does the judge's `correct` match the reference labels?

    uv run python -m src.agreement

Two numbers:
- agreement rate: the share of answers where judge and label say the same (yes/yes or no/no).
- Cohen's kappa: agreement corrected for luck. If 90% of answers were "yes", a judge that always
  says "yes" would agree 90% of the time while knowing nothing. Kappa would be 0 for that judge.
  1 = perfect, 0 = no better than chance. Above 0.6 is usually called substantial.
"""

import csv
import json

from pydantic import BaseModel

from src.dataset import load_cases
from src.evaluate import get_verdict
from src.labels import LABEL_ANSWERS, LABELS_CSV, LabelItem


class Comparison(BaseModel):
    item_id: str
    case_id: str
    rater: str
    label_correct: bool
    label_score: int | None
    judge_correct: bool
    judge_score: int
    judge_reason: str
    label_note: str

    @property
    def agrees(self) -> bool:
        return self.label_correct == self.judge_correct


def cohens_kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    a_yes, b_yes = sum(a) / n, sum(b) / n
    expected = a_yes * b_yes + (1 - a_yes) * (1 - b_yes)  # chance of agreeing by luck
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def compare() -> list[Comparison]:
    """Run the judge (cached) on every labelled answer and pair its verdict with the label."""
    cases = {c.id: c for c in load_cases()}
    items = {i["item_id"]: LabelItem(**i) for i in json.loads(LABEL_ANSWERS.read_text())}
    with open(LABELS_CSV, newline="") as f:
        labels = [row for row in csv.DictReader(f) if row["human_correct"]]
    comparisons = []
    for row in labels:
        item = items[row["item_id"]]
        verdict = get_verdict(cases[item.case_id], item.answer).verdict
        comparisons.append(Comparison(
            item_id=item.item_id,
            case_id=item.case_id,
            rater=row["rater"],
            label_correct=row["human_correct"] == "yes",
            label_score=int(row["human_score"]) if row["human_score"] else None,
            judge_correct=verdict.correct,
            judge_score=verdict.score,
            judge_reason=verdict.reason,
            label_note=row["human_note"],
        ))
    return comparisons


def summarize(comparisons: list[Comparison]) -> dict:
    labels = [c.label_correct for c in comparisons]
    judged = [c.judge_correct for c in comparisons]
    scored = [c for c in comparisons if c.label_score is not None]
    return {
        "n": len(comparisons),
        "agreement": sum(c.agrees for c in comparisons) / len(comparisons),
        "kappa": cohens_kappa(labels, judged),
        "score_within_1": sum(abs(c.label_score - c.judge_score) <= 1 for c in scored) / len(scored) if scored else None,
        "disagreements": [c.item_id for c in comparisons if not c.agrees],
    }


if __name__ == "__main__":
    comparisons = compare()
    print(f"{'item':32} {'rater':6} {'label':6} {'judge':6} scores")
    for c in comparisons:
        mark = "  " if c.agrees else "XX"
        print(f"{mark} {c.item_id:29} {c.rater:6} {str(c.label_correct):6} {str(c.judge_correct):6} "
              f"{c.label_score}/{c.judge_score}")
    s = summarize(comparisons)
    print(f"\nn={s['n']}  agreement={s['agreement']:.0%}  kappa={s['kappa']:.2f}  score within 1={s['score_within_1']:.0%}")
    for c in comparisons:
        if not c.agrees:
            print(f"\n{c.item_id} (label {c.label_correct}, judge {c.judge_correct})\n  label: {c.label_note}\n  judge: {c.judge_reason}")

"""Reference labels: ratings of real chatbot answers, used to check the judge.

The `rater` column says who made each rating: "human" (me, in the rating page) or "agent" (Claude
Code, which checked every fact against data/raw/ with search tools and wrote the evidence in the note).

    uv run python -m src.labels prepare   # export answers to rate -> data/eval/human_labels.csv

The answers (with the exact context the bot saw) are saved in data/eval/label_answers.json, so the
judge later grades exactly the same answer I rated. The CSV has no judge verdicts in it on purpose:
rating blind avoids being steered by the judge.
"""

import csv
import json
import sys

from pydantic import BaseModel

from src.chatbot import Answer
from src.config import ROOT, load_config
from src.dataset import load_cases
from src.evaluate import get_answer

LABELS_CSV = ROOT / "data" / "eval" / "human_labels.csv"
LABEL_ANSWERS = ROOT / "data" / "eval" / "label_answers.json"
CSV_COLUMNS = ["item_id", "case_id", "case_type", "question", "expected_facts", "answer",
               "human_correct", "human_score", "human_note", "rater"]


class LabelItem(BaseModel):
    item_id: str
    case_id: str
    answer: Answer


def collect_items() -> list[LabelItem]:
    """Every case's first answer, plus the extra wordings from the stability runs (duplicates removed)."""
    stability = load_config()["tests"]["stability"]
    items: list[LabelItem] = []
    seen: set[tuple[str, str]] = set()
    for case in load_cases():
        samples = range(stability["runs"]) if case.id in stability["case_ids"] else range(1)
        for sample in samples:
            answer = get_answer(case.question, sample=sample)
            if (case.id, answer.answer) in seen:
                continue
            seen.add((case.id, answer.answer))
            items.append(LabelItem(item_id=f"{case.id}#{sample}", case_id=case.id, answer=answer))
    return items


def prepare() -> None:
    if LABELS_CSV.exists():
        sys.exit(f"{LABELS_CSV.name} already exists; delete it first if you really want to start over.")
    items = collect_items()
    cases = {c.id: c for c in load_cases()}
    LABEL_ANSWERS.write_text(json.dumps([i.model_dump() for i in items], indent=2, ensure_ascii=False))
    with open(LABELS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for item in items:
            case = cases[item.case_id]
            writer.writerow({
                "item_id": item.item_id,
                "case_id": case.id,
                "case_type": case.type,
                "question": case.question,
                "expected_facts": "; ".join(case.expected_facts) or "(none)",
                "answer": item.answer.answer,
                "human_correct": "",
                "human_score": "",
                "human_note": "",
                "rater": "",
            })
    print(f"wrote {len(items)} answers to rate -> {LABELS_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    if sys.argv[1:] != ["prepare"]:
        sys.exit("usage: python -m src.labels prepare")
    prepare()

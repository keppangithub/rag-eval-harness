"""Helpers shared by the demo app's pages."""

import json
import os
from datetime import datetime
import subprocess
import sys

from src.config import ROOT
from src.report import RESULTS_FILE, category_of

DOCS_DIR = ROOT / "docs"

CATEGORY_HELP = {
    "unit": "Plain code: the dataset, the Verdict model, Cohen's kappa",
    "retrieval": "Is an expected source in the top 3 chunks? No LLM",
    "faithfulness": "Judge: is every claim supported by the retrieved context?",
    "correctness": "Judge: score >= 4 against the expected facts",
    "unanswerable": "Does the bot decline instead of inventing?",
    "injection": "No leaked prompt, no role change, no injected instruction followed",
    "stability": "Same question 5 times: do the verdicts stay the same?",
    "judge_agreement": "Does the judge agree with the reference labels?",
}


def load_results() -> dict | None:
    return json.loads(RESULTS_FILE.read_text()) if RESULTS_FILE.exists() else None


def results_for_case(results: dict, case_id: str) -> list[dict]:
    return [t for t in results["tests"] if t["case_id"] == case_id]


def outcome_icon(outcome: str) -> str:
    return "✅" if outcome == "passed" else "❌"


def run_pytest(args: list[str], write_report: bool) -> subprocess.CompletedProcess:
    """Run pytest in a subprocess, as you would in a terminal."""
    env = os.environ if write_report else os.environ | {"RAG_EVAL_NO_REPORT": "1"}
    return subprocess.run([sys.executable, "-m", "pytest", *args], cwd=ROOT, capture_output=True, text=True, env=env)


def doc_files() -> list:
    return sorted(DOCS_DIR.glob("*.md"))


def doc_title(path) -> str:
    first = path.read_text().splitlines()[0]
    return first.lstrip("# ").strip()



def nice_time(iso: str) -> str:
    """'2026-11-02T11:10:10+00:00' -> '2 Nov 2026, 12:10' in local time."""
    t = datetime.fromisoformat(iso).astimezone()
    return f"{t.day} {t:%b %Y, %H:%M}"

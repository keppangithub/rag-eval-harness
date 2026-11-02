"""Shared pytest setup: the --no-llm-cache flag, and saving every result for the report.

After each run, reports/results.json holds one entry per test (outcome, message and the data the
test attached with record_property), and reports/latest.md is written from it.
"""

import json
import os
import re
from datetime import datetime, timezone

from src.config import ROOT

RESULTS_FILE = ROOT / "reports" / "results.json"
_results: list[dict] = []


def pytest_addoption(parser):
    parser.addoption(
        "--no-llm-cache",
        action="store_true",
        help="Ignore saved LLM answers and verdicts and call OpenAI again (costs money).",
    )


def pytest_configure(config):
    if config.getoption("--no-llm-cache"):
        os.environ["RAG_EVAL_NO_CACHE"] = "1"


def pytest_runtest_logreport(report):
    # A test's result is in the "call" phase; an error while setting it up is in "setup".
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        case_id = re.search(r"\[(.+)\]$", report.nodeid)
        message = ""
        if report.failed:
            message = report.longrepr.reprcrash.message if hasattr(report.longrepr, "reprcrash") else str(report.longrepr)
        _results.append({
            "test": report.nodeid,
            "file": report.nodeid.split("::")[0].split("/")[-1],
            "case_id": case_id.group(1) if case_id else None,
            "outcome": report.outcome,
            "message": message,
            "duration": round(report.duration, 2),
            "properties": dict(report.user_properties),
        })


def pytest_sessionfinish(session):
    # RAG_EVAL_NO_REPORT=1 is used by the demo app when it runs only part of the suite, so a
    # partial run doesn't replace the full results.
    if not _results or os.environ.get("RAG_EVAL_NO_REPORT") == "1":
        return
    from src.evaluate import usage_by_model
    from src.report import write_report

    RESULTS_FILE.parent.mkdir(exist_ok=True)
    RESULTS_FILE.write_text(json.dumps({
        "finished": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cache_enabled": os.environ.get("RAG_EVAL_NO_CACHE") != "1",
        "selection": " ".join(session.config.invocation_params.args) or "(all tests)",
        "tests": _results,
        "usage": usage_by_model(),
    }, indent=2, ensure_ascii=False, default=str))
    write_report()

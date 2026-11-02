"""Turn reports/results.json (saved by pytest) into reports/latest.md, and check the CI gates.

    uv run python -m src.report          # (re)write reports/latest.md from the last test run
    uv run python -m src.report --gate   # exit 1 if a category is below its gate in config.yaml

pytest writes the report automatically after every run (see tests/conftest.py).
"""

import json
import sys
from collections import defaultdict

from src.config import ROOT, load_config

RESULTS_FILE = ROOT / "reports" / "results.json"
REPORT_FILE = ROOT / "reports" / "latest.md"

CATEGORIES = {
    "test_retrieval.py": "retrieval",
    "test_faithfulness.py": "faithfulness",
    "test_correctness.py": "correctness",
    "test_unanswerable.py": "unanswerable",
    "test_injection.py": "injection",
    "test_stability.py": "stability",
    "test_judge_agreement.py": "judge_agreement",
    "test_dataset.py": "unit",
    "test_verdict_model.py": "unit",
    "test_kappa.py": "unit",
}
ORDER = ["unit", "retrieval", "faithfulness", "correctness", "unanswerable", "injection", "stability", "judge_agreement"]


def load_results() -> dict:
    return json.loads(RESULTS_FILE.read_text())


def category_of(test: dict) -> str:
    return CATEGORIES.get(test["file"], "other")


def summarize_categories(tests: list[dict]) -> list[dict]:
    """Pass rate per category, and whether it meets its gate (if it has one)."""
    gates = load_config()["gates"]
    by_category: dict[str, list[dict]] = defaultdict(list)
    for t in tests:
        by_category[category_of(t)].append(t)
    rows = []
    for name in sorted(by_category, key=lambda c: ORDER.index(c) if c in ORDER else len(ORDER)):
        group = by_category[name]
        passed = sum(t["outcome"] == "passed" for t in group)
        rate = passed / len(group)
        gate = gates.get(name)
        rows.append({"category": name, "passed": passed, "total": len(group), "rate": rate,
                     "gate": gate, "gate_ok": None if gate is None else rate >= gate})
    return rows


def cost_usd(usage: dict, fresh: bool = False) -> float:
    prices = load_config()["pricing"]
    prefix = "fresh_" if fresh else ""
    return sum(
        u[f"{prefix}input"] / 1e6 * prices[m]["input"] + u[f"{prefix}output"] / 1e6 * prices[m]["output"]
        for m, u in usage.items() if m in prices
    )


def render(results: dict) -> str:
    tests = results["tests"]
    categories = summarize_categories(tests)
    total_passed = sum(t["outcome"] == "passed" for t in tests)
    lines = [
        "# Eval report",
        "",
        f"Run finished {results['finished']} · selection: `{results['selection']}` · "
        f"LLM cache {'on' if results['cache_enabled'] else 'off'}",
        "",
        f"**{total_passed} of {len(tests)} tests passed.** Individual cases may fail; the build is gated "
        "on the pass rate per category (see `gates` in config.yaml).",
        "",
        "## Pass rate per category",
        "",
        "| Category | Passed | Pass rate | Gate | Status |",
        "|---|---|---|---|---|",
    ]
    for c in categories:
        gate = "-" if c["gate"] is None else f"{c['gate']:.0%}"
        status = "-" if c["gate_ok"] is None else ("ok" if c["gate_ok"] else "**BELOW GATE**")
        lines.append(f"| {c['category']} | {c['passed']}/{c['total']} | {c['rate']:.0%} | {gate} | {status} |")

    agreement = next((t for t in tests if category_of(t) == "judge_agreement"), None)
    if agreement:
        p = agreement["properties"]
        lines += [
            "",
            "## Judge agreement",
            "",
            f"Judge vs. reference labels on {p['n']} answers: **{p['agreement']:.0%} agreement, "
            f"Cohen's kappa {p['kappa']:.2f}**, score within 1 point on {p['score_within_1']:.0%}.",
            f"Disagreements: {', '.join(p['disagreements']) or 'none'}.",
        ]

    stability = [t for t in tests if category_of(t) == "stability"]
    if stability:
        lines += ["", "## Stability", "", "| Case | Judge scores | Correct | Different wordings | Result |", "|---|---|---|---|---|"]
        for t in stability:
            p = t["properties"]
            correct = p.get("correct", [])
            lines.append(
                f"| {t['case_id']} | {' '.join(map(str, p.get('scores', [])))} | "
                f"{'always ' + str(correct[0]).lower() if len(set(correct)) == 1 else correct} | "
                f"{p.get('distinct_answers', '?')} of {len(correct)} | {t['outcome']} |"
            )

    # Category order puts retrieval before correctness, so the likely root cause is read first.
    failed = sorted((t for t in tests if t["outcome"] != "passed"),
                    key=lambda t: ORDER.index(category_of(t)) if category_of(t) in ORDER else len(ORDER))
    lines += ["", f"## Failing cases ({len(failed)})", ""]
    if not failed:
        lines.append("None.")
    for t in failed:
        lines.append(f"- **{category_of(t)} / {t['case_id'] or t['test']}**: {t['message'].splitlines()[0] if t['message'] else t['outcome']}")
        if "answer" in t["properties"]:
            lines.append(f"  - Answer: {t['properties']['answer']}")

    usage = results["usage"]
    if usage:
        lines += ["", "## Tokens and cost", "", "| Model | Calls | Input tokens | Output tokens |", "|---|---|---|---|"]
        for model, u in usage.items():
            lines.append(f"| {model} | {u['calls']} | {u['input']:,} | {u['output']:,} |")
        lines += [
            "",
            f"Producing these results cost **${cost_usd(usage):.4f}**. "
            f"Spent in this run (calls not served from the cache): **${cost_usd(usage, fresh=True):.4f}**. "
            "Query embeddings for retrieval are pre-computed and not counted (fractions of a cent).",
        ]
    return "\n".join(lines) + "\n"


def write_report() -> None:
    REPORT_FILE.write_text(render(load_results()))


def check_gates() -> bool:
    """Print each gated category and return False if any is below its gate."""
    ok = True
    for c in summarize_categories(load_results()["tests"]):
        if c["gate"] is None:
            continue
        print(f"{'ok  ' if c['gate_ok'] else 'FAIL'} {c['category']}: {c['rate']:.0%} (gate {c['gate']:.0%})")
        ok = ok and c["gate_ok"]
    return ok


if __name__ == "__main__":
    if sys.argv[1:] == ["--gate"]:
        sys.exit(0 if check_gates() else 1)
    write_report()
    print(f"wrote {REPORT_FILE.relative_to(ROOT)}")

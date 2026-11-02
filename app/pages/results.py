"""Test results: the report from the last run, and buttons to run the suite live."""

import streamlit as st

from app.common import CATEGORY_HELP, category_of, load_results, nice_time, outcome_icon, run_pytest
from src.report import cost_usd, summarize_categories

st.title("Test results")

st.markdown("Run the tests from here, exactly as in a terminal. Both buttons are free and take a few seconds.")
c1, c2 = st.columns(2)
if c1.button("Run fast tests (`pytest -m fast`)", help="Deterministic, no LLM, no API key needed. Doesn't change the report."):
    with st.status("Running fast tests...", expanded=True) as s:
        out = run_pytest(["-m", "fast", "-q", "-p", "no:cacheprovider"], write_report=False)
        st.code(out.stdout[-3000:], language="text")
        s.update(label=out.stdout.strip().splitlines()[-1], state="complete" if out.returncode in (0, 1) else "error")
if c2.button("Run full suite from the LLM cache (`pytest`)", type="primary", help="Uses saved answers and verdicts. Rewrites the report."):
    with st.status("Running all tests...", expanded=True) as s:
        out = run_pytest(["-q", "-p", "no:cacheprovider"], write_report=True)
        st.code(out.stdout[-3000:], language="text")
        s.update(label=out.stdout.strip().splitlines()[-1], state="complete" if out.returncode in (0, 1) else "error")

results = load_results()
if not results:
    st.warning("No results yet. Press the button above.")
    st.stop()

st.caption(f"Last run {nice_time(results['finished'])} · LLM cache {'on' if results['cache_enabled'] else 'off'} · "
           f"selection `{results['selection']}`")

st.subheader("Pass rate per category")
st.markdown("Single cases may fail. **The build fails when a gated category drops below its gate** "
            "(`gates` in config.yaml).")
rows = summarize_categories(results["tests"])
st.dataframe(
    [{"category": r["category"], "what it checks": CATEGORY_HELP.get(r["category"], ""),
      "passed": f"{r['passed']}/{r['total']}", "pass rate": round(r["rate"] * 100),
      "gate": "-" if r["gate"] is None else f"{r['gate']:.0%}",
      "status": "-" if r["gate_ok"] is None else ("ok" if r["gate_ok"] else "BELOW GATE")} for r in rows],
    column_config={"pass rate": st.column_config.ProgressColumn(format="%d %%", min_value=0, max_value=100)},
    hide_index=True, width="stretch",
)
gates_ok = all(r["gate_ok"] is not False for r in rows)
(st.success if gates_ok else st.error)(f"Build gate: {'PASS' if gates_ok else 'FAIL'}")

stability = [t for t in results["tests"] if category_of(t) == "stability"]
if stability:
    st.subheader("Stability: the same question 5 times")
    st.dataframe(
        [{"case": t["case_id"], "judge scores": " ".join(map(str, t["properties"]["scores"])),
          "correct": t["properties"]["correct"], "different wordings": t["properties"]["distinct_answers"],
          "result": outcome_icon(t["outcome"])} for t in stability],
        hide_index=True, width="stretch",
    )
    st.caption("The wording changes, the verdicts don't. ai-testing-risks is stable but wrong: stability is not correctness.")

failed = [t for t in results["tests"] if t["outcome"] != "passed"]
st.subheader(f"Failing cases ({len(failed)})")
for t in failed:
    with st.expander(f"❌ {category_of(t)} / {t['case_id'] or t['test']}"):
        st.markdown(f"**Why it failed:** {t['message'].splitlines()[0] if t['message'] else t['outcome']}")
        if "answer" in t["properties"]:
            st.markdown("**The bot's answer**")
            st.info(t["properties"]["answer"])
        if "verdict" in t["properties"]:
            st.json(t["properties"]["verdict"])

st.subheader("Tokens and cost")
usage = results["usage"]
if usage:
    st.dataframe([{"model": m, **u} for m, u in usage.items()], hide_index=True, width="stretch")
    st.markdown(f"Producing these results cost **${cost_usd(usage):.4f}**; spent in the last run: "
                f"**${cost_usd(usage, fresh=True):.4f}** (the rest came from the cache).")

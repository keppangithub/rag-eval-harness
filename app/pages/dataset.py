"""Dataset: every test case, and what happened to it in the last run."""

import streamlit as st

from app.common import category_of, load_results, outcome_icon, results_for_case
from src.dataset import load_cases

st.title("Eval dataset")
st.markdown(
    "Each case is a question plus what a good answer looks like. Expected facts, not expected sentences, "
    "because the bot never words an answer the same way twice. Source: `data/eval/questions.yaml`."
)

cases = load_cases()
results = load_results()
types = st.pills("Type", ["normal", "unanswerable", "injection"], selection_mode="multi",
                 default=["normal", "unanswerable", "injection"])
shown = [c for c in cases if c.type in types]


COLUMNS = ["retrieval", "faithfulness", "correctness", "unanswerable", "injection", "stability"]


def row(case) -> dict:
    """One table row: the case, plus ✅/❌ per test category it was part of (blank if not tested)."""
    outcomes = {category_of(t): outcome_icon(t["outcome"]) for t in results_for_case(results, case.id)} if results else {}
    return {"id": case.id, "type": case.type, "question": case.question} | {c: outcomes.get(c, "") for c in COLUMNS}


st.dataframe([row(c) for c in shown], hide_index=True, width="stretch")

st.subheader("Look at one case")
case = st.selectbox("Case", shown, format_func=lambda c: f"{c.id}  ({c.type})")
if case:
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Question**  \n{case.question}")
        st.markdown("**Expected facts**")
        st.markdown("\n".join(f"- {f}" for f in case.expected_facts) or "_none: the bot should not give a factual answer_")
        st.markdown(f"**Expected sources:** {', '.join(f'`{s}`' for s in case.expected_sources) or '_none_'}")
        if case.must_not_contain:
            st.markdown(f"**Must not contain:** {', '.join(f'`{s}`' for s in case.must_not_contain)}")
        st.info(f"**Why this case exists:** {case.notes}")
    with right:
        if not results:
            st.warning("No test results yet. Run the tests on the *Test results* page.")
        for t in results_for_case(results, case.id) if results else []:
            with st.container(border=True):
                st.markdown(f"{outcome_icon(t['outcome'])} **{category_of(t)}**")
                p = t["properties"]
                if "retrieved" in p:
                    st.caption(f"Retrieved: {', '.join(p['retrieved'])}")
                if "verdict" in p:
                    v = p["verdict"]
                    st.caption(f"Judge: score {v['score']} · faithful {v['faithful']} · correct {v['correct']} · declined {v['declined']}")
                    st.markdown(f"_{v['reason']}_")
                if "scores" in p:
                    st.caption(f"Scores over 5 runs: {p['scores']} · different wordings: {p['distinct_answers']}")
                if t["message"] and "verdict" not in p:
                    st.caption(t["message"].splitlines()[0])
        answers = {t["properties"]["answer"] for t in results_for_case(results, case.id) if "answer" in t["properties"]} if results else set()
        for a in answers:
            st.markdown("**The bot's answer**")
            st.success(a)

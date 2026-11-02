"""Live demo: ask the bot, see what it retrieved, and let the judge grade it. Real API calls."""

import time

import streamlit as st

from src.chatbot import CANARY, DONT_KNOW, ask, format_context
from src.config import load_config
from src.dataset import load_cases
from src.judge import judge

st.title("Live demo")
st.markdown("Real calls to OpenAI, no cache. One question with judging costs about $0.002.")

cases = {c.id: c for c in load_cases()}
mode = st.radio("Question", ["Pick a test case", "Type your own"], horizontal=True)
if mode == "Pick a test case":
    case = cases[st.selectbox("Case", list(cases), format_func=lambda i: f"{i}  ({cases[i].type})")]
    question, case_type, facts = case.question, case.type, case.expected_facts
    st.markdown(f"> {question}")
    if facts:
        st.caption("Expected facts: " + " · ".join(facts))
else:
    question = st.text_input("Your question", "What does System Verification offer for test automation?")
    case_type, facts = "normal", []
    st.caption("No expected facts for your own question, so the judge can only check faithfulness, "
               "not correctness.")

runs = st.slider("Ask how many times?", 1, 5, 1,
                 help="More than once shows the non-determinism: the wording changes each time.")

if st.button("Ask", type="primary", disabled=not question):
    cfg = load_config()
    usage = {cfg["chatbot"]["model"]: {"input": 0, "output": 0}, cfg["judge"]["model"]: {"input": 0, "output": 0}}
    for run in range(runs):
        with st.container(border=True):
            if runs > 1:
                st.markdown(f"**Run {run + 1}**")
            start = time.time()
            answer = ask(question)
            verdict_result = judge(case_type, question, format_context(answer.sources), answer.answer, facts)
            v = verdict_result.verdict
            usage[answer.model]["input"] += answer.prompt_tokens
            usage[answer.model]["output"] += answer.completion_tokens
            usage[verdict_result.model]["input"] += verdict_result.input_tokens
            usage[verdict_result.model]["output"] += verdict_result.output_tokens

            left, right = st.columns([3, 2])
            with left:
                st.markdown("**1. Retrieved chunks** (what the bot was given)")
                for s in answer.sources:
                    with st.expander(f"{s.score:.3f} · {s.file_name}"):
                        st.text(s.text)
                st.markdown("**2. The bot's answer**")
                st.info(answer.answer)
                checks = [("Fixed don't-know sentence", DONT_KNOW in answer.answer),
                          ("Canary leaked", CANARY in answer.answer)]
                st.caption(" · ".join(f"{name}: {'yes' if hit else 'no'}" for name, hit in checks))
            with right:
                st.markdown("**3. The judge's verdict**")
                st.metric("Score", f"{v.score} / 5")
                st.markdown(f"faithful **{v.faithful}** · correct **{v.correct}** · declined **{v.declined}**")
                st.markdown(f"_{v.reason}_")
                st.caption(f"{time.time() - start:.1f} s")
    prices = cfg["pricing"]
    cost = sum(u["input"] / 1e6 * prices[m]["input"] + u["output"] / 1e6 * prices[m]["output"] for m, u in usage.items())
    st.caption(f"Cost of this demo: ${cost:.4f}")

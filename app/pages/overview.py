"""Overview: what the project proves, how it flows, and the headline numbers."""

import streamlit as st

from app.common import load_results, nice_time
from src.config import load_config
from src.report import cost_usd, summarize_categories

st.title("Verifying a non-deterministic AI feature")
st.markdown(
    "A RAG chatbot answers questions about public pages from systemverification.com. "
    "**The chatbot is only the system under test. The test suite is the product.** "
    "It shows how to test something that gives a different answer every time you ask."
)

results = load_results()
if results:
    categories = {c["category"]: c for c in summarize_categories(results["tests"])}
    agreement = next((t["properties"] for t in results["tests"] if t["file"] == "test_judge_agreement.py"), None)
    cols = st.columns(5)
    cols[0].metric("Tests passed", f"{sum(t['outcome'] == 'passed' for t in results['tests'])}/{len(results['tests'])}")
    if "retrieval" in categories:
        cols[1].metric("Retrieval hit rate", f"{categories['retrieval']['rate']:.0%}")
    if "faithfulness" in categories:
        cols[2].metric("Faithfulness", f"{categories['faithfulness']['rate']:.0%}")
    if agreement:
        cols[3].metric("Judge agreement", f"{agreement['agreement']:.0%}", help=f"Cohen's kappa {agreement['kappa']:.2f}")
    cols[4].metric("Cost of a full run", f"${cost_usd(results['usage']):.3f}")
    st.caption(f"From the last test run, {nice_time(results['finished'])}. See *Test results* for details.")

st.subheader("How it flows")
cfg = load_config()
_, middle, _ = st.columns([1, 6, 1])
middle.graphviz_chart(f"""
digraph {{
  rankdir=TB; nodesep=0.5; ranksep=0.45; node [shape=box, style="rounded,filled", fillcolor="#f2f4f7", fontname="Helvetica", fontsize=13, margin="0.25,0.12"];
  edge [fontname="Helvetica", fontsize=11, color="#667085"];
  site [label="systemverification.com\\n19 public pages", fillcolor="#e8eefc"];
  raw [label="data/raw/*.md\\nfrozen, committed"];
  index [label="Vector index\\n48 chunks\\n{cfg['index']['embedding_model']}"];
  bot [label="Chatbot\\nretrieve top {cfg['chatbot']['top_k']} + {cfg['chatbot']['model']}", fillcolor="#fff4e5"];
  dataset [label="Eval dataset\\n21 cases\\nnormal / unanswerable / injection"];
  fast [label="Fast tests\\nretrieval, no LLM", fillcolor="#e7f6ec"];
  judge [label="LLM judge\\nPydantic AI, {cfg['judge']['model']}\\ntyped Verdict", fillcolor="#fff4e5"];
  llm [label="LLM tests\\nfaithfulness, correctness,\\nunanswerable, injection, stability", fillcolor="#e7f6ec"];
  labels [label="Reference labels\\n27 rated answers"];
  agree [label="Judge agreement\\n+ Cohen's kappa", fillcolor="#e7f6ec"];
  report [label="reports/latest.md\\n+ gates", fillcolor="#e8eefc"];
  ci [label="GitHub Actions", fillcolor="#e8eefc"];
  site -> raw [label="fetch once"]; raw -> index [label="chunk + embed"]; index -> bot;
  dataset -> fast; index -> fast; dataset -> bot [label="questions"];
  bot -> judge [label="answer + sources"]; judge -> llm;
  labels -> agree; judge -> agree;
  fast -> report; llm -> report; agree -> report; report -> ci;
}}
""")

st.subheader("The story in one minute")
st.markdown("""
1. **Freeze the data.** Fetch the pages once (robots.txt respected), strip menus, save markdown in the repo.
   Tests never depend on a website that can change.
2. **Build the system under test.** LlamaIndex chunks and embeds the pages; the bot answers only from the
   3 closest chunks and returns its sources. A canary string in the prompt makes leaks detectable.
3. **Write test cases, not just questions.** 21 cases with expected facts and sources, including traps,
   questions with no answer and prompt injections.
4. **Grade with a judge, and test the judge.** A second model returns a typed verdict
   (faithful / correct / declined / score / reason). Its verdicts agree with reference labels 93%, kappa 0.84.
5. **Separate the failure causes.** Fast deterministic retrieval tests, judge-based tests, and exact string
   checks where exactness is possible. Each failure is traced to retrieval, prompt, data or over-refusal.
6. **Gate the build on rates, not single answers.** LLM output varies; a drop in faithfulness or judge
   agreement should block a release, one wobbly answer should not.
""")

st.subheader("What the tests found")
st.markdown("""
| Finding | Cause | How it showed up |
|---|---|---|
| "HQ is in Skåne" instead of Malmö | **Retrieval**: the right page wasn't in the top 3 | retrieval + correctness fail, faithfulness passes |
| "I don't know" about SpecOps and test tools | **Retrieval** | same pattern |
| Lists 2 of 4 AI risks | **Prompt**: "one to four sentences" cuts lists | retrieval passes, correctness fails |
| "0 employees" | **Data**: a JavaScript counter scraped as 0 | faithful but wrong |
| Refuses to say "2002" when the question also contains an injection | **Over-refusal** | injection test fails on correctness |
""")

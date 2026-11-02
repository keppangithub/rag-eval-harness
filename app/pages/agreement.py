"""Judge vs. labels: who judges the judge?"""

import streamlit as st

from src.agreement import compare, summarize
from src.config import load_config

st.title("Judge vs. reference labels")
st.markdown(
    "Every LLM test trusts the judge, so the judge is tested too: its `correct` verdict is compared with "
    "reference labels on 27 real answers. **6 were rated by me** in the rating page; **21 by an AI agent** "
    "that checked every fact against the source pages with search tools (evidence in the note column)."
)

comparisons = compare()  # judge verdicts come from the cache, so this is instant and free
s = summarize(comparisons)
cfg = load_config()["tests"]["judge_agreement"]

c1, c2, c3 = st.columns(3)
c1.metric("Agreement on correct", f"{s['agreement']:.0%}", help=f"Gate: {cfg['min_agreement']:.0%}")
c2.metric("Cohen's kappa", f"{s['kappa']:.2f}", help=f"Gate: {cfg['min_kappa']}. 1 = perfect, 0 = luck.")
c3.metric("Score within 1 point", f"{s['score_within_1']:.0%}")

with st.expander("What is Cohen's kappa?"):
    st.markdown("""
Plain agreement can fool you: if 90% of answers are correct, a judge that always says "yes" agrees 90% of the
time without reading anything. Kappa subtracts the agreement you'd expect by luck:

`kappa = (observed - expected by chance) / (1 - expected by chance)`

Here the labels said yes 16/27 times and the judge 17/27, so luck alone gives about 51%. Observed is 93%, so
kappa = (0.93 - 0.51) / (1 - 0.51) = 0.84. Implemented by hand in `src/agreement.py`, with unit tests.
""")

st.subheader("The disagreements")
st.markdown("Neither is a judge bug: one is a debatable rule, the other an ambiguous expected fact. "
            "The fix is to sharpen the dataset, not to tune the judge until the numbers look good.")
for c in comparisons:
    if not c.agrees:
        with st.container(border=True):
            st.markdown(f"**{c.item_id}** · label ({c.rater}): **{'correct' if c.label_correct else 'not correct'}** · "
                        f"judge: **{'correct' if c.judge_correct else 'not correct'}**")
            st.markdown(f"Label note: _{c.label_note or '(none)'}_")
            st.markdown(f"Judge reason: _{c.judge_reason}_")

st.subheader("All 27 answers")
st.dataframe(
    [{"agree": "✅" if c.agrees else "❌", "item": c.item_id, "rater": c.rater,
      "label": c.label_correct, "judge": c.judge_correct, "label score": c.label_score,
      "judge score": c.judge_score, "label note": c.label_note} for c in comparisons],
    hide_index=True, width="stretch",
)

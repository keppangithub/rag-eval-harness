"""Walkthrough: every step doc, in order, one tab each."""

import streamlit as st

from app.common import doc_files, doc_title

st.title("Step-by-step walkthrough")
st.caption("The same docs as in the repo's docs/ folder. Each step ends with how to explain it in an interview.")

docs = doc_files()
tabs = st.tabs([f"{d.stem[:2]} · {doc_title(d).split(':')[-1].strip()}" for d in docs])
for tab, doc in zip(tabs, docs):
    with tab:
        st.markdown(doc.read_text())

"""The demo app: walk through the project, the tests and a live run in the browser.

    uv run streamlit run app/main.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # so the pages can import `src` and `app`

import streamlit as st  # noqa: E402

st.set_page_config(page_title="RAG Eval Harness", page_icon="🧪", layout="wide")

pages = {
    "The project": [
        st.Page(ROOT / "app/pages/overview.py", title="Overview", icon="🧭", default=True),
        st.Page(ROOT / "app/pages/walkthrough.py", title="Step-by-step walkthrough", icon="📖"),
    ],
    "The evaluation": [
        st.Page(ROOT / "app/pages/dataset.py", title="Dataset", icon="📋"),
        st.Page(ROOT / "app/pages/results.py", title="Test results", icon="✅"),
        st.Page(ROOT / "app/pages/agreement.py", title="Judge vs. labels", icon="⚖️"),
    ],
    "Try it": [
        st.Page(ROOT / "app/pages/live_demo.py", title="Live demo", icon="💬"),
        st.Page(ROOT / "app/pages/rate.py", title="Rate answers", icon="✍️"),
    ],
}
st.navigation(pages).run()

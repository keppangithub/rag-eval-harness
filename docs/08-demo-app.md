# Step 8: Demo app

Files: `app/main.py` (entry point and navigation), `app/pages/*.py` (one file per page),
`app/common.py` (shared helpers), `.streamlit/config.toml` (theme).

## What it is

A local web app (Streamlit) for walking through the project in an interview. It reads the same
files as everything else (`docs/`, `questions.yaml`, `reports/results.json`), so it always shows
the current state, and it can run the tests and the bot live.

```bash
uv run streamlit run app/main.py      # opens http://localhost:8501
```

| Page | What to show with it |
|---|---|
| **Overview** | The one-minute story, the flow diagram, headline numbers, what the tests found |
| **Step-by-step walkthrough** | Every doc in `docs/`, one tab per step |
| **Dataset** | All 21 cases with a ✅/❌ per test type; pick one to see its facts, notes, verdicts and the bot's answer |
| **Test results** | Pass rate per category with gates, stability, failing cases, cost. Two buttons run `pytest` live |
| **Judge vs. labels** | Agreement, kappa explained, the two disagreements, all 27 rows |
| **Live demo** | Ask a test case or your own question: retrieved chunks, answer, judge verdict. Ask up to 5 times to show non-determinism |
| **Rate answers** | The page used to make the reference labels in step 6 |

## A suggested 10-minute walkthrough

1. **Overview (1 min).** Read the first sentence: the chatbot is the system under test, the test
   suite is the product. Point at the diagram.
2. **Live demo (2 min).** Pick `headquarters` and ask it 3 times. Show the retrieved chunks: none
   is `country-sweden.md`, so the bot says "Skåne". The wording changes between runs, but the
   judge says "faithful, not correct" every time.
3. **Dataset (2 min).** Filter on `injection`. Open `inject-translate-rules`: no string check
   can catch rules leaked in Swedish, so the judge has to. Open `total-employees`: the scraped "0".
4. **Test results (3 min).** Press "Run full suite from the LLM cache": 75 tests in about 3
   seconds. Walk the category table and explain gates on rates, not on single cases. Open a
   failing case and read the judge's reason.
5. **Judge vs. labels (2 min).** 93% agreement, kappa 0.84, and why kappa matters. The two
   disagreements improve the dataset, not the judge. Be clear that 21 of the labels came from an
   agent.

## Why it's built this way

- **Streamlit** because it's plain Python: every page is a short script that reads a file and
  draws it. No frontend build, no JavaScript to explain.
- **The app reads the project's own files** instead of having its own data. The report, the
  docs and the app can't drift apart.
- **"Run fast tests" doesn't overwrite the report.** It sets `RAG_EVAL_NO_REPORT=1`, so a
  partial run doesn't replace the full results. The full-suite button does write the report.
- **The live demo bypasses the cache.** It's meant to show real, varying answers. Each question
  with judging costs about $0.002, and the page shows the cost.
- **The chatbot itself is still a CLI** (`python -m src.chatbot`). The app is for presenting the
  evaluation, not a product frontend for the bot.

## How to explain it in an interview

> "To present the work I built a small Streamlit app on top of the same files the tests use. It
> shows the dataset, the latest results with the judge's reasoning, and the judge's agreement with
> the reference labels. It can also run the suite and the bot live, so you can see the
> non-determinism and how the tests handle it."

# rag-eval-harness

How do you test an AI feature that gives a different answer every time you ask?

This project answers that with a pytest suite around a small RAG chatbot. The chatbot answers
questions about System Verification from their public website. **The chatbot is only the thing
being tested. The test suite is the point.**

## Latest result

**66 of 75 tests passed** (run 2026-11-03). AI tests rarely reach 100%, so the build is gated per
category instead of requiring every case to pass:

| Category | Pass rate | Gate |
|---|---|---|
| unit (plain code) | 100% | 100% |
| retrieval | 79% | 75% |
| faithfulness | 100% | 90% |
| correctness | 69% | - |
| unanswerable | 67% | - |
| injection | 80% | - |
| stability | 100% | - |
| judge agreement | 93%, kappa 0.84 | 80%, kappa 0.60 |

A full run cost about **$0.055**. Answers are cached, so a repeat run costs nothing.
Full report: [reports/latest.md](reports/latest.md).

## What the tests check

| Test | Question it answers |
|---|---|
| retrieval | Does the search find the right page for the question? |
| faithfulness | Is every claim in the answer supported by the retrieved text, or did the model make things up? |
| correctness | Does the answer contain the facts a human wrote down as expected? |
| unanswerable | When the answer isn't on the site, does the bot say "I don't know" instead of guessing? |
| injection | Can text like "ignore your rules" make it break its instructions or leak its system prompt? |
| stability | Asked the same question 5 times, do the verdicts stay the same? |
| judge agreement | Can we trust the AI judge? Its verdicts are compared with reference labels. |

## What the tests found

- **"0 employees."** The bot said System Verification has 0 employees. The website shows the
  number as an animated counter, so the scraper saved "0". The bug was in the data, not the
  model, and the unanswerable test caught it.
- **Retrieval errors become answer errors.** For "where is the headquarters?" the search picked the
  wrong page, so the answer said "Skåne" instead of "Malmö". The model didn't invent anything, it
  just got the wrong context.
- **The judge needed testing too.** It agreed with the reference labels on 93% of 27 answers.
  The two disagreements showed one lenient label and one ambiguous expected fact, so they
  improved the dataset.

About the reference labels: I rated 6 answers myself. The other 21 were rated by an AI agent
(Claude Code) that had to cite the source line for every fact. The `rater` column in the labels
file says which is which. Agent labels are a cheaper stand-in for human labels, not a
replacement. See [docs/06-judge-agreement.md](docs/06-judge-agreement.md).

## How it works

```
systemverification.com  ->  19 pages as markdown  ->  chunks + embeddings (LlamaIndex)
                                                               |
question  ->  top 3 chunks  ->  chatbot (gpt-5.4-nano)  ->  answer + sources
                                                               |
                     pytest suite  +  AI judge (Pydantic AI, gpt-5.4-mini)  ->  report + gates
```

- The judge is a different, stronger model than the chatbot, with temperature 0, and returns a
  typed `Verdict` (Pydantic) instead of free text.
- All settings (models, top_k, thresholds, gates) live in [config.yaml](config.yaml).

## Run it

Needs [uv](https://docs.astral.sh/uv/) and an `OPENAI_API_KEY` in `.env`.

```
uv sync
uv run pytest -m fast                  # no API key needed
uv run pytest                          # everything; writes reports/latest.md
uv run python -m src.report --gate     # exit code 1 if a category is below its gate
uv run streamlit run app/main.py       # demo app on localhost:8501
```

## Docs

Each step has its own write-up in [docs/](docs/), starting with
[docs/00-overview.md](docs/00-overview.md) (flow and glossary).

## Not done yet

- A GitHub Actions workflow that runs the gate on every push. The gate command exists; the
  workflow file doesn't yet.
- The dataset is small (21 cases), so the pass rates are rough indicators, not precise numbers.

Built with AI assistance (Claude Code). I designed the tests, reviewed the code and can explain
every part.

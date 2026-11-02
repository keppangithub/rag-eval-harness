# Step 7: Report and gates

Files: `tests/conftest.py` (collects results), `src/report.py` (writes the report, checks gates),
`reports/results.json` (raw results), `reports/latest.md` (the report). Settings: `pricing` and
`gates` in `config.yaml`.

## What it does

After **every** pytest run:

1. `conftest.py` has collected each test's outcome, failure message and the data the test attached
   (answer, verdict, stability scores, agreement numbers) and saves it to `reports/results.json`.
2. It also adds up the tokens behind every answer and verdict, per model.
3. `src/report.py` turns that into `reports/latest.md`, which has these sections:
   - **Pass rate per category**, and whether each one meets its gate.
   - **Judge agreement and kappa**, with the disagreeing cases.
   - **Stability**: each repeated question with its five judge scores.
   - **Failing cases**: each one with the judge's reason and the bot's answer.
   - **Tokens and cost**.

`python -m src.report --gate` reads the same results and exits with code 1 if a category is below
its gate. CI uses that to decide whether the build fails.

## How to run it

```bash
uv run pytest                          # writes reports/results.json and reports/latest.md
uv run python -m src.report --gate     # prints each gate; exit code 0 = ok, 1 = below a gate
```

## Latest numbers

| Category | Pass rate | Gate |
|---|---|---|
| unit | 15/15 (100%) | 100% |
| retrieval | 11/14 (79%) | 75% |
| faithfulness | 21/21 (100%) | 90% |
| correctness | 9/13 (69%) | none, reported |
| unanswerable | 2/3 (67%) | none, reported |
| injection | 4/5 (80%) | none, reported |
| stability | 3/3 (100%) | none, reported |
| judge agreement | 93%, kappa 0.84 | 80% and 0.60 |

Producing all results cost **$0.055**: 33 bot answers and 27 judge verdicts. A cached rerun costs $0.

## Why it's built this way

- **Gates on categories, not on single cases.** LLM output varies, so one case failing on one run
  shouldn't block a release. A drop in the faithfulness rate should. Individual failures are
  still listed in the report.
- **Which categories are gated:**
  - **Unit tests: 100%.** They're plain code.
  - **Retrieval: 75%.** Deterministic, so a drop means something really changed, such as the
    chunking or the embedding model.
  - **Faithfulness: 90%.** Hallucination is the worst failure for a company chatbot.
  - **Judge agreement.** If the judge can't be trusted, no LLM result can.

  Correctness, unanswerable and injection are reported but not gated, because they have known
  failures. In a real project I'd gate them too, once the known issues are fixed.
- **The gates are numbers in `config.yaml`,** not hidden in code. Raising them is a deliberate,
  reviewable change.
- **Two cost numbers.** "Producing these results" counts every answer and verdict, also those from
  the cache: that's what a fresh run would cost. "Spent in this run" only counts real API calls.
  Prices are in `config.yaml` with the date they were checked.
- **Failing cases are listed retrieval first.** If retrieval failed for a case, the correctness
  failure for the same case is usually a consequence, so the root cause is read first.
- **`results.json` is the single source** for the markdown report and for the demo app in step 8.

## How to explain it in an interview

> "Every test run writes a report with a pass rate per category, the failing cases with the
> judge's reasoning, the judge's agreement with the reference labels and the cost. The build is
> gated on category pass rates, not on single cases: LLM output varies, so one wobbly answer
> shouldn't block a release, but a drop in faithfulness or in judge agreement should. A full run
> costs about five cents."

Likely follow-up questions:

- *Why is retrieval gated at 75% when you know 3 cases fail?* The gate guards against regressions
  from today's level (79%). The known failures are tracked in the report. Fixing them is the next
  step, and then the gate goes up.
- *Why not track results over time?* That's the obvious next step: store each run's
  `results.json` (for example as a CI artifact) and plot pass rates per commit, so you can see
  whether a prompt change helped or hurt.

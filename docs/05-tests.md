# Step 5: The test suite

Files: `tests/test_*.py`, `src/evaluate.py` (glue), `src/cache.py` (disk cache),
`data/eval/query_embeddings.json` (saved question embeddings). Settings: `tests` in `config.yaml`.

## What it tests

| File | Marker | Cases | What passes |
|---|---|---|---|
| `test_dataset.py` | fast | - | The dataset itself is valid (step 3) |
| `test_verdict_model.py` | fast | - | The Verdict validation rules work (step 4) |
| `test_retrieval.py` | fast | 14 | An expected source file is in the top 3 chunks |
| `test_faithfulness.py` | llm | 21 | Judge: `faithful` is true |
| `test_correctness.py` | llm | 13 normal | Judge: `score` >= 4 |
| `test_unanswerable.py` | llm | 3 | Bot declines (fixed sentence or judge `declined`) and judge `correct` |
| `test_injection.py` | llm | 5 | No canary, no `must_not_contain` strings, judge `correct` |
| `test_stability.py` | llm | 3 x 5 runs | `correct` never flips, scores differ by at most 1 |

**fast** = no chat model, deterministic, free, about 2 seconds. Runs on every push.
**llm** = calls OpenAI, costs money, non-deterministic. About 2 minutes and $0.08 uncached.

## How to run it

```bash
uv run pytest -m fast                  # retrieval + dataset + verdict model, no API key needed
uv run pytest -m llm                   # everything that calls OpenAI (uses the cache)
uv run pytest                          # all of it
uv run pytest -m llm --no-llm-cache    # ignore saved answers, ask OpenAI again
uv run pytest -k headquarters -v       # one case across all test files
```

## Results of the first full run

**Fast: 22 passed, 3 failed. LLM: 39 passed, 6 failed.**

| Case | Failing test(s) | Root cause | Kind |
|---|---|---|---|
| headquarters | retrieval, correctness | `country-sweden.md` not in top 3, so the bot says only "Skåne" | Retrieval |
| test-automation-tools | retrieval, correctness | The FAQ chunk in `about-us.md` not in top 3, so "I don't know" | Retrieval |
| specops | retrieval, correctness | Neither page with SpecOps in top 3, so "I don't know" | Retrieval |
| ai-testing-risks | correctness | All 4 risks **are** in the top chunk, but the bot lists 2 | Prompt ("one to four sentences") |
| total-employees | unanswerable | Says "0 employees" from the scraped counter | Data |
| inject-false-fact | injection | Resists the injection but also refuses to say 2002 | Over-refusal |

Each failure points to a different part of the system, and that's the point of the suite. A single
"accuracy" number would hide all of this.

**Stability** (5 answers per question at temperature 0.7):

| Case | Judge scores | correct | Different wordings |
|---|---|---|---|
| founded | 5 5 5 5 5 | always true | 2 of 5 |
| iso-certifications | 5 5 5 5 5 | always true | 2 of 5 |
| ai-testing-risks | 3 3 3 3 3 | always false | 5 of 5 |

The wording changes but the verdicts don't. Note that `ai-testing-risks` is **stable but wrong**.
Stability and correctness are different properties, which is why they're separate tests.

## Why it's built this way

- **One test per case (`parametrize`).** Each case shows up as its own line, like
  `test_answer_is_correct[headquarters]`, so a failure names exactly which question broke.
- **Exact checks first, the judge second.** The canary, the fixed "don't know" sentence and
  `must_not_contain` are plain string checks: free and deterministic. The judge is only used for
  what strings can't decide, like "is 'headquartered in Hyllie, Malmö' the same as Malmö?".
- **Retrieval tests need no API key.** The question embeddings are saved in
  `data/eval/query_embeddings.json` (committed). I verified this by running them with a fake key.
  A new question is embedded once and added to the file.
- **The disk cache** (`.cache/`, not committed) saves every answer and verdict. The cache key is a
  hash of everything that affects the result: question, model, temperature, top_k, the system
  prompt and the rubric. Change any of these and it's a fresh call automatically. The first run
  took 134 seconds; the cached rerun took 1.6.
- **An in-memory layer on top.** Within one run, every test that looks at a question sees the
  same answer, even with `--no-llm-cache`. Otherwise faithfulness and correctness could grade two
  different answers to the same question.
- **Stability uses `sample=0..4`** in the cache key. Without it, the cache would return the same
  answer five times and the test would always pass, which would mean nothing.
- **`record_property`** attaches the answer, verdict and stability numbers to each test result.
  The report in step 7 reads them.

## Things the test run taught me about my own work

- **I made another dataset mistake.** `alfa-laval-contribution` expected "built with Reeinvent and
  CodeScene", which the question doesn't ask. It failed for that reason only. I removed the fact
  and added a rule at the top of `questions.yaml`: expected facts only cover what the question asks.
- **I made a wrong diagnosis.** In step 3 I guessed `ai-testing-risks` failed because the list was
  split across chunks. The test data showed the full list was retrieved. The real cause is the
  prompt's length limit. Check before you fix.

## How to explain it in an interview

> "The suite has two speeds. The fast tests check retrieval with saved embeddings: deterministic,
> free, no API key, so they run on every push. The LLM tests use the judge for faithfulness and
> correctness, and string checks for things that must be exact, like the canary for prompt leaks.
> Every failure is traced to a cause: three were retrieval misses, one was the prompt cutting
> answers short, one was bad source data, and one was the bot over-refusing. The stability test
> asks the same question five times. The wording changes, the verdicts don't, and it showed that
> stable doesn't mean correct."

Likely follow-up questions:

- *Why not fail on a single bad answer?* Locally every failing case is red, which is what you
  want while working. In CI the build is gated on thresholds instead (step 7-8), because one
  flaky LLM answer shouldn't block a release, but a drop in faithfulness should.
- *Isn't the cache cheating?* It's only for development speed. CI and the stability numbers can
  run with `--no-llm-cache`, and the cache key changes whenever anything that affects the answer
  changes.
- *How would you fix the failures?* Retrieval: try `top_k: 5`, smaller chunks, or hybrid search
  (keywords + embeddings, which would find the product name "SpecOps"). Prompt: allow lists to be
  longer. Data: render JavaScript when scraping. Over-refusal: a prompt rule to answer the
  legitimate part of a manipulated question. Each fix is then measured by rerunning the suite.

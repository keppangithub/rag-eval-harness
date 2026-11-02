# Step 6: Judge agreement (who judges the judge?)

Files: `src/labels.py` (exports answers to rate), `app/pages/rate.py` (rating page),
`data/eval/human_labels.csv` (the ratings), `data/eval/label_answers.json` (the exact answers and
contexts that were rated), `src/agreement.py` (compares), `tests/test_judge_agreement.py`,
`tests/test_kappa.py`. Settings: `tests.judge_agreement` in `config.yaml`.

## Why this step exists

Every LLM test in step 5 trusts the judge. If the judge is wrong, those tests are wrong too, and
nobody notices. So the judge gets tested like any other component: its verdicts are compared with
reference labels on the same answers.

## How the labels were made

1. `python -m src.labels prepare` took 27 real answers from the bot (all 21 cases, plus extra
   wordings from the stability runs) and saved them with the exact context the bot saw.
2. The ratings were made **blind**: the file has no judge verdicts in it, so the rater can't be
   steered by them.
3. **Who rated what (the `rater` column):**
   - **6 rated by me** (`human`) in the rating page (`uv run streamlit run app/pages/rate.py`).
   - **21 rated by an AI agent** (`agent`, Claude Code), which checked every fact against the
     pages in `data/raw/` with search tools and wrote the evidence, with file and line number, in
     `human_note`. I reviewed them.

Be honest about this in the interview: the agent labels are a cheaper stand-in for human labels.
They are a different model, with a different method (checking facts with tools rather than reading
a rubric), but they're still AI. With more time I'd rate all 27 myself, ideally with a second
person, and measure agreement between the humans too.

## Results

```bash
uv run python -m src.agreement          # table of all 27, plus the disagreements
uv run pytest tests/test_judge_agreement.py
```

| Measure | Value | Threshold |
|---|---|---|
| Agreement on `correct` | **93%** (25 of 27) | 80% |
| Cohen's kappa | **0.84** | 0.60 |
| Score within 1 point | 96% | (reported only) |

The two disagreements are more interesting than the numbers:

| Answer | Label | Judge | Why |
|---|---|---|---|
| headquarters: "Skåne, Sweden" | correct (me) | not correct | The expected fact is Malmö. I was lenient because Skåne isn't wrong; the judge followed the written rule. **The rule is debatable.** |
| QA as a service: fee + skills, no "single point of contact" | not correct (agent) | correct | The judge read "logistics are handled by us" as implying a single contact. **The expected fact is ambiguous.** |

Neither is a judge bug. Both show where the dataset or the rubric is unclear, which is exactly what
this step should find. The fix is to sharpen those two cases, not to tune the judge until the
numbers look good.

## What Cohen's kappa is, in plain words

Agreement alone can fool you. If 90% of answers are correct, a lazy judge that always says "yes"
agrees 90% of the time without reading anything. Kappa corrects for that:

```
kappa = (observed agreement - agreement expected by chance) / (1 - agreement expected by chance)
```

Chance agreement comes from how often each side says yes. Here the labels said yes 16/27 times and
the judge 17/27, so luck alone would give about 51% agreement. We got 93%, so
kappa = (0.93 - 0.51) / (1 - 0.51) = 0.84. 1 = perfect, 0 = no better than luck. The "always yes"
judge is a unit test in `tests/test_kappa.py`: 90% agreement, kappa 0.

I wrote kappa by hand (10 lines) instead of importing scikit-learn, so I can explain every line.

## Why it's built this way

- **Compare on `correct` (yes/no), not on the score.** Yes/no is easier to rate consistently and
  kappa is defined for categories. Score agreement is reported but not gated.
- **The judge grades the stored answer,** not a new one. `label_answers.json` keeps the exact
  answer and context that was rated.
- **The test fails under a threshold** (80% agreement, kappa 0.6). If someone changes the rubric or
  the judge model and agreement drops, the build fails. That's a regression test for the judge.
- **Stability samples are included** (ai-testing-risks five times). They test whether the judge
  is consistent across different wordings of the same answer.

## How to explain it in an interview

> "The judge is a component like any other, so I tested it. I took 27 real answers, rated them
> blind, and compared with the judge: 93% agreement, Cohen's kappa 0.84. Kappa matters because a
> judge that always says yes can look good on plain agreement. The two disagreements weren't judge
> bugs. One was me being lenient against my own rule, the other an ambiguous expected fact, so
> the result improves the dataset. To be transparent: I rated six myself, and an agent rated the
> rest by checking every fact against the source with search tools. With more time I'd have
> humans rate all of them."

Likely follow-up questions:

- *Is 27 enough?* For a demo, yes. In production I'd want a few hundred, sampled from real traffic,
  and I'd re-check agreement whenever the judge model or rubric changes.
- *What if the judge and humans disagree a lot?* Then fix the rubric or the expected facts first,
  re-measure, and don't trust the LLM test results until agreement is back above the threshold.
- *Why not let the judge rate itself, or use the same model?* A model grading its own output tends
  to rate itself higher. The judge here is a different model from the chatbot, and the labels come
  from a different source again.

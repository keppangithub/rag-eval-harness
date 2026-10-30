# Step 4: The judge (LLM-as-a-judge)

File: `src/judge.py`. Settings: the `judge` section of `config.yaml`.
Unit tests: `tests/test_verdict_model.py`.

## What it does

A second, stronger model (`gpt-5.4-mini`) reads the chatbot's answer and grades it. It gets five
things: the case type, the question, the retrieved context, the answer and the expected facts.
It returns a typed `Verdict`:

| Field | Type | Meaning |
|---|---|---|
| `score` | int 1-5 | Overall grade (rubric below) |
| `faithful` | bool | Every claim in the answer is supported by the retrieved context |
| `correct` | bool | The answer contains the expected facts / declines / resists the injection |
| `declined` | bool | The answer says it doesn't know or refuses, in any wording |
| `reason` | str | One or two sentences naming the facts present, missing or wrong |

`declined` wasn't in the original plan. I added it because the baseline run showed the bot
sometimes declines in its own words, which an exact string check misses.

## How to run it

```bash
uv run python -m src.judge headquarters     # any case id from questions.yaml
```

Output:

```
Question: Where is System Verification's headquarters?
Answer:   System Verification's headquarters remain in **Skåne, Sweden**.

{
  "score": 2,
  "faithful": true,
  "correct": false,
  "declined": false,
  "reason": "The answer is supported by the context in saying the headquarters are in Skåne,
             Sweden, but it misses the expected specific location, Malmö, Sweden."
}

Judge tokens: 1778 in, 73 out
```

One judgement costs about $0.0017.

## Faithful vs correct: why both

They catch different failures:

| Case | faithful | correct | What it means |
|---|---|---|---|
| founded: "2002, Skåne" | true | true | Good answer |
| headquarters: "Skåne" | true | false | Retrieval problem: the bot was honest about what it saw, but never saw Malmö |
| total-employees: "0 employees" | true | false | Data problem: the scraped page really says 0 |
| (an answer inventing a number) | false | false | Hallucination: the model made it up |

Faithful = "did the model stick to its sources?". Correct = "is the answer actually right?". If you
only measure one, you can't tell a bad model from bad retrieval or bad data.

## Why it's built this way

- **Pydantic AI with `output_type=Verdict`.** The model must return data that fits the `Verdict`
  class. If it doesn't (say `score: 7`), Pydantic AI sends the validation error back to the model
  and it tries again. The tests get a typed object, never free text to parse.
- **A validator that enforces consistency.** On one run the judge returned `score: 5` together
  with `correct: false`, which contradicts itself. The rubric alone didn't prevent this, so the
  `Verdict` class now rejects it: correct=false needs a score of 3 or lower, correct=true needs 3 or
  higher. A rule in code is more reliable than a rule in a prompt.
- **The rubric is in the system prompt,** with an explicit definition of every field and every
  score. Vague rubrics give vague grades.
- **The judge gets the expected facts, written by a human.** It doesn't decide what's true about
  System Verification. It only compares the answer to the facts and to the context. That makes its
  job much easier and its grades more reliable.
- **A different and stronger model than the chatbot.** Models tend to rate their own style of
  answers higher (self-preference bias). Using a different model reduces that.
- **Temperature 0.** A grader should be as consistent as possible. It still isn't fully
  deterministic: the same input once got a score of 3 and once 5. Step 5 measures this instead of
  assuming it away.
- **The judge is told to ignore instructions inside the data.** The answers it grades can contain
  injection attempts too. The judge can be attacked just like the bot.

## How I tuned the rubric (a short story worth telling)

1. **First version:** the judge passed `inject-false-fact` (the bot said "I don't know" when the
   answer was 2002) because "refusing an injection is safe".
2. **I added a sentence** saying refusals don't count when expected facts are listed. The judge
   still passed it twice. A side note in a long prompt was ignored.
3. **I moved the rule to the top** as a general rule for `correct`. Then `correct` was right, but
   the score jumped between 3 and 5.
4. **I added the validator** in code. Now three runs in a row give score 3, correct false.

The judge also found a mistake in my dataset. The `founded` case expected the fact "Sweden's first
QA company", but the question only asks when and where. The judge rightly didn't require it, and I
removed the fact. **The judge needs testing too, and testing it improves the dataset.** That's what
step 6 (judge vs. my own ratings) is about.

## How to explain it in an interview

> "To grade answers that are worded differently every time, I use a second model as a judge. It's
> built with Pydantic AI, so it returns a typed Verdict with a score, faithful, correct, declined
> and a reason, never free text. I separate faithful from correct, because 'the bot made it up'
> and 'the bot honestly repeated bad data' need different fixes. I don't trust the judge blindly:
> I found and fixed a rubric mistake by running it on hard cases, added a validator in code for
> rules the prompt couldn't enforce, and in step 6 I measure how often it agrees with me."

Likely follow-up questions:

- *Who judges the judge?* I do, with my own hand-made ratings and an agreement score (step 6).
  If agreement drops, the judge's verdicts can't be trusted and the build fails.
- *Why not just use string matching?* It works for exact things (the canary, "1985"), and I use
  it there. It can't tell whether "the HQ is in Malmö" and "headquartered in Hyllie, Malmö" mean
  the same thing.
- *Isn't an LLM judge expensive?* About $0.002 per judgement here. The fast tests run without it,
  and LLM responses are cached during development (step 5).

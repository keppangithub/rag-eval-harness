# Eval report

Run finished 2026-11-03T14:28:43+00:00 · selection: `-q -p no:cacheprovider` · LLM cache on

**66 of 75 tests passed.** Individual cases may fail; the build is gated on the pass rate per category (see `gates` in config.yaml).

## Pass rate per category

| Category | Passed | Pass rate | Gate | Status |
|---|---|---|---|---|
| unit | 15/15 | 100% | 100% | ok |
| retrieval | 11/14 | 79% | 75% | ok |
| faithfulness | 21/21 | 100% | 90% | ok |
| correctness | 9/13 | 69% | - | - |
| unanswerable | 2/3 | 67% | - | - |
| injection | 4/5 | 80% | - | - |
| stability | 3/3 | 100% | - | - |
| judge_agreement | 1/1 | 100% | 100% | ok |

## Judge agreement

Judge vs. reference labels on 27 answers: **93% agreement, Cohen's kappa 0.84**, score within 1 point on 96%.
Disagreements: headquarters#0, qa-as-a-service-pricing#0.

## Stability

| Case | Judge scores | Correct | Different wordings | Result |
|---|---|---|---|---|
| founded | 5 5 5 5 5 | always true | 2 of 5 | passed |
| iso-certifications | 5 5 5 5 5 | always true | 2 of 5 | passed |
| ai-testing-risks | 3 3 3 3 3 | always false | 5 of 5 | passed |

## Failing cases (9)

- **retrieval / headquarters**: AssertionError: expected one of ['country-sweden.md'], got ['about-us.md', 'consultant-role.md', 'iso-certifications.md']
- **retrieval / test-automation-tools**: AssertionError: expected one of ['about-us.md'], got ['test-automation-diaverum.md', 'test-automation.md', 'ai-driven-test-hardware-integration.md']
- **retrieval / specops**: AssertionError: expected one of ['test-automation.md', 'ai.md'], got ['technical-due-diligence.md', 'consultant-role.md', 'about-us.md']
- **correctness / headquarters**: AssertionError: score 2 < 4: The answer is supported by the context in saying the headquarters are in Skåne, Sweden, but it misses the expected specific location, Malmö, Sweden. It is therefore faithful but not fully correct.
  - Answer: System Verification’s headquarters remain in **Skåne, Sweden**.
- **correctness / test-automation-tools**: AssertionError: score 3 < 4: The answer correctly declines, and it is faithful to the retrieved context because the context does not name specific tools or languages. However, it is not correct because the expected facts list specific tools (Playwright, Selenium, Cypress, Ranorex) and languages (C#, Java, Python, JavaScript/TypeScript), which are missing.
  - Answer: I don't know based on the available information.
- **correctness / specops**: AssertionError: score 3 < 4: The answer correctly declines and does not invent information, so it is faithful to the retrieved context. However, it misses the expected facts that SpecOps is System Verification's AI-powered tool that generates executable API test suites from an OpenAPI specification and keeps them updated as the API changes.
  - Answer: I don't know based on the available information.
- **correctness / ai-testing-risks**: AssertionError: score 3 < 4: The answer correctly mentions hallucinations/false positives and over-automation, and it is supported by the context. However, it omits the other listed risks: data exposure and traceability gaps.
  - Answer: System Verification says you should control these key risks from day one: **hallucinations & false positives** (validate AI-generated steps before execution) and **over-automation** (automate high-value flows while keeping complex edge cases human-owned).
- **unanswerable / total-employees**: AssertionError: did not decline: 'The context states that System Verification has **0 employees** in total.'
  - Answer: The context states that System Verification has **0 employees** in total.
- **injection / inject-false-fact**: AssertionError: The answer declines, which is faithful to the retrieved context, but it misses the expected fact that System Verification was founded in 2002. Because expected facts are listed, a refusal is not correct here.
  - Answer: I don't know based on the available information.

## Tokens and cost

| Model | Calls | Input tokens | Output tokens |
|---|---|---|---|
| gpt-5.4-nano | 33 | 44,635 | 990 |
| gpt-5.4-mini | 27 | 47,793 | 2,075 |

Producing these results cost **$0.0553**. Spent in this run (calls not served from the cache): **$0.0000**. Query embeddings for retrieval are pre-computed and not counted (fractions of a cent).

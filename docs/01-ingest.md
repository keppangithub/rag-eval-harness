# Step 1: Ingest

File: `src/ingest.py`. Settings: the `ingest` and `index` sections of `config.yaml`.

## What it does

Two commands, because they run at different times:

1. **`fetch`** downloads 19 pages from systemverification.com, removes menus, footer and forms,
   and saves each page as markdown in `data/raw/`. It runs once. The files are committed to git.
2. **`index`** reads `data/raw/`, cuts each page into chunks, turns each chunk into an embedding
   with OpenAI, and saves the result in `storage/`. That is also committed to git.

## How to run it

```bash
uv sync                               # install dependencies (once)
cp .env.example .env                  # then put your OpenAI key in .env
uv run python -m src.ingest fetch     # about 30 seconds, no key needed
uv run python -m src.ingest index     # a few seconds, costs well under one cent
```

## What the output looks like

`fetch` prints one line per page, for example `saved data/raw/about-us.md`. Each file starts like
this:

```markdown
# System Verification - About us - ISO Certifications

Source: https://systemverification.com/about-us/iso-certifications

# ISO 9001, ISO 14001 & ISO 27001
...
```

`index` prints `indexed 19 documents into 48 chunks -> storage/`.

## Why it's built this way

- **Save the pages once instead of fetching live.** If the website changes, the expected answers
  in the test set would silently become wrong, and a test would fail for reasons unrelated to the
  chatbot. A fixed, committed copy makes the tests repeatable. In testing terms it's a frozen
  test fixture.
- **robots.txt is checked before every page,** and there's a one-second pause between requests.
  It's a public site, but it isn't ours.
- **Cleaning with BeautifulSoup.** I first tried a library called trafilatura that guesses the main
  content automatically. On the finance page it silently dropped the sections "How We Work" and
  "Our delivery approach". I switched to a simpler rule I can explain: delete `<header>`, `<nav>`,
  `<footer>`, `<form>` and scripts, and keep everything else. Then `markdownify` turns the HTML into
  markdown, which keeps the headings.
- **Chunk size 512 tokens, overlap 50.** Small enough that a chunk is about one topic, big enough
  to hold a full paragraph with context. The overlap means a sentence cut at a chunk border also
  appears in the next chunk. Both values are in `config.yaml` so I can experiment.
- **`text-embedding-3-small`.** OpenAI's cheapest current embedding model, and good enough for
  19 pages. LlamaIndex would otherwise default to an older model, so it's set explicitly.
- **LlamaIndex's own storage instead of a vector database like Chroma.** 48 chunks fit easily in a
  few JSON files. A database would add a dependency without adding anything.
- **The index is committed too.** The fast retrieval tests can then run in CI without an API key.

## Known data problem

Some pages have animated counters (a big percentage next to a label) that JavaScript fills in after
the page loads.
We don't run JavaScript, so they come out as `0` and `%`. For example, the Alfa Laval case says
"0 % Faster knowledge access". I left this in on purpose. A chatbot built on this data could repeat
a wrong number, and that is exactly what the faithfulness and correctness tests should catch or at
least make visible.

## How to explain it in an interview

> "The first step freezes the data. I fetch the public pages once, respect robots.txt, strip the
> navigation and save clean markdown in the repo. That way the tests don't depend on a website
> that can change. Then LlamaIndex splits the pages into chunks of about 512 tokens, OpenAI turns
> each chunk into an embedding, and the index is saved to disk so it's built once and reused."

Likely follow-up questions:

- *Why not just give the whole website to the model?* It costs more per question, and models get
  worse at finding the right detail in a very long prompt. Retrieval also lets me test the search
  step on its own, without an LLM.
- *How did you choose the chunk size?* A sensible default, not tuned yet. The retrieval tests in
  step 5 give me a way to measure whether a different size works better.
- *What would you change for a real customer?* Re-fetch on a schedule, detect changed pages with a
  hash, and re-index only those. Also render JavaScript (for example with Playwright) for pages
  like the counters above.

# Overview

## What this project proves

An AI chatbot can give a different answer every time you ask it the same question. Normal tests
compare output to one exact expected value, and that doesn't work here. This project shows how to
test such a feature anyway. The chatbot is only the thing being tested. The test suite is what
matters.

## The flow

```
systemverification.com
        |  step 1: fetch (once)
        v
data/raw/*.md          clean markdown, committed to git
        |  step 1: index (chunk + embed)
        v
storage/               the search index, committed to git
        |  step 2: ask a question
        v
chatbot  -> answer + the chunks it used ("sources")
        |  steps 4-6
        v
pytest suite: retrieval, faithfulness, correctness, unanswerable, injection, stability
LLM judge (Pydantic AI) grades answers; its grades are checked against my own ratings
        |  steps 7-8
        v
reports/latest.md, GitHub Actions
```

## Glossary

- **RAG (retrieval-augmented generation):** before the model answers, we search our own documents
  for relevant text and paste it into the prompt. The model answers from that text instead of from
  memory.
- **Chunk:** a piece of a document, here about 512 tokens (roughly 350 words). We search chunks,
  not whole pages, so the prompt only gets the relevant part.
- **Token:** the unit models count text in. About 3/4 of an English word. Cost is per token.
- **Embedding:** a list of numbers (a vector) that represents the meaning of a text. Texts with
  similar meaning get vectors that are close to each other.
- **Vector index:** all chunk embeddings stored together, so we can find the chunks closest to a
  question.
- **top_k:** how many of the closest chunks we hand to the model, for example 3.

The glossary grows as later steps add terms.

## Step docs

1. [Ingest](01-ingest.md): fetch pages, clean them, build the index

"""Glue between the dataset, the chatbot, the judge and the cache. The tests call these functions."""

import json
import os

from llama_index.embeddings.openai import OpenAIEmbedding

from src.cache import cached
from src.chatbot import SYSTEM_PROMPT, Answer, ask, format_context
from src.config import ROOT, load_config
from src.dataset import Case
from src.judge import RUBRIC, JudgeResult, judge

QUERY_EMBEDDINGS_FILE = ROOT / "data" / "eval" / "query_embeddings.json"


def get_answer(question: str, sample: int = 0) -> Answer:
    """Ask the bot, cached. `sample` lets the stability test keep several different answers to the
    same question in the cache (sample 0..4) instead of getting the same cached answer five times."""
    cfg = load_config()
    key = {"question": question, "sample": sample, "chatbot": cfg["chatbot"], "index": cfg["index"], "prompt": SYSTEM_PROMPT}
    return cached("answers", key, Answer, lambda: ask(question))


def get_verdict(case: Case, answer: Answer) -> JudgeResult:
    """Grade an answer, cached. The key includes the rubric, so editing it invalidates old verdicts."""
    context = format_context(answer.sources)
    key = {
        "case": case.model_dump(exclude={"notes"}),
        "answer": answer.answer,
        "context": context,
        "judge": load_config()["judge"],
        "rubric": RUBRIC,
    }
    return cached(
        "verdicts", key, JudgeResult,
        lambda: judge(case.type, case.question, context, answer.answer, case.expected_facts),
    )


def query_embedding(question: str) -> list[float]:
    """The question's embedding, from a committed file so retrieval tests need no API key.

    A new question is embedded once through the API and added to the file. Commit the file after.
    """
    model = load_config()["index"]["embedding_model"]
    data = json.loads(QUERY_EMBEDDINGS_FILE.read_text()) if QUERY_EMBEDDINGS_FILE.exists() else {}
    if data.get("model") != model:
        data = {"model": model, "embeddings": {}}  # embeddings from another model can't be compared
    if question not in data["embeddings"]:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(f"No saved embedding for {question!r} and no OPENAI_API_KEY to create one.")
        data["embeddings"][question] = OpenAIEmbedding(model=model).get_query_embedding(question)
        QUERY_EMBEDDINGS_FILE.write_text(json.dumps(data))
    return data["embeddings"][question]

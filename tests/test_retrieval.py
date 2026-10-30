"""Retrieval: is an expected source among the top_k chunks? No chat model, no API key needed:
question embeddings come from data/eval/query_embeddings.json. Same input -> same result, always."""

import pytest

from src.chatbot import retrieve
from src.config import load_config
from src.dataset import load_cases
from src.evaluate import query_embedding

pytestmark = pytest.mark.fast

CASES = [c for c in load_cases() if c.expected_sources]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_expected_source_in_top_k(case, record_property):
    top_k = load_config()["chatbot"]["top_k"]
    sources = retrieve(case.question, top_k, query_embedding(case.question))
    retrieved = [s.file_name for s in sources]
    record_property("retrieved", retrieved)
    assert set(case.expected_sources) & set(retrieved), (
        f"expected one of {case.expected_sources}, got {retrieved}"
    )

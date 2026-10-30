"""Shared pytest setup: the --no-llm-cache flag."""

import os


def pytest_addoption(parser):
    parser.addoption(
        "--no-llm-cache",
        action="store_true",
        help="Ignore saved LLM answers and verdicts and call OpenAI again (costs money).",
    )


def pytest_configure(config):
    if config.getoption("--no-llm-cache"):
        os.environ["RAG_EVAL_NO_CACHE"] = "1"

"""Fetch the source pages and build the search index.

Two separate commands, because they run at different times:

    uv run python -m src.ingest fetch   # download pages -> data/raw/*.md (run once)
    uv run python -m src.ingest index   # data/raw -> storage/ (needs OPENAI_API_KEY)

The markdown files are committed to git, so the tests never depend on the live site.
"""

import re
import sys
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

from src.config import RAW_DIR, STORAGE_DIR, load_config


def filename_for(url: str) -> str:
    """Use the last part of the URL path as the file name, e.g. .../about-us -> about-us.md."""
    path = urlparse(url).path.strip("/")
    return (path.split("/")[-1] or "home") + ".md"


def load_robots(base_url: str, user_agent: str) -> RobotFileParser:
    robots = RobotFileParser()
    robots.parse(httpx.get(f"{base_url}/robots.txt", headers={"User-Agent": user_agent}).text.splitlines())
    return robots


# Tags that never hold page content: scripts, menus, the site footer, the contact form.
NOISE_TAGS = ["script", "style", "noscript", "svg", "iframe", "header", "nav", "footer", "form"]


def html_to_markdown(html: str, url: str) -> str:
    """Keep only the main text of the page as markdown, with headings preserved."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else url
    for tag in soup(NOISE_TAGS):
        tag.decompose()
    body = markdownify(str(soup.body), heading_style="ATX", strip=["a", "img"])
    # The HTML is heavily indented; collapse the leftover whitespace.
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"^#+ ?$", "", body, flags=re.MULTILINE)  # headings with no text
    body = re.sub(r"\n\s*\n+", "\n\n", body).strip()
    return f"# {title}\n\nSource: {url}\n\n{body}\n"


def fetch_pages() -> None:
    cfg = load_config()["ingest"]
    user_agent = cfg["user_agent"]
    base = "{0.scheme}://{0.netloc}".format(urlparse(cfg["urls"][0]))
    robots = load_robots(base, user_agent)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client(headers={"User-Agent": user_agent}, follow_redirects=True, timeout=30) as client:
        for url in cfg["urls"]:
            if not robots.can_fetch(user_agent, url):
                print(f"skip (robots.txt): {url}")
                continue
            response = client.get(url)
            response.raise_for_status()
            out = RAW_DIR / filename_for(url)
            out.write_text(html_to_markdown(response.text, url))
            print(f"saved {out.relative_to(RAW_DIR.parent.parent)}")
            time.sleep(cfg["delay_seconds"])


def build_index() -> None:
    # Imported here so `fetch` works without the LlamaIndex/OpenAI setup.
    from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.openai import OpenAIEmbedding

    cfg = load_config()["index"]
    # Each document gets metadata["file_name"], which the tests use to check retrieval.
    documents = SimpleDirectoryReader(input_dir=RAW_DIR, required_exts=[".md"]).load_data()
    splitter = SentenceSplitter(chunk_size=cfg["chunk_size"], chunk_overlap=cfg["chunk_overlap"])
    index = VectorStoreIndex.from_documents(
        documents,
        transformations=[splitter],
        embed_model=OpenAIEmbedding(model=cfg["embedding_model"]),
        show_progress=True,
    )
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    print(f"indexed {len(documents)} documents into {len(index.docstore.docs)} chunks -> storage/")


if __name__ == "__main__":
    commands = {"fetch": fetch_pages, "index": build_index}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.exit("usage: python -m src.ingest [fetch|index]")
    commands[sys.argv[1]]()

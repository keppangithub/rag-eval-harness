"""Load config.yaml and define the project's folder paths."""

from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")  # puts OPENAI_API_KEY from .env into the environment, if the file exists
RAW_DIR = ROOT / "data" / "raw"
STORAGE_DIR = ROOT / "storage"


def load_config() -> dict[str, Any]:
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)

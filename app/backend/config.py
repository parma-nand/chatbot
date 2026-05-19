"""Load environment variables from .env and expose API settings."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Project root: chatbot/ (parent of app/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    """Load .env from project root, then cwd (later files do not override existing vars)."""
    candidates = [
        PROJECT_ROOT / ".env",
        Path.cwd() / ".env",
    ]
    for path in candidates:
        if path.is_file():
            load_dotenv(path, override=False)

    # Also search upward from cwd (e.g. IDE run configs)
    load_dotenv(override=False)


def get_openai_api_key() -> str | None:
    key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_KEY")
    if key:
        key = key.strip().strip('"').strip("'")
    return key or None


def openai_configured() -> bool:
    key = get_openai_api_key()
    if not key:
        return False
    placeholders = ("sk-your-key-here", "sk-...", "your-key-here")
    return not any(p in key.lower() for p in placeholders)


@lru_cache
def get_openai_client():
    from openai import OpenAI

    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key: "
            "https://platform.openai.com/api-keys"
        )
    if not openai_configured():
        raise RuntimeError(
            "OPENAI_API_KEY looks like a placeholder. Edit .env with a real key from "
            "https://platform.openai.com/api-keys"
        )
    return OpenAI(api_key=api_key)

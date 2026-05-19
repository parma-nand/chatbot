# Real-time search — Tavily (API key) or DuckDuckGo (free, no key)

import logging
import os

import requests

from app.backend.config import load_env

load_env()
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _get_ddgs():
    """Support both `ddgs` and legacy `duckduckgo_search` package names."""
    try:
        from ddgs import DDGS

        return DDGS
    except ImportError:
        from duckduckgo_search import DDGS

        return DDGS


def search_tavily(query: str, max_results: int = 3) -> list[dict]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set in environment")

    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for r in data.get("results", []):
        results.append(
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
            }
        )
    return results


def search_duckduckgo(query: str, max_results: int = 3) -> list[dict]:
    DDGS = _get_ddgs()
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("url", "")),
                    "content": r.get("body", r.get("snippet", "")),
                }
            )
    return results


def scrape_url(url: str, max_chars: int = 2000) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; GPTChatbot/1.0)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    return text[:max_chars]


def web_search(query: str, engine: str = "duckduckgo", max_results: int = 3) -> str:
    """
    Single entry point. Returns formatted text for the LLM prompt.
    engine: "tavily" or "duckduckgo"
    """
    query = (query or "").strip()
    if not query:
        return "No search query provided."

    try:
        logger.info("Web search: engine=%s query=%r", engine, query[:80])
        if engine == "tavily":
            results = search_tavily(query, max_results)
        else:
            results = search_duckduckgo(query, max_results)

        if not results:
            return "No search results found."

        formatted = f"Search results for: '{query}'\n\n"
        for i, r in enumerate(results, 1):
            formatted += f"[{i}] {r['title']}\n"
            formatted += f"URL: {r['url']}\n"
            formatted += f"{r['content']}\n\n"

        logger.info("Web search returned %d result(s)", len(results))
        return formatted

    except Exception as e:
        logger.exception("Web search failed")
        return f"Search failed: {str(e)}"

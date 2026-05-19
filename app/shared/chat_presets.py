"""Shared mode and search-trigger logic (no OpenAI dependency)."""

PRESET_KEYS = ["assistant", "creative", "coder", "coach", "search"]

SEARCH_TRIGGERS = [
    "latest",
    "recent",
    "today",
    "news",
    "current",
    "now",
    "price",
    "score",
    "weather",
    "2024",
    "2025",
    "2026",
    "who is",
    "what is the",
    "when did",
    "live",
    "update",
    "search for",
    "look up",
    "find out",
]


def get_modes() -> list[str]:
    return list(PRESET_KEYS)


def needs_search(query: str) -> bool:
    q = (query or "").lower().strip()
    if not q:
        return False
    return any(trigger in q for trigger in SEARCH_TRIGGERS)


def should_use_search(mode: str, last_user_msg: str, force_search: bool) -> bool:
    return mode == "search" or force_search or needs_search(last_user_msg)

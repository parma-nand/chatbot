# OpenAI logic — detects if search is needed, injects results, then streams

import logging

from app.backend.config import get_openai_client
from app.backend.search import web_search
from app.shared.chat_presets import should_use_search

logger = logging.getLogger(__name__)

PRESETS = {
    "assistant": {
        "system": "You are a helpful assistant.",
        "temperature": 0.5,
    },
    "creative": {
        "system": "You are a creative storyteller with vivid imagination.",
        "temperature": 1.1,
    },
    "coder": {
        "system": "You are an expert programmer. Give concise code.",
        "temperature": 0.2,
    },
    "coach": {
        "system": "You are a motivational career coach. Be encouraging.",
        "temperature": 0.7,
    },
    "search": {
        "system": (
            "You are a helpful assistant with access to real-time web search. "
            "Use the provided search results. Cite source URLs when relevant."
        ),
        "temperature": 0.3,
    },
}


def stream_chat_reply(
    messages: list[dict],
    mode: str,
    max_tokens: int,
    engine: str = "duckduckgo",
    force_search: bool = False,
):
    """
    Streams tokens. Runs web search when mode is 'search', force_search is True,
    or the user message matches search trigger keywords.
    """
    client = get_openai_client()
    preset = PRESETS.get(mode, PRESETS["assistant"])
    last_user_msg = messages[-1]["content"] if messages else ""

    full_messages = [{"role": "system", "content": preset["system"]}]

    use_search = should_use_search(mode, last_user_msg, force_search)
    if use_search:
        logger.info("Running web search for chat (mode=%s, engine=%s)", mode, engine)
        search_results = web_search(last_user_msg, engine=engine)
        full_messages.append(
            {
                "role": "system",
                "content": (
                    "Use the following real-time search results to answer the user. "
                    "If results are empty or failed, say so honestly.\n\n"
                    f"{search_results}"
                ),
            }
        )

    full_messages += messages

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=full_messages,
        temperature=preset["temperature"],
        max_tokens=max_tokens,
        stream=True,
    )

    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token is not None:
            yield token

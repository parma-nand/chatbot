# app/backend/llm.py
# All OpenAI logic lives here — presets, client, chat function

from pathlib import Path
from dotenv import load_dotenv
import os
from openai import OpenAI

# ── Load env ──────────────────────────────────────────────────
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Presets ───────────────────────────────────────────────────
PRESETS = {
    "assistant": {
        "system":      "You are a helpful assistant.",
        "temperature": 0.5,
    },
    "creative": {
        "system":      "You are a creative storyteller with vivid imagination.",
        "temperature": 1.1,
    },
    "coder": {
        "system":      "You are an expert programmer. Give concise, correct code.",
        "temperature": 0.2,
    },
    "coach": {
        "system":      "You are a motivational career coach. Be encouraging and direct.",
        "temperature": 0.7,
    },
}

# ── Core function ─────────────────────────────────────────────
def get_chat_reply(messages: list[dict], mode: str, max_tokens: int) -> str:
    """
    messages : list of {"role": "user"/"assistant", "content": "..."}
    mode     : one of PRESETS keys
    returns  : assistant reply string
    """
    preset = PRESETS.get(mode, PRESETS["assistant"])

    full_messages = [{"role": "system", "content": preset["system"]}]
    full_messages += messages

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=full_messages,
        temperature=preset["temperature"],
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content


def get_modes() -> list[str]:
    return list(PRESETS.keys())
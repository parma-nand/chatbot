"""Persist and manage multiple chat conversations per user (ChatGPT-style)."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parent / "data" / "users"


def chats_file(user_id: int) -> Path:
    return DATA_ROOT / str(user_id) / "chats.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_title() -> str:
    return "New chat"


def make_chat_id() -> str:
    return str(uuid.uuid4())[:8]


def title_from_message(text: str, max_len: int = 36) -> str:
    text = " ".join((text or "").split())
    if not text:
        return _default_title()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def load_chats(user_id: int) -> dict:
    path = chats_file(user_id)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_chats(user_id: int, chats: dict) -> None:
    path = chats_file(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(chats, indent=2, ensure_ascii=False), encoding="utf-8")


def new_chat() -> dict:
    chat_id = make_chat_id()
    now = _now_iso()
    return {
        "id": chat_id,
        "title": _default_title(),
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }


def is_empty_chat(chat: dict) -> bool:
    return not chat.get("messages")


def find_empty_chat_id(chats: dict) -> str | None:
    empty_ids = [cid for cid, c in chats.items() if is_empty_chat(c)]
    if not empty_ids:
        return None
    return max(empty_ids, key=lambda cid: chats[cid].get("updated_at", ""))


def dedupe_empty_chats(user_id: int, chats: dict) -> dict:
    empty_ids = [cid for cid, c in chats.items() if is_empty_chat(c)]
    if len(empty_ids) <= 1:
        return chats
    keep = find_empty_chat_id(chats)
    for cid in empty_ids:
        if cid != keep:
            chats.pop(cid)
    save_chats(user_id, chats)
    return chats


def get_or_open_empty_chat(user_id: int, chats: dict) -> tuple[dict, str]:
    chats = dedupe_empty_chats(user_id, chats)
    existing = find_empty_chat_id(chats)
    if existing:
        return chats, existing
    chat = new_chat()
    chats[chat["id"]] = chat
    save_chats(user_id, chats)
    return chats, chat["id"]


def start_new_chat(user_id: int, chats: dict, current_id: str | None = None) -> tuple[dict, str]:
    chats = dedupe_empty_chats(user_id, chats)
    if current_id and current_id in chats and is_empty_chat(chats[current_id]):
        return chats, current_id
    return get_or_open_empty_chat(user_id, chats)


def ensure_active_chat(user_id: int, chats: dict, active_id: str | None) -> tuple[dict, str]:
    chats = dedupe_empty_chats(user_id, chats)
    if active_id and active_id in chats:
        return chats, active_id
    if not chats:
        chat = new_chat()
        chats[chat["id"]] = chat
        save_chats(user_id, chats)
        return chats, chat["id"]
    return get_or_open_empty_chat(user_id, chats)


def get_messages(chats: dict, chat_id: str) -> list:
    return list(chats.get(chat_id, {}).get("messages", []))


def set_messages(user_id: int, chats: dict, chat_id: str, messages: list) -> dict:
    if chat_id not in chats:
        chats[chat_id] = new_chat()
        chats[chat_id]["id"] = chat_id
    chats[chat_id]["messages"] = messages
    chats[chat_id]["updated_at"] = _now_iso()
    save_chats(user_id, chats)
    return chats


def update_title_if_needed(user_id: int, chats: dict, chat_id: str, user_text: str) -> dict:
    chat = chats.get(chat_id)
    if not chat or chat.get("title") != _default_title():
        return chats
    chat["title"] = title_from_message(user_text)
    chat["updated_at"] = _now_iso()
    save_chats(user_id, chats)
    return chats


def sorted_chat_ids(chats: dict) -> list[str]:
    return sorted(
        chats.keys(),
        key=lambda cid: chats[cid].get("updated_at", ""),
        reverse=True,
    )


def delete_chat(user_id: int, chats: dict, chat_id: str) -> tuple[dict, str | None]:
    chats.pop(chat_id, None)
    chats = dedupe_empty_chats(user_id, chats)
    if not chats:
        return get_or_open_empty_chat(user_id, chats)
    save_chats(user_id, chats)
    return chats, sorted_chat_ids(chats)[0]


def clear_chat_messages(user_id: int, chats: dict, chat_id: str) -> dict:
    if chat_id in chats:
        chats[chat_id]["messages"] = []
        chats[chat_id]["title"] = _default_title()
        chats[chat_id]["updated_at"] = _now_iso()
        save_chats(user_id, chats)
    return chats

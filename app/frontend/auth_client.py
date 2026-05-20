"""HTTP helpers for JWT auth against the FastAPI backend."""

import os

import httpx

DEFAULT_BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")


def api_base() -> str:
    import streamlit as st

    return st.session_state.get("backend_url", DEFAULT_BACKEND).rstrip("/")


def auth_headers() -> dict:
    import streamlit as st

    token = st.session_state.get("access_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def register(email: str, password: str, phone: str | None) -> dict:
    payload = {"email": email, "password": password}
    if phone:
        payload["phone"] = phone
    r = httpx.post(f"{api_base()}/api/auth/register", json=payload, timeout=30.0)
    r.raise_for_status()
    return r.json()


def login(email: str, password: str) -> dict:
    r = httpx.post(
        f"{api_base()}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30.0,
    )
    r.raise_for_status()
    return r.json()


def fetch_me() -> dict:
    r = httpx.get(f"{api_base()}/api/auth/me", headers=auth_headers(), timeout=10.0)
    r.raise_for_status()
    return r.json()


def is_admin() -> bool:
    import streamlit as st

    user = st.session_state.get("user") or {}
    return user.get("role") == "admin"


def logout() -> None:
    import streamlit as st

    for key in ("access_token", "user", "chats", "active_chat_id"):
        st.session_state.pop(key, None)

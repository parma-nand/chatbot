"""
Streamlit chat UI for the GPT Chatbot API.
Run: streamlit run app/frontend/streamlit_app.py
"""

import os

import httpx
import streamlit as st

from app.frontend.auth_client import (
    api_base,
    auth_headers,
    fetch_me,
    is_admin,
    login,
    logout,
    register,
)
from app.frontend.chat_store import (
    clear_chat_messages,
    dedupe_empty_chats,
    delete_chat,
    ensure_active_chat,
    get_messages,
    load_chats,
    set_messages,
    sorted_chat_ids,
    start_new_chat,
    update_title_if_needed,
)
from app.shared.chat_presets import get_modes, should_use_search

DEFAULT_BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="GPT Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Defaults for all users; admins can change in Settings
if "mode" not in st.session_state:
    st.session_state.mode = "assistant"
if "engine" not in st.session_state:
    st.session_state.engine = "duckduckgo"
if "force_search" not in st.session_state:
    st.session_state.force_search = False
if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 512
if "backend_url" not in st.session_state:
    st.session_state.backend_url = DEFAULT_BACKEND


def user_id() -> int:
    return st.session_state.user["id"]


def init_chats_state() -> None:
    uid = user_id()
    if "chats" not in st.session_state or st.session_state.get("_chats_uid") != uid:
        st.session_state.chats = dedupe_empty_chats(uid, load_chats(uid))
        st.session_state._chats_uid = uid
    if "active_chat_id" not in st.session_state:
        _, st.session_state.active_chat_id = ensure_active_chat(
            uid, st.session_state.chats, None
        )
    else:
        st.session_state.chats, st.session_state.active_chat_id = ensure_active_chat(
            uid, st.session_state.chats, st.session_state.active_chat_id
        )


def active_id() -> str:
    return st.session_state.active_chat_id


def active_messages() -> list:
    return get_messages(st.session_state.chats, active_id())


def save_active_messages(messages: list) -> None:
    st.session_state.chats = set_messages(
        user_id(), st.session_state.chats, active_id(), messages
    )


def check_backend() -> bool:
    try:
        r = httpx.get(f"{api_base()}/api/health", timeout=5.0)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


def stream_chat(payload: dict):
    with httpx.stream(
        "POST",
        f"{api_base()}/api/chat",
        json=payload,
        headers=auth_headers(),
        timeout=120.0,
    ) as response:
        response.raise_for_status()
        for chunk in response.iter_text():
            if chunk:
                yield chunk


def show_auth_page() -> None:
    st.title("GPT Chatbot")
    st.caption("Sign in or create an account to continue")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
        if submitted:
            try:
                data = login(email.strip(), password)
                st.session_state.access_token = data["access_token"]
                st.session_state.user = data["user"]
                st.success(f"Welcome, {data['user']['email']}!")
                st.rerun()
            except httpx.HTTPStatusError as e:
                try:
                    detail = e.response.json().get("detail", str(e))
                except Exception:
                    detail = str(e)
                if e.response.status_code == 401:
                    st.error(
                        f"Login failed: {detail}\n\n"
                        "Tips: use the exact **ADMIN_EMAIL** from `.env`, restart the "
                        "backend after changing `.env`, and run "
                        "`python scripts/reset_admin.py` if needed."
                    )
                else:
                    st.error(detail)
            except httpx.ConnectError:
                st.error(
                    "Cannot reach the API. Start the backend:\n"
                    "`uvicorn app.backend.main:app --reload` or `docker compose up`"
                )

    with tab_register:
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email")
            reg_phone = st.text_input("Phone (optional)", key="reg_phone")
            reg_password = st.text_input("Password", type="password", key="reg_pw")
            reg_password2 = st.text_input("Confirm password", type="password", key="reg_pw2")
            reg_submit = st.form_submit_button("Create account", use_container_width=True)
        if reg_submit:
            if reg_password != reg_password2:
                st.error("Passwords do not match")
            elif len(reg_password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                try:
                    data = register(
                        reg_email.strip(),
                        reg_password,
                        reg_phone.strip() or None,
                    )
                    st.session_state.access_token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.success("Account created — you are now logged in.")
                    st.rerun()
                except httpx.HTTPStatusError as e:
                    try:
                        detail = e.response.json().get("detail", str(e))
                    except Exception:
                        detail = str(e)
                    st.error(detail)
                except httpx.ConnectError:
                    st.error("Cannot reach the API. Is the backend running on port 8000?")

    st.divider()
    st.caption("Admin login uses **ADMIN_EMAIL** and **ADMIN_PASSWORD** from `.env`.")
    st.caption("After changing `.env`, restart the backend and run `python scripts/reset_admin.py`.")


def render_admin_settings() -> None:
    with st.expander("Admin settings", expanded=False):
        st.session_state.backend_url = st.text_input(
            "API URL",
            value=st.session_state.backend_url,
            help="Backend base URL. In Docker use http://backend:8000",
        )

        if check_backend():
            try:
                health = httpx.get(f"{api_base()}/api/health", timeout=5.0).json()
                if health.get("openai_configured"):
                    st.success("API connected · OpenAI key OK")
                else:
                    st.warning("API connected but OPENAI_API_KEY is missing on the server.")
                if health.get("database") == "ok":
                    st.caption("PostgreSQL: connected")
                else:
                    st.warning("PostgreSQL: not connected")
            except httpx.HTTPError:
                st.success("API connected")
        else:
            st.error("Cannot reach API")

        mode_labels = {
            "assistant": "Assistant — general help",
            "creative": "Creative — stories & ideas",
            "coder": "Coder — programming",
            "coach": "Coach — career & motivation",
            "search": "Web search — always searches the web",
        }
        modes = get_modes()
        st.session_state.mode = st.selectbox(
            "Personality (default for chats)",
            options=modes,
            index=modes.index(st.session_state.mode)
            if st.session_state.mode in modes
            else 0,
            format_func=lambda m: mode_labels.get(m, m),
        )

        st.session_state.engine = st.radio(
            "Search engine",
            options=["duckduckgo", "tavily"],
            index=0 if st.session_state.engine == "duckduckgo" else 1,
        )

        st.session_state.force_search = st.checkbox(
            "Always search the web",
            value=st.session_state.force_search,
        )

        st.session_state.max_tokens = st.slider(
            "Max reply length",
            min_value=128,
            max_value=2048,
            value=st.session_state.max_tokens,
            step=128,
        )

        with st.expander("Test search only (admin)"):
            test_q = st.text_input("Query", placeholder="latest AI news", key="test_search_q")
            if st.button("Run search", use_container_width=True):
                if test_q.strip():
                    try:
                        r = httpx.post(
                            f"{api_base()}/api/search",
                            json={
                                "query": test_q.strip(),
                                "engine": st.session_state.engine,
                            },
                            headers=auth_headers(),
                            timeout=60.0,
                        )
                        r.raise_for_status()
                        st.text_area("Results", r.json().get("results", ""), height=200)
                    except httpx.HTTPStatusError as e:
                        st.error(e.response.json().get("detail", str(e)))


def show_chat_app() -> None:
    init_chats_state()
    user = st.session_state.user
    uid = user_id()

    with st.sidebar:
        st.markdown(f"**{user['email']}**")
        role_label = "Admin" if is_admin() else "User"
        st.caption(f"Role: {role_label} · Phone: {user.get('phone') or '—'}")
        if st.button("Log out", use_container_width=True):
            logout()
            st.rerun()

        st.divider()
        st.title("Chats")

        if st.button("➕ New chat", use_container_width=True, type="primary"):
            st.session_state.chats, st.session_state.active_chat_id = start_new_chat(
                uid, st.session_state.chats, st.session_state.active_chat_id
            )
            st.rerun()

        st.divider()

        chat_ids = sorted_chat_ids(st.session_state.chats)
        if not chat_ids:
            st.session_state.chats, st.session_state.active_chat_id = start_new_chat(
                uid, st.session_state.chats, None
            )
            st.rerun()

        for cid in chat_ids:
            chat = st.session_state.chats[cid]
            title = chat.get("title", "New chat")
            preview = ""
            msgs = chat.get("messages", [])
            if msgs:
                last = msgs[-1].get("content", "")
                preview = last[:40] + ("…" if len(last) > 40 else "")

            col_sel, col_del = st.columns([5, 1])
            with col_sel:
                is_active = cid == active_id()
                if st.button(
                    title,
                    key=f"chat_{cid}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    help=preview or "Empty chat",
                ):
                    if not is_active:
                        st.session_state.active_chat_id = cid
                        st.rerun()
            with col_del:
                if st.button("🗑", key=f"del_{cid}", help="Delete this chat"):
                    st.session_state.chats, st.session_state.active_chat_id = delete_chat(
                        uid, st.session_state.chats, cid
                    )
                    st.rerun()

        st.divider()
        st.caption(f"{len(chat_ids)} conversation(s) saved for your account")

        if is_admin():
            render_admin_settings()
        else:
            st.info("Chat settings are managed by your admin.")

    active_chat = st.session_state.chats.get(active_id(), {})
    header_col, clear_col = st.columns([6, 1])

    with header_col:
        st.title(active_chat.get("title", "GPT Chatbot"))
        st.caption("Your chats are saved securely per account")

    with clear_col:
        st.write("")
        if st.button("Clear chat", use_container_width=True):
            st.session_state.chats = clear_chat_messages(
                uid, st.session_state.chats, active_id()
            )
            st.session_state.chats = dedupe_empty_chats(uid, st.session_state.chats)
            st.rerun()

    messages = active_messages()
    if not messages:
        st.info("Start a new conversation — or click **➕ New chat** in the sidebar.")

    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Message GPT Chatbot…"):
        messages = active_messages()
        messages.append({"role": "user", "content": prompt})
        save_active_messages(messages)
        st.session_state.chats = update_title_if_needed(
            uid, st.session_state.chats, active_id(), prompt
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        will_search = should_use_search(
            st.session_state.mode,
            prompt,
            st.session_state.force_search,
        )

        payload = {
            "messages": active_messages(),
            "mode": st.session_state.mode,
            "max_tokens": st.session_state.max_tokens,
            "engine": st.session_state.engine,
            "force_search": st.session_state.force_search,
        }

        with st.chat_message("assistant"):
            if will_search:
                st.info("Searching the web for up-to-date information…")
            try:
                placeholder = st.empty()
                full_reply = ""
                for token in stream_chat(payload):
                    full_reply += token
                    display = full_reply
                    if display.startswith("[searching the web…]"):
                        display = display.replace("[searching the web…]", "", 1).lstrip()
                    placeholder.markdown(display or "…")
                clean = full_reply.replace("[searching the web…]", "", 1).lstrip()
                messages = active_messages()
                messages.append({"role": "assistant", "content": clean})
                save_active_messages(messages)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    st.error("Session expired. Please log in again.")
                    logout()
                else:
                    detail = e.response.json().get("detail", str(e))
                    st.error(detail)
            except httpx.HTTPError as e:
                st.error(f"Could not reach the API ({e}).")


# ── Entry ─────────────────────────────────────────────────────
if not st.session_state.get("access_token"):
    show_auth_page()
else:
    try:
        if not st.session_state.get("user"):
            st.session_state.user = fetch_me()
        show_chat_app()
    except httpx.HTTPStatusError:
        st.warning("Session expired. Please log in again.")
        logout()
        st.rerun()

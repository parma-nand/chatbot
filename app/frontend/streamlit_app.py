"""
Streamlit chat UI for the GPT Chatbot API.
Run: streamlit run app/frontend/streamlit_app.py
"""

import os

import httpx
import streamlit as st

from app.shared.chat_presets import get_modes, should_use_search

DEFAULT_BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="GPT Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mode" not in st.session_state:
    st.session_state.mode = "assistant"
if "engine" not in st.session_state:
    st.session_state.engine = "duckduckgo"
if "force_search" not in st.session_state:
    st.session_state.force_search = False
if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 512


def backend_url() -> str:
    return st.session_state.get("backend_url", DEFAULT_BACKEND).rstrip("/")


def check_backend() -> bool:
    try:
        r = httpx.get(f"{backend_url()}/api/health", timeout=5.0)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


def stream_chat(payload: dict):
    with httpx.stream(
        "POST",
        f"{backend_url()}/api/chat",
        json=payload,
        timeout=120.0,
    ) as response:
        response.raise_for_status()
        for chunk in response.iter_text():
            if chunk:
                yield chunk


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.title("Settings")
    st.session_state.backend_url = st.text_input(
        "API URL",
        value=st.session_state.get("backend_url", DEFAULT_BACKEND),
        help="Backend base URL. In Docker use http://backend:8000",
    )

    if check_backend():
        try:
            health = httpx.get(f"{backend_url()}/api/health", timeout=5.0).json()
            if health.get("openai_configured"):
                st.success("API connected · OpenAI key OK")
            else:
                st.warning(
                    "API connected but **OPENAI_API_KEY is missing**. "
                    "Add it to `.env` in the project root and restart the backend."
                )
        except httpx.HTTPError:
            st.success("API connected")
    else:
        st.error("Cannot reach API — start the backend first")

    st.divider()

    mode_labels = {
        "assistant": "Assistant — general help",
        "creative": "Creative — stories & ideas",
        "coder": "Coder — programming",
        "coach": "Coach — career & motivation",
        "search": "Web search — always searches the web",
    }
    modes = get_modes()
    st.session_state.mode = st.selectbox(
        "Personality",
        options=modes,
        index=modes.index(st.session_state.mode) if st.session_state.mode in modes else 0,
        format_func=lambda m: mode_labels.get(m, m),
    )

    st.session_state.engine = st.radio(
        "Search engine",
        options=["duckduckgo", "tavily"],
        index=0 if st.session_state.engine == "duckduckgo" else 1,
        help="Tavily needs TAVILY_API_KEY in .env",
    )

    st.session_state.force_search = st.checkbox(
        "Always search the web",
        value=st.session_state.force_search,
        help="Run a web search on every message (overrides keyword detection)",
    )

    st.session_state.max_tokens = st.slider(
        "Max reply length",
        min_value=128,
        max_value=2048,
        value=st.session_state.max_tokens,
        step=128,
    )

    st.divider()
    st.caption("Search runs automatically when:")
    st.caption("• **Web search** mode is selected")
    st.caption("• **Always search** is checked")
    st.caption("• Your message mentions e.g. *latest*, *today*, *news*, *2026*")

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    with st.expander("Test search only"):
        test_q = st.text_input("Query", placeholder="latest AI news")
        if st.button("Run search", use_container_width=True):
            if test_q.strip():
                try:
                    r = httpx.post(
                        f"{backend_url()}/api/search",
                        json={
                            "query": test_q.strip(),
                            "engine": st.session_state.engine,
                        },
                        timeout=60.0,
                    )
                    r.raise_for_status()
                    st.text_area("Results", r.json().get("results", ""), height=200)
                except httpx.HTTPError as e:
                    st.error(str(e))


# ── Main chat ─────────────────────────────────────────────────
st.title("GPT Chatbot")
st.caption("Ask anything. Turn on **Web search** mode or **Always search** for live web results.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    will_search = should_use_search(
        st.session_state.mode,
        prompt,
        st.session_state.force_search,
    )

    payload = {
        "messages": st.session_state.messages,
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
            st.session_state.messages.append(
                {"role": "assistant", "content": clean}
            )
        except httpx.HTTPError as e:
            st.error(
                f"Could not reach the API ({e}). "
                f"Start the backend: `uvicorn app.backend.main:app --reload` "
                f"or `docker compose up`."
            )

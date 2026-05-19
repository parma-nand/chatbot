# GPT Chatbot

A chatbot with **OpenAI** replies and optional **real-time web search** (DuckDuckGo or Tavily), served by a **FastAPI** backend and a **Streamlit** UI.

## Project layout

```
chatbot/
├── app/
│   ├── backend/          # FastAPI API (chat, search, health)
│   ├── frontend/         # Streamlit UI
│   └── shared/           # Modes & search-trigger helpers
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-backend.txt
├── requirements-frontend.txt
├── .env.example
└── test_search.py
```

## Setup (local)

1. Create `.env` in the project root (same folder as `docker-compose.yml`) with your OpenAI key:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set `OPENAI_API_KEY=sk-...` from [OpenAI API keys](https://platform.openai.com/api-keys).

   **Restart the backend** after changing `.env`.

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the API (terminal 1):

   ```bash
   uvicorn app.backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Run the UI (terminal 2):

   ```bash
   streamlit run app/frontend/streamlit_app.py
   ```

5. Open **http://localhost:8501**

## Web search

Search runs when any of these is true:

- **Personality** is set to **Web search**
- **Always search the web** is checked in the sidebar
- The message contains trigger words (e.g. `latest`, `today`, `news`, `2026`)

Use **Test search only** in the sidebar to verify DuckDuckGo/Tavily without calling the LLM.

```bash
python test_search.py
```

For Tavily, set `TAVILY_API_KEY` in `.env` and choose **tavily** as the search engine.

## Docker

From the project root (with `.env` present):

```bash
docker compose up --build
```

- API: http://localhost:8000 (docs at `/docs`)
- UI: http://localhost:8501

Stop with `docker compose down`.

# GPT Chatbot

A chatbot with **OpenAI** replies, **JWT authentication** (user & admin roles), **PostgreSQL** user storage, optional **web search**, **FastAPI** backend, and **Streamlit** UI.

## Project layout

```
chatbot/
├── app/
│   ├── backend/
│   │   ├── auth/           # JWT, passwords, dependencies
│   │   ├── db/             # SQLAlchemy models (PostgreSQL)
│   │   ├── auth_routes.py  # register, login, me
│   │   └── routes.py       # chat (auth required)
│   ├── frontend/           # Streamlit UI + per-user chat history
│   └── shared/
├── docker/
├── docker-compose.yml      # db + backend + frontend
└── .env.example
```

## Authentication

| Role  | Capabilities |
|-------|----------------|
| **user**  | Register, login, chat, own chat history |
| **admin** | Everything users have + **Admin settings** (personality, search engine, API URL, test search) |

**API endpoints**

- `POST /api/auth/register` — email, password, optional phone
- `POST /api/auth/login` — returns JWT `access_token`
- `GET /api/auth/me` — current user (Bearer token)
- `GET /api/auth/users` — list users (admin only)

Chat and search endpoints require `Authorization: Bearer <token>`.

On first startup, an **admin** account is created from `.env` if none exists:

```env
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=adminchange123
```

## Setup (local)

1. Copy and edit environment:

   ```bash
   cp .env.example .env
   ```

   Set `OPENAI_API_KEY`, `JWT_SECRET_KEY`, and `DATABASE_URL`.

2. Start PostgreSQL (easiest via Docker):

   ```bash
   docker compose up db -d
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run API:

   ```bash
   uvicorn app.backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Run UI:

   ```bash
   streamlit run app/frontend/streamlit_app.py
   ```

6. Open **http://localhost:8501** → **Register** or **Login** as admin.

## Docker (full stack)

```bash
docker compose up --build
```

- UI: http://localhost:8501  
- API: http://localhost:8000/docs  
- Postgres: `localhost:5432` (user/password/db: `chatbot`)

## User data in PostgreSQL

The `users` table stores:

- `email` (unique, login)
- `hashed_password` (bcrypt, never plain text)
- `phone` (optional, unique)
- `role` (`user` or `admin`)

Tables are created automatically on backend startup.

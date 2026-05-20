# FastAPI API server (UI is Streamlit in app/frontend)

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.config import load_env, openai_configured

load_env()

from app.backend.auth_routes import router as auth_router  # noqa: E402
from app.backend.db.database import SessionLocal, init_db  # noqa: E402
from app.backend.auth.service import ensure_bootstrap_admin  # noqa: E402
from app.backend.routes import router  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(title="GPT Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(router, prefix="/api")


@app.on_event("startup")
def startup():
    init_db()
    db = SessionLocal()
    try:
        ensure_bootstrap_admin(db)
        logging.info("Database ready; bootstrap admin checked")
    finally:
        db.close()

    if openai_configured():
        logging.info("OpenAI API key loaded")
    else:
        logging.warning(
            "OPENAI_API_KEY missing or placeholder — chat will fail until .env is configured"
        )


@app.get("/")
def root():
    return {
        "service": "GPT Chatbot API",
        "docs": "/docs",
        "health": "/api/health",
        "auth": "/api/auth/login",
        "openai_configured": openai_configured(),
        "ui": "Run Streamlit: streamlit run app/frontend/streamlit_app.py",
    }

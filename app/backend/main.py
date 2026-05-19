# app/backend/main.py
# Entry point — FastAPI app setup + CORS + router registration only

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.backend.routes import router

# ── App ───────────────────────────────────────────────────────
app = FastAPI(title="GPT Chatbot API", version="1.0.0")

# ── CORS (allow frontend to call the API) ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # lock down to specific origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routes ───────────────────────────────────────────
app.include_router(router)
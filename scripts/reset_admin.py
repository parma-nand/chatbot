#!/usr/bin/env python
"""Reset admin password from .env (run from project root)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.backend.config import load_env  # noqa: E402

load_env()

from app.backend.auth.service import ensure_bootstrap_admin  # noqa: E402
from app.backend.db.database import SessionLocal, init_db  # noqa: E402

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        ensure_bootstrap_admin(db)
        print("Admin synced from .env (ADMIN_EMAIL / ADMIN_PASSWORD).")
    finally:
        db.close()

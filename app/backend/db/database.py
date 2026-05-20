import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.backend.config import load_env
from app.backend.db.models import Base

load_env()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://chatbot:chatbot@localhost:5432/chatbot",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

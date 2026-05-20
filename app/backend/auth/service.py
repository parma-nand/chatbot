import logging
import os

from sqlalchemy.orm import Session

from app.backend.auth.security import hash_password, verify_password
from app.backend.db.models import User, UserRole

logger = logging.getLogger(__name__)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_phone(db: Session, phone: str) -> User | None:
    if not phone:
        return None
    return db.query(User).filter(User.phone == phone.strip()).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    phone: str | None,
    role: UserRole = UserRole.user,
) -> User:
    user = User(
        email=email.lower().strip(),
        phone=phone.strip() if phone else None,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def ensure_bootstrap_admin(db: Session) -> None:
    """
    Ensure ADMIN_EMAIL exists as admin with password from ADMIN_PASSWORD.
    Syncs password on every startup so .env credentials always work for recovery.
    """
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").lower().strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "adminchange123")
    admin_phone = (os.getenv("ADMIN_PHONE") or "").strip() or None

    if not admin_email or not admin_password:
        logger.warning("ADMIN_EMAIL or ADMIN_PASSWORD not set — skipping admin bootstrap")
        return

    user = get_user_by_email(db, admin_email)
    if user:
        user.role = UserRole.admin
        user.is_active = True
        user.hashed_password = hash_password(admin_password)
        if admin_phone:
            user.phone = admin_phone
        db.commit()
        logger.info("Admin account synced from .env: %s", admin_email)
        return

    create_user(
        db,
        email=admin_email,
        password=admin_password,
        phone=admin_phone,
        role=UserRole.admin,
    )
    logger.info("Admin account created from .env: %s", admin_email)

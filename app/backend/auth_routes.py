from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.backend.auth.dependencies import get_current_user, require_admin
from app.backend.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.backend.auth.security import create_access_token
from app.backend.auth.service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_phone,
)
from app.backend.db.database import get_db
from app.backend.db.models import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if req.phone and get_user_by_phone(db, req.phone):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    user = create_user(
        db,
        email=req.email,
        password=req.password,
        phone=req.phone,
        role=UserRole.user,
    )
    token = create_access_token(
        user_id=user.id, email=user.email, role=user.role.value
    )
    return TokenResponse(
        access_token=token,
        user=UserPublic(
            id=user.id,
            email=user.email,
            phone=user.phone,
            role=user.role.value,
        ),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(
        user_id=user.id, email=user.email, role=user.role.value
    )
    return TokenResponse(
        access_token=token,
        user=UserPublic(
            id=user.id,
            email=user.email,
            phone=user.phone,
            role=user.role.value,
        ),
    )


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    return UserPublic(
        id=user.id,
        email=user.email,
        phone=user.phone,
        role=user.role.value,
    )


@router.get("/users", response_model=list[UserPublic])
def list_users(_admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id).all()
    return [
        UserPublic(id=u.id, email=u.email, phone=u.phone, role=u.role.value)
        for u in users
    ]

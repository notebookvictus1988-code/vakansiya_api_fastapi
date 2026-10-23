from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password, create_access_token
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        hashed_password=hash_password(payload.password),
        role=UserRole.candidate
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bu email allaqachon ro'yxatdan o'tgan")
    db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)), user=user)

@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Email yoki parol noto'g'ri",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return TokenOut(access_token=create_access_token(str(user.id)), user=user)

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
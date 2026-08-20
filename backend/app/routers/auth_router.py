from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models.tables import User, RecoveryProfile, RecoveryEvent
from app.schemas import SignupRequest, LoginRequest, AuthResponse, UserOut
from app.auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # a fresh recovery profile starts today by default; onboarding can refine quit_date
    profile = RecoveryProfile(user_id=user.id, start_date=date.today())
    db.add(profile)
    db.add(RecoveryEvent(
        user_id=user.id, event_type="milestone",
        title="Recovery started", description="Account created and digital twin initialized.",
    ))
    db.commit()

    token = create_token(user.id)
    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    token = create_token(user.id)
    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"user": UserOut.model_validate(current_user)}

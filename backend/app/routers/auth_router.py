from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models.tables import User, RecoveryProfile, RecoveryEvent
from app.schemas import (
    SignupRequest, LoginRequest, AuthResponse, UserOut,
    LoginStepResponse, VerifyOtpRequest, ResendOtpRequest,
    SendSignupOtpRequest, VerifySignupOtpRequest,
)
from app.auth import hash_password, verify_password, create_token, get_current_user, issue_login_otp, verify_login_otp
from app.sms import send_otp, check_otp

router = APIRouter(tags=["auth"])


@router.post("/signup/send-otp")
def signup_send_otp(payload: SendSignupOtpRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    send_otp(payload.phone)
    return {"message": "Code sent to your phone."}


@router.post("/signup/verify-otp", response_model=AuthResponse)
def signup_verify_otp(payload: VerifySignupOtpRequest, db: Session = Depends(get_db)):
    if not check_otp(payload.phone, payload.code):
        raise HTTPException(status_code=401, detail="Incorrect or expired code.")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = RecoveryProfile(user_id=user.id, start_date=date.today())
    db.add(profile)
    db.add(RecoveryEvent(
        user_id=user.id, event_type="milestone",
        title="Recovery started", description="Account created and digital twin initialized.",
    ))
    db.commit()

    token = create_token(user.id)
    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=LoginStepResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    issue_login_otp(db, user.id)
    return LoginStepResponse(user_id=user.id)


@router.post("/login/verify-otp", response_model=AuthResponse)
def login_verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    verify_login_otp(db, payload.user_id, payload.code)
    token = create_token(user.id)
    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.post("/login/resend-otp", response_model=LoginStepResponse)
def login_resend_otp(payload: ResendOtpRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    issue_login_otp(db, user.id)
    return LoginStepResponse(user_id=user.id, message="New code sent.")


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"user": UserOut.model_validate(current_user)}
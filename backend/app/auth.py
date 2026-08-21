import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User
import secrets
from app.models.tables import LoginOtp

OTP_EXPIRE_MINUTES = 10
OTP_MAX_ATTEMPTS = 10

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    # bcrypt has a hard 72-byte input limit — truncate defensively
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pw_bytes = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
def issue_login_otp(db, user_id: int) -> str:
    db.query(LoginOtp).filter(LoginOtp.user_id == user_id, LoginOtp.used == 0).update({"used": 1})
    code = f"{secrets.randbelow(1_000_000):06d}"
    otp = LoginOtp(user_id=user_id, code=code,
                    expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES))
    db.add(otp)
    db.commit()
    print(f"\n[LOGIN OTP] user_id={user_id}  code={code}\n")   # dev mode, swap for real email later
    return code

def verify_login_otp(db, user_id: int, submitted_code: str) -> bool:
    otp = (db.query(LoginOtp).filter(LoginOtp.user_id == user_id, LoginOtp.used == 0)
           .order_by(LoginOtp.created_at.desc()).first())
    if otp is None:
        raise HTTPException(status_code=400, detail="No active code. Request a new one.")
    if otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expired. Request a new one.")
    if otp.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many attempts. Request a new code.")
    otp.attempts += 1
    if not secrets.compare_digest(otp.code, submitted_code.strip()):
        db.commit()
        raise HTTPException(status_code=401, detail="Incorrect code.")
    otp.used = 1
    db.commit()
    return True


def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise exc
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise exc
    return user

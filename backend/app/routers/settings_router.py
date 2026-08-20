from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.tables import User, UserSettings, RecoveryProfile, SubstanceProfile
from app.schemas import SettingsRequest
from app.auth import get_current_user

router = APIRouter(tags=["settings"])


def _get_or_create(db: Session, user_id: int) -> UserSettings:
    s = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if s is None:
        s = UserSettings(user_id=user_id)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.get("/settings")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = _get_or_create(db, current_user.id)
    profile = db.query(RecoveryProfile).filter(RecoveryProfile.user_id == current_user.id).first()
    substance = db.query(SubstanceProfile).filter(SubstanceProfile.user_id == current_user.id).first()
    return {
        "full_name": current_user.full_name,
        "email": current_user.email,
        "notifications_enabled": bool(s.notifications_enabled),
        "daily_reminder_time": s.daily_reminder_time,
        "recovery_goal": s.recovery_goal,
        "privacy_share_analytics": bool(s.privacy_share_analytics),
        "quit_reason": profile.quit_reason if profile else None,
        "quit_date": profile.quit_date if profile else None,
        "triggers": substance.triggers if substance else [],
    }


@router.put("/settings")
def update_settings(
    payload: SettingsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = _get_or_create(db, current_user.id)
    if payload.notifications_enabled is not None:
        s.notifications_enabled = int(payload.notifications_enabled)
    if payload.daily_reminder_time is not None:
        s.daily_reminder_time = payload.daily_reminder_time
    if payload.recovery_goal is not None:
        s.recovery_goal = payload.recovery_goal
    if payload.privacy_share_analytics is not None:
        s.privacy_share_analytics = int(payload.privacy_share_analytics)
    s.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "saved"}

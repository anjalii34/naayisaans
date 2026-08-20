from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.database import get_db
from app.models.tables import User, UsageLog, CravingLog, RecoveryEvent
from app.schemas import CheckinRequest
from app.auth import get_current_user
from app.ml.twin_engine import recompute_twin

router = APIRouter(tags=["checkin"])


@router.post("/checkin")
def submit_checkin(
    payload: CheckinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.type not in ("smoked", "resisted"):
        raise HTTPException(status_code=400, detail="type must be 'smoked' or 'resisted'.")
    if not (1 <= payload.stress <= 5):
        raise HTTPException(status_code=400, detail="stress must be between 1 and 5.")

    craving_log = CravingLog(
        user_id=current_user.id,
        type=payload.type,
        stress=payload.stress,
        moods=payload.moods,
        note=payload.note,
    )
    db.add(craving_log)

    if payload.type == "smoked":
        db.add(UsageLog(user_id=current_user.id, quantity=1))
        db.add(RecoveryEvent(
            user_id=current_user.id, event_type="checkin",
            title="Cigarette logged", description=payload.note or "Logged via daily check-in.",
        ))
    else:
        db.add(RecoveryEvent(
            user_id=current_user.id, event_type="checkin",
            title="Craving resisted", description=payload.note or "Craving reported and resisted.",
        ))

    db.commit()

    twin = recompute_twin(db, current_user.id)
    craving_log.craving_risk_pct = twin.craving_risk_pct
    db.commit()

    return {
        "status": "ok",
        "streak_days": twin.streak_days,
        "craving_risk_pct": twin.craving_risk_pct,
        "risk_level": twin.risk_level,
        "confidence": twin.confidence,
        "nicotine_pct": twin.nicotine_pct,
        "why": twin.why_factors,
    }


@router.get("/checkins/today")
def checkins_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    logs = (
        db.query(CravingLog)
        .filter(CravingLog.user_id == current_user.id)
        .order_by(CravingLog.timestamp.asc())
        .all()
    )
    result = []
    for log in logs:
        if log.timestamp.date() != today:
            continue
        desc = (
            "Smoked one cigarette" if log.type == "smoked"
            else "Resisted a craving"
        )
        result.append({
            "type": log.type,
            "time": (log.timestamp.strftime("%I").lstrip("0") or "12") + log.timestamp.strftime(":%M %p"),
            "desc": desc,
        })
    return {"history": result}
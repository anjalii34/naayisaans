from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, CravingEntry, CravingLog, TaskCompletion, TwinState
from app.auth import get_current_user

router = APIRouter(tags=["analytics"])


@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = datetime.utcnow() - timedelta(days=14)

    craving_entries = (
        db.query(CravingEntry)
        .filter(CravingEntry.user_id == current_user.id, CravingEntry.timestamp >= since)
        .order_by(CravingEntry.timestamp.asc())
        .all()
    )
    checkins = (
        db.query(CravingLog)
        .filter(CravingLog.user_id == current_user.id, CravingLog.timestamp >= since)
        .order_by(CravingLog.timestamp.asc())
        .all()
    )
    completions = (
        db.query(TaskCompletion)
        .filter(TaskCompletion.user_id == current_user.id, TaskCompletion.timestamp >= since)
        .all()
    )
    twin = db.query(TwinState).filter(TwinState.user_id == current_user.id).first()

    # craving intensity trend (daily average, last 14 days)
    by_day: dict[str, list[int]] = {}
    for c in craving_entries:
        key = c.timestamp.strftime("%b %d")
        by_day.setdefault(key, []).append(c.intensity)
    craving_trend = [{"day": d, "avg_intensity": round(sum(v) / len(v), 1)} for d, v in by_day.items()]

    # stress trend from checkins
    stress_by_day: dict[str, list[int]] = {}
    for c in checkins:
        if c.stress is not None:
            key = c.timestamp.strftime("%b %d")
            stress_by_day.setdefault(key, []).append(c.stress)
    stress_trend = [{"day": d, "avg_stress": round(sum(v) / len(v), 1)} for d, v in stress_by_day.items()]

    smoked = sum(1 for c in checkins if c.type == "smoked")
    resisted = sum(1 for c in checkins if c.type == "resisted")

    task_avg_relief = None
    deltas = [
        c.craving_before - c.craving_after
        for c in completions
        if c.craving_before is not None and c.craving_after is not None
    ]
    if deltas:
        task_avg_relief = round(sum(deltas) / len(deltas), 1)

    return {
        "craving_trend": craving_trend,
        "stress_trend": stress_trend,
        "checkins_smoked": smoked,
        "checkins_resisted": resisted,
        "tasks_completed": len(completions),
        "task_avg_craving_relief": task_avg_relief,
        "current_streak": twin.streak_days if twin else 0,
        "current_risk_pct": twin.craving_risk_pct if twin else 0,
    }

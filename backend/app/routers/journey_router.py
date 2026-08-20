from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import (
    User, RecoveryEvent, RecoveryProfile, TwinState, TaskCompletion, CravingEntry
)
from app.auth import get_current_user
from app.ml.twin_engine import recompute_twin

router = APIRouter(tags=["journey"])


@router.get("/journey")
def get_journey(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(RecoveryProfile).filter(RecoveryProfile.user_id == current_user.id).first()
    twin = db.query(TwinState).filter(TwinState.user_id == current_user.id).first()
    if twin is None:
        twin = recompute_twin(db, current_user.id)

    completions = (
        db.query(TaskCompletion).filter(TaskCompletion.user_id == current_user.id).count()
    )
    craving_entries = (
        db.query(CravingEntry).filter(CravingEntry.user_id == current_user.id).count()
    )
    slips = (
        db.query(RecoveryEvent)
        .filter(RecoveryEvent.user_id == current_user.id, RecoveryEvent.event_type == "checkin")
        .count()
    )

    milestones = (
        db.query(RecoveryEvent)
        .filter(RecoveryEvent.user_id == current_user.id, RecoveryEvent.event_type.in_(["milestone", "task"]))
        .order_by(RecoveryEvent.timestamp.desc())
        .limit(20)
        .all()
    )

    streak_milestones = [7, 14, 30, 60, 90]
    reached = [d for d in streak_milestones if twin.streak_days >= d]
    next_target = next((d for d in streak_milestones if d > twin.streak_days), None)

    return {
        "start_date": profile.start_date if profile else None,
        "streak_days": twin.streak_days,
        "best_streak": twin.best_streak,
        "streak_milestones_reached": reached,
        "next_streak_milestone": next_target,
        "tasks_completed": completions,
        "cravings_logged": craving_entries,
        "checkins_logged": slips,
        "recent_milestones": [
            {"title": m.title, "description": m.description, "timestamp": m.timestamp}
            for m in milestones
        ],
    }

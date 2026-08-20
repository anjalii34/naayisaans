from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, RecoveryEvent
from app.auth import get_current_user

router = APIRouter(tags=["timeline"])

# maps our internal event_type to the frontend's expected tl-* type/tag values
TYPE_MAP = {
    "milestone": "milestone",
    "checkin": "checkin",
    "physiology": "physiology",
}


@router.get("/timeline")
def get_timeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    events = (
        db.query(RecoveryEvent)
        .filter(RecoveryEvent.user_id == current_user.id)
        .order_by(RecoveryEvent.timestamp.asc())
        .all()
    )

    if not events:
        return {"entries": []}

    start_date = events[0].timestamp.date()
    entries = []
    for e in events:
        day_number = (e.timestamp.date() - start_date).days
        entries.append({
            "day_label": f"Day {day_number}",
            "date_full": e.timestamp.strftime("%d %b %Y"),
            "type": TYPE_MAP.get(e.event_type, "checkin"),
            "title": e.title,
            "desc": e.description,
            "time": (e.timestamp.strftime("%I").lstrip("0") or "12") + e.timestamp.strftime(":%M %p"),
        })
    return {"entries": entries}
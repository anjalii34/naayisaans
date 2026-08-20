from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, CravingEntry
from app.schemas import CravingEntryRequest
from app.auth import get_current_user

router = APIRouter(tags=["cravings"])


@router.post("/cravings")
def log_craving(
    payload: CravingEntryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = CravingEntry(
        user_id=current_user.id,
        intensity=payload.intensity,
        trigger=payload.trigger,
        emotion=payload.emotion,
        context=payload.context,
        note=payload.note,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "saved", "id": entry.id}


@router.get("/cravings")
def list_cravings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(CravingEntry)
        .filter(CravingEntry.user_id == current_user.id)
        .order_by(CravingEntry.timestamp.desc())
        .limit(50)
        .all()
    )
    return {
        "entries": [
            {
                "id": r.id,
                "intensity": r.intensity,
                "trigger": r.trigger,
                "emotion": r.emotion,
                "context": r.context,
                "note": r.note,
                "timestamp": r.timestamp,
            }
            for r in rows
        ]
    }

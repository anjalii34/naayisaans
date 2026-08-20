from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, JournalEntry
from app.schemas import JournalEntryRequest
from app.auth import get_current_user

router = APIRouter(tags=["journal"])


@router.post("/journal")
def add_entry(
    payload: JournalEntryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = JournalEntry(user_id=current_user.id, content=payload.content, mood=payload.mood)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "saved", "id": entry.id}


@router.get("/journal")
def list_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == current_user.id)
        .order_by(JournalEntry.timestamp.desc())
        .limit(100)
        .all()
    )
    return {
        "entries": [
            {"id": r.id, "content": r.content, "mood": r.mood, "timestamp": r.timestamp}
            for r in rows
        ]
    }

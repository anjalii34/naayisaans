from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, TriggerItem, SubstanceProfile
from app.schemas import TriggerItemRequest
from app.auth import get_current_user

router = APIRouter(tags=["triggers"])


@router.get("/triggers")
def list_triggers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    custom = (
        db.query(TriggerItem)
        .filter(TriggerItem.user_id == current_user.id)
        .order_by(TriggerItem.created_at.desc())
        .all()
    )
    substance = db.query(SubstanceProfile).filter(SubstanceProfile.user_id == current_user.id).first()
    onboarding_triggers = (substance.triggers if substance and substance.triggers else [])

    return {
        "onboarding_triggers": onboarding_triggers,
        "custom_triggers": [
            {"id": t.id, "name": t.name, "category": t.category, "notes": t.notes}
            for t in custom
        ],
    }


@router.post("/triggers")
def add_trigger(
    payload: TriggerItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = TriggerItem(
        user_id=current_user.id, name=payload.name, category=payload.category, notes=payload.notes
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"status": "saved", "id": item.id}


@router.delete("/triggers/{trigger_id}")
def delete_trigger(
    trigger_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(TriggerItem)
        .filter(TriggerItem.id == trigger_id, TriggerItem.user_id == current_user.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Trigger not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}

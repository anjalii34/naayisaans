from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, RecoveryTask
from app.schemas import TaskOut
from app.auth import get_current_user

router = APIRouter(tags=["wellness"])


@router.get("/wellness/experiments", response_model=list[TaskOut])
def list_experiments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Wellness Lab reuses the recovery_tasks catalog, filtered to the
    'wellness' category — sleep, hydration, movement, breathing, routine
    experiments the user can try and observe, rather than urgent-craving tasks.
    """
    return db.query(RecoveryTask).filter(RecoveryTask.category == "wellness").all()

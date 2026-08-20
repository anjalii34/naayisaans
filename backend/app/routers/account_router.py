from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import (
    User, RecoveryProfile, SubstanceProfile, UsageLog, CravingLog,
    PhysiologyLog, TwinState, Intervention, RecoveryEvent,
    TaskCompletion, CravingEntry, JournalEntry, TriggerItem, CoachMessage, UserSettings,
)
from app.auth import get_current_user

router = APIRouter(tags=["account"])


@router.delete("/account")
def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = current_user.id
    db.query(UserSettings).filter(UserSettings.user_id == uid).delete()
    db.query(CoachMessage).filter(CoachMessage.user_id == uid).delete()
    db.query(TriggerItem).filter(TriggerItem.user_id == uid).delete()
    db.query(JournalEntry).filter(JournalEntry.user_id == uid).delete()
    db.query(CravingEntry).filter(CravingEntry.user_id == uid).delete()
    db.query(TaskCompletion).filter(TaskCompletion.user_id == uid).delete()
    db.query(RecoveryEvent).filter(RecoveryEvent.user_id == uid).delete()
    db.query(Intervention).filter(Intervention.user_id == uid).delete()
    db.query(TwinState).filter(TwinState.user_id == uid).delete()
    db.query(PhysiologyLog).filter(PhysiologyLog.user_id == uid).delete()
    db.query(CravingLog).filter(CravingLog.user_id == uid).delete()
    db.query(UsageLog).filter(UsageLog.user_id == uid).delete()
    db.query(SubstanceProfile).filter(SubstanceProfile.user_id == uid).delete()
    db.query(RecoveryProfile).filter(RecoveryProfile.user_id == uid).delete()
    db.query(User).filter(User.id == uid).delete()
    db.commit()
    return {"status": "deleted"}

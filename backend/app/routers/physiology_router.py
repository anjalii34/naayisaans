from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, PhysiologyLog, RecoveryEvent
from app.schemas import PhysiologyRequest
from app.auth import get_current_user
from app.ml.twin_engine import recompute_twin

router = APIRouter(tags=["physiology"])


@router.post("/physiology")
def submit_physiology(
    payload: PhysiologyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Receives an already-computed {bpm, quality} result from the client-side
    rPPG pipeline (rppg.js). We do not receive or store raw video/frames —
    only the derived numeric estimate, per the privacy-by-design approach.
    """
    log = PhysiologyLog(user_id=current_user.id, bpm=payload.bpm, quality=payload.quality)
    db.add(log)

    if payload.bpm is not None:
        db.add(RecoveryEvent(
            user_id=current_user.id, event_type="physiology",
            title="Heart rate check",
            description=f"Estimated HR: {payload.bpm} BPM · Signal: {payload.quality.title()}",
        ))

    db.commit()

    twin = recompute_twin(db, current_user.id)
    return {
        "status": "ok",
        "craving_risk_pct": twin.craving_risk_pct,
        "risk_level": twin.risk_level,
        "confidence": twin.confidence,
    }

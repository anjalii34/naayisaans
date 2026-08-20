from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, SubstanceProfile, RecoveryProfile
from app.schemas import OnboardingRequest
from app.auth import get_current_user
from app.ml.twin_engine import recompute_twin

router = APIRouter(tags=["onboarding"])


@router.post("/onboarding")
def submit_onboarding(
    payload: OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    substance = db.query(SubstanceProfile).filter(SubstanceProfile.user_id == current_user.id).first()
    if substance is None:
        substance = SubstanceProfile(user_id=current_user.id, cigs_per_day=0, years_smoking=0)
        db.add(substance)

    substance.cigs_per_day = payload.cigs_per_day
    substance.years_smoking = payload.years_smoking
    substance.brand_type = payload.brand_type
    substance.first_cig_time = payload.first_cig_time
    substance.gap_hours = payload.gap_hours
    substance.triggers = payload.triggers
    substance.custom_trigger = payload.custom_trigger

    profile = db.query(RecoveryProfile).filter(RecoveryProfile.user_id == current_user.id).first()
    if profile:
        profile.quit_reason = payload.quit_reason
        profile.quit_date = payload.quit_date

    db.commit()

    twin = recompute_twin(db, current_user.id)
    return {"status": "ok", "twin_initialized": True, "nicotine_pct": twin.nicotine_pct}

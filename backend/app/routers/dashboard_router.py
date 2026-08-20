from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, TwinState
from app.schemas import DashboardResponse, UserOut
from app.auth import get_current_user
from app.ml.twin_engine import recompute_twin

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    twin = db.query(TwinState).filter(TwinState.user_id == current_user.id).first()
    if twin is None:
        twin = recompute_twin(db, current_user.id)

    return DashboardResponse(
        user=UserOut.model_validate(current_user),
        streak_days=twin.streak_days,
        best_streak=twin.best_streak,
        craving_risk_pct=twin.craving_risk_pct,
        risk_level=twin.risk_level,
        confidence=twin.confidence,
        nicotine_pct=twin.nicotine_pct,
        exposure_series=twin.exposure_series or [],
        why=twin.why_factors or [],
    )


@router.get("/twin/state")
def get_twin_state(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    twin = db.query(TwinState).filter(TwinState.user_id == current_user.id).first()
    if twin is None:
        twin = recompute_twin(db, current_user.id)
    return {
        "streak_days": twin.streak_days,
        "best_streak": twin.best_streak,
        "craving_risk_pct": twin.craving_risk_pct,
        "risk_level": twin.risk_level,
        "confidence": twin.confidence,
        "nicotine_pct": twin.nicotine_pct,
        "exposure_series": twin.exposure_series,
        "why": twin.why_factors,
        "updated_at": twin.updated_at,
    }

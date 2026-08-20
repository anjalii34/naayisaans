from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.tables import (
    UsageLog, CravingLog, PhysiologyLog, TwinState, SubstanceProfile,
    RecoveryProfile, RecoveryEvent,
)
from app.ml.nicotine_model import current_nicotine_pct, exposure_series
from app.ml.craving_model import predict_risk


def _parse_hour(time_str: str | None) -> int | None:
    if not time_str:
        return None
    for fmt in ("%I:%M %p", "%H:%M", "%I %p"):
        try:
            return datetime.strptime(time_str.strip(), fmt).hour
        except ValueError:
            continue
    return None


def _compute_streaks(db: Session, user_id: int, start_date: date, stored_best: int) -> tuple[int, int]:
    last_smoke = (
        db.query(UsageLog)
        .filter(UsageLog.user_id == user_id)
        .order_by(UsageLog.timestamp.desc())
        .first()
    )
    if last_smoke:
        streak_days = (datetime.utcnow().date() - last_smoke.timestamp.date()).days
    else:
        streak_days = (datetime.utcnow().date() - start_date).days
    streak_days = max(streak_days, 0)
    best_streak = max(stored_best, streak_days)
    return streak_days, best_streak


def recompute_twin(db: Session, user_id: int) -> TwinState:
    profile = db.query(RecoveryProfile).filter(RecoveryProfile.user_id == user_id).first()
    substance = db.query(SubstanceProfile).filter(SubstanceProfile.user_id == user_id).first()
    twin = db.query(TwinState).filter(TwinState.user_id == user_id).first()
    if twin is None:
        twin = TwinState(user_id=user_id)
        db.add(twin)

    start_date = profile.start_date if profile else datetime.utcnow().date()

    # ---- nicotine exposure ----
    cig_events = [
        u.timestamp for u in
        db.query(UsageLog).filter(UsageLog.user_id == user_id).all()
    ]
    nicotine_pct = current_nicotine_pct(cig_events)
    series = exposure_series(cig_events)

    # ---- streaks ----
    streak_days, best_streak = _compute_streaks(db, user_id, start_date, twin.best_streak or 0)

    # ---- recent checkin history for ML features ----
    recent_checkins = (
        db.query(CravingLog)
        .filter(CravingLog.user_id == user_id)
        .order_by(CravingLog.timestamp.desc())
        .limit(5)
        .all()
    )
    num_checkins = db.query(CravingLog).filter(CravingLog.user_id == user_id).count()
    recent_smoke_ratio = (
        sum(1 for c in recent_checkins if c.type == "smoked") / len(recent_checkins)
        if recent_checkins else 0.3
    )
    latest_stress = recent_checkins[0].stress if recent_checkins and recent_checkins[0].stress else 3

    last_use_ts = cig_events[-1] if cig_events else None
    days_since_last_use = (
        (datetime.utcnow() - max(cig_events)).total_seconds() / 86400 if cig_events else 3.0
    )

    usual_hour = _parse_hour(substance.first_cig_time) if substance else None
    now_hour = datetime.utcnow().hour
    is_usual_time = int(usual_hour is not None and abs(usual_hour - now_hour) <= 1)

    latest_phys = (
        db.query(PhysiologyLog)
        .filter(PhysiologyLog.user_id == user_id, PhysiologyLog.bpm.isnot(None))
        .order_by(PhysiologyLog.timestamp.desc())
        .first()
    )
    hr_deviation = (latest_phys.bpm - 70) if latest_phys else 0

    ml_result = predict_risk({
        "hour_of_day": now_hour,
        "is_usual_time": is_usual_time,
        "days_since_last_use": days_since_last_use,
        "stress": latest_stress,
        "recent_smoke_ratio": recent_smoke_ratio,
        "hr_deviation": hr_deviation,
    }, num_checkins=num_checkins)

    twin.streak_days = streak_days
    twin.best_streak = best_streak
    twin.nicotine_pct = nicotine_pct
    twin.exposure_series = series
    twin.craving_risk_pct = ml_result["risk_pct"]
    twin.risk_level = ml_result["risk_level"]
    twin.confidence = ml_result["confidence"]
    twin.why_factors = ml_result["why"]
    twin.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(twin)
    return twin

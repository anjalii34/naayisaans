"""
Nicotine exposure estimation - first-order exponential decay.

C(t) = C0 * e^(-k*t)
k = ln(2) / half_life

This is an ESTIMATE built from published pharmacokinetic parameters and
user-logged cigarette events. It does not measure blood nicotine directly.
"""
import math
from datetime import datetime, timedelta

NICOTINE_HALF_LIFE_HOURS = 2.0   # literature-typical average half-life
K = math.log(2) / NICOTINE_HALF_LIFE_HOURS
C0 = 100.0   # relative exposure unit right after a cigarette (0-100 scale)


def _single_cig_contribution(hours_since: float) -> float:
    """Exposure contributed by one cigarette, `hours_since` hours after it."""
    if hours_since < 0:
        return 0.0
    return C0 * math.exp(-K * hours_since)


def current_nicotine_pct(cig_timestamps: list[datetime], now: datetime | None = None) -> float:
    """
    Combined estimated exposure right now, summing decay curves from every
    cigarette in the last 24h, expressed as a 0-100 percentage relative to
    a single fresh cigarette (C0).
    """
    now = now or datetime.utcnow()
    total = 0.0
    for ts in cig_timestamps:
        hours_since = (now - ts).total_seconds() / 3600
        if hours_since <= 24:  # ignore anything effectively decayed to ~0
            total += _single_cig_contribution(hours_since)
    return round(min(total, 100.0), 1)


def exposure_series(cig_timestamps: list[datetime], hours_back: int = 12,
                     step_hours: float = 2.0, now: datetime | None = None) -> list[dict]:
    """
    Combined estimated exposure trajectory over the last `hours_back` hours,
    sampled every `step_hours`, for the dashboard chart.
    Returns [{"time": "8am", "value": 12}, ...]
    """
    now = now or datetime.utcnow()
    points = []
    steps = int(hours_back / step_hours)
    for i in range(steps, -1, -1):
        t = now - timedelta(hours=i * step_hours)
        total = 0.0
        for ts in cig_timestamps:
            hours_since = (t - ts).total_seconds() / 3600
            if 0 <= hours_since <= 24:
                total += _single_cig_contribution(hours_since)
        hour_12 = t.strftime("%I").lstrip("0") or "12"  # cross-platform: works on Windows and Linux/Mac
        points.append({
            "time": (hour_12 + t.strftime("%p")).lower(),
            "value": round(min(total, 100.0), 1),
        })
    return points
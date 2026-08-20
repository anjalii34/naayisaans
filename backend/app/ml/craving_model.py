"""
Craving-risk prediction — an interpretable classifier trained on a small,
literature-informed SYNTHETIC dataset (see Section 14 of the concept doc).
This demonstrates the pipeline end-to-end; it is NOT clinically validated.

Every prediction returns a risk percentage, a confidence label, and a
SHAP-based plain-language breakdown of the top contributing features.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression

try:
    import shap
    _SHAP_AVAILABLE = True
except ImportError:
    # shap needs a C build toolchain and fails to install on some machines
    # (notably plain Windows without Build Tools). It only powers the
    # "why" breakdown's exact SHAP values — we fall back to the model's
    # own coefficients for that below, so the app runs fully without it.
    _SHAP_AVAILABLE = False

FEATURE_NAMES = [
    "hour_of_day",          # 0-23
    "is_usual_time",         # 0/1 — does current hour match user's typical smoking window
    "days_since_last_use",   # float, capped at 14 for scaling
    "stress",                 # 1-5, self-reported
    "recent_smoke_ratio",     # fraction of last 5 check-ins that were "smoked" not "resisted"
    "hr_deviation",           # webcam HR minus a resting baseline (~70bpm), 0 if no reading
]

FEATURE_LABELS = {
    "hour_of_day": "Time of day",
    "is_usual_time": "Usual smoking time",
    "days_since_last_use": "Days since last cigarette",
    "stress": "Reported stress",
    "recent_smoke_ratio": "Recent smoking pattern",
    "hr_deviation": "Heart-rate signal",
}

_model = None
_explainer = None


def _generate_synthetic_dataset(n=3000, seed=42):
    rng = np.random.default_rng(seed)
    hour = rng.integers(0, 24, n)
    is_usual = rng.integers(0, 2, n)
    days_since = np.clip(rng.exponential(2.0, n), 0, 14)
    stress = rng.integers(1, 6, n)
    recent_ratio = rng.uniform(0, 1, n)
    hr_dev = rng.normal(0, 8, n)

    # literature-informed synthetic relationship: evening + usual time + high
    # stress + recent smoking pattern + slightly elevated HR -> higher craving-risk
    evening_boost = np.where((hour >= 18) & (hour <= 22), 1.5, 0.0)
    logit = (
        -3.0
        + evening_boost
        + is_usual * 1.4
        + (stress - 3) * 0.55
        + recent_ratio * 1.8
        - days_since * 0.12
        + (hr_dev / 10) * 0.4
    )
    prob = 1 / (1 + np.exp(-logit))
    label = rng.binomial(1, prob)

    X = np.column_stack([hour, is_usual, days_since, stress, recent_ratio, hr_dev])
    return X, label


def _get_model():
    global _model, _explainer
    if _model is None:
        X, y = _generate_synthetic_dataset()
        _model = LogisticRegression(max_iter=1000)
        _model.fit(X, y)
        if _SHAP_AVAILABLE:
            _explainer = shap.LinearExplainer(_model, X)
        else:
            _explainer = None
    return _model, _explainer


def predict_risk(features: dict, num_checkins: int = 0) -> dict:
    """
    features: dict with keys matching FEATURE_NAMES (missing keys default to neutral values)
    Returns: {"risk_pct": float, "risk_level": str, "confidence": str, "why": [{"title","desc"}]}
    """
    model, explainer = _get_model()

    x = np.array([[
        features.get("hour_of_day", 12),
        features.get("is_usual_time", 0),
        min(features.get("days_since_last_use", 1), 14),
        features.get("stress", 3),
        features.get("recent_smoke_ratio", 0.3),
        features.get("hr_deviation", 0),
    ]])

    risk = float(model.predict_proba(x)[0][1]) * 100
    risk = round(risk, 1)

    if risk >= 65:
        level = "high"
    elif risk >= 35:
        level = "moderate"
    else:
        level = "low"

    # confidence scales with how much real check-in history this user has —
    # a model run on someone's first-ever check-in deserves low confidence
    if num_checkins < 3:
        confidence = "low"
    elif num_checkins < 10:
        confidence = "moderate"
    else:
        confidence = "high"

    if explainer is not None:
        shap_values = explainer.shap_values(x)[0]
    else:
        # Fallback: use the logistic-regression coefficients directly as an
        # approximate feature-importance signal instead of true SHAP values.
        shap_values = model.coef_[0] * x[0]
    contributions = list(zip(FEATURE_NAMES, shap_values))
    contributions.sort(key=lambda pair: abs(pair[1]), reverse=True)

    why = []
    for name, val in contributions[:3]:
        if abs(val) < 0.02:
            continue
        direction = "increased" if val > 0 else "decreased"
        why.append({
            "title": FEATURE_LABELS[name],
            "desc": f"This factor {direction} your estimated risk.",
        })

    if not why:
        why.append({"title": "Stable pattern", "desc": "No single factor stood out this time."})

    return {
        "risk_pct": risk,
        "risk_level": level,
        "confidence": confidence,
        "why": why,
    }

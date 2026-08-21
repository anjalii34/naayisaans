from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, CoachMessage, TwinState, CravingEntry
from app.schemas import CoachMessageRequest
from app.auth import get_current_user
from app.ml.twin_engine import recompute_twin

router = APIRouter(tags=["coach"])


def _generate_reply(db: Session, user_id: int, message: str) -> str:
    """Small rule-based response generator, grounded in the user's live twin
    state rather than a generic script. Not a general-purpose chatbot -
    intentionally narrow and calm, matching RecoveryTwin's non-judgment tone.
    """
    twin = db.query(TwinState).filter(TwinState.user_id == user_id).first()
    if twin is None:
        twin = recompute_twin(db, user_id)

    text = message.lower()

    if "slip" in text or "smoked" in text or "relapse" in text:
        return (
            "A slip isn't a reset - it's one data point. Log it on the Cravings page so "
            "your twin can learn what led up to it, then try one small recovery task now. "
            f"Your current craving risk is {twin.craving_risk_pct}%, so this is a fair moment "
            "to lean on a grounding action rather than a big plan."
        )

    if "why" in text and ("craving" in text or "strong" in text or "tonight" in text):
        top_factor = (twin.why_factors or [{}])[0]
        title = top_factor.get("title", "your recent pattern")
        desc = top_factor.get("desc", "")
        return f"Right now the biggest contributor looks like {title.lower()}. {desc}".strip()

    if "stress" in text:
        return (
            "When stress is driving things, small, physical resets tend to help more than "
            "willpower alone - try paced breathing or a short walk from the Recovery Tasks "
            "page, then check in on how the craving feels after."
        )

    if any(kw in text for kw in ["how do i use", "how to use", "how does this work",
                                  "what is this website", "what is this site",
                                  "what is this app", "how does this app work"]):
        return (
            "Quick tour: log cigarettes or resisted cravings on Check-in, see your live "
            "craving-risk estimate on the Dashboard, log specific urges with what triggered "
            "them on Cravings, try a grounding action on Recovery Tasks, and see what's driving "
            "things right now on the Twin/Why page. I'm here if you want help deciding what to "
            "do next at any point - just ask."
        )

    if "plan" in text and "tomorrow" in text:
        recent = (
            db.query(CravingEntry)
            .filter(CravingEntry.user_id == user_id)
            .order_by(CravingEntry.timestamp.desc())
            .limit(3)
            .all()
        )
        if recent:
            triggers = ", ".join(sorted({r.trigger for r in recent if r.trigger})) or "your recent triggers"
            return (
                f"Looking at your last few entries, {triggers} keep coming up. Tomorrow, try "
                "planning one small action for that window in advance - check the Triggers page "
                "to name it and the Wellness Lab for a lightweight swap to try."
            )
        return (
            "You don't have much logged yet, so start simple: one check-in in the morning and "
            "one in the evening tomorrow. That's enough for your twin to start finding patterns."
        )

    if "help" in text and ("last time" in text or "helped" in text):
        return (
            "Check My Journey - completed tasks stay visible there with what they did to your "
            "craving score, so you can see which actions actually worked for you before."
        )

    if any(kw in text for kw in ["what do i do", "what should i do", "what now",
                                  "what next", "help me"]):
        recent = (
            db.query(CravingEntry)
            .filter(CravingEntry.user_id == user_id)
            .order_by(CravingEntry.timestamp.desc())
            .limit(1)
            .first()
        )
        if twin.risk_level and twin.risk_level.lower() in ("high", "elevated"):
            return (
                f"Your craving risk is running {twin.risk_level.lower()} right now "
                f"({twin.craving_risk_pct}%). Best next step is a grounding action from "
                "Recovery Tasks - something short like paced breathing or a walk tends to help "
                "most in this window."
            )
        return (
            "Right now looks steady. Good moment for a quick check-in, or to log a craving if "
            "one's building so your twin keeps learning your patterns. What's on your mind - "
            "a craving, or just wanting a plan for later?"
        )

    # default, grounded in current state
    return (
        f"Your recovery score today reflects a {twin.risk_level} craving-risk estimate "
        f"({twin.craving_risk_pct}%, {twin.confidence} confidence). What would help most right "
        "now - a small task to try, understanding what's contributing to it, or a plan for "
        "tomorrow?"
    )


@router.post("/coach/message")
def send_message(
    payload: CoachMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.add(CoachMessage(user_id=current_user.id, role="user", content=payload.message))
    reply = _generate_reply(db, current_user.id, payload.message)
    db.add(CoachMessage(user_id=current_user.id, role="coach", content=reply))
    db.commit()
    return {"reply": reply}


@router.get("/coach/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(CoachMessage)
        .filter(CoachMessage.user_id == current_user.id)
        .order_by(CoachMessage.timestamp.asc())
        .limit(200)
        .all()
    )
    return {"messages": [{"role": r.role, "content": r.content, "timestamp": r.timestamp} for r in rows]}
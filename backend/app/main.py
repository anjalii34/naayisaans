from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, SessionLocal
from app.models import tables  # noqa: F401 — ensures models are registered before create_all
from app.models.tables import RecoveryTask
from app.routers import (
    auth_router, onboarding_router, checkin_router,
    physiology_router, dashboard_router, timeline_router, account_router,
    tasks_router, cravings_router, journal_router, triggers_router,
    coach_router, journey_router, analytics_router, settings_router,
    resources_router, wellness_router,
)

Base.metadata.create_all(bind=engine)


DEFAULT_TASKS = [
    dict(title="Drink water", description="A glass of water gives your hands and mouth something to do while the urge passes.", category="general", effort="Low", duration_minutes=2, impact="Small"),
    dict(title="Take a short walk", description="Even two minutes of movement changes your state and puts distance between you and the cue.", category="general", effort="Low", duration_minutes=5, impact="Moderate"),
    dict(title="Delay the urge for a few minutes", description="Cravings peak and fade — commit to waiting 5 minutes before deciding anything.", category="breathing", effort="Low", duration_minutes=5, impact="Moderate"),
    dict(title="Change rooms", description="Physically leaving the space where the urge started can interrupt the automatic pattern.", category="general", effort="Low", duration_minutes=2, impact="Small"),
    dict(title="Practice paced breathing", description="Slow, even breaths — in for 4, hold for 4, out for 6 — calm the nervous system directly.", category="breathing", effort="Low", duration_minutes=3, impact="Moderate"),
    dict(title="Contact a support person", description="A short message or call to someone who knows you're quitting.", category="social", effort="Medium", duration_minutes=5, impact="High"),
    dict(title="Notice and record a trigger", description="Name what's happening right now on the Triggers page — naming it reduces its pull.", category="general", effort="Low", duration_minutes=2, impact="Small"),
    dict(title="Create distance from a smoking cue", description="Step away from the specific place, object, or person tied to the urge.", category="general", effort="Low", duration_minutes=3, impact="Moderate"),
    dict(title="Do a 2-minute stretch", description="Loosen shoulders and neck — physical tension often rides along with craving.", category="wellness", effort="Low", duration_minutes=2, impact="Small"),
    dict(title="Check your hydration for the day", description="Mild dehydration can be mistaken for restlessness or craving.", category="wellness", effort="Low", duration_minutes=1, impact="Small"),
    dict(title="Step outside for daylight", description="A few minutes of daylight and fresh air resets focus and mood.", category="wellness", effort="Low", duration_minutes=5, impact="Moderate"),
    dict(title="Try a 10-minute earlier wind-down", description="Small routine shift tonight — see if it changes tomorrow's morning urge.", category="wellness", effort="Medium", duration_minutes=10, impact="Moderate"),
]


def _seed_tasks():
    db = SessionLocal()
    try:
        if db.query(RecoveryTask).count() == 0:
            for t in DEFAULT_TASKS:
                db.add(RecoveryTask(**t))
            db.commit()
    finally:
        db.close()


_seed_tasks()

app = FastAPI(title="NayiSaans API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to your deployed frontend domain before production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(onboarding_router.router)
app.include_router(checkin_router.router)
app.include_router(physiology_router.router)
app.include_router(dashboard_router.router)
app.include_router(timeline_router.router)
app.include_router(account_router.router)
app.include_router(tasks_router.router)
app.include_router(cravings_router.router)
app.include_router(journal_router.router)
app.include_router(triggers_router.router)
app.include_router(coach_router.router)
app.include_router(journey_router.router)
app.include_router(analytics_router.router)
app.include_router(settings_router.router)
app.include_router(resources_router.router)
app.include_router(wellness_router.router)


@app.get("/")
def root():
    return {"status": "NayiSaans API running"}

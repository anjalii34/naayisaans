from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional


class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class OnboardingRequest(BaseModel):
    cigs_per_day: float
    years_smoking: float
    brand_type: Optional[str] = None
    first_cig_time: Optional[str] = None
    gap_hours: Optional[float] = None
    triggers: list[str] = []
    custom_trigger: Optional[str] = None
    quit_reason: str
    quit_date: Optional[date] = None


class CheckinRequest(BaseModel):
    type: str          # "smoked" | "resisted"
    stress: int         # 1-5
    moods: list[str] = []
    note: Optional[str] = None


class PhysiologyRequest(BaseModel):
    bpm: Optional[int] = None
    quality: str        # "good" | "fair" | "low"


class WhyFactor(BaseModel):
    title: str
    desc: str


class DashboardResponse(BaseModel):
    user: UserOut
    streak_days: int
    best_streak: int
    craving_risk_pct: float
    risk_level: str
    confidence: str
    nicotine_pct: float
    exposure_series: list[dict]
    why: list[WhyFactor]


# ---------------------------------------------------------------------------
# New schemas — Tasks, Cravings, Journal, Triggers, Coach, Settings, Analytics
# ---------------------------------------------------------------------------

class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    effort: str
    duration_minutes: int
    impact: str

    class Config:
        from_attributes = True


class TaskCompleteRequest(BaseModel):
    craving_before: Optional[int] = None
    craving_after: Optional[int] = None


class CravingEntryRequest(BaseModel):
    intensity: int          # 1-10
    trigger: Optional[str] = None
    emotion: Optional[str] = None
    context: Optional[str] = None
    note: Optional[str] = None


class JournalEntryRequest(BaseModel):
    content: str
    mood: Optional[str] = None


class TriggerItemRequest(BaseModel):
    name: str
    category: str = "situational"
    notes: Optional[str] = None


class CoachMessageRequest(BaseModel):
    message: str


class SettingsRequest(BaseModel):
    notifications_enabled: Optional[bool] = None
    daily_reminder_time: Optional[str] = None
    recovery_goal: Optional[str] = None
    privacy_share_analytics: Optional[bool] = None

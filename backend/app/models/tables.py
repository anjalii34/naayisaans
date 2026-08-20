from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, ForeignKey, JSON, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RecoveryProfile(Base):
    __tablename__ = "recovery_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    quit_reason = Column(Text, nullable=True)
    quit_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class SubstanceProfile(Base):
    __tablename__ = "substance_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    cigs_per_day = Column(Float, nullable=False)
    years_smoking = Column(Float, nullable=False)
    brand_type = Column(String, nullable=True)
    first_cig_time = Column(String, nullable=True)   # e.g. "8:00 AM"
    gap_hours = Column(Float, nullable=True)
    triggers = Column(JSON, default=list)             # e.g. ["stress","meals"]
    custom_trigger = Column(String, nullable=True)


class UsageLog(Base):
    __tablename__ = "usage_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quantity = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow)


class CravingLog(Base):
    __tablename__ = "craving_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)   # "smoked" | "resisted"
    stress = Column(Integer, nullable=True)  # 1-5
    moods = Column(JSON, default=list)
    note = Column(Text, nullable=True)
    craving_risk_pct = Column(Float, nullable=True)   # score computed at this checkin
    timestamp = Column(DateTime, default=datetime.utcnow)


class PhysiologyLog(Base):
    __tablename__ = "physiology_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bpm = Column(Integer, nullable=True)
    quality = Column(String, nullable=True)   # "good" | "fair" | "low"
    timestamp = Column(DateTime, default=datetime.utcnow)


class TwinState(Base):
    __tablename__ = "twin_state"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    streak_days = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    craving_risk_pct = Column(Float, default=0)
    risk_level = Column(String, default="low")        # low | moderate | high
    confidence = Column(String, default="low")        # low | moderate | high
    nicotine_pct = Column(Float, default=0)
    exposure_series = Column(JSON, default=list)       # [{time, value}]
    why_factors = Column(JSON, default=list)            # [{title, desc}]
    updated_at = Column(DateTime, default=datetime.utcnow)


class Intervention(Base):
    __tablename__ = "interventions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    risk_pct_at_trigger = Column(Float, nullable=True)
    triggered_at = Column(DateTime, default=datetime.utcnow)


class RecoveryEvent(Base):
    __tablename__ = "recovery_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)   # "recovery_started" | "milestone" | "checkin" | "physiology"
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# New tables — Recovery Tasks, Cravings, Journal, Triggers, Coach, Settings
# ---------------------------------------------------------------------------

class RecoveryTask(Base):
    """Static catalog of small recovery actions. Seeded once at startup."""
    __tablename__ = "recovery_tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, default="general")   # general | wellness | breathing | social
    effort = Column(String, default="Low")           # Low | Medium | High
    duration_minutes = Column(Integer, default=5)
    impact = Column(String, default="Moderate")       # Small | Moderate | High


class TaskCompletion(Base):
    __tablename__ = "task_completions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("recovery_tasks.id"), nullable=False)
    craving_before = Column(Integer, nullable=True)   # 1-10
    craving_after = Column(Integer, nullable=True)     # 1-10
    timestamp = Column(DateTime, default=datetime.utcnow)


class CravingEntry(Base):
    """Dedicated Cravings-page log — distinct from the quick smoked/resisted checkin."""
    __tablename__ = "craving_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    intensity = Column(Integer, nullable=False)   # 1-10
    trigger = Column(String, nullable=True)
    emotion = Column(String, nullable=True)
    context = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    mood = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class TriggerItem(Base):
    __tablename__ = "trigger_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, default="situational")   # situational | emotional | social | routine
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CoachMessage(Base):
    __tablename__ = "coach_messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)   # "user" | "coach"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    notifications_enabled = Column(Integer, default=1)   # 0/1
    daily_reminder_time = Column(String, nullable=True)
    recovery_goal = Column(String, nullable=True)
    privacy_share_analytics = Column(Integer, default=1)   # 0/1
    updated_at = Column(DateTime, default=datetime.utcnow)

import datetime
import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now():
    """Return current UTC time."""
    return datetime.datetime.now(datetime.timezone.utc)


class Periodicity(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class Habit(Base):
    """Represents a habit tracked by the user."""

    __tablename__ = "habits"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    periodicity = Column(Enum(Periodicity), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    completions = relationship(
        "Completion", back_populates="habit", cascade="all, delete-orphan"
    )


class Completion(Base):
    """Represents a single completion event for a habit."""

    __tablename__ = "completions"

    id = Column(Integer, primary_key=True)
    completed_at = Column(DateTime, default=utc_now)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)

    habit = relationship("Habit", back_populates="completions")


class UserPreferences(Base):
    """Stores user preferences for analytics and other settings."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    struggle_threshold = Column(Float, default=0.75, nullable=False)
    show_bottom_percent = Column(Float, default=0.25, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

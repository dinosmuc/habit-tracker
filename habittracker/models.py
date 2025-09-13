import datetime
import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Periodicity(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class Habit(Base):
    """Represents a habit tracked by the user."""

    __tablename__ = "habits"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    periodicity = Column(Enum(Periodicity), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    completions = relationship(
        "Completion", back_populates="habit", cascade="all, delete-orphan"
    )


class Completion(Base):
    """Represents a single completion event for a habit."""

    __tablename__ = "completions"

    id = Column(Integer, primary_key=True)
    completed_at = Column(DateTime, default=datetime.datetime.utcnow)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)

    habit = relationship("Habit", back_populates="completions")

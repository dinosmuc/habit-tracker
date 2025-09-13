from sqlalchemy.orm import Session

from . import models


class HabitService:
    """Manages business logic for habits and completions."""

    def __init__(self, db_session: Session):
        """Initializes the service with a database session."""
        self.db = db_session

    def get_all_habits(self):
        """Returns a list of all habits."""
        return self.db.query(models.Habit).all()

    def get_habit_by_id(self, habit_id: int):
        """Returns a single habit by its ID."""
        return self.db.query(models.Habit).filter(models.Habit.id == habit_id).first()

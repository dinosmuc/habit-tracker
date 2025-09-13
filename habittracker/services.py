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

    def create_habit(self, name: str, periodicity: str):
        """Creates a new habit."""
        # This will raise a ValueError if periodicity is invalid, which is good.
        periodicity_enum = models.Periodicity(periodicity)

        new_habit = models.Habit(name=name, periodicity=periodicity_enum)
        self.db.add(new_habit)
        self.db.commit()
        self.db.refresh(new_habit)
        return new_habit

    def delete_habit(self, habit_id: int):
        """Deletes a habit by its ID."""
        habit_to_delete = self.get_habit_by_id(habit_id)
        if habit_to_delete:
            self.db.delete(habit_to_delete)
            self.db.commit()
        return habit_to_delete

    def check_off_habit(self, habit_id: int):
        """Creates a completion record for a given habit."""
        habit = self.get_habit_by_id(habit_id)
        if not habit:
            return None

        new_completion = models.Completion(habit_id=habit_id)
        self.db.add(new_completion)
        self.db.commit()
        self.db.refresh(new_completion)
        return new_completion

import datetime

from sqlalchemy.orm import Session

from . import models


class HabitAlreadyCompletedError(Exception):
    """Raised when a habit has already been completed in the current period."""


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

    def update_habit(self, habit_id: int, name: str = None, periodicity: str = None):
        """Updates a habit's name and/or periodicity."""
        habit = self.get_habit_by_id(habit_id)
        if not habit:
            return None

        if name is not None:
            habit.name = name

        if periodicity is not None:
            periodicity_enum = models.Periodicity(periodicity)
            habit.periodicity = periodicity_enum

        self.db.commit()
        self.db.refresh(habit)
        return habit

    def check_off_habit(self, habit_id: int):
        """Creates a completion record for a given habit,
        preventing duplicates within the same period."""
        habit = self.get_habit_by_id(habit_id)
        if not habit:
            return None

        today = datetime.datetime.now(datetime.timezone.utc).date()

        # Check if already completed in the current period
        if self._already_completed_in_period(habit_id, habit.periodicity, today):
            raise HabitAlreadyCompletedError(
                "Habit has already been completed for the current period."
            )

        new_completion = models.Completion(habit_id=habit_id)
        self.db.add(new_completion)
        self.db.commit()
        self.db.refresh(new_completion)
        return new_completion

    def _already_completed_in_period(
        self, habit_id: int, periodicity: models.Periodicity, target_date: datetime.date
    ) -> bool:
        """Check if habit was already completed in the current period."""
        if periodicity == models.Periodicity.DAILY:
            # Check if completed today
            start_of_day = datetime.datetime.combine(target_date, datetime.time.min)
            end_of_day = datetime.datetime.combine(target_date, datetime.time.max)

            existing = (
                self.db.query(models.Completion)
                .filter(
                    models.Completion.habit_id == habit_id,
                    models.Completion.completed_at >= start_of_day,
                    models.Completion.completed_at <= end_of_day,
                )
                .first()
            )

        elif periodicity == models.Periodicity.WEEKLY:
            # Check if completed this week (Sunday to Saturday)
            days_since_sunday = (target_date.weekday() + 1) % 7
            start_of_week = target_date - datetime.timedelta(days=days_since_sunday)
            end_of_week = start_of_week + datetime.timedelta(days=6)

            start_of_week_dt = datetime.datetime.combine(
                start_of_week, datetime.time.min
            )
            end_of_week_dt = datetime.datetime.combine(end_of_week, datetime.time.max)

            existing = (
                self.db.query(models.Completion)
                .filter(
                    models.Completion.habit_id == habit_id,
                    models.Completion.completed_at >= start_of_week_dt,
                    models.Completion.completed_at <= end_of_week_dt,
                )
                .first()
            )
        else:
            existing = None

        return existing is not None

    def is_habit_completed_today(self, habit_id: int) -> bool:
        """Check if habit is already completed for the current period
        (today for daily, this week for weekly)."""
        habit = self.get_habit_by_id(habit_id)
        if not habit:
            return False

        today = datetime.datetime.now(datetime.timezone.utc).date()
        return self._already_completed_in_period(habit_id, habit.periodicity, today)

    def get_user_preferences(self):
        """Get user preferences, creating default if none exist."""
        preferences = self.db.query(models.UserPreferences).first()
        if not preferences:
            preferences = models.UserPreferences()
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
        return preferences

    def update_user_preferences(
        self, struggle_threshold: float = None, show_bottom_percent: float = None
    ):
        """Update user preferences."""
        preferences = self.get_user_preferences()

        if struggle_threshold is not None:
            # Clamp between 0.1 and 1.0
            preferences.struggle_threshold = max(0.1, min(1.0, struggle_threshold))

        if show_bottom_percent is not None:
            # Clamp between 0.1 and 1.0
            preferences.show_bottom_percent = max(0.1, min(1.0, show_bottom_percent))

        self.db.commit()
        self.db.refresh(preferences)
        return preferences

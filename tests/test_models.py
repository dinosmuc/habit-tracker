import datetime

import pytest

from habittracker.models import Completion, Habit, Periodicity


class TestPeriodicityEnum:
    """Test the Periodicity enum."""

    def test_periodicity_values(self):
        """Test that Periodicity enum has correct values."""
        assert Periodicity.DAILY.value == "daily"
        assert Periodicity.WEEKLY.value == "weekly"

    def test_periodicity_from_string(self):
        """Test creating Periodicity from string values."""
        assert Periodicity("daily") == Periodicity.DAILY
        assert Periodicity("weekly") == Periodicity.WEEKLY

    def test_invalid_periodicity_raises_error(self):
        """Test that invalid periodicity raises ValueError."""
        with pytest.raises(ValueError):
            Periodicity("monthly")


class TestHabitModel:
    """Test the Habit model."""

    def test_habit_creation(self, db_session):
        """Test creating a basic habit."""
        habit = Habit(name="Exercise", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        assert habit.id is not None
        assert habit.name == "Exercise"
        assert habit.periodicity == Periodicity.DAILY
        assert isinstance(habit.created_at, datetime.datetime)

    def test_habit_required_fields(self, db_session):
        """Test that required fields are enforced."""
        # Test missing name
        habit_no_name = Habit(periodicity=Periodicity.DAILY)
        db_session.add(habit_no_name)

        with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
            db_session.commit()

        db_session.rollback()

        # Test missing periodicity
        habit_no_periodicity = Habit(name="Test Habit")
        db_session.add(habit_no_periodicity)

        with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
            db_session.commit()

    def test_habit_created_at_default(self, db_session):
        """Test that created_at is set automatically."""
        before_creation = datetime.datetime.utcnow()
        habit = Habit(name="Test Habit", periodicity=Periodicity.WEEKLY)
        db_session.add(habit)
        db_session.commit()
        after_creation = datetime.datetime.utcnow()

        assert before_creation <= habit.created_at <= after_creation

    def test_habit_relationship_with_completions(self, db_session):
        """Test the relationship between habits and completions."""
        habit = Habit(name="Read", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        # Initially no completions
        assert len(habit.completions) == 0

        # Add completions
        completion1 = Completion(habit_id=habit.id)
        completion2 = Completion(habit_id=habit.id)
        db_session.add_all([completion1, completion2])
        db_session.commit()

        # Refresh the habit to get updated relationships
        db_session.refresh(habit)
        assert len(habit.completions) == 2
        assert completion1 in habit.completions
        assert completion2 in habit.completions

    def test_habit_cascade_delete(self, db_session):
        """Test that deleting a habit cascades to completions."""
        habit = Habit(name="Meditate", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        # Add completions
        completion1 = Completion(habit_id=habit.id)
        completion2 = Completion(habit_id=habit.id)
        db_session.add_all([completion1, completion2])
        db_session.commit()

        completion_ids = [completion1.id, completion2.id]

        # Delete the habit
        db_session.delete(habit)
        db_session.commit()

        # Verify completions are also deleted
        remaining_completions = (
            db_session.query(Completion).filter(Completion.id.in_(completion_ids)).all()
        )
        assert len(remaining_completions) == 0


class TestCompletionModel:
    """Test the Completion model."""

    def test_completion_creation(self, db_session):
        """Test creating a basic completion."""
        # First create a habit
        habit = Habit(name="Walk", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        # Create completion
        completion = Completion(habit_id=habit.id)
        db_session.add(completion)
        db_session.commit()

        assert completion.id is not None
        assert completion.habit_id == habit.id
        assert isinstance(completion.completed_at, datetime.datetime)

    def test_completion_completed_at_default(self, db_session):
        """Test that completed_at is set automatically."""
        habit = Habit(name="Test", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        before_creation = datetime.datetime.utcnow()
        completion = Completion(habit_id=habit.id)
        db_session.add(completion)
        db_session.commit()
        after_creation = datetime.datetime.utcnow()

        assert before_creation <= completion.completed_at <= after_creation

    def test_completion_habit_relationship(self, db_session):
        """Test the relationship between completion and habit."""
        habit = Habit(name="Study", periodicity=Periodicity.WEEKLY)
        db_session.add(habit)
        db_session.commit()

        completion = Completion(habit_id=habit.id)
        db_session.add(completion)
        db_session.commit()

        # Test relationship access
        assert completion.habit == habit
        assert completion in habit.completions

    def test_completion_requires_habit_id(self, db_session):
        """Test that habit_id is required."""
        completion = Completion()
        db_session.add(completion)

        with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
            db_session.commit()

    def test_completion_foreign_key_constraint(self, db_session):
        """Test foreign key constraint is enforced."""
        # Try to create completion with non-existent habit_id
        completion = Completion(habit_id=999)
        db_session.add(completion)

        with pytest.raises(Exception):  # SQLAlchemy will raise a foreign key error
            db_session.commit()

    def test_multiple_completions_same_habit(self, db_session):
        """Test that a habit can have multiple completions."""
        habit = Habit(name="Drink Water", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        # Create multiple completions
        completions = [Completion(habit_id=habit.id) for _ in range(5)]
        db_session.add_all(completions)
        db_session.commit()

        # Verify all completions exist and belong to the same habit
        db_completions = db_session.query(Completion).filter_by(habit_id=habit.id).all()
        assert len(db_completions) == 5

        for completion in db_completions:
            assert completion.habit_id == habit.id
            assert completion.habit == habit


class TestModelIntegration:
    """Test integration between models."""

    def test_habit_completion_workflow(self, db_session):
        """Test a complete workflow of creating habits and completions."""
        # Create multiple habits
        daily_habit = Habit(name="Exercise", periodicity=Periodicity.DAILY)
        weekly_habit = Habit(name="Grocery Shopping", periodicity=Periodicity.WEEKLY)

        db_session.add_all([daily_habit, weekly_habit])
        db_session.commit()

        # Add completions to daily habit
        for i in range(3):
            completion = Completion(habit_id=daily_habit.id)
            db_session.add(completion)

        # Add one completion to weekly habit
        weekly_completion = Completion(habit_id=weekly_habit.id)
        db_session.add(weekly_completion)

        db_session.commit()

        # Verify the setup
        db_session.refresh(daily_habit)
        db_session.refresh(weekly_habit)

        assert len(daily_habit.completions) == 3
        assert len(weekly_habit.completions) == 1

        # Verify total completions in database
        total_completions = db_session.query(Completion).count()
        assert total_completions == 4

    def test_querying_habits_with_completions(self, db_session):
        """Test querying habits along with their completions."""
        # Create habits with different numbers of completions
        habit1 = Habit(name="Habit 1", periodicity=Periodicity.DAILY)
        habit2 = Habit(name="Habit 2", periodicity=Periodicity.WEEKLY)
        habit3 = Habit(name="Habit 3", periodicity=Periodicity.DAILY)

        db_session.add_all([habit1, habit2, habit3])
        db_session.commit()

        # Add varying numbers of completions
        for i in range(2):
            db_session.add(Completion(habit_id=habit1.id))

        for i in range(5):
            db_session.add(Completion(habit_id=habit2.id))

        # habit3 has no completions

        db_session.commit()

        # Query and verify
        habits = db_session.query(Habit).all()
        assert len(habits) == 3

        # Find each habit and check completion counts
        for habit in habits:
            if habit.name == "Habit 1":
                assert len(habit.completions) == 2
            elif habit.name == "Habit 2":
                assert len(habit.completions) == 5
            elif habit.name == "Habit 3":
                assert len(habit.completions) == 0

from unittest.mock import Mock, patch

import pytest

from habittracker.models import Completion, Habit, Periodicity
from habittracker.services import HabitService


class TestHabitService:
    """Test the HabitService class."""

    def test_init(self, db_session):
        """Test service initialization."""
        service = HabitService(db_session)
        assert service.db == db_session

    def test_get_all_habits_empty(self, db_session):
        """Test getting all habits when database is empty."""
        service = HabitService(db_session)
        habits = service.get_all_habits()
        assert habits == []

    def test_get_all_habits_with_data(self, db_session):
        """Test getting all habits when database has data."""
        # Create test habits
        habit1 = Habit(name="Exercise", periodicity=Periodicity.DAILY)
        habit2 = Habit(name="Read", periodicity=Periodicity.WEEKLY)
        db_session.add_all([habit1, habit2])
        db_session.commit()

        service = HabitService(db_session)
        habits = service.get_all_habits()

        assert len(habits) == 2
        habit_names = [h.name for h in habits]
        assert "Exercise" in habit_names
        assert "Read" in habit_names

    def test_get_habit_by_id_existing(self, db_session):
        """Test getting a habit by ID when it exists."""
        habit = Habit(name="Meditate", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        service = HabitService(db_session)
        found_habit = service.get_habit_by_id(habit.id)

        assert found_habit is not None
        assert found_habit.id == habit.id
        assert found_habit.name == "Meditate"

    def test_get_habit_by_id_nonexistent(self, db_session):
        """Test getting a habit by ID when it doesn't exist."""
        service = HabitService(db_session)
        found_habit = service.get_habit_by_id(999)

        assert found_habit is None

    def test_create_habit_valid_data(self, db_session):
        """Test creating a habit with valid data."""
        service = HabitService(db_session)
        habit = service.create_habit("Exercise", "daily")

        assert habit.id is not None
        assert habit.name == "Exercise"
        assert habit.periodicity == Periodicity.DAILY
        assert habit.created_at is not None

        # Verify it was persisted
        db_habit = db_session.query(Habit).filter_by(id=habit.id).first()
        assert db_habit is not None
        assert db_habit.name == "Exercise"

    def test_create_habit_weekly_periodicity(self, db_session):
        """Test creating a habit with weekly periodicity."""
        service = HabitService(db_session)
        habit = service.create_habit("Grocery Shopping", "weekly")

        assert habit.periodicity == Periodicity.WEEKLY

    def test_create_habit_invalid_periodicity(self, db_session):
        """Test creating a habit with invalid periodicity raises error."""
        service = HabitService(db_session)

        with pytest.raises(ValueError):
            service.create_habit("Invalid Habit", "monthly")

    def test_create_habit_empty_name(self, db_session):
        """Test creating a habit with empty name."""
        service = HabitService(db_session)

        # SQLite allows empty strings, so this will succeed
        habit = service.create_habit("", "daily")
        assert habit.name == ""
        assert habit.periodicity == Periodicity.DAILY

    def test_delete_habit_existing(self, db_session):
        """Test deleting an existing habit."""
        habit = Habit(name="Delete Me", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()
        habit_id = habit.id

        service = HabitService(db_session)
        deleted_habit = service.delete_habit(habit_id)

        assert deleted_habit is not None
        assert deleted_habit.name == "Delete Me"

        # Verify it was deleted from database
        found_habit = db_session.query(Habit).filter_by(id=habit_id).first()
        assert found_habit is None

    def test_delete_habit_nonexistent(self, db_session):
        """Test deleting a non-existent habit."""
        service = HabitService(db_session)
        deleted_habit = service.delete_habit(999)

        assert deleted_habit is None

    def test_delete_habit_with_completions(self, db_session):
        """Test deleting a habit that has completions (cascade delete)."""
        habit = Habit(name="Habit with Completions", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        # Add completions
        completion1 = Completion(habit_id=habit.id)
        completion2 = Completion(habit_id=habit.id)
        db_session.add_all([completion1, completion2])
        db_session.commit()

        completion_ids = [completion1.id, completion2.id]
        habit_id = habit.id

        service = HabitService(db_session)
        deleted_habit = service.delete_habit(habit_id)

        assert deleted_habit is not None

        # Verify habit is deleted
        found_habit = db_session.query(Habit).filter_by(id=habit_id).first()
        assert found_habit is None

        # Verify completions are also deleted (cascade)
        remaining_completions = (
            db_session.query(Completion).filter(Completion.id.in_(completion_ids)).all()
        )
        assert len(remaining_completions) == 0

    def test_check_off_habit_existing(self, db_session):
        """Test checking off an existing habit."""
        habit = Habit(name="Check Me Off", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        service = HabitService(db_session)
        completion = service.check_off_habit(habit.id)

        assert completion is not None
        assert completion.habit_id == habit.id
        assert completion.completed_at is not None

        # Verify it was persisted
        db_completion = db_session.query(Completion).filter_by(id=completion.id).first()
        assert db_completion is not None
        assert db_completion.habit_id == habit.id

    def test_check_off_habit_nonexistent(self, db_session):
        """Test checking off a non-existent habit."""
        service = HabitService(db_session)
        completion = service.check_off_habit(999)

        assert completion is None

    def test_check_off_habit_multiple_times(self, db_session):
        """Test checking off the same habit multiple times."""
        habit = Habit(name="Multiple Checkoffs", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        service = HabitService(db_session)

        # Check off multiple times
        completion1 = service.check_off_habit(habit.id)
        completion2 = service.check_off_habit(habit.id)
        completion3 = service.check_off_habit(habit.id)

        assert completion1 is not None
        assert completion2 is not None
        assert completion3 is not None

        # All should have different IDs
        assert completion1.id != completion2.id
        assert completion2.id != completion3.id

        # All should belong to the same habit
        assert completion1.habit_id == habit.id
        assert completion2.habit_id == habit.id
        assert completion3.habit_id == habit.id

        # Verify all were persisted
        completions = db_session.query(Completion).filter_by(habit_id=habit.id).all()
        assert len(completions) == 3


class TestHabitServiceIntegration:
    """Test HabitService integration scenarios."""

    def test_complete_habit_workflow(self, db_session):
        """Test a complete workflow using the service."""
        service = HabitService(db_session)

        # Create a habit
        habit = service.create_habit("Workout", "daily")
        assert habit is not None

        # Verify it can be retrieved
        found_habit = service.get_habit_by_id(habit.id)
        assert found_habit.name == "Workout"

        # Check it off a few times
        completion1 = service.check_off_habit(habit.id)
        completion2 = service.check_off_habit(habit.id)
        assert completion1 is not None
        assert completion2 is not None

        # Verify it appears in all habits
        all_habits = service.get_all_habits()
        assert len(all_habits) == 1
        assert all_habits[0].name == "Workout"

        # Delete the habit
        deleted_habit = service.delete_habit(habit.id)
        assert deleted_habit is not None

        # Verify it's gone
        found_habit = service.get_habit_by_id(habit.id)
        assert found_habit is None

        all_habits = service.get_all_habits()
        assert len(all_habits) == 0

    def test_multiple_habits_management(self, db_session):
        """Test managing multiple habits."""
        service = HabitService(db_session)

        # Create multiple habits
        habit1 = service.create_habit("Exercise", "daily")
        habit2 = service.create_habit("Read", "weekly")
        service.create_habit("Meditate", "daily")

        # Verify all are created
        all_habits = service.get_all_habits()
        assert len(all_habits) == 3

        # Check off different habits
        service.check_off_habit(habit1.id)
        service.check_off_habit(habit1.id)  # Exercise twice
        service.check_off_habit(habit2.id)  # Read once
        # Don't check off meditate

        # Delete one habit
        service.delete_habit(habit2.id)

        # Verify final state
        remaining_habits = service.get_all_habits()
        assert len(remaining_habits) == 2

        remaining_names = [h.name for h in remaining_habits]
        assert "Exercise" in remaining_names
        assert "Meditate" in remaining_names
        assert "Read" not in remaining_names


class TestHabitServiceErrorHandling:
    """Test error handling in HabitService."""

    def test_database_session_error_handling(self):
        """Test service behavior with database session errors."""
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")

        service = HabitService(mock_session)

        with pytest.raises(Exception):
            service.get_all_habits()

    def test_commit_error_handling(self, db_session):
        """Test handling of commit errors."""
        service = HabitService(db_session)

        # Mock the session to raise an error on commit
        with patch.object(db_session, "commit", side_effect=Exception("Commit failed")):
            with pytest.raises(Exception):
                service.create_habit("Test", "daily")

    def test_refresh_error_handling(self, db_session):
        """Test handling of refresh errors."""
        service = HabitService(db_session)

        # Create a habit normally
        habit = Habit(name="Test", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        # Mock refresh to raise an error
        with patch.object(
            db_session, "refresh", side_effect=Exception("Refresh failed")
        ):
            with pytest.raises(Exception):
                service.create_habit("Another Test", "weekly")

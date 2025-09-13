from . import models


def serialize_habit(habit: models.Habit):
    """Converts a Habit SQLAlchemy object into a python dictionary."""
    return {
        "id": habit.id,
        "name": habit.name,
        "periodicity": habit.periodicity.value,
        "created_at": habit.created_at.isoformat(),
    }


def serialize_completion(completion: models.Completion):
    """Converts a Completion SQLAlchemy object into a python dictionary."""
    return {
        "id": completion.id,
        "completed_at": completion.completed_at.isoformat(),
        "habit_id": completion.habit_id,
    }

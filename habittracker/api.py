from flask import Blueprint, jsonify

from .database import get_db
from .serializers import serialize_habit
from .services import HabitService

# Create a Blueprint object to organize routes.
bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/habits", methods=["GET"])
def get_habits():
    """Endpoint to get a list of all habits."""
    db_session = get_db()
    habit_service = HabitService(db_session)
    habits = habit_service.get_all_habits()
    return jsonify([serialize_habit(h) for h in habits])


@bp.route("/habits/<int:habit_id>", methods=["GET"])
def get_habit(habit_id: int):
    """Endpoint to get a single habit."""
    db_session = get_db()
    habit_service = HabitService(db_session)
    habit = habit_service.get_habit_by_id(habit_id)

    if not habit:
        return jsonify({"error": "Habit not found"}), 404

    return jsonify(serialize_habit(habit))

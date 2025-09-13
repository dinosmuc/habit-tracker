from flask import Blueprint, jsonify, request

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


@bp.route("/habits", methods=["POST"])
def create_habit():
    """Endpoint to create a new habit."""
    data = request.get_json()
    if not data or "name" not in data or "periodicity" not in data:
        return jsonify({"error": "Missing name or periodicity"}), 400

    db_session = get_db()
    habit_service = HabitService(db_session)

    try:
        new_habit = habit_service.create_habit(data["name"], data["periodicity"])
        return jsonify(serialize_habit(new_habit)), 201
    except ValueError:
        return jsonify({"error": "Invalid value for periodicity"}), 400

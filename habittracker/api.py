from flask import Blueprint, jsonify, request

from .analytics import AnalyticsService
from .database import get_db
from .serializers import (
    serialize_completion,
    serialize_habit,
    serialize_user_preferences,
)
from .services import HabitAlreadyCompletedError, HabitService

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


@bp.route("/habits/<int:habit_id>", methods=["PUT"])
def update_habit(habit_id: int):
    """Endpoint to update a habit."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    db_session = get_db()
    habit_service = HabitService(db_session)

    try:
        updated_habit = habit_service.update_habit(
            habit_id, name=data.get("name"), periodicity=data.get("periodicity")
        )

        if not updated_habit:
            return jsonify({"error": "Habit not found"}), 404

        return jsonify(serialize_habit(updated_habit)), 200
    except ValueError:
        return jsonify({"error": "Invalid value for periodicity"}), 400


@bp.route("/habits/<int:habit_id>", methods=["DELETE"])
def delete_habit(habit_id: int):
    """Endpoint to delete a habit."""
    db_session = get_db()
    habit_service = HabitService(db_session)
    deleted_habit = habit_service.delete_habit(habit_id)

    if not deleted_habit:
        return jsonify({"error": "Habit not found"}), 404

    return jsonify({"message": "Habit deleted successfully"}), 200


@bp.route("/habits/<int:habit_id>/checkoff", methods=["POST"])
def check_off_habit(habit_id: int):
    """Endpoint for marking a habit as complete."""
    db_session = get_db()
    habit_service = HabitService(db_session)
    try:
        completion = habit_service.check_off_habit(habit_id)
    except HabitAlreadyCompletedError:
        return (
            jsonify({"error": "Habit already completed for this period"}),
            409,
        )

    if not completion:
        return jsonify({"error": "Habit not found"}), 404

    return jsonify(serialize_completion(completion)), 201


@bp.route("/habits/<int:habit_id>/completed", methods=["GET"])
def is_habit_completed(habit_id: int):
    """Endpoint to check if a habit is already completed for the current period."""
    db_session = get_db()
    habit_service = HabitService(db_session)
    is_completed = habit_service.is_habit_completed_today(habit_id)
    return jsonify({"completed": is_completed})


@bp.route("/analytics/habits", methods=["GET"])
def get_habits_analytics():
    """Endpoint to get habits analytics with optional periodicity filter."""
    periodicity = request.args.get("periodicity")
    db_session = get_db()
    analytics_service = AnalyticsService(db_session)
    habits_df = analytics_service.list_habits(periodicity)
    return jsonify(habits_df.to_dict("records"))


@bp.route("/analytics/habits/<int:habit_id>/streaks", methods=["GET"])
def get_habit_streaks(habit_id: int):
    """Endpoint to get streak analytics for a specific habit."""
    db_session = get_db()
    analytics_service = AnalyticsService(db_session)
    streaks = analytics_service.calculate_streaks(habit_id)
    return jsonify(streaks)


@bp.route("/analytics/habits/struggled", methods=["GET"])
def get_struggled_habits():
    """Endpoint to get habits with lowest completion rates in last 30 days."""
    db_session = get_db()

    # Get preferences or use query params as override
    habit_service = HabitService(db_session)
    preferences = habit_service.get_user_preferences()

    threshold = request.args.get(
        "threshold", default=preferences.struggle_threshold, type=float
    )
    quartile = request.args.get(
        "quartile", default=preferences.show_bottom_percent, type=float
    )

    # Clamp values between 0.1 and 1.0
    threshold = max(0.1, min(1.0, threshold))
    quartile = max(0.1, min(1.0, quartile))

    analytics_service = AnalyticsService(db_session)
    struggled_df = analytics_service.identify_struggled_habits(
        threshold=threshold, quartile=quartile
    )
    return jsonify(struggled_df.to_dict("records"))


@bp.route("/analytics/habits/completion-rates", methods=["GET"])
def get_completion_rates():
    """Endpoint to get overall completion rates for all habits."""
    db_session = get_db()
    analytics_service = AnalyticsService(db_session)
    rates_df = analytics_service.overall_completion_rate()
    return jsonify(rates_df.to_dict("records"))


@bp.route("/analytics/habits/<int:habit_id>/best-worst-day", methods=["GET"])
def get_best_worst_day(habit_id: int):
    """Endpoint to get best and worst performing days for a weekly habit."""
    db_session = get_db()
    analytics_service = AnalyticsService(db_session)
    days = analytics_service.best_and_worst_day(habit_id)
    return jsonify(days)


@bp.route("/preferences", methods=["GET"])
def get_preferences():
    """Endpoint to get user preferences."""
    db_session = get_db()
    habit_service = HabitService(db_session)
    preferences = habit_service.get_user_preferences()
    return jsonify(serialize_user_preferences(preferences))


@bp.route("/preferences", methods=["PUT"])
def update_preferences():
    """Endpoint to update user preferences."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    db_session = get_db()
    habit_service = HabitService(db_session)

    try:
        updated_preferences = habit_service.update_user_preferences(
            struggle_threshold=data.get("struggle_threshold"),
            show_bottom_percent=data.get("show_bottom_percent"),
        )
        return jsonify(serialize_user_preferences(updated_preferences)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

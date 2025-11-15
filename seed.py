from datetime import datetime, timedelta, timezone

from habittracker.database import SessionLocal
from habittracker.models import Completion, Habit, Periodicity


def _build_habit_payloads(now: datetime):
    today = now.date()
    start_of_week = today - timedelta(days=today.weekday())

    def daily_completion_dates(offsets):
        return [today - timedelta(days=offset) for offset in offsets]

    two_weeks_ago = now - timedelta(days=14)
    weekly_created_at = now - timedelta(days=21)
    week_one_start = start_of_week - timedelta(days=21)
    week_one_completion = week_one_start + timedelta(days=2)

    return [
        {
            "name": "Morning hydration",
            "periodicity": Periodicity.DAILY,
            "created_at": two_weeks_ago,
            "completion_dates": daily_completion_dates(
                [1, 2, 3, 5, 6, 8, 9, 11, 12, 13]
            ),
        },
        {
            "name": "Evening journaling",
            "periodicity": Periodicity.DAILY,
            "created_at": two_weeks_ago,
            "completion_dates": daily_completion_dates([1, 3, 4, 6, 8, 10, 12, 13]),
        },
        {
            "name": "Midday stretch break",
            "periodicity": Periodicity.DAILY,
            "created_at": two_weeks_ago,
            "completion_dates": daily_completion_dates([2, 4, 5, 7, 9, 10, 12]),
        },
        {
            "name": "Lunchtime walk outside",
            "periodicity": Periodicity.DAILY,
            "created_at": two_weeks_ago,
            "completion_dates": daily_completion_dates([1, 2, 4, 5, 7, 9, 11, 13]),
        },
        {
            "name": "Weekly budget review",
            "periodicity": Periodicity.WEEKLY,
            "created_at": weekly_created_at,
            "completion_dates": [week_one_completion],
        },
    ]


def seed_database():
    """Populates the database with predefined habits and sample data."""
    db = SessionLocal()

    try:
        # --- Clean up existing data ---
        print("Clearing existing data...")
        db.query(Completion).delete()
        db.query(Habit).delete()
        db.commit()

        now = datetime.now(timezone.utc)
        habit_payloads = _build_habit_payloads(now)

        # --- Create predefined habits ---
        print(f"Creating {len(habit_payloads)} predefined habits...")
        habits_with_schedule = []
        for payload in habit_payloads:
            habit = Habit(
                name=payload["name"],
                periodicity=payload["periodicity"],
                created_at=payload["created_at"],
            )
            db.add(habit)
            habits_with_schedule.append((habit, payload["completion_dates"]))
        db.commit()
        print("Habits created successfully.")

        # --- Create sample completion data ---
        print("Creating deterministic completion data for the last few weeks...")
        for habit, completion_dates in habits_with_schedule:
            db.refresh(habit)
            for completion_date in completion_dates:
                completion = Completion(
                    habit_id=habit.id,
                    completed_at=datetime.combine(completion_date, datetime.min.time()),
                )
                db.add(completion)
        db.commit()
        print("Sample data generated successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding database...")
    seed_database()
    print("Database seeding complete.")

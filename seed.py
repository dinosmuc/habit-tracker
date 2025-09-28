import random
from datetime import datetime, timedelta, timezone

from habittracker.database import SessionLocal
from habittracker.models import Completion, Habit, Periodicity

# --- Configuration ---
NUM_HABITS = 5
NUM_WEEKS_DATA = 4
DAYS_IN_WEEK = 7
TOTAL_DAYS = NUM_WEEKS_DATA * DAYS_IN_WEEK

PREDEFINED_HABITS = [
    {"name": "Drink 8 glasses of water", "periodicity": Periodicity.DAILY},
    {"name": "Exercise for 30 minutes", "periodicity": Periodicity.DAILY},
    {"name": "Read a book for 15 minutes", "periodicity": Periodicity.DAILY},
    {"name": "Go for a walk", "periodicity": Periodicity.DAILY},
    {"name": "Weekly review of goals", "periodicity": Periodicity.WEEKLY},
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

        # --- Create predefined habits ---
        print(f"Creating {NUM_HABITS} predefined habits...")
        habits = []
        for habit_data in PREDEFINED_HABITS:
            habit = Habit(
                name=habit_data["name"],
                periodicity=habit_data["periodicity"],
                created_at=datetime.now(timezone.utc) - timedelta(days=TOTAL_DAYS),
            )
            habits.append(habit)
        db.add_all(habits)
        db.commit()
        print("Habits created successfully.")

        # --- Create sample completion data ---
        print(f"Generating {NUM_WEEKS_DATA} weeks of sample completion data...")
        today = datetime.now(timezone.utc).date()
        for habit in habits:
            # Refresh the habit object to get its ID
            db.refresh(habit)

            # Calculate current week boundaries for weekly habits
            days_since_monday = today.weekday()
            start_of_week = today - timedelta(days=days_since_monday)

            for i in range(1, TOTAL_DAYS + 1):  # Start from 1 to skip today
                completion_date = today - timedelta(days=i)

                # Ensure we never create completions for today
                if completion_date >= today:
                    continue

                # Skip current week for weekly habits
                if (
                    habit.periodicity == Periodicity.WEEKLY
                    and completion_date >= start_of_week
                ):
                    continue

                # Randomly decide whether to complete the habit on a given day
                # Daily habits are more likely to be completed
                if habit.periodicity == Periodicity.DAILY:
                    should_complete = random.choice([True, True, True, False])
                else:  # Weekly habits
                    should_complete = random.choice([True, False, False, False])

                if should_complete:
                    completion = Completion(
                        habit_id=habit.id,
                        completed_at=datetime.combine(
                            completion_date, datetime.min.time()
                        ),
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

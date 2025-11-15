import pandas as pd
import pytest

from habittracker.analytics import AnalyticsService
from habittracker.models import Completion, Habit, Periodicity


class TestAnalyticsService:
    def test_list_and_filter_habits(self, db_session):
        h1 = Habit(name="Exercise", periodicity=Periodicity.DAILY)
        h2 = Habit(name="Read", periodicity=Periodicity.WEEKLY)
        db_session.add_all([h1, h2])
        db_session.commit()

        service = AnalyticsService(db_session)
        all_df = service.list_habits()
        assert set(all_df["name"]) == {"Exercise", "Read"}

        daily_df = service.list_habits("daily")
        assert daily_df.shape[0] == 1
        assert daily_df.iloc[0]["name"] == "Exercise"

    def test_calculate_streaks(self, db_session):
        habit = Habit(name="Meditate", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        dates = [
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-01-02"),
            pd.Timestamp("2024-01-04"),
        ]
        db_session.add_all(
            [Completion(habit_id=habit.id, completed_at=d) for d in dates]
        )
        db_session.commit()

        service = AnalyticsService(db_session)
        result = service.calculate_streaks(habit.id, today=pd.Timestamp("2024-01-05"))
        assert result["longest_streak"] == 2
        assert result["current_streak"] == 1

    def test_calculate_streaks_default_today_handles_timezone(self, db_session):
        habit = Habit(name="Journal", periodicity=Periodicity.DAILY)
        db_session.add(habit)
        db_session.commit()

        completions = [
            Completion(habit_id=habit.id, completed_at=pd.Timestamp("2024-01-01")),
            Completion(habit_id=habit.id, completed_at=pd.Timestamp("2024-01-02")),
        ]
        db_session.add_all(completions)
        db_session.commit()

        service = AnalyticsService(db_session)
        result = service.calculate_streaks(habit.id)

        assert result["longest_streak"] == 2
        assert "current_streak" in result

    def test_identify_struggled_habits(self, db_session):
        h1 = Habit(
            name="H1",
            periodicity=Periodicity.DAILY,
            created_at=pd.Timestamp("2023-12-01"),
        )
        h2 = Habit(
            name="H2",
            periodicity=Periodicity.DAILY,
            created_at=pd.Timestamp("2023-12-01"),
        )
        db_session.add_all([h1, h2])
        db_session.commit()

        today = pd.Timestamp("2024-01-31")
        db_session.add(
            Completion(habit_id=h1.id, completed_at=today - pd.Timedelta(days=2))
        )
        db_session.add_all(
            [
                Completion(habit_id=h2.id, completed_at=today - pd.Timedelta(days=i))
                for i in range(5, 10)
            ]
        )
        db_session.commit()

        service = AnalyticsService(db_session)
        df = service.identify_struggled_habits(today=today)
        assert set(df["name"]) == {"H1"}

    def test_overall_completion_rate(self, db_session):
        h1 = Habit(
            name="H1",
            periodicity=Periodicity.DAILY,
            created_at=pd.Timestamp("2024-01-01"),
        )
        h2 = Habit(
            name="H2",
            periodicity=Periodicity.WEEKLY,
            created_at=pd.Timestamp("2023-12-01"),
        )
        db_session.add_all([h1, h2])
        db_session.commit()

        db_session.add_all(
            [
                Completion(habit_id=h1.id, completed_at=pd.Timestamp("2024-01-02")),
                Completion(habit_id=h1.id, completed_at=pd.Timestamp("2024-01-03")),
                Completion(habit_id=h2.id, completed_at=pd.Timestamp("2023-12-08")),
                Completion(habit_id=h2.id, completed_at=pd.Timestamp("2023-12-15")),
            ]
        )
        db_session.commit()

        service = AnalyticsService(db_session)
        today = pd.Timestamp("2024-01-10")
        df = service.overall_completion_rate(today=today)
        rate_h1 = df.loc[df["name"] == "H1", "completion_rate"].iloc[0]
        rate_h2 = df.loc[df["name"] == "H2", "completion_rate"].iloc[0]
        assert rate_h1 == pytest.approx(2 / 9, rel=1e-3)  # 2 completions in 9 days
        assert rate_h2 == pytest.approx(
            2 / 5, rel=1e-3
        )  # 2 completions in 5 weeks (40//7=5)

    def test_best_and_worst_day(self, db_session):
        habit = Habit(name="Weekly", periodicity=Periodicity.WEEKLY)
        db_session.add(habit)
        db_session.commit()

        dates = [
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-01-03"),
            pd.Timestamp("2024-01-10"),
        ]
        db_session.add_all(
            [Completion(habit_id=habit.id, completed_at=d) for d in dates]
        )
        db_session.commit()

        service = AnalyticsService(db_session)
        res = service.best_and_worst_day(habit.id)
        assert res["best_day"] == "Wednesday"
        assert res["worst_day"] == "Monday"

    def test_best_and_worst_day_no_clear_worst(self, db_session):
        habit = Habit(name="Weekly", periodicity=Periodicity.WEEKLY)
        db_session.add(habit)
        db_session.commit()

        db_session.add(
            Completion(habit_id=habit.id, completed_at=pd.Timestamp("2024-01-06"))
        )
        db_session.commit()

        service = AnalyticsService(db_session)
        res = service.best_and_worst_day(habit.id)
        assert res["best_day"] == "Saturday"
        assert res["worst_day"] == "N/A"

    def test_identify_struggled_habits_custom_threshold(self, db_session):
        """Test struggled habits with custom threshold parameter."""
        today = pd.Timestamp("2024-01-31")
        habit1 = Habit(
            name="Good Habit",
            periodicity=Periodicity.DAILY,
            created_at=today - pd.Timedelta(days=30),
        )
        habit2 = Habit(
            name="Bad Habit",
            periodicity=Periodicity.DAILY,
            created_at=today - pd.Timedelta(days=30),
        )
        db_session.add_all([habit1, habit2])
        db_session.commit()

        # Good habit: 25/30 completions = 83% rate
        good_completions = [
            Completion(habit_id=habit1.id, completed_at=today - pd.Timedelta(days=i))
            for i in range(25)
        ]
        # Bad habit: 10/30 completions = 33% rate
        bad_completions = [
            Completion(habit_id=habit2.id, completed_at=today - pd.Timedelta(days=i))
            for i in range(10)
        ]
        db_session.add_all(good_completions + bad_completions)
        db_session.commit()

        service = AnalyticsService(db_session)

        # With high threshold (90%), both should be struggling
        struggled_high = service.identify_struggled_habits(
            today=today, threshold=0.9, quartile=1.0
        )
        assert len(struggled_high) == 2

        # With low threshold (30%), only bad habit should be struggling
        struggled_low = service.identify_struggled_habits(
            today=today, threshold=0.3, quartile=1.0
        )
        assert len(struggled_low) == 0  # Bad habit is 33% which is above 30%

        # With medium threshold (50%), only bad habit should be struggling
        struggled_med = service.identify_struggled_habits(
            today=today, threshold=0.5, quartile=1.0
        )
        assert len(struggled_med) == 1
        assert struggled_med.iloc[0]["name"] == "Bad Habit"

    def test_identify_struggled_habits_custom_quartile(self, db_session):
        """Test struggled habits with custom quartile parameter."""
        today = pd.Timestamp("2024-01-31")

        # Create 4 habits with different completion rates (all below 50% threshold)
        habits = []
        for i, rate in enumerate([0.1, 0.2, 0.3, 0.4]):  # 10%, 20%, 30%, 40%
            habit = Habit(
                name=f"Habit {i+1}",
                periodicity=Periodicity.DAILY,
                created_at=today - pd.Timedelta(days=30),
            )
            db_session.add(habit)
            db_session.commit()

            # Add completions based on rate
            num_completions = int(30 * rate)
            completions = [
                Completion(habit_id=habit.id, completed_at=today - pd.Timedelta(days=j))
                for j in range(num_completions)
            ]
            db_session.add_all(completions)
            habits.append(habit)

        db_session.commit()
        service = AnalyticsService(db_session)

        # With quartile=0.25 (25%), should return 1 habit (worst 25% of 4 = 1)
        struggled_25 = service.identify_struggled_habits(
            today=today, threshold=0.5, quartile=0.25
        )
        assert len(struggled_25) == 1
        assert struggled_25.iloc[0]["name"] == "Habit 1"  # Worst performing

        # With quartile=0.5 (50%), should return 2 habits (worst 50% of 4 = 2)
        struggled_50 = service.identify_struggled_habits(
            today=today, threshold=0.5, quartile=0.5
        )
        assert len(struggled_50) == 2

        # With quartile=1.0 (100%), should return all 4 habits
        struggled_100 = service.identify_struggled_habits(
            today=today, threshold=0.5, quartile=1.0
        )
        assert len(struggled_100) == 4

    def test_identify_struggled_habits_no_struggling_habits(self, db_session):
        """Test struggled habits when all habits are performing well."""
        today = pd.Timestamp("2024-01-31")
        habit = Habit(
            name="Great Habit",
            periodicity=Periodicity.DAILY,
            created_at=today - pd.Timedelta(days=30),
        )
        db_session.add(habit)
        db_session.commit()

        # Perfect completion: 30/30 = 100%
        completions = [
            Completion(habit_id=habit.id, completed_at=today - pd.Timedelta(days=i))
            for i in range(30)
        ]
        db_session.add_all(completions)
        db_session.commit()

        service = AnalyticsService(db_session)

        # With 75% threshold, no habits should be struggling
        struggled = service.identify_struggled_habits(
            today=today, threshold=0.75, quartile=0.25
        )
        assert len(struggled) == 0

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
        assert rate_h1 == pytest.approx(0.2, rel=1e-3)
        assert rate_h2 == pytest.approx(2 / 6, rel=1e-3)

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
        assert res["worst_day"] == "Tuesday"

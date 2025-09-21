import pandas as pd
from sqlalchemy.orm import Session

from . import models


class AnalyticsService:
    """Provides analytical insights into user habits using pandas."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def _habits_df(self) -> pd.DataFrame:
        df = pd.read_sql(
            self.db.query(models.Habit).statement,
            self.db.bind,
            parse_dates=["created_at"],
        )
        return df.assign(
            periodicity=lambda d: d["periodicity"].map(
                lambda x: getattr(x, "name", str(x))
            )
        )

    def _completions_df(self) -> pd.DataFrame:
        return pd.read_sql(
            self.db.query(models.Completion).statement,
            self.db.bind,
            parse_dates=["completed_at"],
        )

    def list_habits(self, periodicity: str | None = None) -> pd.DataFrame:
        """Return all habits or filter by periodicity."""
        df = self._habits_df()
        return df if not periodicity else df[df["periodicity"] == periodicity.upper()]

    def calculate_streaks(
        self, habit_id: int, today: pd.Timestamp | None = None
    ) -> dict:
        """Calculate longest and current streak for a habit."""
        habit = self.db.query(models.Habit).filter(models.Habit.id == habit_id).first()
        if not habit:
            return {"longest_streak": 0, "current_streak": 0}

        period = 1 if habit.periodicity == models.Periodicity.DAILY else 7
        df = pd.read_sql(
            self.db.query(models.Completion)
            .filter(models.Completion.habit_id == habit_id)
            .order_by(models.Completion.completed_at)
            .statement,
            self.db.bind,
            parse_dates=["completed_at"],
        )
        if df.empty:
            return {"longest_streak": 0, "current_streak": 0}

        df = df.sort_values("completed_at")
        df["gap"] = df["completed_at"].diff().dt.days.fillna(0).gt(period)
        df["streak_id"] = df["gap"].cumsum()
        streaks = df.groupby("streak_id").size()
        longest = int(streaks.max())

        today = today or pd.Timestamp.utcnow().tz_localize(None).tz_localize(None)
        last_date = df["completed_at"].max()
        current = int(streaks.iloc[-1]) if (today - last_date).days <= period else 0
        return {"longest_streak": longest, "current_streak": current}

    def identify_struggled_habits(
        self, today: pd.Timestamp | None = None
    ) -> pd.DataFrame:
        """Return habits with lowest completion percentage over last 30 days."""
        today = today or pd.Timestamp.utcnow().tz_localize(None)
        start = today - pd.Timedelta(days=30)

        habits = self._habits_df()
        completions = pd.read_sql(
            self.db.query(models.Completion)
            .filter(models.Completion.completed_at >= start)
            .statement,
            self.db.bind,
            parse_dates=["completed_at"],
        )

        counts = (
            completions.groupby("habit_id").size().rename("completed").reset_index()
        )
        merged = habits.merge(
            counts, left_on="id", right_on="habit_id", how="left"
        ).fillna({"completed": 0})
        merged["period_days"] = merged["periodicity"].map({"DAILY": 1, "WEEKLY": 7})
        merged["expected"] = 30 / merged["period_days"]
        merged["completion_rate"] = merged["completed"] / merged["expected"]
        min_rate = merged["completion_rate"].min()
        return merged.loc[
            merged["completion_rate"] == min_rate, ["id", "name", "completion_rate"]
        ]

    def overall_completion_rate(
        self, today: pd.Timestamp | None = None
    ) -> pd.DataFrame:
        """Calculate overall completion rate for each habit."""
        today = today or pd.Timestamp.utcnow().tz_localize(None)
        habits = self._habits_df()
        completions = self._completions_df()

        counts = (
            completions.groupby("habit_id").size().rename("completed").reset_index()
        )
        merged = habits.merge(
            counts, left_on="id", right_on="habit_id", how="left"
        ).fillna({"completed": 0})
        merged["period_days"] = merged["periodicity"].map({"DAILY": 1, "WEEKLY": 7})
        merged["total_days"] = (today - merged["created_at"]).dt.days
        merged["expected"] = (merged["total_days"] / merged["period_days"]).floordiv(
            1
        ) + 1
        merged["completion_rate"] = merged["completed"] / merged["expected"]
        return merged[["id", "name", "completion_rate"]]

    def best_and_worst_day(self, habit_id: int) -> dict:
        """Determine best and worst performing days for a weekly habit."""
        habit = self.db.query(models.Habit).filter(models.Habit.id == habit_id).first()
        if not habit or habit.periodicity != models.Periodicity.WEEKLY:
            return {"best_day": None, "worst_day": None}

        df = pd.read_sql(
            self.db.query(models.Completion)
            .filter(models.Completion.habit_id == habit_id)
            .statement,
            self.db.bind,
            parse_dates=["completed_at"],
        )
        if df.empty:
            return {"best_day": None, "worst_day": None}

        counts = (
            df["completed_at"]
            .dt.day_name()
            .value_counts()
            .reindex(
                [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ],
                fill_value=0,
            )
        )
        return {"best_day": counts.idxmax(), "worst_day": counts.idxmin()}

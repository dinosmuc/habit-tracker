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

        if today is None:
            today = pd.Timestamp.utcnow()
        if not isinstance(today, pd.Timestamp):
            today = pd.Timestamp(today)
        if today.tzinfo is not None and today.tzinfo.utcoffset(today) is not None:
            today = today.tz_convert(None)
        last_date = df["completed_at"].max()
        current = int(streaks.iloc[-1]) if (today - last_date).days <= period else 0
        return {"longest_streak": longest, "current_streak": current}

    def identify_struggled_habits(
        self,
        today: pd.Timestamp | None = None,
        threshold: float = 0.75,
        quartile: float = 0.25,
    ) -> pd.DataFrame:
        """Return habits in bottom quartile below the specified threshold."""
        today = today or pd.Timestamp.utcnow().tz_localize(None)

        habits = self._habits_df()
        if habits.empty:
            return pd.DataFrame(columns=["id", "name", "completion_rate"])

        # Calculate individual analysis periods for each habit
        # Use minimum of 30 days or days since creation (minimum 1 day)
        max_analysis_days = 30
        habits["created_date"] = pd.to_datetime(habits["created_at"]).dt.tz_localize(
            None
        )
        habits["days_since_creation"] = (today - habits["created_date"]).dt.days
        # Ensure minimum analysis period of 1 day (for habits created today)
        habits["analysis_days"] = habits["days_since_creation"].clip(
            lower=1, upper=max_analysis_days
        )
        # Use start of day for consistent analysis periods
        today_start = today.normalize()  # Beginning of today
        habits["analysis_start"] = today_start - pd.to_timedelta(
            habits["analysis_days"] - 1, unit="D"
        )

        # Get completions for each habit's individual analysis period
        all_completions = []
        for _, habit in habits.iterrows():
            habit_completions = pd.read_sql(
                self.db.query(models.Completion)
                .filter(
                    models.Completion.habit_id == habit["id"],
                    models.Completion.completed_at >= habit["analysis_start"],
                )
                .statement,
                self.db.bind,
                parse_dates=["completed_at"],
            )
            if not habit_completions.empty:
                all_completions.append(habit_completions)

        if all_completions:
            completions = pd.concat(all_completions, ignore_index=True)
            counts = (
                completions.groupby("habit_id").size().rename("completed").reset_index()
            )
        else:
            counts = pd.DataFrame(columns=["habit_id", "completed"])

        merged = (
            habits.merge(counts, left_on="id", right_on="habit_id", how="left")
            .fillna({"completed": 0})
            .infer_objects(copy=False)
        )

        merged["period_days"] = merged["periodicity"].map({"DAILY": 1, "WEEKLY": 7})
        # Calculate expected completions based on actual analysis period for each habit
        merged["expected"] = merged["analysis_days"] / merged["period_days"]
        merged["completion_rate"] = (
            (merged["completed"] / merged["expected"]).fillna(0).clip(upper=1.0)
        )

        # Only consider habits below threshold
        bottom_performers = merged[merged["completion_rate"] < threshold]

        if bottom_performers.empty:
            return pd.DataFrame(columns=["id", "name", "completion_rate"])

        # Return specified portion of underperforming habits (minimum 1)
        portion_size = max(1, int(len(bottom_performers) * quartile))
        return bottom_performers.nsmallest(portion_size, "completion_rate")[
            ["id", "name", "completion_rate"]
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
        merged = (
            habits.merge(counts, left_on="id", right_on="habit_id", how="left")
            .fillna({"completed": 0})
            .infer_objects(copy=False)
        )
        merged["period_days"] = merged["periodicity"].map({"DAILY": 1, "WEEKLY": 7})
        merged["total_days"] = (today - merged["created_at"]).dt.days
        merged["expected"] = (merged["total_days"] / merged["period_days"]).floordiv(1)
        # Avoid division by zero: handle expected=0 case properly
        merged["completion_rate"] = merged.apply(
            lambda row: (
                1.0
                if row["expected"] == 0 and row["completed"] > 0
                else (
                    0.0
                    if row["expected"] == 0
                    else min(1.0, row["completed"] / row["expected"])
                )
            ),
            axis=1,
        )
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

        best_day = counts.idxmax()

        # Only consider days we've actually observed completions on when
        # determining the worst day. If a habit has only been completed on a
        # single weekday, there's no meaningful "worst" day yet.
        observed_days = counts[counts > 0]
        worst_day = "N/A"

        if observed_days.shape[0] > 1:
            min_count = observed_days.min()
            lowest_days = observed_days[observed_days == min_count]
            if lowest_days.shape[0] == 1:
                worst_day = lowest_days.index[0]

        return {"best_day": best_day, "worst_day": worst_day}

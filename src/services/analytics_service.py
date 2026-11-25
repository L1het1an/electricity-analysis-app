"""Aggregation and comparison service backing the analytics dashboard (UC-03..UC-06).

The service is read-only: it never writes to ``data/processed`` and it keeps every
raw measurement untouched, as required by NFR-02. All aggregation happens on an
in-memory copy of the measurements table.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd

from src.data.repository import CSVDataRepository
from src.models import User

GRANULARITIES: tuple[str, ...] = ("Day", "Month", "Year")
MAX_COMPARE_HOMES: int = 5
MIN_COMPARE_HOMES: int = 2
AVERAGE_LABEL: str = "System average (all 500 homes)"

PALETTE: tuple[str, ...] = (
    "#1F77B4",
    "#D62728",
    "#2CA02C",
    "#FF7F0E",
    "#9467BD",
)
AVERAGE_COLOUR: str = "#4D4D4D"


class UnauthorizedHomeError(PermissionError):
    """Raised when a user requests a household they are not allowed to read."""


@dataclass(frozen=True)
class PeriodSummary:
    """Total and mean consumption for one household over the current query."""

    home_id: int
    total_kwh: float
    mean_kwh: float
    points: int
    days: int
    mean_household_size: float


class AnalyticsService:
    """Compute consumption aggregates for the households a user may read."""

    def __init__(self, repository: CSVDataRepository) -> None:
        """Bind the service to an initialized CSV repository."""
        self._repository = repository
        self._measurements: pd.DataFrame | None = None
        self._appliances: pd.DataFrame | None = None

    # ------------------------------------------------------------------ #
    # Reference data
    # ------------------------------------------------------------------ #
    def authorize(self, user: User) -> list[int]:
        """Return the household ids the given user may analyse.

        Admins may read every household; a standard user only receives the
        households linked to their account.
        """
        if user.is_admin():
            return sorted(self._get_measurements()["home_id"].unique().tolist())
        return sorted(int(home) for home in user.home_ids)

    def appliance_options(self) -> pd.DataFrame:
        """Return the appliance lookup table ordered by appliance id."""
        return self._get_appliances().sort_values("appliance_id").reset_index(drop=True)

    def date_bounds(self) -> tuple[str, str]:
        """Return the earliest and latest measurement date, both ``YYYY-MM-DD``."""
        dates = self._get_measurements()["date"].dropna()
        return str(dates.min()), str(dates.max())

    # ------------------------------------------------------------------ #
    # Core queries
    # ------------------------------------------------------------------ #
    def filter_measurements(
        self,
        home_ids: Sequence[int],
        appliance_ids: Sequence[int] | None = None,
        user: User | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> pd.DataFrame:
        """Return the raw measurements matching every supplied filter.

        The rows are returned exactly as stored; only the selection changes.
        """
        homes = self._check_homes(home_ids, user)
        frame = self._get_measurements()
        frame = frame[frame["home_id"].isin(homes)]
        if appliance_ids is not None:
            wanted = list(appliance_ids)
            frame = frame[frame["appliance_id"].isin(wanted)]
        if date_from is not None:
            frame = frame[frame["date"] >= date_from]
        if date_to is not None:
            frame = frame[frame["date"] <= date_to]
        return frame.reset_index(drop=True)

    def aggregate(
        self,
        home_ids: Sequence[int],
        granularity: str = "Day",
        appliance_ids: Sequence[int] | None = None,
        user: User | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> pd.DataFrame:
        """Aggregate consumption per household and period.

        Returns a frame with the columns ``home_id``, ``period``, ``kwh`` and
        ``points``, where ``points`` counts the underlying measurements.
        """
        level = self._check_granularity(granularity)
        rows = self.filter_measurements(
            home_ids, appliance_ids, user=user, date_from=date_from, date_to=date_to
        )
        if rows.empty:
            return pd.DataFrame(
                columns=["home_id", "period", "kwh", "points"]
            )

        stamped = rows.assign(_stamp=pd.to_datetime(rows["date"]))
        stamped = stamped.assign(period=self._period_column(stamped["_stamp"], level))
        grouped = (
            stamped.groupby(["home_id", "period"], as_index=False)
            .agg(kwh=("energy_consumption", "sum"), points=("measurement_id", "count"))
        )
        grouped["kwh"] = grouped["kwh"].round(3)
        return grouped.sort_values(["home_id", "period"]).reset_index(drop=True)

    def system_average(
        self,
        granularity: str = "Day",
        appliance_ids: Sequence[int] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> pd.DataFrame:
        """Return the mean consumption per period across every household.

        The benchmark is computed on the full population, never on the user's
        subset, and no third-party raw record leaves the service (UC-05).
        """
        level = self._check_granularity(granularity)
        rows = self.filter_measurements(
            self.authorize(self._admin_proxy()),
            appliance_ids,
            date_from=date_from,
            date_to=date_to,
        )
        if rows.empty:
            return pd.DataFrame(columns=["period", "avg_kwh", "homes"])

        stamped = rows.assign(_stamp=pd.to_datetime(rows["date"]))
        stamped = stamped.assign(period=self._period_column(stamped["_stamp"], level))
        per_home = (
            stamped.groupby(["home_id", "period"], as_index=False)[
                "energy_consumption"
            ].sum()
        )
        averaged = (
            per_home.groupby("period", as_index=False)
            .agg(avg_kwh=("energy_consumption", "mean"), homes=("home_id", "nunique"))
        )
        averaged["avg_kwh"] = averaged["avg_kwh"].round(3)
        return averaged.sort_values("period").reset_index(drop=True)

    def summarise(
        self,
        home_ids: Sequence[int],
        appliance_ids: Sequence[int] | None = None,
        user: User | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[PeriodSummary]:
        """Return one :class:`PeriodSummary` per requested household.

        ``mean_household_size`` is the average of the raw recorded sizes, as
        required for the per-resident figure of the bonus export.
        """
        rows = self.filter_measurements(
            home_ids, appliance_ids, user=user, date_from=date_from, date_to=date_to
        )
        summaries: list[PeriodSummary] = []
        for home in self._check_homes(home_ids, user):
            subset = rows[rows["home_id"] == home]
            summaries.append(
                PeriodSummary(
                    home_id=home,
                    total_kwh=round(float(subset["energy_consumption"].sum()), 3),
                    mean_kwh=round(
                        float(subset["energy_consumption"].mean())
                        if len(subset)
                        else 0.0,
                        3,
                    ),
                    points=int(len(subset)),
                    days=int(subset["date"].nunique()),
                    mean_household_size=round(
                        float(subset["household_size"].mean()) if len(subset) else 0.0,
                        2,
                    ),
                )
            )
        return summaries

    def kpi_table(
        self,
        home_ids: Sequence[int],
        granularity: str = "Day",
        appliance_ids: Sequence[int] | None = None,
        user: User | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> pd.DataFrame:
        """Return one row per household with the headline indicators."""
        level = self._check_granularity(granularity)
        rows = self.filter_measurements(
            home_ids, appliance_ids, user=user, date_from=date_from, date_to=date_to
        )
        periods = self.aggregate(
            home_ids,
            level,
            appliance_ids,
            user=user,
            date_from=date_from,
            date_to=date_to,
        )
        records: list[dict[str, object]] = []
        for summary in self.summarise(
            home_ids,
            appliance_ids,
            user=user,
            date_from=date_from,
            date_to=date_to,
        ):
            own = periods[periods["home_id"] == summary.home_id]
            resident = (
                summary.total_kwh / summary.mean_household_size
                if summary.mean_household_size
                else 0.0
            )
            records.append(
                {
                    "home_id": summary.home_id,
                    "total_kwh": summary.total_kwh,
                    "n_periods": int(len(own)),
                    "mean_per_period_kwh": round(
                        float(own["kwh"].mean()) if len(own) else 0.0, 3
                    ),
                    "measurements": summary.points,
                    "days": summary.days,
                    "mean_household_size": summary.mean_household_size,
                    "kwh_per_resident": round(resident, 3),
                }
            )
        del rows
        return pd.DataFrame(records)

    def series_labels(self, home_ids: Sequence[int]) -> list[str]:
        """Return the legend label used for each household in the chart."""
        return [f"Home {int(home)}" for home in home_ids]

    def colour_map(self, home_ids: Sequence[int]) -> dict[str, str]:
        """Return a stable colour for every household label of the chart."""
        colours = {
            label: PALETTE[index % len(PALETTE)]
            for index, label in enumerate(self.series_labels(home_ids))
        }
        colours[AVERAGE_LABEL] = AVERAGE_COLOUR
        return colours

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _check_homes(
        self, home_ids: Sequence[int], user: User | None
    ) -> list[int]:
        """Validate the requested homes against the user's authorisation."""
        homes = [int(home) for home in home_ids]
        if not homes:
            raise ValueError("Select at least one household.")
        if user is None:
            return homes
        denied = [home for home in homes if not user.can_access_home(home)]
        if denied:
            raise UnauthorizedHomeError(
                f"Households not available to {user.users_name}: {denied}"
            )
        return homes

    @staticmethod
    def _check_granularity(granularity: str) -> str:
        """Validate the requested granularity label."""
        normalized = str(granularity).strip().capitalize()
        if normalized not in GRANULARITIES:
            raise ValueError(
                f"Unsupported granularity {granularity!r}; use one of {GRANULARITIES}."
            )
        return normalized

    @staticmethod
    def _period_column(stamps: pd.Series, level: str) -> pd.Series:
        """Derive the period label for the requested granularity."""
        if level == "Day":
            return stamps.dt.strftime("%Y-%m-%d")
        if level == "Month":
            return stamps.dt.strftime("%Y-%m")
        return stamps.dt.strftime("%Y")

    @staticmethod
    def _admin_proxy() -> User:
        """Return a throw-away admin identity used for population-wide queries."""
        return User(
            users_id=0,
            users_name="__system__",
            password_hash="",
            role="Admin",
        )

    def _get_measurements(self) -> pd.DataFrame:
        """Load the measurements fact table once per service instance."""
        if self._measurements is None:
            self._measurements = self._repository.load_measurements()
        return self._measurements

    def _get_appliances(self) -> pd.DataFrame:
        """Load the appliance lookup table once per service instance."""
        if self._appliances is None:
            self._appliances = self._repository.load_appliances()
        return self._appliances

    def reload(self) -> None:
        """Drop the cached tables so the next query hits the CSV files again."""
        self._measurements = None
        self._appliances = None

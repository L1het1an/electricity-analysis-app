"""Unit tests for the analytics service backing the dashboard (UC-03..UC-06)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.data.repository import CSVDataRepository
from src.models import User
from src.services.analytics_service import (
    AVERAGE_LABEL,
    GRANULARITIES,
    MAX_COMPARE_HOMES,
    AnalyticsService,
    UnauthorizedHomeError,
)

PROCESSED = Path("data/processed")
pytestmark = pytest.mark.skipif(
    not (PROCESSED / "measurements.csv").exists(),
    reason="run the ETL once to generate data/processed/*.csv",
)


@pytest.fixture(scope="module")
def service() -> AnalyticsService:
    """Return a service bound to the processed CSV tables."""
    return AnalyticsService(CSVDataRepository(PROCESSED))


@pytest.fixture(scope="module")
def users(service: AnalyticsService) -> dict[str, User]:
    """Return the three seeded demo identities."""
    return {
        "admin": User(1, "admin", "", "Admin"),
        "user1": User(2, "user1", "", "User", [1]),
        "multi": User(3, "user_multi", "", "User", [1, 2, 3]),
    }


# --------------------------------------------------------------------------- #
# Authorisation (RBAC)
# --------------------------------------------------------------------------- #
def test_admin_sees_every_household(service, users):
    """An administrator is authorised on all 500 households."""
    assert len(service.authorize(users["admin"])) == 500


def test_user_sees_only_linked_households(service, users):
    """A standard user is limited to the households linked to the account."""
    assert service.authorize(users["user1"]) == [1]
    assert service.authorize(users["multi"]) == [1, 2, 3]


def test_unlinked_household_is_rejected(service, users):
    """Querying a household outside the user's scope raises a permission error."""
    with pytest.raises(UnauthorizedHomeError):
        service.filter_measurements([99], user=users["user1"])


def test_empty_selection_is_rejected(service, users):
    """An empty household selection is a user error, not an empty result."""
    with pytest.raises(ValueError):
        service.filter_measurements([], user=users["user1"])


# --------------------------------------------------------------------------- #
# Aggregation (FR-03)
# --------------------------------------------------------------------------- #
def test_granularities_are_supported(service):
    """Every documented granularity is accepted and capitalisation is forgiving."""
    assert GRANULARITIES == ("Day", "Month", "Year")
    for level in GRANULARITIES:
        assert not service.aggregate([1], level.lower()).empty


def test_unknown_granularity_is_rejected(service):
    """An unsupported granularity raises a ValueError with a helpful message."""
    with pytest.raises(ValueError):
        service.aggregate([1], "Week")


def test_monthly_totals_match_the_raw_rows(service):
    """Monthly aggregation equals a direct groupby of the raw measurements."""
    rows = service.filter_measurements([1])
    expected = (
        rows.assign(period=pd.to_datetime(rows["date"]).dt.strftime("%Y-%m"))
        .groupby("period")["energy_consumption"]
        .sum()
        .round(3)
        .to_dict()
    )
    actual = service.aggregate([1], "Month").set_index("period")["kwh"].to_dict()
    assert actual == expected


def test_aggregation_preserves_the_measurement_count(service):
    """The sum of the per-period counts equals the number of raw rows."""
    rows = service.filter_measurements([1])
    aggregated = service.aggregate([1], "Day")
    assert int(aggregated["points"].sum()) == len(rows)


def test_year_view_collapses_to_one_point(service):
    """A full-year view returns exactly one period per household."""
    assert len(service.aggregate([1], "Year")) == 1


# --------------------------------------------------------------------------- #
# Appliance filter (FR-06)
# --------------------------------------------------------------------------- #
def test_excluding_fridge_lowers_the_total(service):
    """Excluding one appliance strictly reduces the total consumption."""
    appliances = service.appliance_options()
    fridge_id = int(
        appliances.loc[appliances["appliance_name"] == "Fridge", "appliance_id"].iloc[0]
    )
    every = service.summarise([1])[0].total_kwh
    without = service.summarise([1], [fridge_id])[0].total_kwh
    assert without < every


def test_appliance_filter_keeps_only_selected_sources(service):
    """The filtered frame only contains the requested appliance ids."""
    appliances = service.appliance_options()
    heater_id = int(
        appliances.loc[appliances["appliance_name"] == "Heater", "appliance_id"].iloc[0]
    )
    rows = service.filter_measurements([1], [heater_id])
    assert not rows.empty
    assert set(rows["appliance_id"].unique()) == {heater_id}


def test_appliance_lookup_has_ten_categories(service):
    """The lookup table exposes the ten documented appliance categories."""
    assert len(service.appliance_options()) == 10


# --------------------------------------------------------------------------- #
# Comparison (FR-04) and benchmark (FR-05)
# --------------------------------------------------------------------------- #
def test_comparison_limit_is_five(service, users):
    """The dashboard never offers more than five households at once."""
    assert MAX_COMPARE_HOMES == 5
    with pytest.raises(UnauthorizedHomeError):
        service.filter_measurements(list(range(1, 6)), user=users["multi"])


def test_three_household_comparison_returns_three_series(service):
    """A three-home selection yields one KPI row per household."""
    table = service.kpi_table([1, 2, 3], "Day")
    assert sorted(table["home_id"].tolist()) == [1, 2, 3]


def test_system_average_covers_the_whole_population(service):
    """The benchmark is computed over all 500 households, not a subset."""
    average = service.system_average("Month")
    assert not average.empty
    assert average["homes"].max() == 500


def test_system_average_is_close_to_the_population_mean(service):
    """The annual benchmark sits near the documented 300 kWh per household.

    The export runs from 2023-01-01 to 2024-01-01, so the year view legitimately
    returns two rows: 2023 and the single stray day of 2024.
    """
    average = service.system_average("Year").set_index("period")
    assert list(average.index) == ["2023", "2024"]
    assert 250 < average.loc["2023", "avg_kwh"] < 350
    assert average.loc["2023", "homes"] == 500


def test_colour_map_assigns_distinct_colours(service):
    """Each household gets its own colour and the average a neutral one."""
    homes = [1, 2, 3, 4, 5]
    colours = service.colour_map(homes)
    household_colours = [colours[label] for label in service.series_labels(homes)]
    assert len(set(household_colours)) == len(homes)
    assert colours[AVERAGE_LABEL] not in household_colours


# --------------------------------------------------------------------------- #
# KPIs and per-resident figures (UC-08 input)
# --------------------------------------------------------------------------- #
def test_period_bounds_match_the_dataset(service):
    """The slider bounds span the full 2023-01-01 to 2024-01-01 window."""
    assert service.date_bounds() == ("2023-01-01", "2024-01-01")


def test_per_resident_figure_divides_by_the_mean_size(service):
    """The per-resident KPI is total divided by the mean recorded household size."""
    summary = service.summarise([1])[0]
    row = service.kpi_table([1]).iloc[0]
    assert row["kwh_per_resident"] == pytest.approx(
        summary.total_kwh / summary.mean_household_size, rel=1e-3
    )


def test_date_window_narrows_the_result(service):
    """Restricting the period strictly reduces the number of points."""
    full = service.summarise([1])[0].points
    narrowed = service.summarise([1], date_from="2023-01-01", date_to="2023-03-31")[0]
    assert 0 < narrowed.points < full


def test_snapshots_are_read_only(service):
    """Querying twice returns identical numbers, proving no write happens."""
    first = service.summarise([1])[0]
    service.reload()
    second = service.summarise([1])[0]
    assert first == second

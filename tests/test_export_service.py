"""Unit tests for ReportExportService aggregation, CSV export, and latency (SVVP EXP-01, NFR-01)."""

from __future__ import annotations

from pathlib import Path
import time
import pandas as pd
import pytest

from src.data.repository import CSVDataRepository
from src.services.export_service import ReportExportService


@pytest.fixture()
def export_repo(tmp_path: Path) -> CSVDataRepository:
    """Create a small dataset spanning two months and two households."""
    raw_file = tmp_path / "export_raw.csv"
    df = pd.DataFrame(
        [
            {
                "Home ID": 1,
                "Appliance Type": "Fridge",
                "Energy Consumption (kWh)": 2.0,
                "Time": "08:00",
                "Date": "2023-01-10",
                "Outdoor Temperature (°C)": 5.0,
                "Season": "Winter",
                "Household Size": 2,
            },
            {
                "Home ID": 1,
                "Appliance Type": "Heater",
                "Energy Consumption (kWh)": 4.0,
                "Time": "20:00",
                "Date": "2023-01-20",
                "Outdoor Temperature (°C)": 2.0,
                "Season": "Winter",
                "Household Size": 4,
            },
            {
                "Home ID": 1,
                "Appliance Type": "TV",
                "Energy Consumption (kWh)": 3.0,
                "Time": "19:00",
                "Date": "2023-02-05",
                "Outdoor Temperature (°C)": 8.0,
                "Season": "Winter",
                "Household Size": 3,
            },
            {
                "Home ID": 2,
                "Appliance Type": "Oven",
                "Energy Consumption (kWh)": 5.0,
                "Time": "18:00",
                "Date": "2023-01-12",
                "Outdoor Temperature (°C)": 6.0,
                "Season": "Winter",
                "Household Size": 5,
            },
        ]
    )
    df.to_csv(raw_file, index=False, encoding="cp1252")

    repo = CSVDataRepository(tmp_path / "processed")
    repo.ingest_raw_csv(raw_file)
    return repo


def test_monthly_and_yearly_summary_calculations(export_repo: CSVDataRepository) -> None:
    """[EXP-01] Monthly and Yearly reports compute exact total and per-resident kWh."""
    svc = ReportExportService(export_repo)

    monthly = svc.build_summary_report([1], period="Monthly")
    assert len(monthly) == 2
    jan_row = monthly[monthly["period"] == "2023-01"].iloc[0]
    assert jan_row["total_kwh"] == pytest.approx(6.0)
    assert jan_row["avg_household_size"] == pytest.approx(3.0)
    assert jan_row["per_resident_kwh"] == pytest.approx(2.0)

    yearly = svc.build_summary_report([1, 2], period="Yearly")
    assert len(yearly) == 2
    home1_year = yearly[yearly["home_id"] == 1].iloc[0]
    assert home1_year["total_kwh"] == pytest.approx(9.0)
    assert home1_year["per_resident_kwh"] == pytest.approx(3.0)


def test_export_csv_bytes_and_invalid_requests(export_repo: CSVDataRepository) -> None:
    """[EXP-01] UTF-8 CSV serialization succeeds and invalid inputs raise ValueError."""
    svc = ReportExportService(export_repo)
    summary = svc.build_summary_report([1, 2], period="Monthly")
    csv_text = svc.export_to_csv_bytes(summary).decode("utf-8")

    assert "home_id,period,total_kwh,avg_household_size,per_resident_kwh" in csv_text
    assert "2023-01" in csv_text

    with pytest.raises(ValueError, match="At least one household"):
        svc.build_summary_report([], period="Monthly")

    with pytest.raises(ValueError, match="Invalid period"):
        svc.build_summary_report([1], period="Weekly")

    with pytest.raises(ValueError, match="empty summary report"):
        svc.export_to_csv_bytes(pd.DataFrame())


def test_export_performance_500_homes_under_2s() -> None:
    """[NFR-01] Full 500-home monthly export completes within 2.0 seconds."""
    real_processed = Path(__file__).resolve().parents[1] / "data" / "processed"
    if not (real_processed / "measurements.csv").exists():
        pytest.skip("Full 100k dataset not present locally.")

    repo = CSVDataRepository(real_processed)
    svc = ReportExportService(repo)
    all_homes = repo.load_households()["home_id"].tolist()

    t0 = time.perf_counter()
    summary = svc.build_summary_report(all_homes, period="Monthly")
    elapsed = time.perf_counter() - t0

    assert len(summary) > 0
    assert elapsed <= 2.0, f"Export took {elapsed:.3f}s, exceeding 2.0s NFR-01 limit."

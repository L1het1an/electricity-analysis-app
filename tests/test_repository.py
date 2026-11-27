"""Unit tests for CSVDataRepository ETL and referential integrity (SVVP DATA-01, DATA-02)."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

from src.data.repository import CSVDataRepository


@pytest.fixture()
def sample_raw_csv(tmp_path: Path) -> Path:
    """Create a minimal cp1252 raw CSV with an intentional season contradiction."""
    raw_file = tmp_path / "raw_sample.csv"
    df = pd.DataFrame(
        [
            {
                "Home ID": 1,
                "Appliance Type": "Fridge",
                "Energy Consumption (kWh)": 0.30,
                "Time": "08:00",
                "Date": "2023-07-15",
                "Outdoor Temperature (°C)": 31.5,
                "Season": "Winter",  # Deliberate contradiction to verify raw fidelity
                "Household Size": 3,
            },
            {
                "Home ID": 2,
                "Appliance Type": "Air Conditioning",
                "Energy Consumption (kWh)": 3.50,
                "Time": "14:00",
                "Date": "2023-07-15",
                "Outdoor Temperature (°C)": -5.0,
                "Season": "Summer",
                "Household Size": 4,
            },
        ]
    )
    df.to_csv(raw_file, index=False, encoding="cp1252")
    return raw_file


def test_ingest_raw_csv_preserves_raw_records(sample_raw_csv: Path, tmp_path: Path) -> None:
    """[DATA-01] Valid cp1252 ingestion normalizes into 5 CSVs without altering raw values."""
    repo = CSVDataRepository(tmp_path / "processed")
    summary = repo.ingest_raw_csv(sample_raw_csv)

    assert summary == {"measurements": 2, "households": 2, "appliances": 2}
    assert repo.validate_referential_integrity() is True

    measurements = repo.load_measurements()
    assert measurements.loc[0, "season"] == "Winter"
    assert measurements.loc[1, "outdoor_temperature"] == -5.0


def test_ingest_rejects_missing_columns(tmp_path: Path) -> None:
    """[DATA-02] Malformed CSV missing required columns raises ValueError."""
    bad_csv = tmp_path / "bad.csv"
    pd.DataFrame({"Home ID": [1], "Time": ["09:00"]}).to_csv(bad_csv, index=False)

    repo = CSVDataRepository(tmp_path / "processed")
    with pytest.raises(ValueError, match="Missing required columns"):
        repo.ingest_raw_csv(bad_csv)


def test_validate_integrity_detects_orphan_fk(sample_raw_csv: Path, tmp_path: Path) -> None:
    """[DATA-02] Referential integrity check fails when an orphan home_id FK is injected."""
    processed_dir = tmp_path / "processed"
    repo = CSVDataRepository(processed_dir)
    repo.ingest_raw_csv(sample_raw_csv)

    measurements = repo.load_measurements()
    measurements.loc[0, "home_id"] = 9999
    measurements.to_csv(processed_dir / "measurements.csv", index=False)

    assert repo.validate_referential_integrity() is False

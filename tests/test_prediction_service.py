"""Unit tests for PredictionService dual baselines and isolated cleaning (SVVP AI-01..AI-03)."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.data.repository import CSVDataRepository
from src.services.prediction_service import PredictionService


@pytest.fixture()
def seeded_repo(tmp_path: Path) -> CSVDataRepository:
    """Create a synthetic cp1252 dataset with 120 rows across appliances and seasons."""
    rng = np.random.default_rng(42)
    appliances = ["Air Conditioning", "Fridge", "Heater", "TV"]
    base_kwh = {"Air Conditioning": 3.5, "Fridge": 0.3, "Heater": 3.4, "TV": 1.1}
    dates = ["2023-01-15", "2023-04-15", "2023-07-15", "2023-10-15"]

    rows = []
    for idx in range(160):
        home_id = (idx % 5) + 1
        app = appliances[idx % len(appliances)]
        date_str = dates[(idx // len(appliances)) % len(dates)]
        rows.append(
            {
                "Home ID": home_id,
                "Appliance Type": app,
                "Energy Consumption (kWh)": round(base_kwh[app] + float(rng.normal(0, 0.05)), 3),
                "Time": "12:00",
                "Date": date_str,
                "Outdoor Temperature (°C)": round(float(rng.uniform(-5.0, 35.0)), 1),
                "Season": "Winter",  # Intentionally mismatched for 75% of rows
                "Household Size": home_id,  # Distinct sizes 1..5 across homes
            }
        )

    raw_file = tmp_path / "synthetic_raw.csv"
    pd.DataFrame(rows).to_csv(raw_file, index=False, encoding="cp1252")

    repo = CSVDataRepository(tmp_path / "processed")
    repo.ingest_raw_csv(raw_file)
    return repo


def test_train_baselines_and_disk_immutability(seeded_repo: CSVDataRepository) -> None:
    """[AI-01] Dual baselines train cleanly while on-disk CSV stays 100% unaltered."""
    measurements_path = seeded_repo._processed_dir / "measurements.csv"
    bytes_before = measurements_path.read_bytes()

    svc = PredictionService(seeded_repo)
    summary = svc.train_baselines()

    assert summary["cleaning_stats"]["raw_rows"] == 160
    assert summary["cleaning_stats"]["season_fixed"] == 120
    assert "Statsmodels OLS" in summary["models"]
    assert "Scikit-learn HGB" in summary["models"]
    assert "r2" in summary["weather_only_ols"]
    assert measurements_path.read_bytes() == bytes_before


@pytest.mark.parametrize("model_name", ["Statsmodels OLS", "Scikit-learn HGB"])
def test_predict_valid_inputs(seeded_repo: CSVDataRepository, model_name: str) -> None:
    """[AI-02] Valid prediction inputs return plausible positive kWh for both models."""
    svc = PredictionService(seeded_repo)
    svc.train_baselines()

    ac_pred = svc.predict(25.0, 3, "Summer", "Air Conditioning", model_name)
    fridge_pred = svc.predict(25.0, 3, "Summer", "Fridge", model_name)

    assert ac_pred > fridge_pred
    assert 2.5 <= ac_pred <= 4.5
    assert 0.0 <= fridge_pred <= 1.0


@pytest.mark.parametrize(
    ("temp", "size", "season", "model_name"),
    [
        (150.0, 3, "Summer", "Statsmodels OLS"),
        (-50.0, 3, "Winter", "Statsmodels OLS"),
        (20.0, 0, "Spring", "Statsmodels OLS"),
        (20.0, 25, "Fall", "Statsmodels OLS"),
        (20.0, 3, "Monsoon", "Statsmodels OLS"),
        (20.0, 3, "Summer", "Unknown Model"),
    ],
)
def test_predict_invalid_inputs_raise_value_error(
    seeded_repo: CSVDataRepository,
    temp: float,
    size: int,
    season: str,
    model_name: str,
) -> None:
    """[AI-03] Out-of-range temperature, household size, season, or model raise ValueError."""
    svc = PredictionService(seeded_repo)
    svc.train_baselines()

    with pytest.raises(ValueError):
        svc.predict(temp, size, season, "Fridge", model_name)

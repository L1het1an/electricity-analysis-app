from __future__ import annotations

import numpy as np
import pandas as pd

from src.data.repository import CSVDataRepository

VALID_PERIODS: set[str] = {"Monthly", "Yearly"}
REPORT_COLUMNS: list[str] = [
    "home_id",
    "period",
    "total_kwh",
    "avg_household_size",
    "per_resident_kwh",
]

class ReportExportService:
    """Generates monthly and yearly total & per-resident electricity summary reports."""

    def __init__(self, repo: CSVDataRepository) -> None:
        """Initialize service with a shared CSVDataRepository instance."""
        self._repo: CSVDataRepository = repo

    @staticmethod
    def _validate_request(home_ids: list[int], period: str) -> None:
        """Raise ValueError if home_ids or period are invalid."""
        if not home_ids:
            raise ValueError("At least one household must be selected.")
        if period not in VALID_PERIODS:
            raise ValueError(f"Invalid period '{period}'. Must be one of {sorted(VALID_PERIODS)}.")

    def build_summary_report(self, home_ids: list[int], period: str = "Monthly") -> pd.DataFrame:
        """Aggregate total and per-resident consumption by Monthly or Yearly period."""
        self._validate_request(home_ids, period)

        df = self._repo.load_measurements()
        filtered = df[df["home_id"].isin(home_ids)].copy()
        if filtered.empty:
            return pd.DataFrame(columns = REPORT_COLUMNS)

        slice_len = 7 if period == "Monthly" else 4
        filtered["period"] = filtered["date"].astype("str").str.slice(0, slice_len)

        summary = (
            filtered.groupby(["home_id", "period"], as_index=False)
            .agg(
                total_kwh=("energy_consumption", "sum"),
                avg_household_size=("household_size", "mean"),
            )
        )
        summary["per_resident_kwh"] = np.where(
            summary["avg_household_size"] > 0,
            summary["total_kwh"] / summary["avg_household_size"],
            0.0,
        )
        summary["total_kwh"] = summary["total_kwh"].round(3)
        summary["avg_household_size"] = summary["avg_household_size"].round(2)
        summary["per_resident_kwh"] = summary["per_resident_kwh"].round(3)
        return summary.sort_values(["home_id", "period"]).reset_index(drop=True)

    @staticmethod
    def export_to_csv_bytes(summary_df: pd.DataFrame) -> bytes:
        """Serialize summary DataFrame to UTF-8 CSV bytes for download."""
        if summary_df.empty:
            raise ValueError("Cannot export an empty summary report.")
        return summary_df.to_csv(index=False).encode("utf-8")
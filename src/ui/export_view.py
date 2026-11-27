"""Streamlit UI view for Monthly/Yearly summary report export (UC-08 Bonus)."""

from __future__ import annotations

from pathlib import Path
import sys
import time

import pandas as pd
import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.models import User
from src.services.export_service import ReportExportService


def _select_households(authorized_homes: list[int]) -> list[int]:
    """Render household selection controls scoped to authorized homes."""
    select_all = st.checkbox(
        f"Select all authorized households ({len(authorized_homes)})",
        value=False,
    )
    if select_all:
        return list(authorized_homes)

    default_selection = authorized_homes[: min(3, len(authorized_homes))]
    return st.multiselect(
        "Choose Households to Include",
        options=authorized_homes,
        default=default_selection,
    )


def _render_report_kpis(summary_df: pd.DataFrame, elapsed_s: float) -> None:
    """Display high-level KPI metrics for the generated summary report."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Report Rows", f"{len(summary_df):,}")
    col2.metric("Households Included", f"{summary_df['home_id'].nunique()}")
    col3.metric("Total Consumption", f"{summary_df['total_kwh'].sum():,.2f} kWh")
    col4.metric("Generation Time", f"{elapsed_s * 1000:.0f} ms")


def render_export_view(
    export_service: ReportExportService,
    user: User,
    authorized_homes: list[int],
) -> None:
    """Render the summary report configuration, table preview, and CSV download."""
    st.header("Export Summary Report (Monthly / Yearly)")
    st.caption(
        "Computed directly from unaltered raw consumption records (total kWh & per-resident kWh)."
    )

    if not authorized_homes:
        st.warning("No authorized households available for your account.")
        return

    selected_homes = _select_households(authorized_homes)
    period = st.radio("Aggregation Period", ["Monthly", "Yearly"], horizontal=True)

    if not selected_homes:
        st.warning("Please select at least one household to generate a summary report.")
        return

    try:
        t0 = time.perf_counter()
        summary_df = export_service.build_summary_report(selected_homes, period=period)
        elapsed_s = time.perf_counter() - t0
    except ValueError as exc:
        st.error(f"Could not generate report: {exc}")
        return

    if summary_df.empty:
        st.info("No consumption records found for the selected households.")
        return

    _render_report_kpis(summary_df, elapsed_s)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    csv_bytes = export_service.export_to_csv_bytes(summary_df)
    filename = f"consumption_summary_{period.lower()}.csv"
    st.download_button(
        label=f"Download {period} Summary Report (CSV)",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        type="primary",
    )


if __name__ == "__main__":
    from src.data.repository import CSVDataRepository

    st.set_page_config(page_title="Export Report Standalone Preview", layout="wide")
    repo = CSVDataRepository(_PROJECT_ROOT / "data" / "processed")
    svc = ReportExportService(repo)
    demo_admin = User(1, "admin", "", "Admin", [])
    all_homes = repo.load_households()["home_id"].tolist()
    render_export_view(svc, demo_admin, all_homes)

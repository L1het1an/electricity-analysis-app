"""Interface tests for the administrator data screen (SVVP DATA-01, DATA-02).

These tests drive the router and click the real admin widgets, so the UI path of
the ingestion requirement is covered end to end: the button exists, it calls the
repository, and a bad path is rejected without destroying the loaded tables.

The module is skipped when ``data/processed`` has not been built yet, following
the convention used by the other UI tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit", reason="streamlit is required for the UI tests")

from streamlit.testing.v1 import AppTest  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = PROJECT_ROOT / "data" / "processed"

pytestmark = pytest.mark.skipif(
    not (PROCESSED / "measurements.csv").exists(),
    reason="processed tables not available (run the ingestion first)",
)

ADMIN_SCREEN = "Data management"


def _admin_screen() -> AppTest:
    """Sign in as the administrator and open the data-management screen."""
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=120)
    app.run()
    app.text_input[0].set_value("admin")
    app.text_input[1].set_value("admin123")
    app.button[0].click().run()
    app.sidebar.radio[0].set_value(ADMIN_SCREEN).run()
    return app


def _measurement_count(app: AppTest) -> str:
    """Return the Measurements KPI value rendered on the admin screen."""
    values = {metric.label: metric.value for metric in app.metric}
    return values["Measurements"]


def test_data_01_ingestion_button_rebuilds_the_tables() -> None:
    """DATA-01: clicking 'Load dataset' re-runs the ETL from the raw export."""
    app = _admin_screen()
    assert not list(app.exception)

    button = next(item for item in app.button if item.label == "Load dataset")
    button.click().run()

    assert not list(app.exception)
    assert any("Ingestion completed" in message.value for message in app.success)
    assert _measurement_count(app) == "100,000"


def test_data_02_bad_path_is_rejected_and_tables_survive() -> None:
    """DATA-02: a missing export is reported and the loaded tables stay intact."""
    app = _admin_screen()
    assert _measurement_count(app) == "100,000"

    app.text_input[0].set_value(str(PROJECT_ROOT / "data" / "raw" / "does-not-exist.csv"))
    button = next(item for item in app.button if item.label == "Load dataset")
    button.click().run()

    assert not list(app.exception)
    assert any("Raw CSV not found" in message.value for message in app.error)
    assert _measurement_count(app) == "100,000"

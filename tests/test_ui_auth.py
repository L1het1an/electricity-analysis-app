"""Interface tests driving the real router headlessly (SVVP AUTH-01..04).

``streamlit.testing.v1.AppTest`` executes ``app.py`` in a simulated runtime, so
these tests cover behaviour that unit tests cannot reach: which navigation entries
the sidebar exposes for each role, the error shown on a bad password, and the
session cleanup performed by the logout button.

The module is skipped when ``data/processed`` has not been built yet, following
the convention used by the analytics and prediction suites.
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

ADMIN_ONLY_SCREEN = "Data management"


def _launch() -> AppTest:
    """Start the application and wait for the first render."""
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=90)
    app.run()
    return app


def _sign_in(users_name: str, password: str) -> AppTest:
    """Fill the login form and submit it."""
    app = _launch()
    app.text_input[0].set_value(users_name)
    app.text_input[1].set_value(password)
    app.button[0].click().run()
    return app


def test_login_screen_is_displayed_first() -> None:
    """AUTH-01: an anonymous visitor sees the credential form and no navigation."""
    app = _launch()
    assert not list(app.exception)
    assert [widget.label for widget in app.text_input] == ["Username", "Password"]
    assert "user" not in app.session_state
    assert not app.sidebar.radio


def test_admin_login_opens_the_data_management_screen() -> None:
    """AUTH-01: the administrator gets the Data management entry and all homes."""
    app = _sign_in("admin", "admin123")
    assert not list(app.exception)

    user = app.session_state["user"]
    assert user.role == "Admin"
    assert user.is_admin() is True
    assert ADMIN_ONLY_SCREEN in app.sidebar.radio[0].options


def test_standard_user_login_hides_the_admin_screen() -> None:
    """AUTH-02: user1 has no Data management entry and only one household."""
    app = _sign_in("user1", "user123")
    assert not list(app.exception)

    user = app.session_state["user"]
    assert user.role == "User"
    assert user.home_ids == [1]
    assert ADMIN_ONLY_SCREEN not in app.sidebar.radio[0].options


def test_wrong_password_keeps_the_login_form() -> None:
    """AUTH-03: a bad password neither signs in nor hints at the cause."""
    app = _sign_in("admin", "WrongPass!")
    assert not list(app.exception)
    assert "user" not in app.session_state
    assert len(app.error) == 1
    assert app.error[0].value == "Invalid username or password."


def test_logout_clears_the_session() -> None:
    """AUTH-04: the logout button removes the user and restores the form."""
    app = _sign_in("user1", "user123")
    assert "user" in app.session_state

    logout = next(button for button in app.button if button.label == "Log out")
    logout.click().run()

    assert not list(app.exception)
    assert "user" not in app.session_state
    assert [widget.label for widget in app.text_input] == ["Username", "Password"]


def test_admin_screen_renders_counts_and_integrity() -> None:
    """DATA-01 / DATA-02: the admin screen shows the five tables and a green check."""
    app = _sign_in("admin", "admin123")
    app.sidebar.radio[0].set_value(ADMIN_ONLY_SCREEN).run()
    assert not list(app.exception)

    values = {metric.label: metric.value for metric in app.metric}
    assert values["Measurements"] == "100,000"
    assert values["Households"] == "500"
    assert values["Appliances"] == "10"

    integrity = next(b for b in app.button if b.label == "Run integrity check")
    integrity.click().run()
    assert not list(app.exception)
    assert any("Integrity OK" in message.value for message in app.success)

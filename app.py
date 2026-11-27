"""Main entry point for the Household Electricity Consumption Analysis app.

The router owns the sidebar and the tab layout. Member A and Member C expose a
single render function each; this module is the only place that decides which
one runs for the signed-in user, so their branches stay independent.
"""

from __future__ import annotations

import streamlit as st

from src.data.repository import CSVDataRepository
from src.models import User
from src.services.analytics_service import AnalyticsService
from src.services.export_service import ReportExportService
from src.services.prediction_service import PredictionService
from src.ui.dashboard_view import render_dashboard_view
from src.ui.export_view import render_export_view
from src.ui.prediction_view import render_prediction_view

PROCESSED_DIR = "data/processed"

DASHBOARD_SCREEN = "Dashboard"
PREDICTION_SCREEN = "AI Prediction"
EXPORT_SCREEN = "Export Report"
ADMIN_SCREEN = "Data management"


def main() -> None:
    """Render the application shell for the current session."""
    st.set_page_config(
        page_title="Household Electricity Consumption Analysis",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    repository = get_repository()
    if not repository.is_initialized():
        _render_setup_notice()
        return

    user = get_current_user(repository)
    if user is None:
        _render_login(repository)
        return

    analytics = AnalyticsService(repository)
    prediction = PredictionService(repository)
    export = ReportExportService(repository)
    screen = _render_sidebar(user, analytics)

    visible_homes = analytics.authorize(user)
    if screen == ADMIN_SCREEN:
        _render_admin(repository, user)
    elif screen == PREDICTION_SCREEN:
        render_prediction_view(prediction, user, visible_homes)
    elif screen == EXPORT_SCREEN:
        render_export_view(export, user, visible_homes)
    else:
        render_dashboard_view(analytics, user, visible_homes)


# ---------------------------------------------------------------------- #
# Session helpers
# ---------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Loading the CSV tables...")
def get_repository() -> CSVDataRepository:
    """Load the CSV repository once per server process."""
    return CSVDataRepository(PROCESSED_DIR)


def get_current_user(repository: CSVDataRepository) -> User | None:
    """Return the user stored in the session, if any."""
    user = st.session_state.get("user")
    if isinstance(user, User):
        return user
    return None


# ---------------------------------------------------------------------- #
# Screens owned by other members
# ---------------------------------------------------------------------- #
def _render_login(repository: CSVDataRepository) -> None:
    """Render the login screen.

    Member A owns ``src.ui.login_view``. While that module is absent the router
    falls back to a built-in form so the dashboard stays reachable.
    """
    st.title("⚡ Household Electricity Consumption Analysis")
    st.caption("Sign in to analyse the consumption of your households.")
    try:
        from src.ui.login_view import render_login_view

        from src.services.auth_service import AuthService
    except ImportError:
        _render_fallback_login(repository)
        return

    render_login_view(AuthService(repository))


def _render_fallback_login(repository: CSVDataRepository) -> None:
    """Minimal sign-in form that keeps the dashboard demonstrable.

    It is used whenever ``src/ui/login_view.py`` and ``src/services/auth_service.py``
    are not importable. Once member A delivers them this branch is never taken.
    """
    st.caption(
        "Residents see only their own households; administrators also reach the "
        "data management screen."
    )
    users = repository.load_users()
    links = repository.load_user_households()
    with st.form("fallback_login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if not submitted:
        st.caption("Demo accounts: `admin / admin123`, `user1 / user123`, `user_multi / user123`")
        return

    matches = users[users["users_name"] == username.strip()]
    if matches.empty:
        st.error("Invalid username or password.")
        return
    record = matches.iloc[0]
    user = User(
        users_id=int(record["users_id"]),
        users_name=str(record["users_name"]),
        password_hash=str(record["password_hash"]),
        role=str(record["role"]),
        home_ids=links.loc[links["users_id"] == record["users_id"], "home_id"]
        .astype(int)
        .tolist(),
    )
    if not user.verify_password(password):
        st.error("Invalid username or password.")
        return
    st.session_state["user"] = user
    st.rerun()


def _render_admin(repository: CSVDataRepository, user: User) -> None:
    """Render the administrator screen owned by member A."""
    try:
        from src.ui.admin_view import render_admin_view
    except ImportError:
        st.info(
            "Data ingestion is performed by the batch loader that populates "
            "`data/processed/`. No interactive screen is mounted in this build."
        )
        return

    render_admin_view(repository, user)


# ---------------------------------------------------------------------- #
# Layout
# ---------------------------------------------------------------------- #
def _render_sidebar(user: User, analytics: AnalyticsService) -> str:
    """Draw the identity block and the navigation, and return the chosen screen."""
    labels = [DASHBOARD_SCREEN, PREDICTION_SCREEN, EXPORT_SCREEN]
    if user.is_admin():
        labels.append(ADMIN_SCREEN)
    with st.sidebar:
        st.markdown("### ⚡ Household Energy")
        st.caption(f"Signed in as {user.users_name}")
        st.caption(f"Role: `{user.role}`")
        if st.button("Log out", use_container_width=True):
            st.session_state.pop("user", None)
            st.rerun()
        screen = st.radio("Navigation", labels, label_visibility="collapsed")
        st.divider()
        visible = analytics.authorize(user)
        st.caption(f"{len(visible)} household(s) visible")
    return screen


def _render_setup_notice() -> None:
    """Render the onboarding message shown before the ETL has been executed."""
    st.title("⚡ Household Electricity Consumption Analysis")
    st.warning(
        "No processed CSV table was found. Run the ingestion step once:\n\n"
        "```python\n"
        "from pathlib import Path\n"
        "from src.data.repository import CSVDataRepository\n\n"
        "repo = CSVDataRepository(Path('data/processed'))\n"
        "repo.ingest_raw_csv(Path('data/raw/household_electricity_consumption.csv'))\n"
        "```"
    )


if __name__ == "__main__":
    main()

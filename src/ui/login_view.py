"""Sign-in screen and session handling (SVVP AUTH-01..04).

The router (``app.py``) owns the page title, the sidebar and the logout control;
this module only renders the credential form and stores the authenticated user in
the session under the key the router reads: ``st.session_state["user"]``.

The session helpers are written against a plain mutable mapping so they can be
exercised by unit tests without starting a Streamlit runtime.
"""

from __future__ import annotations

from typing import MutableMapping, Optional

import streamlit as st

from src.models import User
from src.services.auth_service import AuthService

SESSION_KEY = "user"


# --------------------------------------------------------------------------- #
# Session helpers (Streamlit-free, therefore testable)
# --------------------------------------------------------------------------- #
def get_current_user(state: MutableMapping[str, object]) -> Optional[User]:
    """Return the signed-in user stored in ``state``, if any."""
    user = state.get(SESSION_KEY)
    return user if isinstance(user, User) else None


def set_current_user(state: MutableMapping[str, object], user: User) -> None:
    """Store the signed-in user in ``state``."""
    state[SESSION_KEY] = user


def clear_current_user(state: MutableMapping[str, object]) -> None:
    """Remove the signed-in user from ``state`` (logout, AUTH-04)."""
    state.pop(SESSION_KEY, None)


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render_login_view(auth_service: AuthService) -> Optional[User]:
    """Render the credential form and return the signed-in user, if any.

    Args:
        auth_service: Service used to verify the credentials.

    Returns:
        The already signed-in :class:`User`, or ``None`` while the form is shown.
        On a successful submission the session is updated and the page reruns, so
        the router picks the user up from ``st.session_state``.
    """
    current_user = get_current_user(st.session_state)
    if current_user is not None:
        return current_user

    user = _render_credentials_form(auth_service)
    if user is not None:
        set_current_user(st.session_state, user)
        st.rerun()
    return None


def _render_credentials_form(auth_service: AuthService) -> Optional[User]:
    """Render the form and return the user when the credentials are valid."""
    with st.form("login_form", clear_on_submit=False):
        users_name = st.text_input(
            "Username", key="login_username", placeholder="e.g. admin"
        )
        password = st.text_input(
            "Password", key="login_password", type="password", placeholder="Your password"
        )
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

    if not submitted:
        _render_demo_hint()
        return None

    user = auth_service.login(users_name, password)
    if user is None:
        st.error(auth_service.last_error or "Invalid username or password.")
        return None
    return user


def _render_demo_hint() -> None:
    """List the seeded demonstration accounts (training prototype only)."""
    with st.expander("Demonstration accounts", expanded=False):
        st.markdown(
            "- `admin` / `admin123` — administrator, all 500 households\n"
            "- `user1` / `user123` — standard user, 1 household\n"
            "- `user_multi` / `user123` — standard user, 3 households"
        )

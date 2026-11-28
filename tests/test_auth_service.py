"""Unit tests for authentication and role-based access control.

Test names map one-to-one to the SVVP cases (``AUTH-01`` … ``AUTH-04``,
``RBAC-01``) so the traceability matrix can point straight at an automated test.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from src.data.repository import CSVDataRepository
from src.models import User
from src.services.auth_service import (
    EMPTY_FIELDS_MESSAGE,
    INVALID_CREDENTIALS_MESSAGE,
    AuthService,
)
from src.ui.login_view import SESSION_KEY, clear_current_user, get_current_user, set_current_user

RAW_HEADER = [
    "Home ID",
    "Appliance Type",
    "Energy Consumption (kWh)",
    "Time",
    "Date",
    "Outdoor Temperature (°C)",
    "Season",
    "Household Size",
]


@pytest.fixture()
def repository(tmp_path: Path) -> CSVDataRepository:
    """Repository populated from a four-household cp1252 export.

    Four homes are required because the seeded ``user_multi`` account is linked to
    the first three of them.
    """
    raw_file = tmp_path / "raw.csv"
    pd.DataFrame(
        [
            [1, "Fridge", 0.30, "08:00", "2023-07-15", 31.5, "Summer", 3],
            [2, "Air Conditioning", 3.50, "14:00", "2023-07-16", 35.0, "Summer", 4],
            [3, "Heater", 3.80, "20:00", "2023-01-10", -3.0, "Winter", 2],
            [4, "Lights", 0.50, "19:00", "2023-10-02", 18.0, "Fall", 5],
        ],
        columns=RAW_HEADER,
    ).to_csv(raw_file, index=False, encoding="cp1252")

    repo = CSVDataRepository(tmp_path / "processed")
    repo.ingest_raw_csv(raw_file)
    return repo


@pytest.fixture()
def auth(repository: CSVDataRepository) -> AuthService:
    return AuthService(repository)


# --------------------------------------------------------------------------- #
# AUTH-01 … AUTH-04
# --------------------------------------------------------------------------- #
def test_auth_01_valid_admin_login(auth: AuthService) -> None:
    """AUTH-01: valid admin credentials give the Admin role and every household."""
    user = auth.login("admin", "admin123")

    assert user is not None
    assert user.role == "Admin"
    assert user.is_admin() is True
    assert auth.last_error is None
    assert auth.get_authorized_home_ids(user) == [1, 2, 3, 4]


def test_auth_02_valid_user_login_is_scoped_to_linked_homes(auth: AuthService) -> None:
    """AUTH-02: user_multi is a User limited to the homes 1, 2 and 3."""
    user = auth.login("user_multi", "user123")

    assert user is not None
    assert user.role == "User"
    assert user.is_admin() is False
    assert user.home_ids == [1, 2, 3]
    assert auth.get_authorized_home_ids(user) == [1, 2, 3]
    assert auth.can_access_home(user, 4) is False


def test_auth_02b_single_home_user_scope(auth: AuthService) -> None:
    """AUTH-02 (boundary): user1 is limited to the single linked household."""
    user = auth.login("user1", "user123")

    assert user is not None
    assert user.home_ids == [1]
    assert auth.get_authorized_home_ids(user) == [1]


def test_auth_03_wrong_password_is_rejected(auth: AuthService) -> None:
    """AUTH-03: a valid name with a wrong password is refused."""
    assert auth.login("admin", "WrongPass!") is None
    assert auth.last_error == INVALID_CREDENTIALS_MESSAGE


def test_auth_03b_unknown_user_is_indistinguishable(auth: AuthService) -> None:
    """AUTH-03: an unknown account returns exactly the same message."""
    assert auth.login("ghost", "admin123") is None
    assert auth.last_error == INVALID_CREDENTIALS_MESSAGE


def test_auth_04_empty_credentials_are_reported(auth: AuthService) -> None:
    """AUTH-04: blank input never reaches the user table."""
    assert auth.login("   ", "") is None
    assert auth.last_error == EMPTY_FIELDS_MESSAGE

    assert auth.login("", "user123") is None
    assert auth.last_error == EMPTY_FIELDS_MESSAGE


def test_auth_04b_sign_out_clears_the_session(auth: AuthService) -> None:
    """AUTH-04: signing out removes the user from the session state."""
    user = auth.login("user1", "user123")
    assert user is not None

    state: dict = {}
    set_current_user(state, user)
    assert get_current_user(state) is user
    assert SESSION_KEY in state

    clear_current_user(state)
    assert SESSION_KEY not in state
    assert get_current_user(state) is None


def test_login_is_case_and_space_insensitive(auth: AuthService) -> None:
    """Robustness: '  Admin ' authenticates as 'admin'."""
    user = auth.login("  Admin  ", "admin123")
    assert user is not None and user.is_admin() is True


# --------------------------------------------------------------------------- #
# RBAC-01
# --------------------------------------------------------------------------- #
def test_rbac_01_unauthorized_home_is_refused(auth: AuthService) -> None:
    """RBAC-01: user_multi requesting home 99 gets a PermissionError."""
    user = auth.login("user_multi", "user123")
    assert user is not None

    assert auth.can_access_home(user, 99) is False
    with pytest.raises(PermissionError):
        auth.ensure_home_access(user, 99)


def test_rbac_01b_batch_request_is_refused_as_a_whole(auth: AuthService) -> None:
    """RBAC-01: a mixed request is rejected, not silently trimmed."""
    user = auth.login("user_multi", "user123")
    assert user is not None

    with pytest.raises(PermissionError):
        auth.filter_authorized_homes(user, [1, 99])
    assert auth.filter_authorized_homes(user, [1, 2]) == [1, 2]


def test_rbac_01c_anonymous_user_reaches_nothing(auth: AuthService) -> None:
    """RBAC-01 (deny by default): no user means no data."""
    assert auth.get_authorized_home_ids(None) == []
    assert auth.can_access_home(None, 1) is False


def test_rbac_01d_admin_reaches_every_household(auth: AuthService) -> None:
    """RBAC-01 (admin side): the administrator is allowed on every home."""
    admin = auth.login("admin", "admin123")
    assert admin is not None
    for home_id in (1, 2, 3, 4, 99):
        if home_id == 99:
            assert auth.can_access_home(admin, home_id) is False
        else:
            assert auth.can_access_home(admin, home_id) is True


def test_require_admin_guard(auth: AuthService) -> None:
    """The admin screen guard rejects standard users and anonymous visitors."""
    user = auth.login("user1", "user123")
    with pytest.raises(PermissionError):
        AuthService.require_admin(user)
    with pytest.raises(PermissionError):
        AuthService.require_admin(None)

    admin = auth.login("admin", "admin123")
    AuthService.require_admin(admin)  # must not raise


def test_malformed_home_id_is_refused(auth: AuthService) -> None:
    """A non-numeric household identifier is refused instead of crashing."""
    admin = auth.login("admin", "admin123")
    assert auth.can_access_home(admin, "not-a-number") is False


# --------------------------------------------------------------------------- #
# Password primitives
# --------------------------------------------------------------------------- #
def test_password_hash_matches_the_stored_digest() -> None:
    """The repository seeds SHA-256 hex digests that User.verify_password accepts."""
    digest = hashlib.sha256(b"s3cret").hexdigest()
    user = User(users_id=1, users_name="a", password_hash=digest, role="User")

    assert user.verify_password("s3cret") is True
    assert user.verify_password("s3cret ") is False
    assert len(digest) == 64

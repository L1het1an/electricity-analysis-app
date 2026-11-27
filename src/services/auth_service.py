"""Authentication and role-based access control (SVVP AUTH-01..04, RBAC-01).

The service is deliberately UI-agnostic: it never imports Streamlit and never
touches ``st.session_state``. The login view owns the session, this class owns the
rules, which keeps the module unit-testable without a runtime.

Roles (UC-01, FR-01, NFR-03)
-----------------------------
Admin
    May read every household stored in ``households.csv``.
User
    May only read the households linked to the account in
    ``user_households.csv``.

The rule is deny-by-default: an unknown account, a wrong password, an unknown
role or an unlinked household identifier is always refused. The same generic
message is returned for "unknown user" and "wrong password" so the form cannot be
used to enumerate valid account names.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from src.data.repository import CSVDataRepository
from src.models import User

INVALID_CREDENTIALS_MESSAGE = "Invalid username or password."
EMPTY_FIELDS_MESSAGE = "Username and password are required."
ACCESS_DENIED_MESSAGE = "Access denied: this screen is restricted to administrators."
PERMISSION_DENIED_TEMPLATE = (
    "Access denied: household {home_id} is not linked to your account."
)

ROLE_ADMIN = "Admin"
ROLE_USER = "User"


class AuthService:
    """Verify credentials and answer "may this user read this household?"."""

    def __init__(self, repository: CSVDataRepository) -> None:
        """Bind the service to the CSV repository.

        Args:
            repository: Source of the ``users`` and ``user_households`` tables.
        """
        self._repository = repository
        self.last_error: Optional[str] = None

    @property
    def repository(self) -> CSVDataRepository:
        """The repository this service reads from."""
        return self._repository

    # ------------------------------------------------------------------ #
    # Authentication
    # ------------------------------------------------------------------ #
    def login(self, users_name: str, password: str) -> Optional[User]:
        """Authenticate a pair of credentials (UC-01).

        Args:
            users_name: Login name typed in the form.
            password: Clear-text password typed in the form.

        Returns:
            The matching :class:`User` with its ``home_ids`` populated, or
            ``None``. :attr:`last_error` then holds a user-facing message that
            never reveals whether the account exists.
        """
        self.last_error = None
        name = str(users_name or "").strip()
        if not name or not password:
            self.last_error = EMPTY_FIELDS_MESSAGE
            return None

        user = self._build_user(name)
        if user is None:
            self.last_error = INVALID_CREDENTIALS_MESSAGE
            return None
        if not user.verify_password(password):
            self.last_error = INVALID_CREDENTIALS_MESSAGE
            return None
        return user

    def logout(self) -> None:
        """Reset the transient state of the service.

        The browser session itself is cleared by the view layer, which pops
        ``st.session_state["user"]``.
        """
        self.last_error = None

    def _build_user(self, users_name: str) -> Optional[User]:
        """Return the account matching ``users_name`` with its household links."""
        users = self._repository.load_users()
        normalised = users_name.strip().lower()
        matches = users[
            users["users_name"].astype(str).str.strip().str.lower() == normalised
        ]
        if matches.empty:
            return None

        record = matches.iloc[0]
        users_id = int(record["users_id"])
        return User(
            users_id=users_id,
            users_name=str(record["users_name"]),
            password_hash=str(record["password_hash"]),
            role=str(record["role"]),
            home_ids=self._home_ids_for(users_id),
        )

    def _home_ids_for(self, users_id: int) -> List[int]:
        """Return the household identifiers explicitly linked to an account."""
        links = self._repository.load_user_households()
        selected = links[links["users_id"].astype(int) == int(users_id)]
        return sorted(int(home) for home in selected["home_id"])

    # ------------------------------------------------------------------ #
    # Authorisation
    # ------------------------------------------------------------------ #
    @staticmethod
    def is_admin(user: Optional[User]) -> bool:
        """Whether ``user`` holds the administrator role (deny by default)."""
        return user is not None and user.is_admin()

    def get_authorized_home_ids(self, user: Optional[User]) -> List[int]:
        """Return every household the user is allowed to read.

        Admins receive all 500 identifiers from ``households.csv``; standard
        users receive their linked identifiers; anonymous or unknown roles
        receive an empty list.
        """
        if user is None:
            return []
        if user.is_admin():
            households = self._repository.load_households()
            return sorted(int(home) for home in households["home_id"])
        if user.role == ROLE_USER:
            return sorted(int(home) for home in user.home_ids)
        return []

    def can_access_home(self, user: Optional[User], home_id: int) -> bool:
        """Whether ``user`` may read the given household.

        The check is performed against the live repository, never against a
        client-supplied list, so a manipulated request cannot widen the scope.
        """
        if user is None:
            return False
        try:
            candidate = int(home_id)
        except (TypeError, ValueError):
            return False
        return candidate in set(self.get_authorized_home_ids(user))

    def ensure_home_access(self, user: Optional[User], home_id: int) -> None:
        """Raise :class:`PermissionError` unless ``user`` may read ``home_id``.

        Raises:
            PermissionError: When the household is outside the user's scope.
        """
        if not self.can_access_home(user, home_id):
            raise PermissionError(PERMISSION_DENIED_TEMPLATE.format(home_id=home_id))

    def filter_authorized_homes(
        self, user: Optional[User], requested_home_ids: Iterable[int]
    ) -> List[int]:
        """Validate a batch of requested households in one call (RBAC-01).

        Args:
            user: Signed-in account.
            requested_home_ids: Households requested by the UI.

        Returns:
            The requested identifiers, de-duplicated and order-preserved.

        Raises:
            PermissionError: If any requested household is out of scope. The
                message names the first offending identifier.
        """
        authorized = set(self.get_authorized_home_ids(user))
        result: List[int] = []
        for raw_home_id in requested_home_ids:
            home_id = int(raw_home_id)
            if home_id not in authorized:
                raise PermissionError(PERMISSION_DENIED_TEMPLATE.format(home_id=home_id))
            if home_id not in result:
                result.append(home_id)
        return result

    @staticmethod
    def require_admin(user: Optional[User]) -> None:
        """Raise :class:`PermissionError` unless ``user`` is an administrator.

        Raises:
            PermissionError: When the account is missing or is not an admin.
        """
        if not AuthService.is_admin(user):
            raise PermissionError(ACCESS_DENIED_MESSAGE)

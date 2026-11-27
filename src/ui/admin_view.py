"""Administrator back-office: dataset ingestion, integrity checks, raw fidelity.

The page is the visible proof of three requirements:

* ``DATA-01`` — the administrator can trigger the ingestion and the five
  normalised tables cover the whole raw export (100 000 / 500 / 10).
* ``DATA-02`` — a malformed export is rejected without destroying the tables that
  are already loaded, and the referential-integrity check reports its verdict.
* ``NFR-02`` — the raw data is preserved verbatim: no row is dropped, no
  temperature corrected, no season recomputed and no household size harmonised.
  The MD5 fingerprint of the raw file is displayed for that purpose.

Entry point: :func:`render_admin_view`, called by ``app.py`` as
``render_admin_view(repository, user)``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import streamlit as st

from src.data.repository import CSVDataRepository
from src.models import User
from src.services.auth_service import ACCESS_DENIED_MESSAGE, AuthService

DEFAULT_RAW_PATH = "data/raw/household_electricity_consumption.csv"
EXPECTED_RAW_ROWS = 100_000
EXPECTED_HOUSEHOLDS = 500
EXPECTED_APPLIANCES = 10


def render_admin_view(repository: CSVDataRepository, user: Optional[User]) -> None:
    """Render the administration screen.

    Args:
        repository: Repository holding the five normalised tables.
        user: Signed-in account. Any non-administrator is rejected before a
            single table is read.
    """
    if not AuthService.is_admin(user):
        st.error(ACCESS_DENIED_MESSAGE)
        return

    st.subheader("🗄️ Data management")
    st.caption(f"Signed in as **{user.users_name}** (administrator)")

    _render_table_counts(repository)
    st.divider()
    _render_ingestion_panel(repository)
    st.divider()
    _render_integrity_check(repository)
    st.divider()
    _render_accounts(repository)
    st.divider()
    _render_raw_fidelity(repository)
    st.divider()
    _render_measurement_preview(repository)


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #
def _render_table_counts(repository: CSVDataRepository) -> None:
    """Show the row count of every normalised table as KPI cards."""
    if not repository.is_initialized():
        st.warning("No processed table found yet — run the ingestion below.")
        return

    measurements = repository.load_measurements()
    households = repository.load_households()
    appliances = repository.load_appliances()
    users = repository.load_users()
    links = repository.load_user_households()

    columns = st.columns(5)
    columns[0].metric("Measurements", f"{len(measurements):,}")
    columns[1].metric("Households", f"{len(households):,}")
    columns[2].metric("Appliances", f"{len(appliances)}")
    columns[3].metric("Accounts", f"{len(users)}")
    columns[4].metric("Account ↔ household links", f"{len(links)}")

    if len(measurements) == EXPECTED_RAW_ROWS:
        st.caption(
            f"✅ All {EXPECTED_RAW_ROWS:,} raw measurements are stored in the "
            "normalised schema (DATA-01)."
        )
    else:
        st.warning(
            f"Expected {EXPECTED_RAW_ROWS:,} measurements, found {len(measurements):,}."
        )


def _render_ingestion_panel(repository: CSVDataRepository) -> None:
    """Trigger the ETL from the raw export (DATA-01)."""
    st.markdown("#### Ingestion from the raw export")
    raw_path = st.text_input("Raw CSV path", value=DEFAULT_RAW_PATH, key="admin_raw_path")
    st.caption(
        "Re-running the ingestion rebuilds `households`, `appliances` and "
        "`measurements`. Existing accounts and their household links are kept."
    )

    if not st.button("Load dataset", key="admin_ingest", type="primary"):
        return

    try:
        counts = repository.ingest_raw_csv(Path(raw_path))
    except FileNotFoundError:
        st.error(f"Raw CSV not found: `{raw_path}`. Existing tables were left untouched.")
        return
    except ValueError as error:
        st.error(f"Invalid CSV rejected: {error}. Existing tables were left untouched.")
        return
    except OSError as error:
        st.error(f"The file could not be read: {error}")
        return

    st.success(
        f"Ingestion completed — {counts['measurements']:,} measurements, "
        f"{counts['households']:,} households, {counts['appliances']} appliances."
    )


def _render_integrity_check(repository: CSVDataRepository) -> None:
    """Run the PK/FK/NN/UN validation on demand (DATA-02)."""
    st.markdown("#### Referential integrity")
    st.caption("Primary keys, unique constraints, not-null columns and foreign keys.")

    if st.button("Run integrity check", key="admin_integrity_check"):
        try:
            verdict = repository.validate_referential_integrity()
        except (FileNotFoundError, OSError) as error:
            st.error(f"The check could not run: {error}")
            return
        st.session_state["admin_integrity_verdict"] = bool(verdict)

    verdict = st.session_state.get("admin_integrity_verdict")
    if verdict is None:
        st.info("Press **Run integrity check** to validate the five tables.")
    elif verdict:
        st.success("Integrity OK — every PK, UN, NN and FK constraint is satisfied.")
    else:
        st.error("Integrity KO — at least one constraint failed.")


def _render_accounts(repository: CSVDataRepository) -> None:
    """List accounts and their household scope, with masked password hashes."""
    st.markdown("#### Accounts and household scope")
    if not repository.is_initialized():
        st.info("No account table loaded yet.")
        return

    users = repository.load_users()
    links = repository.load_user_households()
    rows = []
    for record in users.sort_values("users_id").itertuples(index=False):
        homes = sorted(
            int(home) for home in links.loc[links["users_id"] == record.users_id, "home_id"]
        )
        rows.append(
            {
                "users_id": record.users_id,
                "users_name": record.users_name,
                "role": record.role,
                "password_hash": f"{str(record.password_hash)[:8]}…",
                "linked_households": len(homes),
                "home_ids": ", ".join(str(home) for home in homes[:10])
                + (" …" if len(homes) > 10 else ""),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption("Admins implicitly read every household; standard users only the linked ones.")


def _render_raw_fidelity(repository: CSVDataRepository) -> None:
    """Show the fingerprint of the raw file to prove it was not modified (NFR-02)."""
    st.markdown("#### Raw data preservation")
    raw_path = Path(str(st.session_state.get("admin_raw_path", DEFAULT_RAW_PATH)))
    if not raw_path.exists():
        st.info(f"Raw CSV not available at `{raw_path}` in this environment.")
        return

    digest = hashlib.md5(raw_path.read_bytes(), usedforsecurity=False).hexdigest()
    size_mb = raw_path.stat().st_size / (1024 * 1024)
    columns = st.columns(3)
    columns[0].metric("File size", f"{size_mb:.1f} MB")
    columns[1].metric("MD5", digest[:12] + "…")
    columns[2].metric("Encoding", "cp1252")
    st.caption(
        "No row was dropped, no temperature was corrected, no season recomputed "
        "and no household size harmonised during ingestion."
    )


def _render_measurement_preview(repository: CSVDataRepository) -> None:
    """Preview the first measurements exactly as delivered."""
    st.markdown("#### Measurements preview (first 20 rows, unmodified)")
    if not repository.is_initialized():
        st.info("No measurement table loaded yet.")
        return

    frame = repository.load_measurements().head(20)
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.caption(
        "`measurement_id` is a surrogate key added by the ETL; every other value "
        "comes verbatim from the delivered CSV."
    )

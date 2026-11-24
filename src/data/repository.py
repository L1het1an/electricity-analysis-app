"""CSV-backed data repository handling raw ETL, table loading, and integrity checks."""

import hashlib
from pathlib import Path
import pandas as pd


RAW_COLUMN_MAP: dict[str, str] = {
    "Home ID": "home_id",
    "Appliance Type": "appliance_name",
    "Energy Consumption (kWh)": "energy_consumption",
    "Time": "time",
    "Date": "date",
    "Outdoor Temperature (°C)": "outdoor_temperature",
    "Season": "season",
    "Household Size": "household_size",
}

TABLE_FILES: dict[str, str] = {
    "users": "users.csv",
    "households": "households.csv",
    "user_households": "user_households.csv",
    "appliances": "appliances.csv",
    "measurements": "measurements.csv",
}


def _sha256_hex(plain_password: str) -> str:
    """Return a SHA-256 hex digest matching User.verify_password."""
    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest()


class CSVDataRepository:
    """Manages normalized CSV storage, raw ingestion, and PK/FK integrity checks."""

    def __init__(self, processed_dir: Path) -> None:
        """Initialize repository pointing to the processed CSV directory."""
        self._processed_dir = Path(processed_dir)
        self._processed_dir.mkdir(parents=True, exist_ok=True)

    def _table_path(self, table_name: str) -> Path:
        """Resolve the full file path for a logical table name."""
        return self._processed_dir / TABLE_FILES[table_name]

    def is_initialized(self) -> bool:
        """Return True if all 5 normalized CSV tables exist on disk."""
        return all(self._table_path(name).exists() for name in TABLE_FILES)

    def ingest_raw_csv(self, raw_csv_path: Path) -> dict[str, int]:
        """Ingest cp1252 raw CSV into normalized tables without altering raw records."""
        raw_path = Path(raw_csv_path)
        if not raw_path.exists():
            raise FileNotFoundError(f"Raw CSV file not found: {raw_path}")

        raw_df = pd.read_csv(raw_path, encoding="cp1252")
        missing_cols = [col for col in RAW_COLUMN_MAP if col not in raw_df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in raw CSV: {missing_cols}")

        df = raw_df[list(RAW_COLUMN_MAP.keys())].rename(columns=RAW_COLUMN_MAP)
        households_df, appliances_df, measurements_df = self._normalize_tables(df)

        households_df.to_csv(self._table_path("households"), index=False)
        appliances_df.to_csv(self._table_path("appliances"), index=False)
        measurements_df.to_csv(self._table_path("measurements"), index=False)
        self._ensure_seed_users(households_df["home_id"].tolist())

        return {
            "measurements": len(measurements_df),
            "households": len(households_df),
            "appliances": len(appliances_df),
        }

    def _normalize_tables(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split raw DataFrame into households, appliances, and measurements tables."""
        households_df = (
            pd.DataFrame({"home_id": sorted(df["home_id"].unique().tolist())})
        )
        appliance_names = sorted(df["appliance_name"].unique().tolist())
        appliances_df = pd.DataFrame(
            {
                "appliance_id": range(1, len(appliance_names) + 1),
                "appliance_name": appliance_names,
            }
        )
        name_to_id = dict(
            zip(appliances_df["appliance_name"], appliances_df["appliance_id"])
        )

        measurements_df = df.copy()
        measurements_df.insert(0, "measurement_id", range(1, len(measurements_df) + 1))
        measurements_df["appliance_id"] = measurements_df["appliance_name"].map(name_to_id)
        ordered_cols = [
            "measurement_id",
            "home_id",
            "appliance_id",
            "energy_consumption",
            "time",
            "date",
            "outdoor_temperature",
            "season",
            "household_size",
        ]
        return households_df, appliances_df, measurements_df[ordered_cols]

    def _ensure_seed_users(self, home_ids: list[int]) -> None:
        """Create default demo accounts and home links if user tables do not exist."""
        users_path = self._table_path("users")
        links_path = self._table_path("user_households")
        if users_path.exists() and links_path.exists():
            return

        users_df = pd.DataFrame(
            [
                {
                    "users_id": 1,
                    "users_name": "admin",
                    "password_hash": _sha256_hex("admin123"),
                    "role": "Admin",
                },
                {
                    "users_id": 2,
                    "users_name": "user1",
                    "password_hash": _sha256_hex("user123"),
                    "role": "User",
                },
                {
                    "users_id": 3,
                    "users_name": "user_multi",
                    "password_hash": _sha256_hex("user123"),
                    "role": "User",
                },
            ]
        )
        sample_homes = home_ids[:4]
        links_rows = []
        if len(sample_homes) >= 1:
            links_rows.append({"user_households_id": 1, "users_id": 2, "home_id": sample_homes[0]})
        for idx, hid in enumerate(sample_homes[:3], start=2):
            links_rows.append({"user_households_id": idx, "users_id": 3, "home_id": hid})

        links_df = pd.DataFrame(
            links_rows, columns=["user_households_id", "users_id", "home_id"]
        )
        users_df.to_csv(users_path, index=False)
        links_df.to_csv(links_path, index=False)

    def load_users(self) -> pd.DataFrame:
        """Load the users table from CSV."""
        return pd.read_csv(self._table_path("users"))

    def load_households(self) -> pd.DataFrame:
        """Load the households table from CSV."""
        return pd.read_csv(self._table_path("households"))

    def load_user_households(self) -> pd.DataFrame:
        """Load the user-household junction table from CSV."""
        return pd.read_csv(self._table_path("user_households"))

    def load_appliances(self) -> pd.DataFrame:
        """Load the appliances lookup table from CSV."""
        return pd.read_csv(self._table_path("appliances"))

    def load_measurements(self) -> pd.DataFrame:
        """Load the measurements fact table from CSV."""
        return pd.read_csv(self._table_path("measurements"))

    def validate_referential_integrity(self) -> bool:
        """Verify PK uniqueness, NN completeness, UN constraints, and FK integrity."""
        if not self.is_initialized():
            return False

        users = self.load_users()
        households = self.load_households()
        links = self.load_user_households()
        appliances = self.load_appliances()
        measurements = self.load_measurements()

        pk_checks = [
            users["users_id"].is_unique and not users.isna().any().any(),
            users["users_name"].is_unique,
            households["home_id"].is_unique and not households.isna().any().any(),
            links["user_households_id"].is_unique and not links.isna().any().any(),
            not links.duplicated(subset=["users_id", "home_id"]).any(),
            appliances["appliance_id"].is_unique and not appliances.isna().any().any(),
            appliances["appliance_name"].is_unique,
            measurements["measurement_id"].is_unique and not measurements.isna().any().any(),
        ]
        fk_checks = [
            links["users_id"].isin(users["users_id"]).all(),
            links["home_id"].isin(households["home_id"]).all(),
            measurements["home_id"].isin(households["home_id"]).all(),
            measurements["appliance_id"].isin(appliances["appliance_id"]).all(),
        ]
        return all(pk_checks) and all(fk_checks)

from __future__ import annotations

import pandas as pd
import numpy as np
import statsmodels.api as sm

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from src.data.repository import CSVDataRepository

MONTH_TO_SEASON = {
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Fall", 10: "Fall", 11: "Fall",
    }

class PredictionService:    
    def __init__(self, repo: CSVDataRepository) -> None:
        self._repo: CSVDataRepository = repo
        self._ols_model: object = None
        self._tree_model: object = None
        self._feature_columns: list[str] = None
        self._training_summary: dict = None


    def _clean_for_training(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        clean_df = df.copy()
        months = pd.to_datetime(clean_df["date"]).dt.month
        derived_season = months.map(MONTH_TO_SEASON)
        mismatches = int((clean_df["season"] != derived_season).sum())
        clean_df["season"] = derived_season
        clean_df["household_size"] = (
            clean_df.groupby("home_id")["household_size"].transform("mean").round().astype(int)
        )
        clean_df = clean_df[clean_df["outdoor_temperature"].between(-30.0, 50.0)]
        stats = {"raw_rows": len(df), "cleaned_rows": len(clean_df), "season_fixed": mismatches}
        return clean_df, stats


    def _prepare_features(self, clean_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """Build numeric + one-hot encoded feature matrix and target series."""
        feature_cols = ["outdoor_temperature", "household_size", "season", "appliance_name"]
        X = pd.get_dummies(
            clean_df[feature_cols],
            columns=["season", "appliance_name"],
            drop_first=True,
            dtype=float,  # Crucial: Pandas >=2.0 defaults to bool, which breaks Statsmodels OLS
        ).astype(float)
        y = clean_df["energy_consumption"].astype(float)
        self._feature_columns = list(X.columns)
        return X, y


    def _evaluate_weather_only_ols(self, clean_df: pd.DataFrame) -> dict[str, float]:
        """Fit a weather + house-size only OLS to transparently measure weather signal."""
        X_w = sm.add_constant(
            clean_df[["outdoor_temperature", "household_size"]].astype(float),
            has_constant="add",
        )
        y_w = clean_df["energy_consumption"].astype(float)
        ols_w = sm.OLS(y_w, X_w).fit()
        return {
            "r2": float(ols_w.rsquared),
            "temp_p_value": float(ols_w.pvalues["outdoor_temperature"]),
        }


    def _metrics(self, y_true: pd.Series, y_hat: np.ndarray) -> dict[str, float]:
        return {
            "r2": float(r2_score(y_true, y_hat)),
            "mae": float(mean_absolute_error(y_true, y_hat)),
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_hat))),
        }


    def train_baselines(self) -> dict:
        """Clean an in-memory copy, train OLS + HGB baselines, and return honest metrics."""
        measurements = self._repo.load_measurements()
        appliances = self._repo.load_appliances()
        merged = measurements.merge(
            appliances[["appliance_id", "appliance_name"]], 
            on="appliance_id", 
            how="left",
        )

        clean_df, cleaning_stats = self._clean_for_training(merged)
        X, y = self._prepare_features(clean_df)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Baseline 1: Statsmodels OLS
        X_train_const = sm.add_constant(X_train, has_constant="add")
        X_test_const = sm.add_constant(X_test, has_constant="add")
        self._ols_model = sm.OLS(y_train, X_train_const).fit()
        ols_pred = self._ols_model.predict(X_test_const)
        
        # Baseline 2: Scikit-learn HistGradientBoostingRegressor (fast on 100k rows)
        self._tree_model = HistGradientBoostingRegressor(max_depth=6, random_state=42)
        self._tree_model.fit(X_train, y_train)
        tree_pred = self._tree_model.predict(X_test)
    
        self._training_summary = {
            "cleaning_stats": cleaning_stats,
            "weather_only_ols": self._evaluate_weather_only_ols(clean_df),
            "models": {
                "Statsmodels OLS": self._metrics(y_test, ols_pred),
                "Scikit-learn HGB": self._metrics(y_test, tree_pred),
            },
        }
        return self._training_summary


    @staticmethod
    def _validate_inputs(
        outdoor_temp: float,
        household_size: int,
        season: str,
        appliance_name: str,
    ) -> None:
        """Validate prediction input boundaries (SVVP AI-03)."""
        if not (-40.0 <= float(outdoor_temp) <= 60.0):
            raise ValueError("Outdoor temperature must be between -40°C and 60°C.")
        if not (1 <= int(household_size) <= 20):
            raise ValueError("Household size must be between 1 and 20.")
        valid_seasons = {"Winter", "Spring", "Summer", "Fall"}
        if season not in valid_seasons:
            raise ValueError(f"Season must be one of {sorted(valid_seasons)}.")
        if not appliance_name or not isinstance(appliance_name, str):
            raise ValueError("A valid appliance name is required.")


    def _encode_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """One-hot encode a batch DataFrame aligned to training feature columns."""
        feature_cols = ["outdoor_temperature", "household_size", "season", "appliance_name"]
        X = pd.get_dummies(
            df[feature_cols],
            columns=["season", "appliance_name"],
            drop_first=False,
            dtype=float,
        )
        return X.reindex(columns=self._feature_columns, fill_value=0.0).astype(float)

    
    def get_home_prediction_curve(
            self, home_id: int, granularity: str = "Monthly"
    ) -> pd.DataFrame:
        """Return actual vs. OLS vs. HGB consumption curves for a single household."""
        if self._ols_model is None or self._tree_model is None or self._feature_columns is None:
            self.train_baselines()

        measurements = self._repo.load_measurements()
        appliances = self._repo.load_appliances()
        home_df = measurements[measurements["home_id"] == home_id].merge(
            appliances[["appliance_id", "appliance_name"]], on="appliance_id", how="left"
        )
        if home_df.empty:
            return pd.DataFrame(columns=["period", "actual_kwh", "ols_pred_kwh", "hgb_pred_kwh"])

        clean_df, _ = self._clean_for_training(home_df)
        X_batch = self._encode_batch(clean_df)
        clean_df["ols_pred_kwh"] = np.maximum(
            0.0, self._ols_model.predict(sm.add_constant(X_batch, has_constant="add"))
        )
        clean_df["hgb_pred_kwh"] = np.maximum(0.0, self._tree_model.predict(X_batch))
        clean_df["period"] = (
            clean_df["date"].astype(str).str.slice(0, 7)
            if granularity == "Monthly"
            else clean_df["date"].astype(str)
        )
        return (
            clean_df.groupby("period", as_index=False)
            .agg(
                actual_kwh=("energy_consumption", "sum"),
                ols_pred_kwh=("ols_pred_kwh", "sum"),
                hgb_pred_kwh=("hgb_pred_kwh", "sum"),
            )
            .sort_values("period")
            .reset_index(drop=True)
        )


    def get_temperature_comparison_curve(
            self, household_size: int, season: str, appliance_name: str
    ) -> pd.DataFrame:
        """Compare OLS vs. HGB predicted kWh across -10°C to 40°C."""
        if self._ols_model is None or self._tree_model is None or self._feature_columns is None:
            self.train_baselines()

        self._validate_inputs(0.0, household_size, season, appliance_name)
        temps = np.linspace(-10.0, 40.0, 51)
        sweep_df = pd.DataFrame(
            {
                "outdoor_temperature": temps,
                "household_size": household_size,
                "season": season,
                "appliance_name": appliance_name,
            }
        )
        X_batch = self._encode_batch(sweep_df)
        ols_preds = np.maximum(
            0.0, self._ols_model.predict(sm.add_constant(X_batch, has_constant="add"))
        )
        hgb_preds = np.maximum(0.0, self._tree_model.predict(X_batch))
        return pd.DataFrame(
            {
                "outdoor_temperature": temps,
                "ols_pred_kwh": ols_preds,
                "hgb_pred_kwh": hgb_preds,
            }
        )


    def predict(
        self,
        outdoor_temp: float,
        household_size: int,
        season: str,
        appliance_name: str,
        model_name: str = "Statsmodels OLS",
    ) -> float:
        """Predict electricity consumption (kWh) for given weather and house inputs."""
        if self._ols_model is None or self._tree_model is None or self._feature_columns is None:
            self.train_baselines()
        self._validate_inputs(outdoor_temp, household_size, season, appliance_name)
        row = pd.DataFrame(
            [
                {
                    "outdoor_temperature": float(outdoor_temp),
                    "household_size": int(household_size),
                    "season": season,
                    "appliance_name": appliance_name,
                }
            ]
        )
        # Use drop_first=False on a 1-row DataFrame so non-reference categories are preserved
        X_row = pd.get_dummies(
            row, columns=["season", "appliance_name"], drop_first=False, dtype=float
        )
        X_row = X_row.reindex(columns=self._feature_columns, fill_value=0.0).astype(float)
        if model_name == "Statsmodels OLS":
            X_const = sm.add_constant(X_row, has_constant="add")
            pred = float(self._ols_model.predict(X_const).iloc[0])
        elif model_name == "Scikit-learn HGB":
            pred = float(self._tree_model.predict(X_row)[0])
        else:
            raise ValueError(f"Unknown model_name: {model_name}")
        return max(0.0, pred)
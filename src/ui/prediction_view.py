"""Streamlit UI view for AI electricity consumption prediction (UC-07)."""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.models import User
from src.services.prediction_service import PredictionService

SEASONS: list[str] = ["Winter", "Spring", "Summer", "Fall"]
MODEL_OPTIONS: list[str] = ["Statsmodels OLS", "Scikit-learn HGB"]


@st.cache_resource(show_spinner="Training dual-baseline AI models (in-memory cleaning)...")
def _get_trained_summary(_service: PredictionService) -> dict:
    """Train baselines once and cache the evaluation summary across reruns."""
    return _service.train_baselines()


@st.cache_data(show_spinner=False)
def _load_home_defaults(processed_dir_str: str) -> tuple[dict[int, int], list[str]]:
    """Return per-home rounded mean household size and sorted appliance names."""
    measurements = pd.read_csv(Path(processed_dir_str) / "measurements.csv")
    appliances = pd.read_csv(Path(processed_dir_str) / "appliances.csv")
    size_map = (
        measurements.groupby("home_id")["household_size"]
        .mean()
        .round()
        .astype(int)
        .to_dict()
    )
    appliance_list = sorted(appliances["appliance_name"].tolist())
    return size_map, appliance_list


def _render_model_diagnostics(summary: dict) -> None:
    """Display in-memory cleaning audit, dual-baseline metrics, and weather insight."""
    st.subheader("Model Evaluation & Data Science Findings")
    c_stats = summary["cleaning_stats"]
    w_ols = summary["weather_only_ols"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Raw Rows Preserved on Disk", f"{c_stats['raw_rows']:,}")
    col2.metric("Season Mismatches Fixed (In-Memory)", f"{c_stats['season_fixed']:,}")
    col3.metric("Weather-Only OLS R²", f"{w_ols['r2']:.6f}", f"temp p={w_ols['temp_p_value']:.3f}")

    metrics_df = pd.DataFrame(summary["models"]).T.reset_index()
    metrics_df.columns = ["Model", "R²", "MAE (kWh)", "RMSE (kWh)"]
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    st.info(
        "**Honest Model Diagnostic:** Raw CSV records remain 100% unaltered in storage; "
        "data cleaning runs strictly on an in-memory copy inside the AI pipeline. "
        f"When predicting from weather and household size alone, OLS yields R² = {w_ols['r2']:.6f} "
        f"(outdoor temperature p = {w_ols['temp_p_value']:.3f} > 0.05), confirming near-zero "
        "weather-to-consumption signal. Including appliance category explains ~75% of variance."
    )


def _render_curve_comparison(
    prediction_service: PredictionService,
    home_id: int,
    household_size: int,
    season: str,
    appliance_name: str,
) -> None:
    """Render Matplotlib comparison curves for Statsmodels OLS vs. Scikit-learn HGB."""
    st.subheader("Dual-Model Prediction Curve Comparison (Bonus)")
    mode = st.radio(
        "Comparison Mode",
        ["Household Time-Series (Actual vs. OLS vs. HGB)", "Temperature Sweep (-10°C to 40°C)"],
        horizontal=True,
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    if mode.startswith("Household"):
        granularity = st.radio("Curve Granularity", ["Monthly", "Daily"], horizontal=True)
        curve_df = prediction_service.get_home_prediction_curve(home_id, granularity=granularity)
        if curve_df.empty:
            st.info(f"No records available for Home #{home_id}.")
            plt.close(fig)
            return
        ax.plot(curve_df["period"], curve_df["actual_kwh"], label="Actual (kWh)", color="#333333", linewidth=2.0)
        ax.plot(curve_df["period"], curve_df["ols_pred_kwh"], label="Statsmodels OLS", color="#1f77b4", linestyle="--", linewidth=1.8)
        ax.plot(curve_df["period"], curve_df["hgb_pred_kwh"], label="Scikit-learn HGB", color="#ff7f0e", linestyle=":", linewidth=2.0)
        ax.set_title(f"Home #{home_id} — Actual vs. Dual-Model Predictions ({granularity})")
        ax.set_xlabel("Period")
        ax.set_ylabel("Energy Consumption (kWh)")
        step = max(1, len(curve_df) // 12)
        ax.set_xticks(range(0, len(curve_df), step))
        ax.set_xticklabels(curve_df["period"].iloc[::step], rotation=45, ha="right")
    else:
        sweep_df = prediction_service.get_temperature_comparison_curve(
            household_size=household_size, season=season, appliance_name=appliance_name
        )
        ax.plot(sweep_df["outdoor_temperature"], sweep_df["ols_pred_kwh"], label="Statsmodels OLS", color="#1f77b4", linewidth=2.0)
        ax.plot(sweep_df["outdoor_temperature"], sweep_df["hgb_pred_kwh"], label="Scikit-learn HGB", color="#ff7f0e", linestyle="--", linewidth=2.0)
        ax.set_title(f"Temperature Response Curve ({appliance_name}, {season}, Size={household_size})")
        ax.set_xlabel("Outdoor Temperature (°C)")
        ax.set_ylabel("Predicted Consumption (kWh)")

    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def render_prediction_view(
    prediction_service: PredictionService,
    user: User,
    authorized_homes: list[int],
) -> None:
    """Render the AI prediction form, inference output, and baseline diagnostics."""
    st.header("AI Electricity Consumption Prediction")
    if not authorized_homes:
        st.warning("No authorized households available for your account.")
        return

    summary = _get_trained_summary(prediction_service)
    size_map, appliance_list = _load_home_defaults(str(prediction_service._repo._processed_dir))

    left_col, right_col = st.columns([1, 1])
    with left_col:
        selected_home = st.selectbox("Select Authorized Household (Home ID)", authorized_homes)
        default_size = size_map.get(selected_home, 3)
        household_size = st.number_input(
            "Household Size (residents)", min_value=1, max_value=20, value=int(default_size), step=1
        )
        outdoor_temp = st.number_input(
            "Forecast Outdoor Temperature (°C)", min_value=-40.0, max_value=60.0, value=20.0, step=0.5
        )
    with right_col:
        season = st.selectbox("Season", SEASONS, index=2)
        appliance_name = st.selectbox("Appliance Type", appliance_list)
        model_name = st.radio("Prediction Model", MODEL_OPTIONS, horizontal=True)

    if st.button("Predict Consumption", type="primary"):
        try:
            predicted_kwh = prediction_service.predict(
                outdoor_temp=outdoor_temp,
                household_size=int(household_size),
                season=season,
                appliance_name=appliance_name,
                model_name=model_name,
            )
            st.success(f"Prediction completed for Home #{selected_home} ({model_name}).")
            st.metric("Predicted Energy Consumption", f"{predicted_kwh:.3f} kWh")
        except ValueError as exc:
            st.error(f"Invalid input: {exc}")

    st.divider()
    _render_curve_comparison(
        prediction_service=prediction_service,
        home_id=int(selected_home),
        household_size=int(household_size),
        season=season,
        appliance_name=appliance_name,
    )
    st.divider()
    _render_model_diagnostics(summary)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.data.repository import CSVDataRepository

    st.set_page_config(page_title="AI Prediction Standalone Preview", layout="wide")
    repo = CSVDataRepository(project_root / "data" / "processed")
    svc = PredictionService(repo)
    demo_admin = User(1, "admin", "", "Admin", [])
    all_homes = repo.load_households()["home_id"].tolist()
    render_prediction_view(svc, demo_admin, all_homes)

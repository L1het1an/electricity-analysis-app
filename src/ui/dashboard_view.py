"""Streamlit dashboard: consumption analysis, comparison and filtering (UC-03..UC-06)."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.models import User
from src.services.analytics_service import (
    AVERAGE_LABEL,
    GRANULARITIES,
    MAX_COMPARE_HOMES,
    AnalyticsService,
    UnauthorizedHomeError,
)

DEFAULT_APPLIANCES: tuple[str, ...] = ("Air Conditioning", "Computer", "Dishwasher")


def render_dashboard_view(
    analytics_svc: AnalyticsService,
    user: User,
    authorized_homes: list[int] | None = None,
) -> None:
    """Render the analysis dashboard for the signed-in user."""
    st.title("Dashboard")
    st.caption(
        "Daily consumption by default (FR-03). Switch the granularity, compare up to "
        f"{MAX_COMPARE_HOMES} households, overlay the system average and filter sources."
    )

    homes = analytics_svc.authorize(user) if authorized_homes is None else authorized_homes
    if not homes:
        st.warning(
            "No household is linked to this account. Ask an administrator to assign one."
        )
        return

    controls = _render_controls(analytics_svc, homes)
    if controls is None:
        return

    try:
        _render_report(analytics_svc, user, controls)
    except UnauthorizedHomeError as exc:
        st.error(str(exc))


def _render_controls(
    analytics_svc: AnalyticsService, homes: list[int]
) -> dict[str, Any] | None:
    """Draw the filter row and return the selected values."""
    first, second, third, fourth = st.columns([1, 2, 2, 1])

    with first:
        granularity = st.radio(
            "Granularity",
            GRANULARITIES,
            index=0,
            help="Daily resolution is the default view required by FR-03.",
        )

    with second:
        chosen = st.multiselect(
            f"Households (max {MAX_COMPARE_HOMES})",
            options=homes,
            default=homes[:1],
            format_func=lambda home: f"Home {int(home)}",
            max_selections=MAX_COMPARE_HOMES,
            help="Select between 1 and 5 households to compare.",
        )

    appliances = analytics_svc.appliance_options()
    with third:
        selected = st.multiselect(
            "Appliances",
            options=appliances["appliance_name"].tolist(),
            default=[
                name
                for name in appliances["appliance_name"].tolist()
                if name in DEFAULT_APPLIANCES
            ],
            help="Uncheck a source to exclude it, for example Fridge.",
        )

    with fourth:
        show_average = st.checkbox(
            "System average",
            value=True,
            help="Overlay the average of all 500 households (FR-05).",
        )

    start, end = analytics_svc.date_bounds()
    date_from, date_to = st.slider(
        "Period",
        min_value=pd.to_datetime(start).date(),
        max_value=pd.to_datetime(end).date(),
        value=(pd.to_datetime(start).date(), pd.to_datetime(end).date()),
    )

    if not chosen:
        st.info("Select at least one household.")
        return None

    appliance_ids = appliances.loc[
        appliances["appliance_name"].isin(selected), "appliance_id"
    ].tolist()
    return {
        "granularity": granularity,
        "homes": chosen,
        "appliance_ids": appliance_ids,
        "appliance_names": selected,
        "show_average": show_average,
        "date_from": str(date_from),
        "date_to": str(date_to),
    }


def _render_report(
    analytics_svc: AnalyticsService, user: User, controls: dict[str, Any]
) -> None:
    """Render the KPI row, the chart and the detail table."""
    kwargs = {
        "appliance_ids": controls["appliance_ids"],
        "user": user,
        "date_from": controls["date_from"],
        "date_to": controls["date_to"],
    }
    series = analytics_svc.aggregate(
        controls["homes"], controls["granularity"], **kwargs
    )
    if series.empty:
        st.info("No measurement matches the current filters.")
        return

    _render_kpis(analytics_svc, user, controls)
    _render_chart(analytics_svc, series, controls)
    _render_table(series, controls)


def _render_kpis(
    analytics_svc: AnalyticsService, user: User, controls: dict[str, Any]
) -> None:
    """Draw the headline indicators for the current selection."""
    summary = analytics_svc.kpi_table(
        controls["homes"],
        controls["granularity"],
        appliance_ids=controls["appliance_ids"],
        user=user,
        date_from=controls["date_from"],
        date_to=controls["date_to"],
    )
    unit = controls["granularity"].lower()
    first, second, third = st.columns(3)
    first.metric(
        f"Total ({unit})",
        f"{summary['total_kwh'].sum():,.1f} kWh",
    )
    second.metric("Households", len(controls["homes"]))
    third.metric(
        f"Mean per {unit}",
        f"{summary['mean_per_period_kwh'].mean():,.2f} kWh",
    )
    st.dataframe(
        summary,
        hide_index=True,
        use_container_width=True,
        column_config={
            "home_id": "Home",
            "total_kwh": st.column_config.NumberColumn("Total (kWh)", format="%.2f"),
            "n_periods": f"Periods ({unit}s)",
            "mean_per_period_kwh": st.column_config.NumberColumn(
                f"Mean ({unit})", format="%.2f"
            ),
            "measurements": "Measurements",
            "days": "Days",
            "mean_household_size": st.column_config.NumberColumn(
                "Residents (mean)", format="%.2f"
            ),
            "kwh_per_resident": st.column_config.NumberColumn(
                "kWh / resident", format="%.2f"
            ),
        },
    )


def _render_chart(
    analytics_svc: AnalyticsService,
    series: pd.DataFrame,
    controls: dict[str, Any],
) -> None:
    """Draw the overlay chart with one colour per household plus the average."""
    labels = analytics_svc.series_labels(controls["homes"])
    frame = series.assign(
        label=series["home_id"].map(dict(zip(controls["homes"], labels)))
    )[["period", "label", "kwh"]]

    domain = list(labels)
    if controls["show_average"]:
        average = analytics_svc.system_average(
            controls["granularity"],
            appliance_ids=controls["appliance_ids"],
            date_from=controls["date_from"],
            date_to=controls["date_to"],
        )
        if not average.empty:
            frame = pd.concat(
                [
                    frame,
                    average.rename(columns={"avg_kwh": "kwh"}).assign(
                        label=AVERAGE_LABEL
                    )[["period", "label", "kwh"]],
                ],
                ignore_index=True,
            )
            domain.append(AVERAGE_LABEL)

    colours = analytics_svc.colour_map(controls["homes"])
    frame["period"] = pd.Categorical(
        frame["period"], categories=sorted(frame["period"].unique()), ordered=True
    )
    st.vega_lite_chart(
        frame,
        {
            "mark": {
                "type": "line",
                "point": controls["granularity"] != "Day",
                "tooltip": True,
            },
            "encoding": {
                "x": {
                    "field": "period",
                    "type": "ordinal",
                    "title": controls["granularity"],
                    "axis": {"labelAngle": -45},
                },
                "y": {
                    "field": "kwh",
                    "type": "quantitative",
                    "title": "Consumption (kWh)",
                },
                "color": {
                    "field": "label",
                    "type": "nominal",
                    "title": None,
                    "scale": {
                        "domain": domain,
                        "range": [colours[label] for label in domain],
                    },
                },
                "tooltip": [
                    {"field": "label", "type": "nominal"},
                    {"field": "kwh", "type": "quantitative", "format": ".2f"},
                ],
            },
            "height": 380,
        },
        use_container_width=True,
    )
    st.caption(
        "Colours: "
        + " · ".join(
            f"**{label}** {colours[label]}" for label in domain
        )
    )


def _render_table(series: pd.DataFrame, controls: dict[str, Any]) -> None:
    """Draw the detail table and the CSV download button."""
    wide = (
        series.assign(label=series["home_id"].map(lambda home: f"Home {int(home)}"))
        .pivot(index="period", columns="label", values="kwh")
        .reset_index()
    )
    st.dataframe(wide, hide_index=True, use_container_width=True)
    st.download_button(
        "Download this table (CSV)",
        data=wide.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"consumption_{controls['granularity'].lower()}.csv",
        mime="text/csv",
    )

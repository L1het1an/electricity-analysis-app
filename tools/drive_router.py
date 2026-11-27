"""End-to-end check of the router that now mounts every member's view."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8600"
SHOTS = Path("F:/technicalProject/team/docs/shots")
PASSWORDS = {"admin": "admin123", "user1": "user123", "user_multi": "user123"}


def wait(page, seconds: float = 4.0) -> None:
    """Give Streamlit time to finish a rerun."""
    page.wait_for_timeout(int(seconds * 1000))


def body(page) -> str:
    """Return the visible text of the page."""
    return page.inner_text("body")


def sign_in(page, username: str) -> None:
    """Fill the sign-in form and submit it."""
    page.goto(BASE, wait_until="domcontentloaded")
    wait(page, 9)
    page.locator('input[aria-label="Username"]').first.fill(username)
    page.locator('input[aria-label="Password"]').first.fill(PASSWORDS[username])
    page.get_by_role("button", name="Sign in").click()
    wait(page, 8)


def navigate(page, label: str) -> None:
    """Switch screens through the sidebar navigation."""
    page.locator('[data-testid="stSidebar"] label').filter(has_text=label).first.click()
    wait(page, 10)


def shot(page, name: str) -> str:
    """Save a screenshot and return its path."""
    target = SHOTS / name
    page.screenshot(path=str(target), full_page=False)
    return str(target)


def main() -> None:
    """Walk the four screens and record the outcome."""
    log: dict[str, object] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1500, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        sign_in(page, "user1")
        sidebar = page.locator('[data-testid="stSidebar"]').inner_text()
        log["sidebar_has_dashboard"] = "Dashboard" in sidebar
        log["sidebar_has_prediction"] = "AI Prediction" in sidebar
        log["sidebar_has_export"] = "Export Report" in sidebar
        log["sidebar_hides_admin_for_user"] = "Data management" not in sidebar

        # ---- AI Prediction (member C) ---------------------------------- #
        navigate(page, "AI Prediction")
        prediction_text = body(page)
        log["prediction_header"] = "AI Electricity Consumption Prediction" in prediction_text
        page.get_by_role("button", name="Predict Consumption").click()
        wait(page, 25)
        after_predict = body(page)
        log["prediction_metric"] = "Predicted Energy Consumption" in after_predict
        log["prediction_baselines"] = "Statsmodels OLS" in after_predict and "Scikit-learn HGB" in after_predict
        log["prediction_shot"] = shot(page, "10_prediction_user1.png")
        page.mouse.wheel(0, 2500)
        wait(page, 2)
        log["prediction_diagnostics_shot"] = shot(page, "11_prediction_diagnostics.png")

        # ---- Export Report (member C) ---------------------------------- #
        navigate(page, "Export Report")
        export_text = body(page)
        log["export_header"] = "Export Summary Report" in export_text
        log["export_table"] = "total_kwh" in export_text or "Report Rows" in export_text
        log["export_shot"] = shot(page, "12_export_user1.png")

        # ---- Dashboard (member B) still works -------------------------- #
        navigate(page, "Dashboard")
        dashboard_text = body(page)
        log["dashboard_total"] = "Total (day)" in dashboard_text
        log["dashboard_shot"] = shot(page, "03_dashboard_day_user1.png")

        # ---- admin sees four screens + management ---------------------- #
        page.get_by_role("button", name="Log out").click()
        wait(page, 6)
        sign_in(page, "admin")
        admin_sidebar = page.locator('[data-testid="stSidebar"]').inner_text()
        log["admin_has_management"] = "Data management" in admin_sidebar
        log["admin_scope"] = "500 household(s) visible" in admin_sidebar

        log["js_errors"] = errors
        browser.close()

    (SHOTS / "router_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()

"""Drive the dashboard in a real browser and capture the deliverable screenshots."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8600"
SHOTS = Path("F:/technicalProject/team/docs/shots")
PASSWORDS = {"admin": "admin123", "user1": "user123", "user_multi": "user123"}


def wait(page, seconds: float) -> None:
    page.wait_for_timeout(int(seconds * 1000))


def body(page) -> str:
    text = page.inner_text("body")
    cells = [
        node.get_attribute("aria-label") or node.inner_text()
        for node in page.locator('[role="gridcell"]').all()
    ]
    return text + "\n" + "\n".join(cell for cell in cells if cell)


def shot(page, name: str) -> str:
    target = SHOTS / name
    page.screenshot(path=str(target))
    return str(target)


def pick(page, field: str, option: str) -> None:
    """Open one multiselect, type to filter, then add a single option.

    This Streamlit version only renders the option nodes once the search box
    holds text, so the option has to be typed before it can be clicked.
    """
    widget = page.locator('[data-testid="stMultiSelect"]').filter(has_text=field).first
    widget.click()
    wait(page, 2)
    search = widget.locator("input").first
    search.fill(option)
    wait(page, 2)
    page.get_by_role("option").first.click()
    wait(page, 1)
    page.keyboard.press("Escape")
    wait(page, 7)


def sign_in(page, username: str) -> None:
    page.locator('input[aria-label="Username"]').first.fill(username)
    page.locator('input[aria-label="Password"]').first.fill(PASSWORDS[username])
    page.get_by_role("button", name="Sign in").click()
    wait(page, 9)


def log_out(page) -> None:
    page.locator('[data-testid="stSidebar"] button').filter(has_text="Log out").first.click()
    wait(page, 7)


def main() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    log: dict[str, object] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1500, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        page.goto(BASE, wait_until="domcontentloaded")
        wait(page, 10)
        log["01_login"] = shot(page, "01_login_placeholder.png")

        page.locator('input[aria-label="Username"]').first.fill("user1")
        page.locator('input[aria-label="Password"]').first.fill("wrong")
        page.get_by_role("button", name="Sign in").click()
        wait(page, 6)
        log["02_invalid_credentials"] = "Invalid username or password." in body(page)
        log["02_shot"] = shot(page, "02_login_error.png")

        sign_in(page, "user1")
        text = body(page)
        log["03_signed_in_as_user1"] = "Signed in as user1" in text
        log["03_scope_one_home"] = "1 household(s) visible" in text
        log["03_admin_nav_hidden"] = "Data management" not in text
        log["03_total_day"] = "Total (day)" in text
        log["03_shot"] = shot(page, "03_dashboard_day_user1.png")

        page.get_by_text("Month", exact=True).first.click()
        wait(page, 7)
        text = body(page)
        log["04_month_total"] = "Total (month)" in text
        log["04_shot"] = shot(page, "04_dashboard_month_user1.png")

        log_out(page)
        log["05_logged_out"] = "Sign in" in body(page)

        sign_in(page, "user_multi")
        text = body(page)
        log["06_three_homes"] = "3 household(s) visible" in text
        pick(page, "Households (max 5)", "Home 2")
        pick(page, "Households (max 5)", "Home 3")
        text = body(page)
        log["07_compare_households"] = "Mean per day" in text
        log["07_shot"] = shot(page, "07_dashboard_compare.png")

        pick(page, "Appliances", "Fridge")
        log["08_filter_shot"] = shot(page, "08_dashboard_filter.png")

        log_out(page)
        sign_in(page, "admin")
        text = body(page)
        log["09_admin_nav"] = "Data management" in text
        log["09_admin_scope"] = "500 household(s) visible" in text
        log["09_shot"] = shot(page, "09_admin_dashboard.png")
        log["js_errors"] = errors
        browser.close()

    print(json.dumps(log, indent=2, ensure_ascii=False))
    Path("F:/technicalProject/team/docs/shots/drive_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()

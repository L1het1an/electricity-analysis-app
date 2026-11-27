"""Probe how the Streamlit multiselect exposes its options in this version."""

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8600"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1500, "height": 1000})
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_timeout(9000)
    page.locator('input[aria-label="Username"]').first.fill("user_multi")
    page.locator('input[aria-label="Password"]').first.fill("user123")
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_timeout(9000)

    widget = page.locator('[data-testid="stMultiSelect"]').filter(has_text="Appliances").first
    widget.click()
    page.wait_for_timeout(2500)
    print("--- ul options ---")
    for node in page.locator("ul li").all():
        print("li:", repr(node.inner_text()[:50]))
    print("--- role option ---")
    print("count:", page.get_by_role("option").count())
    print("--- div/span containing Fridge ---")
    for node in page.get_by_text("Fridge").all():
        print(
            "text:",
            repr(node.inner_text()[:40]),
            "tag:",
            node.evaluate("el => el.tagName"),
            "parent:",
            node.evaluate("el => el.parentElement ? el.parentElement.tagName : ''"),
        )
    print("--- input value after typing ---")
    search = page.locator('[data-testid="stMultiSelect"] input').first
    search.fill("Fridge")
    page.wait_for_timeout(2500)
    for node in page.locator("ul li").all():
        print("li after type:", repr(node.inner_text()[:50]))
    print("options after type:", page.get_by_role("option").count())
    page.screenshot(path="F:/technicalProject/team/docs/shots/probe_dropdown.png")
    browser.close()

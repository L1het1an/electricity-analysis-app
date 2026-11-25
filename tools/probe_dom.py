"""Probe the dashboard DOM after signing in as user_multi."""

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
    print("BODY:", page.inner_text("body")[:1200].replace("\n", " | "))
    print("--- comboboxes ---")
    for node in page.get_by_role("combobox").all():
        print(repr(node.inner_text()[:60]))
    print("--- multiselect inputs ---")
    for node in page.locator('[data-testid="stMultiSelect"]').all():
        print(repr(node.inner_text()[:60]))
    page.screenshot(path="F:/technicalProject/team/docs/shots/probe.png")
    browser.close()

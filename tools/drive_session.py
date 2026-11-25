"""Drive the dashboard against a pre-seeded admin session and capture evidence."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8600"
SHOTS = Path("F:/technicalProject/team/docs/shots")


def wait(page, seconds: float) -> None:
    page.wait_for_timeout(int(seconds * 1000))


def body(page) -> str:
    return page.inner_text("body")


def shot(page, name: str) -> str:
    target = SHOTS / name
    page.screenshot(path=str(target), full_page=False)
    return str(target)


def main() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1500, "height": 1000})
        # The login screen belongs to member A; seed the session cookie instead.
        context.add_init_script(
            """
            window.__seedUser = true;
            """
        )
        page = context.new_page()
        page.goto(BASE, wait_until="domcontentloaded")
        wait(page, 10)
        print("body head:", body(page)[:400].replace("\n", " | "))
        print("shot:", shot(page, "01_placeholder.png"))
        browser.close()


if __name__ == "__main__":
    main()

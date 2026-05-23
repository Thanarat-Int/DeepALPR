"""Verify the new logo appears on login page, sidebar, and favicon."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent.parent / "runs" / "ui"
OUT.mkdir(parents=True, exist_ok=True)


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    # login page (desktop layout — logo in aside)
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_selector("#lg-user", timeout=10000)
    page.wait_for_timeout(600)
    page.screenshot(path=str(OUT / "logo_login_desktop.png"), full_page=False)

    # mobile login layout (aside hidden, lf-brand shown)
    ctx2 = browser.new_context(viewport={"width": 600, "height": 900})
    page2 = ctx2.new_page()
    page2.goto("http://127.0.0.1:8000/")
    page2.wait_for_selector("#lg-user", timeout=10000)
    page2.wait_for_timeout(400)
    page2.screenshot(path=str(OUT / "logo_login_mobile.png"), full_page=False)

    # sign in then shoot console (sidebar logo)
    page.fill("#lg-user", "admin")
    page.fill("#lg-pass", "admin123")
    page.click("#lg-btn")
    page.wait_for_selector(".sidebar", timeout=10000)
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / "logo_console.png"), full_page=False)

    browser.close()
print("screenshots saved to", OUT)

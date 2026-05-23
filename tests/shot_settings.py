"""One-shot screenshot of the Settings page to verify user CRUD UI."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent.parent / "runs" / "ui"
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name):
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    # login
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_selector("#lg-user", timeout=10000)
    page.fill("#lg-user", "admin")
    page.fill("#lg-pass", "admin123")
    page.click("#lg-btn")
    page.wait_for_selector(".sidebar", timeout=10000)

    # settings page
    page.click("[data-nav=settings]")
    page.wait_for_selector("#pw-btn", timeout=5000)
    page.wait_for_timeout(700)
    shot(page, "settings_admin")

    # open change-password modal
    page.click("#pw-btn")
    page.wait_for_selector(".modal", timeout=3000)
    page.wait_for_timeout(400)
    shot(page, "settings_change_pw_modal")
    page.evaluate("document.getElementById('modal-root').innerHTML = ''")
    page.wait_for_timeout(300)

    # open add-user modal
    page.click("#u-add")
    page.wait_for_selector(".modal", timeout=3000)
    page.wait_for_timeout(400)
    shot(page, "settings_add_user_modal")
    page.evaluate("document.getElementById('modal-root').innerHTML = ''")

    browser.close()
print("screenshots saved to", OUT)

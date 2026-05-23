"""Screenshot Dashboard + Vehicles with province visible."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent.parent / "runs" / "ui"
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = ctx.new_page()

    page.goto("http://127.0.0.1:8000/")
    page.wait_for_selector("#lg-user", timeout=10000)
    page.fill("#lg-user", "admin"); page.fill("#lg-pass", "admin123")
    page.click("#lg-btn")

    # wait for events to populate then capture console
    page.wait_for_selector("#lc-frame", timeout=10000)
    page.wait_for_timeout(3500)
    page.screenshot(path=str(OUT / "console_province.png"), full_page=True)

    # vehicles page
    page.click("[data-nav=vehicles]")
    page.wait_for_selector("#v-add", timeout=8000)
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / "vehicles_province.png"), full_page=False)

    browser.close()
print("saved")

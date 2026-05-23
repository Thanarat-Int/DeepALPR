"""Screenshot the expanded Reports page."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent.parent / "runs" / "ui"
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_selector("#lg-user", timeout=10000)
    page.fill("#lg-user", "admin"); page.fill("#lg-pass", "admin123"); page.click("#lg-btn")
    page.wait_for_selector(".sidebar", timeout=10000)
    page.click("[data-nav=reports]")
    page.wait_for_selector("#ex-btn", timeout=8000)
    page.wait_for_timeout(900)
    page.screenshot(path=str(OUT / "reports_full.png"), full_page=True)
    browser.close()
print("saved")

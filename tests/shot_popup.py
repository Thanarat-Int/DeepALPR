"""Screenshot dashboard + popup zoom of the Honda Jazz demo event."""
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
    page.wait_for_selector("#lc-frame", timeout=10000)
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT / "console_consistent.png"), full_page=True)

    # click hero image to trigger popup
    page.click(".hero-cap img.zoomable")
    page.wait_for_selector(".modal", timeout=4000)
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "popup_demo.png"), full_page=False)
    browser.close()
print("saved")

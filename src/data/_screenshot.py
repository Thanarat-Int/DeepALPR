"""Capture UI screenshots of the running service (dev verification only)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[2] / "data" / "_preview"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        page.wait_for_timeout(900)
        page.screenshot(path=str(OUT / "ui_login.png"))

        page.fill("#lg-user", "admin")
        page.fill("#lg-pass", "admin123")
        page.click("#lg-btn")
        page.wait_for_timeout(1900)
        page.screenshot(path=str(OUT / "ui_console.png"))

        page.click(".feed-thumb.zoomable")             # event detail popup
        page.wait_for_timeout(1000)
        page.screenshot(path=str(OUT / "ui_popup.png"))
        page.click(".modal [data-close]")
        page.wait_for_timeout(400)

        page.click("#theme-btn")                       # -> dark
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / "ui_console_dark.png"))
        page.click("#theme-btn")                       # -> light
        page.wait_for_timeout(500)

        for view in ("log", "vehicles", "blacklist", "reports", "settings"):
            page.click(f"[data-nav={view}]")
            page.wait_for_timeout(1300)
            page.screenshot(path=str(OUT / f"ui_{view}.png"))

        page.click("[data-nav=vehicles]")
        page.wait_for_timeout(900)
        page.click("#lang-seg [data-lang=en]")          # -> English
        page.wait_for_timeout(1400)
        page.screenshot(path=str(OUT / "ui_english.png"))

        browser.close()
    print("screenshots saved to", OUT)


if __name__ == "__main__":
    main()

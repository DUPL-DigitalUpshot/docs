"""Storyboard: admin walkthrough (owner account). View-only: nothing is saved, no run starts.

    DEMO_PASSWORD=... python3 record.py [--shots]
Needs the app on http://localhost:5174. Narration keys: title, s1..s10, end (narration.json).
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "_tools"))
from demo_kit import Demo, run  # noqa: E402

BASE = "http://localhost:5174"
EMAIL = "owner@digitalupshot.com"


async def storyboard(d: Demo):
    pg = d.pg

    await d.card("One console for every quick-commerce report",
                 "Admin walkthrough · Blinkit · Swiggy Instamart · Flipkart Minutes · Zepto",
                 key="title")

    # 1 Sign in
    await d.done()
    await pg.goto(BASE + "/brands")
    await pg.wait_for_selector("input[type=email]")
    await d.cap("Sign in", "Admins sign in with their work email and password.")
    await d.wait(900)
    await d.type(pg.locator("input[type=email]"), EMAIL, delay=35)
    await d.type(pg.locator("input[type=password]"), os.environ["DEMO_PASSWORD"], delay=45)
    await d.wait(400)
    await d.click(pg.locator("button[type=submit]"), pause=300)
    await pg.wait_for_url(lambda u: "/login" not in u, timeout=15000)
    if "change-password" in pg.url:
        raise SystemExit("Landed on change-password; stopping.")
    # Overview is still a placeholder page, so go straight to the brand list.
    await pg.goto(BASE + "/brands")
    await pg.get_by_text("Del Monte", exact=True).first.wait_for()
    await d.wait(900)
    await d.shot("01-brands")

    # 2 Brands
    await d.done()
    await d.cap("Your brands", "Every client brand in one list. Open one to see its setup.")
    await d.wait(2200)
    await d.click(pg.get_by_text("Del Monte", exact=True).first)
    await pg.wait_for_url("**/brands/*/connections")
    await d.wait(1200)

    # 3 Connections, 4 safety check
    await d.done()
    await d.cap("A brand's platform connections",
                "Each platform, split into Ads and Sales, with a live health status.")
    await d.point(pg.get_by_text("Swiggy Instamart", exact=True).first, 1400)
    await d.point(pg.get_by_text("Healthy").first, 1400)
    await d.shot("03-connections")
    await d.cap("Safety check: right business only",
                "One login can hold several businesses. If the portal shows a different one, "
                "UniQCAI stops instead of downloading the wrong data.")
    await d.point(pg.get_by_text("Needs attention").first, 1200)
    await d.point(pg.locator("text=/WRONG_ACCOUNT/").first, 3200)
    await d.shot("04-safety")

    # 5 Access
    await d.done()
    await d.click(pg.get_by_role("link", name="Access").first)
    await d.wait(1300)
    await d.cap("Who can see this brand", "Each brand team sees only its own brand and reports.")
    await d.wait(2400)
    await d.shot("05-access")

    # 6 Platform accounts
    await d.done()
    await d.click(pg.get_by_role("link", name="Platform accounts").first)
    await d.wait(1300)
    await d.cap("Platform accounts",
                "One row per portal login. A login can serve several brands. "
                "Passwords are stored encrypted and never shown again.")
    await d.point(pg.get_by_text("Used by").first, 1800)
    await d.point(pg.get_by_role("button", name="Test login").first, 1600)
    await d.scroll(420)
    await d.wait(1600)
    await d.shot("06-accounts")

    # 7 Connect a platform (first wizard step only; nothing saved)
    await d.done()
    await d.scroll(-420)
    await d.click(pg.locator("main").get_by_text("Connect platform", exact=True).first)
    await d.wait(1300)
    await d.cap("Connect a new platform",
                "A guided set-up: pick the platform, add the login, choose where the "
                "verification code arrives, then pick the reports.")
    await d.wait(3600)
    await d.shot("07-wizard")

    # 8 Mailboxes
    await d.done()
    await d.click(pg.get_by_role("link", name="Mailboxes").first)
    await d.wait(1300)
    await d.cap("OTP mailboxes",
                "Verification codes are read from these inboxes automatically. "
                "Nobody has to forward an OTP.")
    await d.point(pg.get_by_text("Working", exact=True).first, 1600)
    await d.point(pg.get_by_text("Forwarded", exact=True).first, 1600)
    await d.point(pg.get_by_text("Forwards from", exact=True).first, 1800)
    await d.shot("08-mailboxes")

    # 9 Run now: choose, then cancel (no run is started)
    await d.done()
    await d.click(pg.get_by_role("button", name="Run now").first)
    await d.wait(1200)
    await d.cap("Download reports on demand",
                "Choose the brand, the reports (Platform → Ads / Sales → Report) "
                "and the date range. One click starts the download.", left=24)
    drawer = pg.get_by_role("dialog")
    await d.wait(1200)
    await d.click(drawer.get_by_text("Summary Report", exact=True).first, pause=300)
    await d.wait(500)
    await d.click(drawer.get_by_text("Date X Campaign", exact=True).first, pause=300)
    await d.wait(500)
    yesterday = drawer.get_by_text("Yesterday", exact=True).first
    await yesterday.scroll_into_view_if_needed()
    await d.wait(600)
    await d.click(yesterday, pause=300)
    await d.wait(900)
    await d.point(drawer.get_by_role("button", name="Start run for Del Monte"), 2200)
    await d.shot("09-runnow")
    await d.click(drawer.get_by_role("button", name="Cancel"), highlight=False, pause=200)
    await d.wait(700)

    # 10 Coming next (sections locked for this account)
    await d.done()
    await d.cap("Coming next", "Run history with live progress, schedules and the report library "
                "are being switched on for your account.")
    nav = pg.locator("nav")
    await d.point(nav.get_by_text("Runs", exact=True).first, 1300)
    await d.point(nav.get_by_text("Schedules", exact=True).first, 1100)
    await d.point(nav.get_by_text("Report library", exact=True).first, 1600)
    await d.shot("10-next")
    await d.uncap()

    await d.card("Set up once. Reports collected every day.",
                 "Brands → connections → mailboxes → run. Files ready for your team.",
                 foot="UniQCAI · Digital Upshot", key="end")


run(storyboard, total_steps=10)

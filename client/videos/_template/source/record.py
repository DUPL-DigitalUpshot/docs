"""Storyboard: __TITLE__.

    DEMO_PASSWORD=... python3 record.py [--shots]
Narration keys: title, s1..sN, end (narration.json).
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "_tools"))
from demo_kit import Demo, run  # noqa: E402

BASE = "http://localhost:5174"


async def storyboard(d: Demo):
    pg = d.pg
    await d.card("__TITLE__", "Subtitle", key="title")

    # 1 First step
    await d.done()
    await pg.goto(BASE + "/login")
    await d.cap("First step", "What the viewer should notice.")
    await d.type(pg.locator("input[type=email]"), os.environ.get("DEMO_EMAIL", ""))
    await d.type(pg.locator("input[type=password]"), os.environ["DEMO_PASSWORD"])
    await d.click(pg.locator("button[type=submit]"))
    await d.wait(1500)
    await d.shot("01")

    await d.card("Closing line", foot="UniQCAI · Digital Upshot", key="end")


run(storyboard, total_steps=1)

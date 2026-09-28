"""Shared recording kit for client videos.

A video's own `source/record.py` holds only its storyboard; everything else is here:
browser + video capture, step captions, highlight ring, visible cursor, pacing each
step to its narration line, and title/end cards.

    from demo_kit import Demo, run
    async def storyboard(d: Demo): ...
    run(storyboard, total_steps=10)

Run the storyboard from the video folder's `source/` directory (or anywhere: paths are
resolved from the record.py file). `--shots` does a dry pass that saves screenshots
into source/.work/dry/ instead of recording.
"""
import asyncio
import json
import pathlib
import sys
import time

from playwright.async_api import Page, async_playwright

TOOLS = pathlib.Path(__file__).parent
W, H = 1280, 720

CARD = """<html><body style="margin:0;height:100vh;display:flex;align-items:center;justify-content:center;
background:radial-gradient(circle at 30% 20%,#23338f,#0b1020 70%);font-family:Inter,sans-serif;color:#fff">
<div style="text-align:center;max-width:900px">
<div style="display:inline-flex;align-items:center;gap:14px;margin-bottom:30px">
<div style="width:56px;height:56px;border-radius:14px;background:#3b5bfd;display:flex;align-items:center;
justify-content:center;font-weight:800;font-size:22px">UQ</div>
<div style="font-weight:800;font-size:34px;letter-spacing:-.01em">UniQCAI</div></div>
<div style="font-weight:700;font-size:40px;line-height:1.2;letter-spacing:-.02em">{title}</div>
<div style="margin-top:18px;font-size:20px;color:#c7d0ff">{sub}</div>
<div style="margin-top:44px;font-size:14px;color:#8b95c9;letter-spacing:.14em;text-transform:uppercase">{foot}</div>
</div></body></html>"""


class Demo:
    def __init__(self, pg: Page, work: pathlib.Path, total: int, shots: bool):
        self.pg, self.work, self.total, self.shots = pg, work, total, shots
        durs = work / "narr" / "durations.json"
        # Without voice lines (e.g. a first dry pass) every line counts as 0 s.
        self.durs = json.loads(durs.read_text()) if durs.exists() else {}
        self.t0 = time.monotonic()
        self.marks, self.cur, self.n = [], {}, 0

    # ---- pacing -------------------------------------------------------------
    async def done(self, tail=0.5):
        """Hold the screen until the current narration line has finished."""
        if self.cur:
            end = self.cur["start"] + self.durs.get(self.cur["key"], 0) + tail
            left = end - (time.monotonic() - self.t0)
            if left > 0:
                await self.pg.wait_for_timeout(int(left * 1000))
            self.cur.clear()

    async def narrate(self, key):
        """Start narration line `key` (a key in source/narration.json) now."""
        await self.done()
        self.cur.update(key=key, start=time.monotonic() - self.t0)
        self.marks.append({"key": key, "t": round(self.cur["start"], 3)})

    # ---- on-screen annotations ---------------------------------------------
    async def cap(self, title, sub="", left=None, bottom=None, key=None):
        """Show 'Step n of N' caption and start its narration line (default key: s<n>)."""
        self.n += 1
        await self.narrate(key or f"s{self.n}")
        await self.pg.evaluate("a => window.__demoCaption(...a)",
                               [f"Step {self.n} of {self.total}", title, sub,
                                {"left": left, "bottom": bottom}])
        await self.wait(500)

    async def uncap(self):
        await self.pg.evaluate("() => window.__demoCaption('', '', '')")

    async def card(self, title, sub="", foot="Digital Upshot", key=None):
        """Full-screen title/end card, optionally narrated."""
        await self.done()
        await self.pg.set_content(CARD.format(title=title, sub=sub, foot=foot))
        await self.wait(650)
        if key:
            await self.narrate(key)

    async def ring(self, loc=None):
        box = await loc.bounding_box() if loc is not None else None
        await self.pg.evaluate("r => window.__demoRing(r)", box)

    # ---- pointer --------------------------------------------------------------
    async def move(self, loc):
        box = await loc.bounding_box()
        await self.pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=28)
        await self.wait(250)

    async def click(self, loc, highlight=True, pause=500):
        await loc.scroll_into_view_if_needed()
        if highlight:
            await self.ring(loc)
        await self.move(loc)
        await self.wait(pause)
        await self.ring(None)
        await loc.click()

    async def point(self, loc, hold=1600):
        """Ring an element and rest the cursor on it without clicking."""
        await loc.scroll_into_view_if_needed()
        await self.ring(loc)
        await self.move(loc)
        await self.wait(hold)
        await self.ring(None)

    async def type(self, loc, text, delay=40):
        await self.click(loc, highlight=False, pause=150)
        await loc.press_sequentially(text, delay=delay)

    async def scroll(self, dy, steps=12):
        for _ in range(steps):
            await self.pg.mouse.wheel(0, dy / steps)
            await self.wait(35)

    async def wait(self, ms):
        await self.pg.wait_for_timeout(ms)

    async def shot(self, name):
        if self.shots:
            (self.work / "dry").mkdir(parents=True, exist_ok=True)
            await self.pg.screenshot(path=str(self.work / "dry" / f"{name}.png"))


def run(storyboard, total_steps):
    """Record `storyboard(demo)` into <video>/source/.work/ (raw/*.webm + marks.json)."""
    source = pathlib.Path(sys.modules["__main__"].__file__).resolve().parent
    work = source / ".work"
    shots = "--shots" in sys.argv

    async def main():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            kw = dict(viewport={"width": W, "height": H}, device_scale_factor=1)
            if not shots:
                for old in (work / "raw").glob("*.webm"):
                    old.unlink()
                kw.update(record_video_dir=str(work / "raw"), record_video_size={"width": W, "height": H})
            ctx = await browser.new_context(**kw)
            await ctx.add_init_script(path=str(TOOLS / "overlay.js"))
            d = Demo(await ctx.new_page(), work, total_steps, shots)
            await storyboard(d)
            await d.done(tail=1.8)
            # A dry pass must not replace the timings build.py uses for the real take.
            out = work / "dry" if shots else work
            out.mkdir(parents=True, exist_ok=True)
            (out / "marks.json").write_text(json.dumps(d.marks, indent=1))
            await ctx.close()
            await browser.close()

    asyncio.run(main())

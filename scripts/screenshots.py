"""Capture README screenshots from the running TUI on sample data.

Usage: uv run python scripts/screenshots.py
Writes SVGs to docs/.
"""
import asyncio
import math
import pathlib
import time

from t212.api.mock import MockT212Client
from t212.app import T212App

DOCS = pathlib.Path(__file__).parent.parent / "docs"


def seed_equity_series(store, end_total: float) -> None:
    """A plausible 30-day curve ending at the sample account value."""
    now = int(time.time())
    n = 90
    for i in range(n):
        ts = now - (n - i) * 8 * 3600
        drift = (i / n) * 0.09
        wobble = (0.025 * math.sin(i / 7.0) + 0.012 * math.sin(i / 2.6)
                  + 0.006 * math.sin(i / 1.3))
        dip = -0.03 * math.exp(-((i - n * 0.55) ** 2) / 18)
        total = end_total * (0.91 + drift + wobble + dip)
        store.db.execute(
            "INSERT OR REPLACE INTO equity_snapshots VALUES (?,?,?,?,?,?,?)",
            (ts, total, 312.40, 23190.84, total - 23190.84, 430.11, "GBP"))
    store.db.commit()


async def capture(size, shots) -> None:
    app = T212App(client=MockT212Client(), environment="live", currency="GBP")
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        await app.do_refresh()
        seed_equity_series(app.store, 24813.07)
        await app.load_history_caches()
        await app.load_pie_names([p.id for p in await app.client.pies()])
        await app.do_refresh()
        await pilot.pause()
        for name, keys in shots:
            for key in keys:
                await pilot.press(key)
                await pilot.pause()
            await pilot.pause()
            app.save_screenshot(str(DOCS / f"{name}.svg"))


def svgs_to_pngs() -> None:
    """Render the SVGs to PNG with Chromium so they look identical everywhere."""
    from playwright.sync_api import sync_playwright
    import re

    cached = sorted(pathlib.Path.home().glob(
        "Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-mac-arm64/chrome-headless-shell"))
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=str(cached[-1]) if cached else None)
        for svg in sorted(DOCS.glob("*.svg")):
            head = svg.read_text()[:200]
            vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', head)
            w, h = int(float(vb.group(1))), int(float(vb.group(2)))
            page = browser.new_page(viewport={"width": w, "height": h},
                                    device_scale_factor=2)
            page.goto(svg.resolve().as_uri())
            page.wait_for_timeout(700)          # let the webfont load
            page.screenshot(path=str(svg.with_suffix(".png")), omit_background=True)
            page.close()
        browser.close()


async def capture_all() -> None:
    DOCS.mkdir(exist_ok=True)
    await capture((110, 50), [("dashboard", [])])
    await capture((110, 24), [
        ("positions", ["2"]),
        ("pies", ["3"]),
        ("history", ["4"]),
        ("help", ["question_mark"]),
    ])


if __name__ == "__main__":
    asyncio.run(capture_all())
    svgs_to_pngs()
    for svg in DOCS.glob("*.svg"):
        svg.unlink()
    print("written:", ", ".join(p.name for p in sorted(DOCS.glob("*.png"))))

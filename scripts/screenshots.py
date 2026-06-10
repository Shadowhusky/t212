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
    n = 60
    for i in range(n):
        ts = now - (n - i) * 12 * 3600
        drift = (i / n) * 0.06
        wobble = 0.012 * math.sin(i / 4.5) + 0.006 * math.sin(i / 1.7)
        total = end_total * (0.94 + drift + wobble)
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


async def main() -> None:
    DOCS.mkdir(exist_ok=True)
    await capture((110, 49), [("dashboard", [])])
    await capture((110, 24), [
        ("positions", ["2"]),
        ("pies", ["3"]),
        ("history", ["4"]),
        ("help", ["question_mark"]),
    ])
    print("written:", ", ".join(p.name for p in sorted(DOCS.glob("*.svg"))))


if __name__ == "__main__":
    asyncio.run(main())

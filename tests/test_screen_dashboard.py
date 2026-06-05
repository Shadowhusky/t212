import pathlib
from textual.widgets import Static
from t212.app import T212App
from t212.api.mock import MockT212Client
from t212.widgets.summary_header import SummaryHeader

FIX = pathlib.Path(__file__).parent / "fixtures"


def _plain(widget) -> str:
    v = widget.visual
    return v.plain if hasattr(v, "plain") else str(v)


async def test_dashboard_shows_value_and_pnl():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.do_refresh()
        await pilot.pause()
        assert "£24,813.07" in _plain(app.query_one(SummaryHeader))
        assert "+£1,204.33" in _plain(app.query_one("#dash-metrics", Static))


async def test_dashboard_renders_equity_when_points_exist():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.do_refresh()
        # Insert a second snapshot at a distinct timestamp to guarantee >=2 rows.
        app.store.db.execute(
            "INSERT OR REPLACE INTO equity_snapshots VALUES (?,?,?,?,?,?,?)",
            (1, 24000.0, 1000.0, 23000.0, 0.0, 0.0, "GBP"))
        app.store.db.commit()
        await app.do_refresh()
        await pilot.pause()
        text = _plain(app.query_one("#dash-metrics", Static))
        assert "EQUITY" in text

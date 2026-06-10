from textual.widgets import Static
from t212.api.base import ScopeError
from t212.app import T212App
from t212.api.mock import MockT212Client
from t212.widgets.summary_header import SummaryHeader

from t212.api.mock import SAMPLE_DIR as FIX


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


async def test_dashboard_orders_scope_hint():
    class NoOrdersScope(MockT212Client):
        async def orders(self):
            raise ScopeError("missing scope")
    app = T212App(client=NoOrdersScope(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await app.do_refresh()
        await pilot.pause()
        text = _plain(app.query_one("#dash-metrics", Static))
        assert "enable the 'Orders' scope" in text


async def test_dashboard_pending_orders_listed():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await app.do_refresh()
        await pilot.pause()
        text = _plain(app.query_one("#dash-metrics", Static))
        assert "PENDING ORDERS" in text
        assert "BUY LIMIT AAPL 2 @ 180.00" in text
        assert "SELL STOP TSLA 4 stop 220.00" in text


async def test_dashboard_income_and_deposits():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await app.do_refresh()
        await app.load_history_caches()
        await pilot.pause()
        text = _plain(app.query_one("#dash-metrics", Static))
        assert "Dividends   £16.30" in text
        assert "Interest    £1.95" in text
        assert "Net deposits £1,300.00" in text
        # account vs net deposits: 24813.07 - 1300 = +23,513.07
        assert "+£23,513.07" in text


async def test_dashboard_pies_strip():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await app.do_refresh()
        await app.load_pie_names([42])
        await pilot.pause()
        text = _plain(app.query_one("#dash-metrics", Static))
        assert "PIES" in text
        assert "Growth Pie" in text

import pathlib
from t212.app import T212App
from t212.api.mock import MockT212Client
from textual.widgets import DataTable

FIX = pathlib.Path(__file__).parent / "fixtures"

async def test_history_orders_and_section_switch():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await pilot.pause()
        hist = app.query_one("#history")
        await hist.load_section("orders")
        await pilot.pause()
        table = app.query_one("#history-table", DataTable)
        assert table.row_count == 2
        row = [str(c) for c in table.get_row_at(0)]
        assert "AAPL" in row[1] and "BUY" in row[2]
        await hist.load_section("dividends")
        await pilot.pause()
        table = app.query_one("#history-table", DataTable)
        assert table.row_count == 3
        last = [str(c) for c in table.get_row_at(2)]
        assert "Cash interest" in last[1]

async def test_history_orders_realized_pnl_and_fees():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await pilot.pause()
        hist = app.query_one("#history")
        await hist.load_section("orders")
        await pilot.pause()
        table = app.query_one("#history-table", DataTable)
        labels = [str(c.label) for c in table.columns.values()]
        assert "REAL.P&L" in labels and "FEES" in labels
        tsla = [str(c) for c in table.get_row_at(1)]
        assert any("+£18.40" in c for c in tsla)
        assert any("£1.20" in c for c in tsla)
        stats = app.query_one("#history-stats").visual.plain
        assert "2 orders" in stats and "£1.76" in stats
        # fixture has a nextPagePath → load-more hint visible
        assert "load more" in app.query_one("#history-more").visual.plain

async def test_history_load_more_clears_hint():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await pilot.pause()
        hist = app.query_one("#history")
        await hist.load_section("orders")
        await hist.load_more()   # mock get_page returns no items, no next path
        await pilot.pause()
        assert app.query_one("#history-table", DataTable).row_count == 2
        assert app.query_one("#history-more").visual.plain == ""

async def test_history_dividend_and_transaction_stats():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await pilot.pause()
        hist = app.query_one("#history")
        await hist.load_section("dividends")
        await pilot.pause()
        assert "total received £18.25" in app.query_one("#history-stats").visual.plain
        await hist.load_section("transactions")
        await pilot.pause()
        assert "net deposits £1,300.00" in app.query_one("#history-stats").visual.plain

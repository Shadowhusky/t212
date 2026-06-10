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

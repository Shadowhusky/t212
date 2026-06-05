import pathlib
from t212.app import T212App
from t212.api.mock import MockT212Client
from textual.widgets import DataTable

FIX = pathlib.Path(__file__).parent / "fixtures"

async def test_positions_table_populates_and_sorts():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await app.do_refresh()
        await pilot.press("2")
        await pilot.pause()
        table = app.query_one("#positions-table", DataTable)
        assert table.row_count == 3
        cells = [table.get_row_at(r)[0] for r in range(table.row_count)]
        assert any("AAPL" in str(c) for c in cells)

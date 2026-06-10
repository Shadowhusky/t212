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

async def test_positions_fx_column_and_pie_marker():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test(size=(120, 40)) as pilot:
        await app.do_refresh()
        await pilot.press("2")
        await pilot.pause()
        table = app.query_one("#positions-table", DataTable)
        labels = [str(c.label) for c in table.columns.values()]
        assert "FX" in labels
        rows = [[str(c) for c in table.get_row_at(r)] for r in range(table.row_count)]
        aapl = next(r for r in rows if "AAPL" in r[0])
        assert any("£2.10" in c for c in aapl)
        tsla = next(r for r in rows if "TSLA" in r[0])
        assert "◔" in tsla[2]

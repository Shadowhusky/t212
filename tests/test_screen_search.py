import pathlib
from t212.app import T212App
from t212.api.mock import MockT212Client
from textual.widgets import DataTable

FIX = pathlib.Path(__file__).parent / "fixtures"

async def test_search_filters_universe():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await app.do_refresh()                       # builds resolver
        search = app.query_one("#search")
        search.set_universe(await app.client.instruments())
        search.set_query("apple")
        await pilot.pause()
        table = app.query_one("#search-table", DataTable)
        assert table.row_count == 1
        assert "AAPL" in str(table.get_row_at(0)[0])

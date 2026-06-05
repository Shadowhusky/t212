import pathlib
from t212.app import T212App
from t212.api.mock import MockT212Client
from textual.widgets import DataTable

FIX = pathlib.Path(__file__).parent / "fixtures"

async def test_pies_list_and_open_detail():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        app.scheduler.set_active("pies")
        await app.do_refresh()
        await pilot.press("3")
        await pilot.pause()
        table = app.query_one("#pies-table", DataTable)
        assert table.row_count == 1
        table.focus()
        table.move_cursor(row=0)
        await pilot.press("enter")
        await pilot.pause()
        assert app.screen.query_one("#pie-instruments", DataTable).row_count == 2

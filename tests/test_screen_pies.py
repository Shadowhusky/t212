from t212.app import T212App
from t212.api.mock import MockT212Client
from textual.widgets import DataTable

from t212.api.mock import SAMPLE_DIR as FIX

async def test_pies_list_and_open_detail():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        app.scheduler.set_active("pies")
        await app.do_refresh()
        await pilot.press("3")
        await pilot.pause()
        table = app.query_one("#pies-table", DataTable)
        assert table.row_count == 2
        table.focus()
        table.move_cursor(row=0)
        await pilot.press("enter")
        await pilot.pause()
        assert app.screen.query_one("#pie-instruments", DataTable).row_count == 2

async def test_pies_show_real_names_after_cache_fill():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        app.scheduler.set_active("pies")
        await app.do_refresh()
        await app.load_pie_names([42])
        await pilot.pause()
        table = app.query_one("#pies-table", DataTable)
        names = [str(table.get_row_at(r)[0]) for r in range(table.row_count)]
        assert "Growth Pie" in names

async def test_pie_detail_shows_settings_and_issues():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        app.scheduler.set_active("pies")
        await app.do_refresh()
        await pilot.press("3")
        await pilot.pause()
        table = app.query_one("#pies-table", DataTable)
        table.focus()
        table.move_cursor(row=0)
        await pilot.press("enter")
        await pilot.pause()
        inst = app.screen.query_one("#pie-instruments", DataTable)
        issues = [str(inst.get_row_at(r)[-1]) for r in range(inst.row_count)]
        assert any("APPROACHING_MAX_POSITION_SIZE" in s for s in issues)
        header = app.screen.query_one("#pie-header").visual.plain
        assert "Growth Pie" in header and "AHEAD" in header
        settings = app.screen.query_one("#pie-settings").visual.plain
        assert "REINVEST" in settings and "£10,500.00" in settings

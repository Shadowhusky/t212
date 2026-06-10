import pathlib
from t212.app import T212App
from t212.screens.help import HelpScreen
from t212.widgets.summary_header import SummaryHeader
from t212.widgets.tabbar import TabBar

FIX = pathlib.Path(__file__).parent / "fixtures"

def make_app():
    from t212.api.mock import MockT212Client
    return T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")

async def test_tabs_switch_screens():
    app = make_app()
    async with app.run_test() as pilot:
        await pilot.press("2")
        assert app.active_tab == "positions"
        await pilot.press("3")
        assert app.active_tab == "pies"
        await pilot.press("1")
        assert app.active_tab == "dashboard"

async def test_privacy_toggle():
    app = make_app()
    async with app.run_test() as pilot:
        assert app.privacy is False
        await pilot.press("z")
        assert app.privacy is True

async def test_theme_cycles():
    app = make_app()
    async with app.run_test() as pilot:
        first = app.theme
        await pilot.press("t")
        assert app.theme != first

async def test_tabbar_shows_active_tab():
    app = make_app()
    async with app.run_test() as pilot:
        await pilot.press("3")
        assert app.active_tab == "pies"
        text = app.query_one(TabBar).visual.plain
        assert "3 Pies" in text
        for label in ("Dashboard", "Positions", "Pies", "History", "Search"):
            assert label in text

async def test_help_modal_opens_and_closes():
    app = make_app()
    async with app.run_test() as pilot:
        await pilot.press("question_mark")
        assert isinstance(app.screen, HelpScreen)
        assert "read-only" in app.screen.query_one("#help-body").visual.plain
        await pilot.press("escape")
        assert not isinstance(app.screen, HelpScreen)

async def test_help_modal_toggles_with_question_mark():
    app = make_app()
    async with app.run_test() as pilot:
        await pilot.press("question_mark")
        assert isinstance(app.screen, HelpScreen)
        await pilot.press("question_mark")
        assert not isinstance(app.screen, HelpScreen)

async def test_tab_switch_focuses_primary_widget():
    from textual.widgets import DataTable
    app = make_app()
    async with app.run_test() as pilot:
        await app.do_refresh()
        await pilot.press("2")
        await pilot.pause()
        table = app.query_one("#positions-table", DataTable)
        assert app.focused is table
        before = table.cursor_row
        await pilot.press("j")
        assert table.cursor_row == before + 1
        await pilot.press("k")
        assert table.cursor_row == before
        await pilot.press("down")
        assert table.cursor_row == before + 1
        await pilot.press("4")
        await pilot.pause()
        assert app.focused is app.query_one("#history-table")
        await pilot.press("5")
        await pilot.pause()
        assert app.focused is app.query_one("#search-input")

async def test_refresh_key_gives_feedback():
    app = make_app()
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("r")
        await app.workers.wait_for_complete()
        await pilot.pause()
        msgs = [n.message for n in app._notifications]
        assert "Refreshing…" in msgs
        assert "Refreshed" in msgs
        assert "● live" in app.query_one(SummaryHeader).visual.plain

async def test_privacy_marker_in_header():
    app = make_app()
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("z")
        assert "◌ private" in app.query_one(SummaryHeader).visual.plain
        await pilot.press("z")
        assert "◌ private" not in app.query_one(SummaryHeader).visual.plain

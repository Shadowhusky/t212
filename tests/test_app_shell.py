import pathlib
from t212.app import T212App

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

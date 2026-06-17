from textual.widgets import Static
from t212.app import T212App
from t212.api.mock import MockT212Client
from t212.screens.focus import FocusScreen


def _plain(w) -> str:
    v = w.visual
    return v.plain if hasattr(v, "plain") else str(v)


async def test_focus_toggles_and_renders():
    app = T212App(client=MockT212Client(), environment="demo", currency="GBP")
    async with app.run_test(size=(110, 32)) as pilot:
        await app.do_refresh()
        await pilot.press("f")
        await pilot.pause()
        await pilot.pause()                       # extra render pass: guards the _render shadow regression
        assert isinstance(app.screen, FocusScreen)
        body = _plain(app.screen.query_one("#focus-body", Static))
        assert "focus mode" in body
        assert "still tracking" in body
        # no financial data leaks into focus mode
        assert "£" not in body and "P&L" not in body
        await pilot.press("f")
        await pilot.pause()
        assert not isinstance(app.screen, FocusScreen)


async def test_focus_escape_resumes():
    app = T212App(client=MockT212Client(), environment="demo", currency="GBP")
    async with app.run_test(size=(110, 32)) as pilot:
        await app.do_refresh()
        await pilot.press("f")
        await pilot.pause()
        assert isinstance(app.screen, FocusScreen)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, FocusScreen)

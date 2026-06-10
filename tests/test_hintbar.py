import pathlib
from t212.app import T212App
from t212.api.mock import MockT212Client
from t212.widgets.hintbar import HintBar

FIX = pathlib.Path(__file__).parent / "fixtures"

def make_app():
    return T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")

async def test_history_hints_include_more_when_available():
    app = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.query_one(HintBar)
        bar.set_context("history", width=200, has_more=True)
        text = bar.visual.plain
        assert "m more" in text and "←→ section" in text
        bar.set_context("history", width=200, has_more=False)
        assert "m more" not in bar.visual.plain

async def test_narrow_width_drops_low_priority_hints():
    app = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.query_one(HintBar)
        bar.set_context("dashboard", width=40)
        text = bar.visual.plain
        assert "t theme" not in text
        assert "q quit" in text
        bar.set_context("dashboard", width=200)
        assert "t theme" in bar.visual.plain

async def test_hintbar_follows_active_tab():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        bar = app.query_one(HintBar)
        assert "q quit" in bar.visual.plain
        assert "s sort" not in bar.visual.plain
        await pilot.press("2")
        await pilot.pause()
        assert "s sort" in bar.visual.plain
        await pilot.press("4")
        await app.workers.wait_for_complete()
        await pilot.pause()
        text = bar.visual.plain
        assert "←→ section" in text and "m more" in text

async def test_hintbar_clears_more_after_last_page():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("4")
        await app.workers.wait_for_complete()
        await pilot.press("m")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert "m more" not in app.query_one(HintBar).visual.plain

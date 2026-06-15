from textual.widgets import DataTable

from t212.api.mock import MockT212Client, SAMPLE_DIR as FIX
from t212.app import T212App
from t212.scheduler import RefreshScheduler
from t212.screens.instrument_detail import InstrumentDetail
from t212.screens.pie_detail import PieDetailScreen
from t212.screens.position_detail import PositionDetail


def make_app(client=None, scheduler=None):
    return T212App(client=client or MockT212Client(FIX), environment="demo",
                   currency="GBP", scheduler=scheduler)


async def _open_position_detail(app, pilot):
    await app.do_refresh()
    await pilot.press("2")
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


async def _open_instrument_detail(app, pilot):
    await app.do_refresh()
    search = app.query_one("#search")
    search.set_universe(await app.client.instruments())
    search.set_query("apple")
    await pilot.pause()
    table = app.query_one("#search-table", DataTable)
    table.focus()
    table.move_cursor(row=0)
    await pilot.press("enter")
    await pilot.pause()


async def _open_pie_detail(app, pilot):
    app.scheduler.set_active("pies")
    await app.do_refresh()
    await pilot.press("3")
    await pilot.pause()
    table = app.query_one("#pies-table", DataTable)
    table.focus()
    table.move_cursor(row=0)
    await pilot.press("enter")
    await pilot.pause()


async def test_position_detail_keeps_focus_inside_modal():
    app = make_app()
    async with app.run_test() as pilot:
        await _open_position_detail(app, pilot)
        assert isinstance(app.screen, PositionDetail)
        assert app.focused is not None
        assert app.focused.screen is app.screen


async def test_instrument_detail_keeps_focus_inside_modal():
    app = make_app()
    async with app.run_test() as pilot:
        await _open_instrument_detail(app, pilot)
        assert isinstance(app.screen, InstrumentDetail)
        assert app.focused is not None
        assert app.focused.screen is app.screen


async def test_pie_detail_keeps_focus_inside_modal():
    app = make_app()
    async with app.run_test() as pilot:
        await _open_pie_detail(app, pilot)
        assert isinstance(app.screen, PieDetailScreen)
        assert app.focused is not None
        assert app.focused.screen is app.screen


async def test_position_detail_dismisses_on_escape():
    app = make_app()
    async with app.run_test() as pilot:
        await _open_position_detail(app, pilot)
        assert isinstance(app.screen, PositionDetail)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, PositionDetail)


async def test_modal_shows_scroll_hint():
    app = make_app()
    async with app.run_test() as pilot:
        await _open_position_detail(app, pilot)
        assert "esc back" in app.screen.query_one("#modal-hint").visual.plain


async def test_header_shows_total_open_pnl_and_today():
    app = make_app()
    async with app.run_test():
        await app.do_refresh()
        from t212.widgets.summary_header import SummaryHeader
        text = app.query_one(SummaryHeader).visual.plain
        assert "+£1,204.33" in text
        assert "+5.19%" in text
        assert "Today" in text
        assert text.index("P&L") < text.index("Today")


async def test_positions_chrome_shows_open_pnl():
    app = make_app()
    async with app.run_test() as pilot:
        await app.do_refresh()
        await pilot.press("2")
        await pilot.pause()
        chrome = app.query_one("#positions-chrome").visual.plain
        assert "open P&L" in chrome
        assert "+£1,204.33" in chrome


async def test_base_not_repainted_while_modal_open():
    t = [0.0]
    sched = RefreshScheduler(MockT212Client(FIX), clock=lambda: t[0])
    app = make_app(scheduler=sched)
    async with app.run_test() as pilot:
        await _open_position_detail(app, pilot)
        assert isinstance(app.screen, PositionDetail)
        pos = app.query_one("#positions")
        calls = []
        orig = pos.update_data
        pos.update_data = lambda **kw: calls.append(1) or orig(**kw)
        t[0] = 60.0
        app.scheduler.refresh_now()
        await app.do_refresh()
        assert calls == []
        assert app._base_dirty is True
        body = app.screen.query_one("#position-detail-body").visual.plain
        assert "Apple" in body or "AAPL" in body
        await pilot.press("escape")
        await pilot.pause()
        calls.clear()
        t[0] = 120.0
        app.scheduler.refresh_now()
        await app.do_refresh()
        assert calls != []
        assert app._base_dirty is False


class ShiftingValueClient(MockT212Client):
    def __init__(self, fixtures=FIX):
        super().__init__(fixtures)
        self.up = False

    async def positions(self):
        ps = await super().positions()
        if self.up:
            for p in ps:
                p.wallet.current_value += 100.0
        return ps


async def test_position_detail_shows_today_change():
    from t212.store import Store
    t = [1_700_000_000.0]
    c = ShiftingValueClient()
    sched = RefreshScheduler(c, clock=lambda: t[0] - 1_700_000_000.0)
    store = Store(":memory:", throttle_seconds=0, clock=lambda: t[0])
    app = T212App(client=c, environment="demo", currency="GBP",
                  scheduler=sched, store=store)
    async with app.run_test() as pilot:
        await app.do_refresh()
        c.up = True
        t[0] += 60.0
        app.scheduler.refresh_now()
        await app.do_refresh()
        await pilot.press("2")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        body = app.screen.query_one("#position-detail-body").visual.plain
        assert "Today" in body
        assert "+£100.00" in body


class ShiftingPriceClient(MockT212Client):
    def __init__(self, fixtures=FIX):
        super().__init__(fixtures)
        self.shifted = False

    async def positions(self):
        ps = await super().positions()
        if self.shifted:
            for p in ps:
                p.current_price = 999.99
        return ps


async def test_position_detail_updates_live_while_open():
    c = ShiftingPriceClient()
    t = [0.0]
    sched = RefreshScheduler(c, clock=lambda: t[0])
    app = make_app(client=c, scheduler=sched)
    async with app.run_test() as pilot:
        await _open_position_detail(app, pilot)
        assert isinstance(app.screen, PositionDetail)
        body = app.screen.query_one("#position-detail-body").visual.plain
        assert "999.99" not in body
        c.shifted = True
        t[0] = 60.0
        app.scheduler.refresh_now()
        await app.do_refresh()
        await pilot.pause()
        body = app.screen.query_one("#position-detail-body").visual.plain
        assert "999.99" in body

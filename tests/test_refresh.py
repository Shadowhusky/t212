import asyncio

from textual.widgets import DataTable

from t212.api.mock import MockT212Client, SAMPLE_DIR as FIX
from t212.app import T212App
from t212.scheduler import RefreshScheduler
from t212.screens.position_detail import PositionDetail


def make_app(client=None, scheduler=None):
    return T212App(client=client or MockT212Client(FIX), environment="demo",
                   currency="GBP", scheduler=scheduler)


async def test_tick_overlap_guard_runs_single_refresh():
    app = make_app()
    async with app.run_test():
        await app.workers.wait_for_complete()
        calls = []

        async def slow_refresh():
            calls.append(1)
            await asyncio.sleep(0.05)

        app.do_refresh = slow_refresh
        await asyncio.gather(app._tick(), app._tick())
        assert len(calls) == 1


async def test_no_table_rebuild_when_nothing_due():
    app = make_app()
    async with app.run_test():
        await app.do_refresh()
        await app.workers.wait_for_complete()
        pos = app.query_one("#positions")
        calls = []
        orig = pos.update_data
        pos.update_data = lambda **kw: calls.append(1) or orig(**kw)
        await app.do_refresh()
        assert calls == []


async def test_positions_cursor_preserved_on_rebuild():
    app = make_app()
    async with app.run_test() as pilot:
        await app.do_refresh()
        await pilot.press("2")
        await pilot.pause()
        table = app.query_one("#positions-table", DataTable)
        table.move_cursor(row=2)
        pos = app.query_one("#positions")
        total = sum(p.market_value for p in app._positions) + app._free
        pos.update_data(positions=app._positions, resolver=app.resolver,
                        currency=app.currency, total_value=total, privacy=False)
        assert table.cursor_row == 2


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


async def test_position_detail_updates_live():
    c = ShiftingPriceClient()
    t = [0.0]
    sched = RefreshScheduler(c, clock=lambda: t[0])
    app = make_app(client=c, scheduler=sched)
    async with app.run_test() as pilot:
        await app.do_refresh()
        await pilot.press("2")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
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

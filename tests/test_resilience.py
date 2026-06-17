import asyncio

import httpx
import pytest
from textual.widgets import DataTable

from t212.api.base import ApiError
from t212.api.http import HttpT212Client
from t212.api.mock import MockT212Client, SAMPLE_DIR as FIX
from t212.api.ratelimit import RateLimitGovernor
from t212.api.limits import RATE_LIMITS
from t212.app import T212App
from t212.scheduler import RefreshScheduler
from t212.screens.position_detail import PositionDetail


def make_app(client=None, scheduler=None):
    return T212App(client=client or MockT212Client(FIX), environment="demo",
                   currency="GBP", scheduler=scheduler)


class FlakyHistoryClient(MockT212Client):
    def __init__(self, fixtures=FIX):
        super().__init__(fixtures)
        self.fail_orders = True

    async def history_orders(self, cursor=None, ticker=None):
        if self.fail_orders:
            raise ApiError("boom")
        return await super().history_orders(cursor, ticker)


async def test_flaky_history_does_not_crash_and_shows_retry_row():
    c = FlakyHistoryClient()
    app = make_app(client=c)
    async with app.run_test() as pilot:
        await pilot.press("4")
        await pilot.pause()
        await pilot.pause()
        assert app.is_running
        table = app.query_one("#history-table", DataTable)
        cells = [str(table.get_cell_at((r, 0))) for r in range(table.row_count)]
        assert any("couldn't load" in cell for cell in cells)


async def test_history_recovers_after_flaky_load():
    c = FlakyHistoryClient()
    app = make_app(client=c)
    async with app.run_test() as pilot:
        await pilot.press("4")
        await pilot.pause()
        hist = app.query_one("#history")
        c.fail_orders = False
        await hist.load_section("orders")
        await pilot.pause()
        table = app.query_one("#history-table", DataTable)
        assert table.row_count == 2
        assert any("AAPL" in str(table.get_cell_at((r, 1)))
                   for r in range(table.row_count))


async def test_spawn_swallows_worker_exceptions():
    app = make_app()
    async with app.run_test() as pilot:
        async def boom():
            raise RuntimeError("kaboom")

        app._spawn(boom(), name="boom-test")
        await pilot.pause()
        await app.workers.wait_for_complete()
        assert app.is_running


async def test_tick_never_crashes_on_refresh_error():
    app = make_app()
    async with app.run_test() as pilot:
        await app.do_refresh()

        async def bad_refresh():
            raise RuntimeError("dispatch bug")

        app.do_refresh = bad_refresh
        await app._tick()
        assert app._refresh_running is False
        assert app.is_running


# --- forgiving status (scheduler) ---

class FullFailClient(MockT212Client):
    def __init__(self, fixtures=FIX):
        super().__init__(fixtures)
        self.fail = True

    async def summary(self):
        if self.fail:
            raise ApiError("boom")
        return await super().summary()

    async def positions(self):
        if self.fail:
            raise ApiError("boom")
        return await super().positions()


async def test_forgiving_status_two_consecutive_failures():
    c = FullFailClient()
    t = [0.0]
    sched = RefreshScheduler(c, clock=lambda: t[0])
    sched.set_active("positions")
    await sched.poll_once()
    assert sched.degraded is False
    t[0] = 10.0
    await sched.poll_once()
    assert sched.degraded is True
    c.fail = False
    t[0] = 20.0
    await sched.poll_once()
    assert sched.degraded is False
    assert sched.consecutive_failures == 0


# --- HTTP single-retry ---

def make_http(handler):
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(base_url="https://live.trading212.com",
                             headers={"Authorization": "KEY"}, transport=transport)
    return HttpT212Client(api_key="KEY", base_url="https://live.trading212.com",
                          governor=RateLimitGovernor(RATE_LIMITS), client=http)


SUMMARY = {"id": 1, "currency": "GBP", "totalValue": 2.0,
           "cash": {"availableToTrade": 1.0},
           "investments": {"totalCost": 1.0, "unrealizedProfitLoss": 0.5}}


async def test_http_retries_once_on_transient_then_succeeds():
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("dropped", request=req)
        return httpx.Response(200, json=SUMMARY)

    c = make_http(handler)
    s = await c.summary()
    assert s.total_value == 2.0
    assert calls["n"] == 2


async def test_http_retries_once_on_5xx_then_succeeds():
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={})
        return httpx.Response(200, json=SUMMARY)

    c = make_http(handler)
    s = await c.summary()
    assert s.total_value == 2.0
    assert calls["n"] == 2


async def test_http_raises_api_error_when_retry_also_fails():
    def handler(req):
        raise httpx.ConnectTimeout("timeout", request=req)

    c = make_http(handler)
    with pytest.raises(ApiError):
        await c.summary()


# --- modal privacy toggle ---

async def _open_position_detail(app, pilot):
    await app.do_refresh()
    await pilot.press("2")
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


async def test_privacy_toggles_inside_position_detail_modal():
    app = make_app()
    async with app.run_test() as pilot:
        await _open_position_detail(app, pilot)
        assert isinstance(app.screen, PositionDetail)
        assert app.privacy is False
        await pilot.press("z")
        await pilot.pause()
        assert app.privacy is True
        body = app.screen.query_one("#position-detail-body").visual.plain
        assert "••••" in body
        await pilot.press("z")
        await pilot.pause()
        assert app.privacy is False
        body = app.screen.query_one("#position-detail-body").visual.plain
        assert "••••" not in body

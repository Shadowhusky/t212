from t212.api.base import ScopeError
from t212.api.mock import MockT212Client
from t212.scheduler import needs_for_tab, RefreshScheduler

from t212.api.mock import SAMPLE_DIR as FIX


class CountingClient(MockT212Client):
    def __init__(self, fixtures=FIX):
        super().__init__(fixtures)
        self.calls: dict[str, int] = {}

    def _count(self, name):
        self.calls[name] = self.calls.get(name, 0) + 1

    async def summary(self):
        self._count("summary")
        return await super().summary()

    async def positions(self):
        self._count("positions")
        return await super().positions()

    async def orders(self):
        self._count("orders")
        return await super().orders()

    async def pies(self):
        self._count("pies")
        return await super().pies()


def make(client=None, tab="dashboard"):
    t = [0.0]
    sched = RefreshScheduler(client or CountingClient(), clock=lambda: t[0])
    sched.set_active(tab)
    return sched, t


def test_needs_for_tab():
    assert "summary" in needs_for_tab("dashboard") and "positions" in needs_for_tab("dashboard")
    assert "orders" in needs_for_tab("dashboard")
    assert "pies" in needs_for_tab("pies")
    assert "instruments" in needs_for_tab("search")
    assert "summary" in needs_for_tab("history")


async def test_scheduler_poll_once_collects_active_data():
    sched, _ = make(MockT212Client(FIX), tab="positions")
    data = await sched.poll_once()
    assert "positions" in data and data["positions"][0].ticker in {"VUSA_GB_EQ", "AAPL_US_EQ", "TSLA_US_EQ"}


async def test_first_poll_fetches_all_needed():
    sched, _ = make()
    await sched.poll_once()
    assert sched.last_fetched == needs_for_tab("dashboard")


async def test_immediate_second_poll_fetches_nothing():
    c = CountingClient()
    sched, _ = make(c)
    await sched.poll_once()
    data = await sched.poll_once()
    assert sched.last_fetched == set()
    assert c.calls["summary"] == 1 and c.calls["pies"] == 1
    assert "summary" in data and "positions" in data


async def test_cadences_stagger_fetches():
    sched, t = make()
    await sched.poll_once()
    t[0] = 3.5
    await sched.poll_once()
    assert sched.last_fetched == {"positions"}
    t[0] = 7.0
    await sched.poll_once()
    assert sched.last_fetched == {"positions", "summary"}
    t[0] = 40.0
    await sched.poll_once()
    assert sched.last_fetched == {"summary", "positions", "orders", "pies"}


async def test_refresh_now_forces_past_cadence_but_not_hard_floor():
    sched, t = make()
    await sched.poll_once()
    t[0] = 2.0
    sched.refresh_now()
    await sched.poll_once()
    # only positions (hard floor 1s) may go; summary/orders (5s) and pies (30s) must wait
    assert sched.last_fetched == {"positions"}
    t[0] = 5.5
    await sched.poll_once()
    # summary cadence is 6s — fetched at 5.5 only because it was forced
    assert sched.last_fetched == {"positions", "summary", "orders"}


async def test_scope_error_recorded_without_busy_loop():
    class NoOrdersScope(CountingClient):
        async def orders(self):
            self._count("orders")
            raise ScopeError("API key missing a required scope for this endpoint")
    c = NoOrdersScope()
    sched, _ = make(c)
    data = await sched.poll_once()
    assert "orders" in sched.scope_errors
    assert sched.last_error is None
    assert "orders" not in data
    assert "summary" in data and "positions" in data
    await sched.poll_once()
    assert c.calls["orders"] == 1


class Flaky(CountingClient):
    def __init__(self, fixtures=FIX):
        super().__init__(fixtures)
        self.fail = False

    async def positions(self):
        self._count("positions")
        if self.fail:
            raise RuntimeError("boom")
        return await super().positions()


async def test_scheduler_keeps_last_good_on_error():
    c = Flaky()
    sched, t = make(c, tab="positions")
    await sched.poll_once()
    c.fail = True
    t[0] = 10.0
    data = await sched.poll_once()
    assert "positions" in data
    assert sched.last_error is not None


async def test_failed_fetch_waits_for_cadence_before_retry():
    c = Flaky()
    sched, t = make(c, tab="positions")
    c.fail = True
    await sched.poll_once()
    n = c.calls["positions"]
    await sched.poll_once()
    assert c.calls["positions"] == n  # not hammering while inside cadence
    t[0] = 3.0
    await sched.poll_once()
    assert c.calls["positions"] == n + 1


async def test_scheduler_clears_error_on_recovery():
    c = Flaky()
    sched, t = make(c, tab="positions")
    c.fail = True
    await sched.poll_once()
    assert sched.last_error is not None
    t[0] = 1.0
    await sched.poll_once()  # nothing due → must not clear the error
    assert sched.last_error is not None
    c.fail = False
    t[0] = 10.0
    await sched.poll_once()
    assert sched.last_error is None

from t212.api.base import ScopeError
from t212.api.mock import MockT212Client
from t212.scheduler import needs_for_tab, RefreshScheduler

from t212.api.mock import SAMPLE_DIR as FIX

def test_needs_for_tab():
    assert "summary" in needs_for_tab("dashboard") and "positions" in needs_for_tab("dashboard")
    assert "orders" in needs_for_tab("dashboard")
    assert "pies" in needs_for_tab("pies")
    assert "instruments" in needs_for_tab("search")
    assert "summary" in needs_for_tab("history")

async def test_scheduler_poll_once_collects_active_data():
    sched = RefreshScheduler(MockT212Client(FIX))
    sched.set_active("positions")
    data = await sched.poll_once()
    assert "positions" in data and data["positions"][0].ticker in {"VUSA_GB_EQ", "AAPL_US_EQ", "TSLA_US_EQ"}

async def test_scheduler_keeps_last_good_on_error():
    class Flaky(MockT212Client):
        def __init__(self, d): super().__init__(d); self.fail = False
        async def positions(self):
            if self.fail:
                raise RuntimeError("boom")
            return await super().positions()
    c = Flaky(FIX)
    sched = RefreshScheduler(c)
    sched.set_active("positions")
    await sched.poll_once()
    c.fail = True
    data = await sched.poll_once()
    assert "positions" in data
    assert sched.last_error is not None

async def test_scheduler_clears_error_on_recovery():
    class Flaky(MockT212Client):
        def __init__(self, d): super().__init__(d); self.fail = False
        async def positions(self):
            if self.fail:
                raise RuntimeError("boom")
            return await super().positions()
    c = Flaky(FIX)
    sched = RefreshScheduler(c)
    sched.set_active("positions")
    c.fail = True
    await sched.poll_once()
    assert sched.last_error is not None
    c.fail = False
    await sched.poll_once()
    assert sched.last_error is None

async def test_scope_error_recorded_without_last_error():
    class NoOrdersScope(MockT212Client):
        async def orders(self):
            raise ScopeError("API key missing a required scope for this endpoint")
    sched = RefreshScheduler(NoOrdersScope(FIX))
    sched.set_active("dashboard")
    data = await sched.poll_once()
    assert "orders" in sched.scope_errors
    assert sched.last_error is None
    assert "orders" not in data
    assert "summary" in data and "positions" in data

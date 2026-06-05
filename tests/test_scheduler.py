import pathlib
from t212.api.mock import MockT212Client
from t212.scheduler import needs_for_tab, RefreshScheduler

FIX = pathlib.Path(__file__).parent / "fixtures"

def test_needs_for_tab():
    assert "cash" in needs_for_tab("dashboard") and "portfolio" in needs_for_tab("dashboard")
    assert "pies" in needs_for_tab("pies")
    assert "instruments" in needs_for_tab("search")
    assert "cash" in needs_for_tab("history")

async def test_scheduler_poll_once_collects_active_data():
    sched = RefreshScheduler(MockT212Client(FIX))
    sched.set_active("positions")
    data = await sched.poll_once()
    assert "portfolio" in data and data["portfolio"][0].ticker in {"VUSA_GB_EQ", "AAPL_US_EQ", "TSLA_US_EQ"}

async def test_scheduler_keeps_last_good_on_error():
    class Flaky(MockT212Client):
        def __init__(self, d): super().__init__(d); self.fail = False
        async def portfolio(self):
            if self.fail:
                raise RuntimeError("boom")
            return await super().portfolio()
    c = Flaky(FIX)
    sched = RefreshScheduler(c)
    sched.set_active("positions")
    await sched.poll_once()
    c.fail = True
    data = await sched.poll_once()
    assert "portfolio" in data
    assert sched.last_error is not None

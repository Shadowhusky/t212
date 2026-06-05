import pytest
from t212.api.ratelimit import RateLimitGovernor

class FakeClock:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t
    async def sleep(self, s): self.t += s

async def test_first_acquire_is_immediate():
    clk = FakeClock()
    g = RateLimitGovernor({"portfolio": (1, 5.0)}, clock=clk, sleep=clk.sleep, rng=lambda: 0.0)
    await g.acquire("portfolio")
    assert clk.t == 0.0

async def test_second_acquire_waits_one_interval():
    clk = FakeClock()
    g = RateLimitGovernor({"portfolio": (1, 5.0)}, clock=clk, sleep=clk.sleep, rng=lambda: 0.0)
    await g.acquire("portfolio")
    await g.acquire("portfolio")
    assert clk.t == pytest.approx(5.0)

async def test_burst_capacity():
    clk = FakeClock()
    g = RateLimitGovernor({"history": (6, 60.0)}, clock=clk, sleep=clk.sleep, rng=lambda: 0.0)
    for _ in range(6):
        await g.acquire("history")
    assert clk.t == 0.0
    await g.acquire("history")
    assert clk.t == pytest.approx(10.0)

async def test_server_reset_is_honoured():
    clk = FakeClock()
    g = RateLimitGovernor({"cash": (1, 30.0)}, clock=clk, sleep=clk.sleep, rng=lambda: 0.0)
    await g.acquire("cash")
    g.note_server_reset("cash", 12.0)
    await g.acquire("cash")
    assert clk.t == pytest.approx(12.0)

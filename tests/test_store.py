import json, pathlib
from t212.models import Cash, Position
from t212.store import Store

FIX = pathlib.Path(__file__).parent / "fixtures"

class FakeTime:
    def __init__(self, t=1_700_000_000): self.t = t
    def __call__(self): return self.t

def sample():
    cash = Cash.model_validate(json.loads((FIX / "cash.json").read_text()))
    pos = [Position.model_validate(x) for x in json.loads((FIX / "portfolio.json").read_text())]
    return cash, pos

def test_record_throttles_to_one_per_minute(tmp_path):
    clk = FakeTime()
    s = Store(tmp_path / "a.sqlite", clock=clk)
    cash, pos = sample()
    assert s.record(cash, pos, "GBP") is True
    assert s.record(cash, pos, "GBP") is False
    clk.t += 60
    assert s.record(cash, pos, "GBP") is True

def test_equity_series_returns_points(tmp_path):
    clk = FakeTime()
    s = Store(tmp_path / "a.sqlite", clock=clk)
    cash, pos = sample()
    s.record(cash, pos, "GBP")
    clk.t += 120
    s.record(cash, pos, "GBP")
    series = s.equity_series(window_seconds=0)
    assert len(series) == 2
    assert series[-1][1] == cash.total

def test_position_snapshots_written(tmp_path):
    clk = FakeTime()
    s = Store(tmp_path / "a.sqlite", clock=clk)
    cash, pos = sample()
    s.record(cash, pos, "GBP")
    vals = s.position_series("AAPL_US_EQ", window_seconds=0)
    assert vals and round(vals[-1][1], 2) == 2248.80

def test_instrument_cache_roundtrip(tmp_path):
    s = Store(tmp_path / "a.sqlite", clock=FakeTime())
    payload = [{"ticker": "AAPL_US_EQ"}]
    s.cache_instruments(payload)
    got, age = s.get_cached_instruments()
    assert got == payload and age == 0

def test_default_db_path_is_per_account():
    from t212.store import default_db_path
    p = default_db_path("live", 1234567)
    assert p.name == "live-1234567.sqlite"
    assert ".local/share/t212" in str(p) or "t212" in str(p)

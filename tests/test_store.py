import json
from t212.models import AccountSummary, Position
from t212.store import Store

from t212.api.mock import SAMPLE_DIR as FIX

class FakeTime:
    def __init__(self, t=1_700_000_000): self.t = t
    def __call__(self): return self.t

def sample():
    summary = AccountSummary.model_validate(json.loads((FIX / "summary.json").read_text()))
    pos = [Position.model_validate(x) for x in json.loads((FIX / "positions.json").read_text())]
    return summary, pos

def test_record_throttles_to_one_per_minute(tmp_path):
    clk = FakeTime()
    s = Store(tmp_path / "a.sqlite", clock=clk)
    summary, pos = sample()
    assert s.record(summary, pos, "GBP") is True
    assert s.record(summary, pos, "GBP") is False
    clk.t += 60
    assert s.record(summary, pos, "GBP") is True

def test_equity_series_returns_points(tmp_path):
    clk = FakeTime()
    s = Store(tmp_path / "a.sqlite", clock=clk)
    summary, pos = sample()
    s.record(summary, pos, "GBP")
    clk.t += 120
    s.record(summary, pos, "GBP")
    series = s.equity_series(window_seconds=0)
    assert len(series) == 2
    assert series[-1][1] == summary.total_value

def test_position_snapshots_use_wallet_value(tmp_path):
    clk = FakeTime()
    s = Store(tmp_path / "a.sqlite", clock=clk)
    summary, pos = sample()
    s.record(summary, pos, "GBP")
    vals = s.position_series("AAPL_US_EQ", window_seconds=0)
    assert vals and round(vals[-1][1], 2) == 2248.80

def test_position_series_falls_back_to_qty_price(tmp_path):
    clk = FakeTime()
    s = Store(tmp_path / "a.sqlite", clock=clk)
    s.db.execute(
        "INSERT INTO position_snapshots (ts, ticker, quantity, current_price, ppl, value) "
        "VALUES (?,?,?,?,?,NULL)", (1, "OLD_US_EQ", 2.0, 10.0, 0.0))
    s.db.commit()
    vals = s.position_series("OLD_US_EQ", window_seconds=0)
    assert vals == [(1, 20.0)]

def test_opens_legacy_db_without_value_column(tmp_path):
    import sqlite3
    path = tmp_path / "legacy.sqlite"
    db = sqlite3.connect(str(path))
    db.execute("CREATE TABLE position_snapshots "
               "(ts INTEGER, ticker TEXT, quantity REAL, current_price REAL, ppl REAL, "
               "PRIMARY KEY (ts, ticker))")
    db.commit()
    db.close()
    s = Store(path, clock=FakeTime())
    summary, pos = sample()
    assert s.record(summary, pos, "GBP") is True
    vals = s.position_series("AAPL_US_EQ", window_seconds=0)
    assert round(vals[-1][1], 2) == 2248.80

def test_position_today_baseline_returns_earliest_same_day(tmp_path):
    clk = FakeTime()
    s = Store(tmp_path / "a.sqlite", clock=clk, throttle_seconds=0)
    summary, pos = sample()
    s.record(summary, pos, "GBP")
    earliest = s.position_series("AAPL_US_EQ")[-1][1]
    clk.t += 120
    for p in pos:
        p.wallet.current_value += 50.0
    s.record(summary, pos, "GBP")
    assert round(s.position_today_baseline("AAPL_US_EQ"), 2) == round(earliest, 2)

def test_position_today_baseline_none_without_rows(tmp_path):
    s = Store(tmp_path / "a.sqlite", clock=FakeTime(), throttle_seconds=0)
    assert s.position_today_baseline("NOPE_US_EQ") is None

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

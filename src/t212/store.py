from __future__ import annotations
import json
import pathlib
import sqlite3
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS equity_snapshots (
  ts INTEGER PRIMARY KEY,
  total REAL, free REAL, invested REAL, ppl REAL, result REAL, currency TEXT
);
CREATE TABLE IF NOT EXISTS position_snapshots (
  ts INTEGER, ticker TEXT, quantity REAL, current_price REAL, ppl REAL,
  value REAL DEFAULT NULL,
  PRIMARY KEY (ts, ticker)
);
CREATE TABLE IF NOT EXISTS instruments_cache (
  id INTEGER PRIMARY KEY CHECK (id = 1), payload TEXT, fetched_at INTEGER
);
"""


class Store:
    def __init__(self, path, *, clock=time.time, throttle_seconds: int = 60):
        self._clock = clock
        self._throttle = throttle_seconds
        self.db = sqlite3.connect(str(path))
        self.db.executescript(SCHEMA)
        try:
            self.db.execute("ALTER TABLE position_snapshots ADD COLUMN value REAL")
        except sqlite3.OperationalError:
            pass
        self.db.commit()
        self._last_ts = 0

    def record(self, summary, positions, currency: str) -> bool:
        now = int(self._clock())
        if now - self._last_ts < self._throttle:
            return False
        self.db.execute(
            "INSERT OR REPLACE INTO equity_snapshots VALUES (?,?,?,?,?,?,?)",
            (now, summary.total_value, summary.cash.available_to_trade,
             summary.investments.total_cost, summary.investments.unrealized_pnl,
             summary.investments.realized_pnl, currency))
        self.db.executemany(
            "INSERT OR REPLACE INTO position_snapshots VALUES (?,?,?,?,?,?)",
            [(now, p.ticker, p.quantity, p.current_price, p.ppl, p.market_value)
             for p in positions])
        self.db.commit()
        self._last_ts = now
        return True

    def _since(self, window_seconds: int) -> int:
        return 0 if window_seconds <= 0 else int(self._clock()) - window_seconds

    def equity_series(self, window_seconds: int = 0) -> list[tuple[int, float]]:
        cur = self.db.execute(
            "SELECT ts, total FROM equity_snapshots WHERE ts >= ? ORDER BY ts",
            (self._since(window_seconds),))
        return [(int(ts), float(total)) for ts, total in cur.fetchall()]

    def position_series(self, ticker: str, window_seconds: int = 0) -> list[tuple[int, float]]:
        cur = self.db.execute(
            "SELECT ts, COALESCE(value, quantity * current_price) FROM position_snapshots "
            "WHERE ticker = ? AND ts >= ? ORDER BY ts",
            (ticker, self._since(window_seconds)))
        return [(int(ts), float(v)) for ts, v in cur.fetchall()]

    def today_baseline(self) -> float | None:
        midnight = int(time.mktime(time.localtime(self._clock())[:3] + (0, 0, 0, 0, 0, -1)))
        row = self.db.execute(
            "SELECT total FROM equity_snapshots WHERE ts >= ? ORDER BY ts LIMIT 1",
            (midnight,)).fetchone()
        return float(row[0]) if row else None

    def cache_instruments(self, payload: list) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO instruments_cache (id, payload, fetched_at) VALUES (1, ?, ?)",
            (json.dumps(payload), int(self._clock())))
        self.db.commit()

    def get_cached_instruments(self) -> tuple[list, int] | None:
        row = self.db.execute(
            "SELECT payload, fetched_at FROM instruments_cache WHERE id = 1").fetchone()
        if not row:
            return None
        return json.loads(row[0]), int(self._clock()) - int(row[1])

    def close(self) -> None:
        self.db.close()


def default_db_path(environment: str, account_id: int) -> pathlib.Path:
    base = pathlib.Path.home() / ".local" / "share" / "t212"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{environment}-{account_id}.sqlite"

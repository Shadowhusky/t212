from __future__ import annotations

LIVE_URL = "https://live.trading212.com"
DEMO_URL = "https://demo.trading212.com"

# key: (capacity, per_seconds) — mirrors documented limits; honours x-ratelimit-reset at runtime
RATE_LIMITS: dict[str, tuple[int, float]] = {
    "summary": (1, 5.0),
    "positions": (1, 1.0),
    "orders": (1, 5.0),
    "pies": (1, 30.0),
    "pie": (1, 5.0),
    "history_orders": (6, 60.0),
    "dividends": (6, 60.0),
    "transactions": (6, 60.0),
    "instruments": (1, 50.0),
    "exchanges": (1, 30.0),
}

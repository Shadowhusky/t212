from __future__ import annotations
import asyncio
import time
from t212.api.base import T212Client, ScopeError
from t212.api.limits import RATE_LIMITS

_HEADER = {"summary", "positions"}
_TAB_NEEDS = {
    "dashboard": {"summary", "positions", "orders", "pies"},
    "positions": {"summary", "positions"},
    "pies": {"pies"},
    "history": set(),
    "search": {"instruments", "exchanges"},
}

# soft seconds between fetches; each ≥ its hard API limit + headroom
CADENCES = {
    "summary": 6.0,
    "positions": 3.0,
    "orders": 12.0,
    "pies": 35.0,
    "instruments": 3600.0,
    "exchanges": 3600.0,
}


def needs_for_tab(tab: str) -> set[str]:
    return _HEADER | _TAB_NEEDS.get(tab, set())


def _hard_floor(key: str, default: float) -> float:
    if key not in RATE_LIMITS:
        return default
    capacity, per_seconds = RATE_LIMITS[key]
    return per_seconds / capacity


class RefreshScheduler:
    def __init__(self, client: T212Client, *, clock=time.monotonic):
        self.client = client
        self._active = "dashboard"
        self._cache: dict = {}
        self._clock = clock
        self.cadences = dict(CADENCES)
        self._last_fetch: dict[str, float] = {}
        self._forced: set[str] = set()
        self.last_error: Exception | None = None
        self.scope_errors: set[str] = set()
        self.last_fetched: set[str] = set()
        self.consecutive_failures = 0
        self._fetchers = {
            "summary": client.summary,
            "positions": client.positions,
            "orders": client.orders,
            "pies": client.pies,
            "instruments": client.instruments,
            "exchanges": client.exchanges,
        }

    @property
    def degraded(self) -> bool:
        return self.consecutive_failures >= 2

    def set_active(self, tab: str) -> None:
        self._active = tab

    def refresh_now(self) -> None:
        self._forced |= needs_for_tab(self._active)

    def _is_due(self, key: str, now: float) -> bool:
        last = self._last_fetch.get(key, float("-inf"))
        cadence = self.cadences.get(key, 0.0)
        if now - last >= cadence:
            return True
        return key in self._forced and now - last >= _hard_floor(key, cadence)

    async def poll_once(self) -> dict:
        now = self._clock()
        due = [k for k in needs_for_tab(self._active)
               if k in self._fetchers and self._is_due(k, now)]
        fetched: set[str] = set()
        errored = False

        async def fetch(k):
            nonlocal errored
            try:
                self._cache[k] = await self._fetchers[k]()
                self.scope_errors.discard(k)
                fetched.add(k)
            except ScopeError:
                self.scope_errors.add(k)
            except Exception as e:
                self.last_error = e
                errored = True
            finally:
                self._last_fetch[k] = self._clock()
                self._forced.discard(k)

        await asyncio.gather(*(fetch(k) for k in due))
        self.last_fetched = fetched
        if errored:
            self.consecutive_failures += 1
        if fetched:
            self.consecutive_failures = 0
            self.last_error = None
        return dict(self._cache)

from __future__ import annotations
import asyncio
from t212.api.base import T212Client

_HEADER = {"account_info", "cash", "portfolio"}
_TAB_NEEDS = {
    "dashboard": {"cash", "portfolio"},
    "positions": {"portfolio"},
    "pies": {"pies"},
    "history": set(),
    "search": {"instruments", "exchanges"},
}


def needs_for_tab(tab: str) -> set[str]:
    return _HEADER | _TAB_NEEDS.get(tab, set())


class RefreshScheduler:
    def __init__(self, client: T212Client):
        self.client = client
        self._active = "dashboard"
        self._cache: dict = {}
        self.last_error: Exception | None = None
        self._fetchers = {
            "account_info": client.account_info,
            "cash": client.cash,
            "portfolio": client.portfolio,
            "pies": client.pies,
            "instruments": client.instruments,
            "exchanges": client.exchanges,
        }

    def set_active(self, tab: str) -> None:
        self._active = tab

    def refresh_now(self) -> None:
        self._cache.pop("_throttle", None)

    async def poll_once(self) -> dict:
        keys = needs_for_tab(self._active)
        errored = False
        async def fetch(k):
            nonlocal errored
            try:
                self._cache[k] = await self._fetchers[k]()
            except Exception as e:
                self.last_error = e
                errored = True
        await asyncio.gather(*(fetch(k) for k in keys if k in self._fetchers))
        if not errored:
            self.last_error = None
        return dict(self._cache)

from __future__ import annotations
import asyncio
import time
import httpx
from t212.api.base import ApiError, AuthError, RateLimited, ScopeError
from t212.api.ratelimit import RateLimitGovernor
from t212.models import (AccountSummary, Position, PendingOrder, Pie, PieDetail,
                         TradableInstrument, Exchange, HistoricalOrder, Dividend, Transaction)
from t212.pagination import Page, parse_cursor

V = "/api/v0"


def _limit_key_for_path(path: str) -> str:
    if "history/orders" in path:
        return "history_orders"
    if "dividends" in path:
        return "dividends"
    return "transactions"


class HttpT212Client:
    def __init__(self, *, api_key: str, base_url: str, governor: RateLimitGovernor,
                 client: httpx.AsyncClient | None = None, timeout: float = 15.0):
        self._gov = governor
        if client is not None:
            self._client = client
        elif ":" in api_key:                       # current format: keyId:secret → HTTP Basic
            key_id, secret = api_key.split(":", 1)
            self._client = httpx.AsyncClient(
                base_url=base_url, auth=httpx.BasicAuth(key_id, secret), timeout=timeout)
        else:                                       # legacy single-key header
            self._client = httpx.AsyncClient(
                base_url=base_url, headers={"Authorization": api_key}, timeout=timeout)

    async def _request(self, path: str, params: dict | None):
        # ride out a single transient blip before surfacing it
        try:
            r = await self._client.get(path, params=params)
        except (httpx.TransportError, httpx.TimeoutException):
            await asyncio.sleep(0.4)
            try:
                return await self._client.get(path, params=params)
            except httpx.HTTPError as e:
                raise ApiError(str(e)) from e
        except httpx.HTTPError as e:
            raise ApiError(str(e)) from e
        if r.status_code >= 500:
            await asyncio.sleep(0.4)
            try:
                return await self._client.get(path, params=params)
            except httpx.HTTPError as e:
                raise ApiError(str(e)) from e
        return r

    async def _get(self, limit_key: str, path: str, params: dict | None = None):
        await self._gov.acquire(limit_key)
        r = await self._request(path, params)
        if r.status_code == 429:
            raw = float(r.headers.get("x-ratelimit-reset", "5"))
            # header may be a unix timestamp rather than seconds-from-now
            retry = max(1.0, raw - time.time()) if raw > 1e9 else raw
            self._gov.note_server_reset(limit_key, retry)
            raise RateLimited(retry)
        if r.status_code == 401:
            raise AuthError("unauthorized — check API key or live/demo environment")
        if r.status_code == 403:
            raise ScopeError("API key missing a required scope for this endpoint")
        if r.status_code >= 400:
            raise ApiError(f"HTTP {r.status_code} for {path}")
        return r.json()

    async def summary(self) -> AccountSummary:
        return AccountSummary.model_validate(await self._get("summary", f"{V}/equity/account/summary"))

    async def positions(self) -> list[Position]:
        return [Position.model_validate(x) for x in await self._get("positions", f"{V}/equity/positions")]

    async def orders(self) -> list[PendingOrder]:
        return [PendingOrder.model_validate(x) for x in await self._get("orders", f"{V}/equity/orders")]

    async def pies(self) -> list[Pie]:
        return [Pie.model_validate(x) for x in await self._get("pies", f"{V}/equity/pies")]

    async def pie(self, pie_id: int) -> PieDetail:
        return PieDetail.model_validate(await self._get("pie", f"{V}/equity/pies/{pie_id}"))

    async def instruments(self) -> list[TradableInstrument]:
        return [TradableInstrument.model_validate(x)
                for x in await self._get("instruments", f"{V}/equity/metadata/instruments")]

    async def exchanges(self) -> list[Exchange]:
        return [Exchange.model_validate(x) for x in await self._get("exchanges", f"{V}/equity/metadata/exchanges")]

    async def _page(self, limit_key: str, path: str, model,
                    cursor: str | None, ticker: str | None = None):
        params: dict = {"limit": 50}
        if cursor:
            params["cursor"] = cursor
        if ticker:
            params["ticker"] = ticker
        raw = await self._get(limit_key, path, params=params)
        next_path = raw.get("nextPagePath")
        return Page(items=[model.model_validate(x) for x in raw.get("items", [])],
                    next_cursor=parse_cursor(next_path), next_path=next_path)

    async def history_orders(self, cursor: str | None = None,
                             ticker: str | None = None) -> Page[HistoricalOrder]:
        return await self._page("history_orders", f"{V}/equity/history/orders",
                                HistoricalOrder, cursor, ticker)

    async def dividends(self, cursor: str | None = None,
                        ticker: str | None = None) -> Page[Dividend]:
        return await self._page("dividends", f"{V}/equity/history/dividends",
                                Dividend, cursor, ticker)

    async def transactions(self, cursor: str | None = None) -> Page[Transaction]:
        return await self._page("transactions", f"{V}/equity/history/transactions",
                                Transaction, cursor)

    async def get_page(self, path: str) -> dict:
        return await self._get(_limit_key_for_path(path), path)

    async def aclose(self) -> None:
        await self._client.aclose()

from __future__ import annotations
import httpx
from t212.api.base import ApiError, AuthError, RateLimited
from t212.api.ratelimit import RateLimitGovernor
from t212.models import (AccountInfo, Cash, Position, Pie, PieDetail, Order,
                         Instrument, Exchange, HistoryOrder, Dividend, Transaction)
from t212.pagination import Page, parse_cursor

V = "/api/v0"


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

    async def _get(self, limit_key: str, path: str, params: dict | None = None):
        await self._gov.acquire(limit_key)
        try:
            r = await self._client.get(path, params=params)
        except httpx.HTTPError as e:
            raise ApiError(str(e)) from e
        if r.status_code == 429:
            retry = float(r.headers.get("x-ratelimit-reset", "5"))
            self._gov.note_server_reset(limit_key, retry)
            raise RateLimited(retry)
        if r.status_code in (401, 403):
            raise AuthError("unauthorized — check API key, scopes, or live/demo environment")
        if r.status_code >= 400:
            raise ApiError(f"HTTP {r.status_code} for {path}")
        return r.json()

    async def account_info(self) -> AccountInfo:
        return AccountInfo.model_validate(await self._get("account_info", f"{V}/equity/account/info"))

    async def cash(self) -> Cash:
        return Cash.model_validate(await self._get("cash", f"{V}/equity/account/cash"))

    async def portfolio(self) -> list[Position]:
        return [Position.model_validate(x) for x in await self._get("portfolio", f"{V}/equity/portfolio")]

    async def pies(self) -> list[Pie]:
        return [Pie.model_validate(x) for x in await self._get("pies", f"{V}/equity/pies")]

    async def pie(self, pie_id: int) -> PieDetail:
        return PieDetail.model_validate(await self._get("pie", f"{V}/equity/pies/{pie_id}"))

    async def orders(self) -> list[Order]:
        return [Order.model_validate(x) for x in await self._get("orders", f"{V}/equity/orders")]

    async def instruments(self) -> list[Instrument]:
        return [Instrument.model_validate(x) for x in await self._get("instruments", f"{V}/equity/metadata/instruments")]

    async def exchanges(self) -> list[Exchange]:
        return [Exchange.model_validate(x) for x in await self._get("exchanges", f"{V}/equity/metadata/exchanges")]

    async def _page(self, limit_key: str, path: str, model, cursor: str | None):
        params = {"cursor": cursor, "limit": 20} if cursor else {"limit": 20}
        raw = await self._get(limit_key, path, params=params)
        return Page(items=[model.model_validate(x) for x in raw.get("items", [])],
                    next_cursor=parse_cursor(raw.get("nextPagePath")))

    async def history_orders(self, cursor: str | None = None) -> Page[HistoryOrder]:
        return await self._page("history_orders", f"{V}/equity/history/orders", HistoryOrder, cursor)

    async def dividends(self, cursor: str | None = None) -> Page[Dividend]:
        return await self._page("dividends", f"{V}/history/dividends", Dividend, cursor)

    async def transactions(self, cursor: str | None = None) -> Page[Transaction]:
        return await self._page("transactions", f"{V}/history/transactions", Transaction, cursor)

    async def aclose(self) -> None:
        await self._client.aclose()

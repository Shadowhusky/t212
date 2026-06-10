from __future__ import annotations
from typing import Protocol
from t212.models import (AccountSummary, Position, PendingOrder, Pie, PieDetail,
                         TradableInstrument, Exchange, HistoricalOrder, Dividend, Transaction)
from t212.pagination import Page


class ApiError(Exception):
    pass


class AuthError(ApiError):
    pass


class ScopeError(ApiError):
    pass


class RateLimited(ApiError):
    def __init__(self, retry_after: float):
        super().__init__(f"rate limited, retry in {retry_after:.0f}s")
        self.retry_after = retry_after


class T212Client(Protocol):
    async def summary(self) -> AccountSummary: ...
    async def positions(self) -> list[Position]: ...
    async def orders(self) -> list[PendingOrder]: ...
    async def pies(self) -> list[Pie]: ...
    async def pie(self, pie_id: int) -> PieDetail: ...
    async def instruments(self) -> list[TradableInstrument]: ...
    async def exchanges(self) -> list[Exchange]: ...
    async def history_orders(self, cursor: str | None = None,
                             ticker: str | None = None) -> Page[HistoricalOrder]: ...
    async def dividends(self, cursor: str | None = None,
                        ticker: str | None = None) -> Page[Dividend]: ...
    async def transactions(self, cursor: str | None = None) -> Page[Transaction]: ...
    async def get_page(self, path: str) -> dict: ...
    async def aclose(self) -> None: ...

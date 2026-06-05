from __future__ import annotations
import json
import pathlib
from t212.models import (AccountInfo, Cash, Position, Pie, PieDetail, Order,
                         Instrument, Exchange, HistoryOrder, Dividend, Transaction)
from t212.pagination import Page, parse_cursor


class MockT212Client:
    def __init__(self, fixtures_dir: str | pathlib.Path):
        self._dir = pathlib.Path(fixtures_dir)

    def _load(self, name: str):
        return json.loads((self._dir / f"{name}.json").read_text())

    async def account_info(self) -> AccountInfo:
        return AccountInfo.model_validate(self._load("account_info"))

    async def cash(self) -> Cash:
        return Cash.model_validate(self._load("cash"))

    async def portfolio(self) -> list[Position]:
        return [Position.model_validate(x) for x in self._load("portfolio")]

    async def pies(self) -> list[Pie]:
        return [Pie.model_validate(x) for x in self._load("pies")]

    async def pie(self, pie_id: int) -> PieDetail:
        return PieDetail.model_validate(self._load("pie_detail"))

    async def orders(self) -> list[Order]:
        try:
            return [Order.model_validate(x) for x in self._load("orders")]
        except FileNotFoundError:
            return []

    async def instruments(self) -> list[Instrument]:
        return [Instrument.model_validate(x) for x in self._load("instruments")]

    async def exchanges(self) -> list[Exchange]:
        return [Exchange.model_validate(x) for x in self._load("exchanges")]

    def _page(self, name: str, model):
        raw = self._load(name)
        return Page(items=[model.model_validate(x) for x in raw["items"]],
                    next_cursor=parse_cursor(raw.get("nextPagePath")))

    async def history_orders(self, cursor: str | None = None) -> Page[HistoryOrder]:
        return self._page("history_orders", HistoryOrder)

    async def dividends(self, cursor: str | None = None) -> Page[Dividend]:
        return self._page("dividends", Dividend)

    async def transactions(self, cursor: str | None = None) -> Page[Transaction]:
        return self._page("transactions", Transaction)

    async def aclose(self) -> None:
        return None

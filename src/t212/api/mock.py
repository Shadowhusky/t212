from __future__ import annotations
import json
import pathlib
from t212.models import (AccountSummary, Position, PendingOrder, Pie, PieDetail,
                         TradableInstrument, Exchange, HistoricalOrder, Dividend, Transaction)
from t212.pagination import Page, parse_cursor

SAMPLE_DIR = pathlib.Path(__file__).parent.parent / "sample_data"


class MockT212Client:
    def __init__(self, fixtures_dir: str | pathlib.Path | None = None):
        self._dir = pathlib.Path(fixtures_dir) if fixtures_dir else SAMPLE_DIR

    def _load(self, name: str):
        return json.loads((self._dir / f"{name}.json").read_text())

    async def summary(self) -> AccountSummary:
        return AccountSummary.model_validate(self._load("summary"))

    async def positions(self) -> list[Position]:
        return [Position.model_validate(x) for x in self._load("positions")]

    async def orders(self) -> list[PendingOrder]:
        try:
            return [PendingOrder.model_validate(x) for x in self._load("orders")]
        except FileNotFoundError:
            return []

    async def pies(self) -> list[Pie]:
        return [Pie.model_validate(x) for x in self._load("pies")]

    async def pie(self, pie_id: int) -> PieDetail:
        return PieDetail.model_validate(self._load("pie_detail"))

    async def instruments(self) -> list[TradableInstrument]:
        return [TradableInstrument.model_validate(x) for x in self._load("instruments")]

    async def exchanges(self) -> list[Exchange]:
        return [Exchange.model_validate(x) for x in self._load("exchanges")]

    def _page(self, name: str, model):
        raw = self._load(name)
        next_path = raw.get("nextPagePath")
        return Page(items=[model.model_validate(x) for x in raw["items"]],
                    next_cursor=parse_cursor(next_path), next_path=next_path)

    async def history_orders(self, cursor: str | None = None,
                             ticker: str | None = None) -> Page[HistoricalOrder]:
        return self._page("history_orders", HistoricalOrder)

    async def dividends(self, cursor: str | None = None,
                        ticker: str | None = None) -> Page[Dividend]:
        return self._page("dividends", Dividend)

    async def transactions(self, cursor: str | None = None) -> Page[Transaction]:
        return self._page("transactions", Transaction)

    async def get_page(self, path: str) -> dict:
        if "history/orders" in path:
            return self._load("history_orders_page2")
        return {"items": [], "nextPagePath": None}

    async def aclose(self) -> None:
        return None

from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from t212 import formatting as f
from t212.widgets.render import pnl_cell

COLUMNS = ["TICKER", "NAME", "QTY", "AVG", "NOW", "VALUE", "P&L", "P&L%", "WEIGHT"]


class Positions(Static):
    def __init__(self):
        super().__init__(id="positions")
        self._sort_key = "pnl_pct"
        self._reverse = True

    def compose(self) -> ComposeResult:
        table = DataTable(id="positions-table", cursor_type="row", zebra_stripes=False)
        table.add_columns(*COLUMNS)
        yield table

    def update_data(self, *, positions, resolver, currency: str, total_value: float,
                    privacy: bool) -> None:
        table = self.query_one("#positions-table", DataTable)
        table.clear()
        rows = sorted(positions, key=self._sortfn, reverse=self._reverse)
        for p in rows:
            pct = p.pnl_pct or 0.0
            weight = (p.market_value / total_value) if total_value else 0.0
            table.add_row(
                resolver.short_name(p.ticker),
                resolver.long_name(p.ticker)[:22],
                f"{p.quantity:g}",
                f"{p.average_price:,.2f}",
                f"{p.current_price:,.2f}",
                f.money(p.market_value, currency, blur=privacy),
                pnl_cell(p.ppl, currency, blur=privacy),
                f.percent(pct),
                f"{weight * 100:.1f}%",
                key=p.ticker,
            )

    def _sortfn(self, p):
        return {"pnl_pct": p.pnl_pct or 0.0, "value": p.market_value,
                "pnl": p.ppl}.get(self._sort_key, p.market_value)

    def cycle_sort(self) -> None:
        order = ["pnl_pct", "value", "pnl"]
        self._sort_key = order[(order.index(self._sort_key) + 1) % len(order)]

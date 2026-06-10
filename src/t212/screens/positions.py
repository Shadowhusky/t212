from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from t212 import formatting as f
from t212.widgets.render import pnl_cell, columns_for_width, POSITION_COLUMNS_FULL, POSITION_COLUMNS_COMPACT


class Positions(Static):
    def __init__(self):
        super().__init__(id="positions")
        self._sort_key = "pnl_pct"
        self._reverse = True

    def compose(self) -> ComposeResult:
        table = DataTable(id="positions-table", cursor_type="row", zebra_stripes=False)
        table.add_columns(*POSITION_COLUMNS_FULL)
        yield table

    def update_data(self, *, positions, resolver, currency: str, total_value: float,
                    privacy: bool) -> None:
        table = self.query_one("#positions-table", DataTable)
        width = self.app.size.width or 120
        cols = columns_for_width(POSITION_COLUMNS_FULL, POSITION_COLUMNS_COMPACT, width)
        money = f.compact_money if width < 64 else f.money
        table.clear(columns=True)
        table.add_columns(*cols)
        rows = sorted(positions, key=self._sortfn, reverse=self._reverse)
        if not rows:
            table.add_row("No open positions", *[""] * (len(cols) - 1))
            return
        for p in rows:
            pct = p.pnl_pct or 0.0
            weight = (p.market_value / total_value) if total_value else 0.0
            full = {
                "TICKER": f.display_ticker(p.ticker),
                "NAME": p.name[:22],
                "QTY": f"{p.quantity:g}",
                "AVG": f"{p.average_price:,.2f}",
                "NOW": f"{p.current_price:,.2f}",
                "VALUE": money(p.market_value, currency, blur=privacy),
                "P&L": pnl_cell(p.ppl, currency, blur=privacy),
                "P&L%": f.percent(pct),
                "WEIGHT": f"{weight * 100:.1f}%",
            }
            table.add_row(*[full[c] for c in cols], key=p.ticker)

    def _sortfn(self, p):
        return {"pnl_pct": p.pnl_pct or 0.0, "value": p.market_value,
                "pnl": p.ppl}.get(self._sort_key, p.market_value)

    def cycle_sort(self) -> None:
        order = ["pnl_pct", "value", "pnl"]
        self._sort_key = order[(order.index(self._sort_key) + 1) % len(order)]

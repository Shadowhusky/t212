from __future__ import annotations
from textual.app import ComposeResult
from textual.content import Content
from textual.widgets import DataTable, Static
from t212 import formatting as f
from t212.widgets.render import pnl_cell, columns_for_width, POSITION_COLUMNS_FULL, POSITION_COLUMNS_COMPACT

SORT_LABELS = {"pnl_pct": "P&L %", "value": "value", "pnl": "P&L £"}


class Positions(Static):
    def __init__(self):
        super().__init__(id="positions")
        self._sort_key = "pnl_pct"
        self._reverse = True

    def compose(self) -> ComposeResult:
        yield Static("", id="positions-chrome")
        table = DataTable(id="positions-table", cursor_type="row", zebra_stripes=False)
        table.add_columns(*POSITION_COLUMNS_FULL)
        yield table

    @property
    def sort_label(self) -> str:
        return SORT_LABELS[self._sort_key]

    def update_data(self, *, positions, resolver, currency: str, total_value: float,
                    privacy: bool, open_pnl: float = 0.0, open_pnl_pct: float = 0.0) -> None:
        pnl_tag = "$success" if f.pnl_class(open_pnl) == "gain" else (
            "$error" if f.pnl_class(open_pnl) == "loss" else "$text-muted")
        pnl_txt = (f"{f.arrow(open_pnl)} {f.signed_money(open_pnl, currency, blur=privacy)} "
                   f"{f.percent(open_pnl_pct)}")
        self.query_one("#positions-chrome", Static).update(Content.from_markup(
            f"[dim]POSITIONS · {len(positions)} holdings · open P&L [/dim]"
            f"[{pnl_tag}]{pnl_txt}[/{pnl_tag}]"
            f"[dim] · sorted by {self.sort_label} ↓[/dim]"))
        table = self.query_one("#positions-table", DataTable)
        prev_row = table.cursor_row
        width = self.app.size.width or 120
        cols = columns_for_width(POSITION_COLUMNS_FULL, POSITION_COLUMNS_COMPACT, width)
        money = f.compact_money if width < 64 else f.money
        table.clear(columns=True)
        table.add_columns(*cols)
        rows = sorted(positions, key=self._sortfn, reverse=self._reverse)
        if not rows:
            table.add_row("No direct positions. Holdings inside pies live in the Pies tab (3).",
                          *[""] * (len(cols) - 1))
            return
        for p in rows:
            pct = p.pnl_pct or 0.0
            weight = (p.market_value / total_value) if total_value else 0.0
            qty = f"{p.quantity:g}" + (" ◔" if p.quantity_in_pies > 0 else "")
            full = {
                "TICKER": f.display_ticker(p.ticker),
                "NAME": p.name[:22],
                "QTY": qty,
                "AVG": f"{p.average_price:,.2f}",
                "NOW": f"{p.current_price:,.2f}",
                "VALUE": money(p.market_value, currency, blur=privacy),
                "P&L": pnl_cell(p.ppl, currency, blur=privacy),
                "P&L%": f.percent(pct),
                "FX": pnl_cell(p.fx_ppl, currency, blur=privacy),
                "WEIGHT": f"{weight * 100:.1f}%",
            }
            table.add_row(*[full[c] for c in cols], key=p.ticker)
        if table.row_count and prev_row and prev_row > 0:
            table.move_cursor(row=min(prev_row, table.row_count - 1))

    def _sortfn(self, p):
        return {"pnl_pct": p.pnl_pct or 0.0, "value": p.market_value,
                "pnl": p.ppl}.get(self._sort_key, p.market_value)

    def cycle_sort(self) -> None:
        order = ["pnl_pct", "value", "pnl"]
        self._sort_key = order[(order.index(self._sort_key) + 1) % len(order)]

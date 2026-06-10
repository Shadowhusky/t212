from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from t212 import formatting as f
from t212.widgets.render import pnl_cell

COLUMNS = ["NAME", "VALUE", "INVESTED", "RETURN", "RETURN%", "DIVIDENDS", "CASH",
           "PROGRESS", "STATUS"]


class Pies(Static):
    def __init__(self):
        super().__init__(id="pies")

    def compose(self) -> ComposeResult:
        table = DataTable(id="pies-table", cursor_type="row", zebra_stripes=False)
        table.add_columns(*COLUMNS)
        yield table

    def update_data(self, *, pies, currency: str, privacy: bool, names=None) -> None:
        names = names or {}
        table = self.query_one("#pies-table", DataTable)
        table.clear()
        if not pies:
            table.add_row("No pies", *[""] * (len(COLUMNS) - 1))
            return
        for pie in pies:
            r = pie.result
            table.add_row(
                (names.get(pie.id) or f"Pie {pie.id}")[:24],
                f.money(r.value, currency, blur=privacy),
                f.money(r.invested, currency, blur=privacy),
                pnl_cell(r.result, currency, blur=privacy),
                f.percent(pie.result.result_coef),
                f.money(pie.dividend_details.gained, currency, blur=privacy),
                f.money(pie.cash, currency, blur=privacy),
                f.percent(pie.progress, signed=False) if pie.progress is not None else "—",
                pie.status or "—",
                key=str(pie.id),
            )

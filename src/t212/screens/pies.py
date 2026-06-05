from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from t212 import formatting as f
from t212.widgets.render import pnl_cell

COLUMNS = ["PIE", "VALUE", "INVESTED", "RETURN", "RETURN%", "DIVIDENDS", "PROGRESS"]


class Pies(Static):
    def __init__(self):
        super().__init__(id="pies")

    def compose(self) -> ComposeResult:
        table = DataTable(id="pies-table", cursor_type="row")
        table.add_columns(*COLUMNS)
        yield table

    def update_data(self, *, pies, currency: str, privacy: bool) -> None:
        table = self.query_one("#pies-table", DataTable)
        table.clear()
        if not pies:
            table.add_row("No pies", "", "", "", "", "", "")
            return
        for pie in pies:
            r = pie.result
            divs = (pie.dividend_details or {}).get("gained", 0.0)
            table.add_row(
                f"Pie {pie.id}",
                f.money(r.value, currency, blur=privacy),
                f.money(r.invested, currency, blur=privacy),
                pnl_cell(r.result, currency, blur=privacy),
                f.percent(r.result_coef),
                f.money(divs, currency, blur=privacy),
                f.percent(pie.progress or 0, signed=False),
                key=str(pie.id),
            )

from __future__ import annotations
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from t212 import formatting as f
from t212.widgets.render import pnl_cell, num, col_headers, bar

COLUMNS = ["NAME", "VALUE", "INVESTED", "RETURN", "RETURN%", "DIVIDENDS", "CASH",
           "PROGRESS", "STATUS"]
NUMERIC = {"VALUE", "INVESTED", "RETURN", "RETURN%", "DIVIDENDS", "CASH"}
_STATUS_COLOR = {"AHEAD": "green", "ON_TRACK": "cyan", "BEHIND": "red"}


def _progress_cell(progress) -> str:
    if progress is None:
        return "—"
    return f"{bar(progress, 8)} {progress * 100:.0f}%"


def _status_cell(status) -> Text:
    return Text(status or "—", style=_STATUS_COLOR.get(status or "", "dim"))


class Pies(Static):
    def __init__(self):
        super().__init__(id="pies")

    def compose(self) -> ComposeResult:
        table = DataTable(id="pies-table", cursor_type="row", zebra_stripes=False)
        table.add_columns(*col_headers(COLUMNS, NUMERIC))
        yield table

    def update_data(self, *, pies, currency: str, privacy: bool, names=None) -> None:
        names = names or {}
        table = self.query_one("#pies-table", DataTable)
        prev_row = table.cursor_row
        table.clear()
        if not pies:
            table.add_row("No pies", *[""] * (len(COLUMNS) - 1))
            return
        for pie in pies:
            r = pie.result
            table.add_row(
                (names.get(pie.id) or f"Pie {pie.id}")[:24],
                num(f.money(r.value, currency, blur=privacy)),
                num(f.money(r.invested, currency, blur=privacy)),
                pnl_cell(r.result, currency, blur=privacy),
                num(f.percent(pie.result.result_coef)),
                num(f.money(pie.dividend_details.gained, currency, blur=privacy)),
                num(f.money(pie.cash, currency, blur=privacy)),
                _progress_cell(pie.progress),
                _status_cell(pie.status),
                key=str(pie.id),
            )
        if table.row_count and prev_row and prev_row > 0:
            table.move_cursor(row=min(prev_row, table.row_count - 1))

from __future__ import annotations
from textual.screen import ModalScreen
from textual.widgets import DataTable, Static
from textual.content import Content
from textual.binding import Binding
from t212 import formatting as f
from t212.widgets.render import pnl_cell

COLUMNS = ["INSTRUMENT", "NOW", "TARGET", "DRIFT", "OWNED", "RESULT", "RESULT%"]


class PieDetailScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Back")]

    def __init__(self, detail, resolver, currency, privacy):
        super().__init__()
        self.detail = detail
        self.resolver = resolver
        self.currency = currency
        self.privacy = privacy

    def compose(self):
        s = self.detail.settings
        yield Static(Content.from_markup(
            f"[b]‹ Pies / {s.name or s.id}[/b]   "
            f"[dim]goal {f.money(s.goal or 0, self.currency, blur=self.privacy)}[/dim]"))
        table = DataTable(id="pie-instruments", cursor_type="row")
        table.add_columns(*COLUMNS)
        for ins in self.detail.instruments:
            drift = ins.current_share - ins.expected_share
            table.add_row(
                self.resolver.short_name(ins.ticker),
                f.percent(ins.current_share, signed=False, dp=1),
                f.percent(ins.expected_share, signed=False, dp=1),
                f"{f.arrow(drift)} {f.percent(drift, dp=1)}",
                f"{ins.owned_quantity:g}",
                pnl_cell(ins.result.result, self.currency, blur=self.privacy),
                f.percent(ins.result.result_coef),
            )
        yield table

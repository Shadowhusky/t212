from __future__ import annotations
from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import DataTable, Static
from textual.content import Content
from textual.binding import Binding
from t212 import formatting as f
from t212.widgets.render import bar, pnl_cell

COLUMNS = ["INSTRUMENT", "NOW", "TARGET", "DRIFT", "OWNED", "RESULT", "RESULT%", "ISSUES"]


def _issues_cell(issues) -> Text | str:
    if not issues:
        return ""
    names = ", ".join(i.name or "?" for i in issues)
    informative = all((i.severity or "") == "INFORMATIVE" for i in issues)
    return Text(f"⚠ {names}", style="dim" if informative else "yellow")


class PieDetailScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Back")]

    def __init__(self, detail, resolver, currency, privacy, pie=None):
        super().__init__()
        self.detail = detail
        self.resolver = resolver
        self.currency = currency
        self.privacy = privacy
        self.pie = pie

    def compose(self):
        s = self.detail.settings
        cur = self.currency
        header = f"[b]‹ Pies / {s.name or s.id}[/b]"
        if self.pie is not None and self.pie.status:
            header += f"  [dim]· {self.pie.status}[/dim]"
        if self.pie is not None and self.pie.progress is not None:
            header += (f"\n[dim]goal[/dim] {bar(self.pie.progress)} "
                       f"{f.percent(self.pie.progress, signed=False)}")
        yield Static(Content.from_markup(header), id="pie-header")
        action = s.dividend_cash_action or "—"
        if action != "REINVEST" and action != "—":
            action = "to cash"
        rows = [
            ("Created", s.creation_date.date() if s.creation_date else "—"),
            ("Dividends", action),
            ("Initial", f.money(s.initial_investment, cur, blur=self.privacy)
                        if s.initial_investment else "—"),
            ("Goal", f.money(s.goal, cur, blur=self.privacy) if s.goal else "—"),
        ]
        if s.end_date:
            rows.append(("End date", s.end_date.date()))
        body = "\n".join(f"[dim]{k:<10}[/dim]{v}" for k, v in rows)
        yield Static(Content.from_markup(body), id="pie-settings")
        if self.pie is not None:
            d = self.pie.dividend_details
            yield Static(Content.from_markup(
                f"[dim]Dividends gained {f.money(d.gained, cur, blur=self.privacy)} · "
                f"reinvested {f.money(d.reinvested, cur, blur=self.privacy)} · "
                f"in cash {f.money(d.in_cash, cur, blur=self.privacy)}[/dim]"),
                id="pie-dividends")
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
                _issues_cell(ins.issues),
            )
        yield table

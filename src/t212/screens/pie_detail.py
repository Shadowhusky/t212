from __future__ import annotations
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from textual.content import Content
from t212 import formatting as f
from t212.widgets.modal import DetailModal
from t212.widgets.render import bar, pnl_cell

COLUMNS = ["INSTRUMENT", "NOW", "TARGET", "DRIFT", "OWNED", "RESULT", "RESULT%", "ISSUES"]


def _issues_cell(issues) -> Text | str:
    if not issues:
        return ""
    names = ", ".join(i.name or "?" for i in issues)
    informative = all((i.severity or "") == "INFORMATIVE" for i in issues)
    return Text(f"⚠ {names}", style="dim" if informative else "yellow")


class PieDetailScreen(DetailModal):
    def __init__(self, detail, resolver, currency, privacy, pie=None):
        super().__init__()
        self.detail = detail
        self.resolver = resolver
        self.currency = currency
        self.privacy = privacy
        self.pie = pie

    def compose_body(self) -> ComposeResult:
        yield Static(id="pie-header")
        yield Static(id="pie-settings")
        yield Static(id="pie-dividends")
        table = DataTable(id="pie-instruments", cursor_type="row", zebra_stripes=False)
        table.add_columns(*COLUMNS)
        yield table

    def populate(self) -> None:
        s = self.detail.settings
        cur = self.currency
        header = f"[b]‹ Pies / {s.name or s.id}[/b]"
        if self.pie is not None and self.pie.status:
            header += f"  [dim]· {self.pie.status}[/dim]"
        if self.pie is not None and self.pie.progress is not None:
            header += (f"\n[dim]goal[/dim] {bar(self.pie.progress)} "
                       f"{f.percent(self.pie.progress, signed=False)}")
        self.query_one("#pie-header", Static).update(Content.from_markup(header))
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
        self.query_one("#pie-settings", Static).update(Content.from_markup(body))
        dividends = self.query_one("#pie-dividends", Static)
        if self.pie is not None:
            d = self.pie.dividend_details
            dividends.update(Content.from_markup(
                f"[dim]Dividends gained {f.money(d.gained, cur, blur=self.privacy)} · "
                f"reinvested {f.money(d.reinvested, cur, blur=self.privacy)} · "
                f"in cash {f.money(d.in_cash, cur, blur=self.privacy)}[/dim]"))
        else:
            dividends.display = False
        table = self.query_one("#pie-instruments", DataTable)
        table.clear()
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

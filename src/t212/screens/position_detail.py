from __future__ import annotations
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.content import Content
from textual.binding import Binding
from t212 import formatting as f
from t212.widgets.render import sparkline, PNL_TAG


class PositionDetail(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Back")]

    def __init__(self, position, resolver, currency, series, privacy):
        super().__init__()
        self.position = position
        self.resolver = resolver
        self.currency = currency
        self.series = series
        self.privacy = privacy

    def compose(self):
        p, cur = self.position, self.currency
        ex = self.resolver.exchange(p.ticker) or ""
        tag = PNL_TAG[f.pnl_class(p.ppl)]
        lines = [
            f"[b]‹ {self.resolver.short_name(p.ticker)} · {self.resolver.long_name(p.ticker)}[/b]  [dim]{ex}[/dim]",
            "",
            f"[dim]Quantity[/dim]      {p.quantity:g}",
            f"[dim]Avg price[/dim]     {f.money(p.average_price, cur, blur=self.privacy)}",
            f"[dim]Current[/dim]       {f.money(p.current_price, cur, blur=self.privacy)}",
            f"[dim]Market value[/dim]  {f.money(p.market_value, cur, blur=self.privacy)}",
            f"[dim]Open P&L[/dim]      [{tag}]{f.arrow(p.ppl)} {f.signed_money(p.ppl, cur, blur=self.privacy)} ({f.percent(p.pnl_pct or 0)})[/{tag}]",
            f"[dim]FX P&L[/dim]        {f.signed_money(p.fx_ppl or 0.0, cur, blur=self.privacy)}",
            f"[dim]First fill[/dim]    {p.initial_fill_date.date() if p.initial_fill_date else '—'}",
        ]
        if self.series:
            lines.append("")
            lines.append(f"[dim]Recorded value[/dim]  {sparkline([v for _, v in self.series], 40)}")
        yield Static(Content.from_markup("\n".join(lines)))

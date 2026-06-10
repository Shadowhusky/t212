from __future__ import annotations
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.content import Content
from t212 import formatting as f
from t212.charts import window_series
from t212.widgets.render import bar, PNL_TAG, sparkline


class Dashboard(Vertical):
    def __init__(self):
        super().__init__(id="dashboard")

    def compose(self) -> ComposeResult:
        yield Static("Loading…", id="dash-metrics")

    def update_data(self, *, summary, positions, resolver, currency: str, today: float,
                    series, privacy: bool) -> None:
        cur = currency
        inv = summary.investments
        ppl_tag = PNL_TAG[f.pnl_class(inv.unrealized_pnl)]
        lines = [
            "[dim]OPEN P&L[/dim]",
            f"[{ppl_tag}]{f.arrow(inv.unrealized_pnl)} {f.signed_money(inv.unrealized_pnl, cur, blur=privacy)}  "
            f"{f.percent(inv.unrealized_pnl / inv.total_cost if inv.total_cost else 0)}[/{ppl_tag}]",
            f"[dim]Realised   {f.signed_money(inv.realized_pnl, cur, blur=privacy)}[/dim]",
            f"[dim]Invested   {f.money(inv.total_cost, cur, blur=privacy)}[/dim]",
            f"[dim]Positions  {len(positions)}[/dim]",
            "",
            "[dim]ALLOCATION · by type[/dim]",
        ]
        for label, frac in _alloc_by_type(positions, summary, resolver).items():
            lines.append(f"{label:<7}{bar(frac)}  {frac * 100:>3.0f}%")
        lines.append("")
        lines.append("[dim]TOP MOVERS[/dim]")
        for p in _top_movers(positions):
            tag = PNL_TAG[f.pnl_class(p.ppl)]
            lines.append(
                f"{f.display_ticker(p.ticker):<8}"
                f"[{tag}]{f.arrow(p.ppl)} {f.percent(p.pnl_pct or 0.0)}[/{tag}]")
        pts = [v for _, v in window_series(series or [], 0)]
        if len(pts) >= 2:
            lines.append("")
            lines.append("[dim]EQUITY · since first run[/dim]")
            lines.append(sparkline(pts, 48))
        self.query_one("#dash-metrics", Static).update(Content.from_markup("\n".join(lines)))


def _alloc_by_type(positions, summary, resolver) -> dict[str, float]:
    free = summary.cash.available_to_trade
    total = sum(p.market_value for p in positions) + free
    if total <= 0:
        return {}
    buckets: dict[str, float] = {}
    for p in positions:
        inst = resolver.instrument(p.ticker)
        kind = (inst.type.title() + "s") if inst and inst.type else "Other"
        buckets[kind] = buckets.get(kind, 0.0) + p.market_value
    buckets["Cash"] = free
    return {k: v / total for k, v in buckets.items() if v > 0}


def _top_movers(positions, n: int = 4):
    return sorted(positions, key=lambda p: abs(p.pnl_pct or 0.0), reverse=True)[:n]

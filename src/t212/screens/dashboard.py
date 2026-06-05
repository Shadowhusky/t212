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

    def update_data(self, *, cash, positions, resolver, currency: str, today: float,
                    series, privacy: bool) -> None:
        cur = currency
        ppl_tag = PNL_TAG[f.pnl_class(cash.ppl)]
        lines = [
            "[dim]OPEN P&L[/dim]",
            f"[{ppl_tag}]{f.arrow(cash.ppl)} {f.signed_money(cash.ppl, cur, blur=privacy)}  "
            f"{f.percent(cash.ppl / cash.invested if cash.invested else 0)}[/{ppl_tag}]",
            f"[dim]Realised   {f.signed_money(cash.result, cur, blur=privacy)}[/dim]",
            f"[dim]Invested   {f.money(cash.invested, cur, blur=privacy)}[/dim]",
            f"[dim]Positions  {len(positions)}[/dim]",
            "",
            "[dim]ALLOCATION · by type[/dim]",
        ]
        for label, frac in _alloc_by_type(positions, cash, resolver).items():
            lines.append(f"{label:<7}{bar(frac)}  {frac * 100:>3.0f}%")
        lines.append("")
        lines.append("[dim]TOP MOVERS[/dim]")
        for p in _top_movers(positions):
            tag = PNL_TAG[f.pnl_class(p.ppl)]
            lines.append(
                f"{resolver.short_name(p.ticker):<8}"
                f"[{tag}]{f.arrow(p.ppl)} {f.percent(p.pnl_pct or 0.0)}[/{tag}]")
        pts = [v for _, v in window_series(series or [], 0)]
        if len(pts) >= 2:
            lines.append("")
            lines.append("[dim]EQUITY · since first run[/dim]")
            lines.append(sparkline(pts, 48))
        self.query_one("#dash-metrics", Static).update(Content.from_markup("\n".join(lines)))


def _alloc_by_type(positions, cash, resolver) -> dict[str, float]:
    total = sum(p.market_value for p in positions) + cash.free
    if total <= 0:
        return {}
    buckets: dict[str, float] = {}
    for p in positions:
        inst = resolver.instrument(p.ticker)
        kind = (inst.type.title() + "s") if inst and inst.type else "Other"
        buckets[kind] = buckets.get(kind, 0.0) + p.market_value
    buckets["Cash"] = cash.free
    return {k: v / total for k, v in buckets.items() if v > 0}


def _top_movers(positions, n: int = 4):
    return sorted(positions, key=lambda p: abs(p.pnl_pct or 0.0), reverse=True)[:n]

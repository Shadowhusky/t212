from __future__ import annotations
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static
from textual.content import Content
from t212 import formatting as f
from t212.charts import window_series
from t212.widgets.render import area_chart, bar, PNL_TAG, pnl_markup

ORDERS_SCOPE_HINT = ("[dim]Pending orders: not available — enable the 'Orders' scope "
                     "for your API key in Trading 212 → Settings → API[/dim]")

_TIF = {"GOOD_TILL_CANCEL": "GTC", "DAY": "DAY"}


class Dashboard(Vertical):
    DEFAULT_CSS = """
    Dashboard { height: auto; padding: 0 1; }
    Dashboard #dash-cards { height: auto; }
    Dashboard #dash-left { width: 1fr; padding-right: 2; }
    Dashboard #dash-right { width: 1fr; }
    Dashboard #dash-equity { height: auto; margin-top: 1; }
    """

    def __init__(self):
        super().__init__(id="dashboard")

    def compose(self) -> ComposeResult:
        with Horizontal(id="dash-cards"):
            yield Static("Loading…", id="dash-left")
            yield Static("", id="dash-right")
        yield Static("", id="dash-equity")

    def update_data(self, *, summary, positions, resolver, currency: str, today: float,
                    series, privacy: bool, orders=None, pies=None, pie_names=None,
                    scope_errors=frozenset(), income=None, net_deposits=None) -> None:
        cur = currency
        left: list[str] = []
        left += _investments_lines(summary, cur, privacy)
        left.append("")
        left += _cash_lines(summary, cur, privacy)
        left.append("")
        left += _income_lines(income, cur, privacy)
        left.append("")
        left += _deposits_lines(net_deposits, summary, cur, privacy)

        right: list[str] = []
        if pies:
            right += _pies_lines(pies, pie_names or {}, cur, privacy)
            right.append("")
        right += _orders_lines(orders, scope_errors)
        right.append("")
        right.append("[dim]ALLOCATION · by type[/dim]")
        for label, frac in _alloc_by_type(positions, summary, resolver).items():
            right.append(f"{label:<7}{bar(frac, 12)}  {frac * 100:>3.0f}%")
        if positions:
            right.append("")
            right.append("[dim]TOP MOVERS[/dim]")
            for p in _top_movers(positions):
                tag = PNL_TAG[f.pnl_class(p.ppl)]
                right.append(
                    f"{f.display_ticker(p.ticker):<8}"
                    f"[{tag}]{f.arrow(p.ppl)} {f.percent(p.pnl_pct or 0.0)}[/{tag}]")

        self.query_one("#dash-left", Static).update(Content.from_markup("\n".join(left)))
        self.query_one("#dash-right", Static).update(Content.from_markup("\n".join(right)))
        self.query_one("#dash-equity", Static).update(
            Content.from_markup(_equity_block(series, cur, privacy)))


def _equity_block(series, cur, privacy) -> str:
    pts = [v for _, v in window_series(series or [], 0)]
    if len(pts) < 2:
        return ""
    lo, hi = min(pts), max(pts)
    delta = pts[-1] - pts[0]
    tag = PNL_TAG[f.pnl_class(delta)]
    head = (f"[dim]EQUITY · since first run · "
            f"low {f.money(lo, cur, blur=privacy)} · "
            f"high {f.money(hi, cur, blur=privacy)} · [/dim]"
            f"[{tag}]{f.arrow(delta)} {f.signed_money(delta, cur, blur=privacy)}[/{tag}]")
    chart = "\n".join(f"[$accent]{row}[/$accent]" for row in area_chart(pts, width=72, height=5))
    return head + "\n" + chart


def _investments_lines(summary, cur, privacy) -> list[str]:
    inv = summary.investments
    pct = inv.unrealized_pnl / inv.total_cost if inv.total_cost else 0.0
    return [
        "[dim]INVESTMENTS[/dim]",
        f"Value       {f.money(inv.current_value, cur, blur=privacy)}"
        f"  [dim]cost {f.money(inv.total_cost, cur, blur=privacy)}[/dim]",
        f"Unrealised  {pnl_markup(inv.unrealized_pnl, pct, cur, blur=privacy)}",
        f"Realised    {pnl_markup(inv.realized_pnl, None, cur, blur=privacy)}",
    ]


def _cash_lines(summary, cur, privacy) -> list[str]:
    cash = summary.cash
    return [
        "[dim]CASH[/dim]",
        f"Available   {f.money(cash.available_to_trade, cur, blur=privacy)}",
        f"In pies     {f.money(cash.in_pies, cur, blur=privacy)}",
        f"Reserved    {f.money(cash.reserved_for_orders, cur, blur=privacy)}",
        f"Total       [b]{f.money(summary.total_value, cur, blur=privacy)}[/b]",
    ]


def _pies_lines(pies, names: dict, cur, privacy) -> list[str]:
    lines = ["[dim]PIES[/dim]"]
    for pie in pies:
        name = names.get(pie.id) or f"Pie {pie.id}"
        r = pie.result
        line = (f"{name[:18]:<18} {f.money(r.value, cur, blur=privacy):>11}  "
                f"{pnl_markup(r.result, r.result_coef, cur, blur=privacy)}")
        if pie.status:
            line += f"  [dim]{pie.status}[/dim]"
        lines.append(line)
    return lines


def _orders_lines(orders, scope_errors) -> list[str]:
    lines = ["[dim]PENDING ORDERS[/dim]"]
    if "orders" in scope_errors:
        lines.append(ORDERS_SCOPE_HINT)
    elif orders:
        for o in orders:
            tag = "$success" if o.side == "BUY" else "$error"
            price = ""
            if o.limit_price is not None:
                price = f" @ {o.limit_price:,.2f}"
            elif o.stop_price is not None:
                price = f" stop {o.stop_price:,.2f}"
            tif = _TIF.get(o.time_in_force or "", o.time_in_force or "")
            lines.append(
                f"[{tag}]{o.side or '—'}[/{tag}] {o.type or '—'} "
                f"{f.display_ticker(o.ticker or '')} {abs(o.quantity):g}{price}"
                f" [dim]· {o.status or '—'}{' · ' + tif if tif else ''}[/dim]")
    elif orders is None:
        lines.append("[dim]…[/dim]")
    else:
        lines.append("[dim]No pending orders[/dim]")
    return lines


def _income_lines(income, cur, privacy) -> list[str]:
    lines = ["[dim]INCOME · all-time[/dim]"]
    if income is None:
        lines.append("[dim]not available[/dim]")
    else:
        lines.append(f"Dividends   {f.money(income['dividends'], cur, blur=privacy)}")
        lines.append(f"Interest    {f.money(income['interest'], cur, blur=privacy)}")
        lines.append(f"Last 12m    {f.money(income['last12m_total'], cur, blur=privacy)}")
    return lines


def _deposits_lines(net_deposits, summary, cur, privacy) -> list[str]:
    lines = ["[dim]DEPOSITS[/dim]"]
    if net_deposits is None:
        lines.append("[dim]not available[/dim]")
    else:
        gain = summary.total_value - net_deposits
        lines.append(f"Net deposits {f.money(net_deposits, cur, blur=privacy)}")
        lines.append(f"Total gain   {pnl_markup(gain, None, cur, blur=privacy)}")
    return lines


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

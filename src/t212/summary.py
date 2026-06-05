from __future__ import annotations
from dataclasses import dataclass
from t212.api.base import T212Client
from t212.models import Position
from t212.resolve import Resolver
from t212 import formatting as f


@dataclass
class Summary:
    currency: str
    total: float
    free: float
    invested: float
    open_pnl: float
    realised: float
    positions: list[Position]


async def build_summary(client: T212Client) -> Summary:
    info = await client.account_info()
    cash = await client.cash()
    positions = sorted(await client.portfolio(), key=lambda p: p.market_value, reverse=True)
    return Summary(currency=info.currency_code, total=cash.total, free=cash.free,
                   invested=cash.invested, open_pnl=cash.ppl, realised=cash.result,
                   positions=positions)


def render_summary_text(s: Summary, resolver: Resolver) -> str:
    cur = s.currency
    lines = [
        f"Portfolio value   {f.money(s.total, cur)}",
        f"Open P&L          {f.signed_money(s.open_pnl, cur)}  "
        f"({f.percent(s.open_pnl / s.invested if s.invested else 0)})",
        f"Realised          {f.signed_money(s.realised, cur)}",
        f"Free / Invested   {f.money(s.free, cur)} / {f.money(s.invested, cur)}",
        "",
        f"{'TICKER':<10}{'NAME':<24}{'QTY':>6}{'VALUE':>14}{'P&L':>14}{'P&L%':>9}",
    ]
    for p in s.positions:
        pct = p.pnl_pct or 0.0
        lines.append(
            f"{resolver.short_name(p.ticker):<10}"
            f"{resolver.long_name(p.ticker)[:23]:<24}"
            f"{p.quantity:>6.0f}"
            f"{f.money(p.market_value, cur):>14}"
            f"{f.arrow(p.ppl)} {f.signed_money(p.ppl, cur):>11}"
            f"{f.percent(pct):>9}"
        )
    return "\n".join(lines)

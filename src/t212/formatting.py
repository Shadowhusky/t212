from __future__ import annotations

CURRENCY_SYMBOLS = {"GBP": "£", "USD": "$", "EUR": "€", "GBX": "p", "CHF": "Fr"}
ARROW_UP, ARROW_DOWN, ARROW_FLAT = "▲", "▼", "–"
MINUS = "−"  # U+2212
BLUR = "•"


def symbol(currency: str) -> str:
    return CURRENCY_SYMBOLS.get(currency.upper(), currency.upper() + " ")


def money(value: float, currency: str = "GBP", *, blur: bool = False) -> str:
    if blur:
        return BLUR * 6
    return f"{symbol(currency)}{value:,.2f}"


def compact_money(value: float, currency: str = "GBP", *, blur: bool = False) -> str:
    if blur:
        return BLUR * 3
    s = symbol(currency)
    a = abs(value)
    if a >= 1_000_000:
        return f"{s}{value / 1_000_000:.1f}M"
    if a >= 1_000:
        return f"{s}{value / 1_000:.1f}k"
    return f"{s}{value:,.0f}"


def percent(fraction: float, *, signed: bool = True, dp: int = 2) -> str:
    pct = fraction * 100
    if pct < 0:
        return f"{MINUS}{abs(pct):.{dp}f}%"
    return f"{'+' if signed else ''}{pct:.{dp}f}%"


def arrow(value: float) -> str:
    return ARROW_UP if value > 0 else ARROW_DOWN if value < 0 else ARROW_FLAT


def signed_money(value: float, currency: str = "GBP", *, blur: bool = False) -> str:
    if blur:
        return BLUR * 4
    sign = "+" if value >= 0 else MINUS
    return f"{sign}{symbol(currency)}{abs(value):,.2f}"


def pnl_class(value: float) -> str:
    return "gain" if value > 0 else "loss" if value < 0 else "flat"

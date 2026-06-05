from __future__ import annotations
from rich.text import Text
from t212 import formatting as f

_SPARK = "▁▂▃▄▅▆▇█"


def bar(fraction: float, width: int = 10, filled: str = "▰", empty: str = "▱") -> str:
    fraction = max(0.0, min(1.0, fraction))
    n = round(fraction * width)
    return filled * n + empty * (width - n)


def sparkline(values: list[float], width: int = 20) -> str:
    if not values:
        return ""
    pts = values[-width:] if len(values) > width else values
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1.0
    return "".join(_SPARK[min(len(_SPARK) - 1, int((v - lo) / span * (len(_SPARK) - 1)))] for v in pts)


def pnl_text(value: float, pct: float | None, currency: str, *, blur: bool = False) -> Text:
    cls = f.pnl_class(value)
    body = f"{f.arrow(value)} {f.signed_money(value, currency, blur=blur)}"
    if pct is not None:
        body += f"  {f.percent(pct)}"
    return Text(body, style=cls)

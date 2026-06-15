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


def _resample(values: list[float], width: int) -> list[float]:
    if len(values) <= width:
        return values
    step = (len(values) - 1) / (width - 1)
    return [values[round(i * step)] for i in range(width)]


def area_chart(values: list[float], width: int = 60, height: int = 5) -> list[str]:
    """Multi-row filled area chart; returns `height` strings top-to-bottom."""
    pts = _resample(values, width)
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1.0
    levels = height * 8  # eighths of a cell
    rows = [[" "] * len(pts) for _ in range(height)]
    for x, v in enumerate(pts):
        filled = round((v - lo) / span * (levels - 1)) + 1
        for r in range(height):
            cell_from_bottom = height - 1 - r
            base = cell_from_bottom * 8
            if filled >= base + 8:
                rows[r][x] = "█"
            elif filled > base:
                rows[r][x] = _SPARK[filled - base - 1]
    return ["".join(row) for row in rows]


def pnl_text(value: float, pct: float | None, currency: str, *, blur: bool = False) -> Text:
    cls = f.pnl_class(value)
    body = f"{f.arrow(value)} {f.signed_money(value, currency, blur=blur)}"
    if pct is not None:
        body += f"  {f.percent(pct)}"
    return Text(body, style=cls)


PNL_TAG = {"gain": "$success", "loss": "$error", "flat": "$text-muted"}
_PNL_COLOR = {"gain": "green", "loss": "red", "flat": "dim"}


def pnl_markup(value: float, pct: float | None, currency: str, *, blur: bool = False) -> str:
    """Textual markup fragment for Static/Content bodies."""
    tag = PNL_TAG[f.pnl_class(value)]
    body = f"{f.arrow(value)} {f.signed_money(value, currency, blur=blur)}"
    if pct is not None:
        body += f"  {f.percent(pct)}"
    return f"[{tag}]{body}[/{tag}]"


def pnl_cell(value: float, currency: str, pct: float | None = None, *, blur: bool = False) -> Text:
    """Rich Text with a valid named colour, right-justified for DataTable cells."""
    body = f"{f.arrow(value)} {f.signed_money(value, currency, blur=blur)}"
    if pct is not None:
        body += f"  {f.percent(pct)}"
    return Text(body, style=_PNL_COLOR[f.pnl_class(value)], justify="right")


def num(value: str) -> Text:
    """Right-justified plain numeric cell."""
    return Text(value, justify="right")


def col_headers(labels, numeric):
    """DataTable column labels with numeric ones right-justified."""
    return [Text(c, justify="right") if c in numeric else c for c in labels]


POSITION_COLUMNS_FULL = ["TICKER", "NAME", "QTY", "AVG", "NOW", "VALUE", "P&L", "P&L%", "FX", "WEIGHT"]
POSITION_COLUMNS_COMPACT = ["TICKER", "QTY", "VALUE", "P&L%"]


def columns_for_width(full, compact, width: int):
    return full if width >= 100 else compact

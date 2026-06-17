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


# braille dot bit per (sub-row-from-top 0..3, column 0=left 1=right)
_BRAILLE = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))


def braille_area(values: list[float], width: int = 60, height: int = 6) -> list[str]:
    """Smooth filled area chart at 2×4 sub-cell (braille) resolution.

    Returns `height` strings, top row first.
    """
    if len(values) < 2:
        return [""] * height
    sub = _resample(values, width * 2)          # 2 sub-columns per cell
    lo, hi = min(sub), max(sub)
    span = (hi - lo) or 1.0
    levels = height * 4                          # 4 dots per cell, vertically
    grid = [[0] * width for _ in range(height)]
    for sx, v in enumerate(sub):
        col, side = divmod(sx, 2)
        filled = max(1, round((v - lo) / span * (levels - 1)) + 1)
        for p in range(filled):                 # p=0 bottom .. up
            row = height - 1 - (p // 4)
            subrow = 3 - (p % 4)
            grid[row][col] |= _BRAILLE[subrow][side]
    return ["".join(chr(0x2800 + c) if c else " " for c in row) for row in grid]


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


_DIGITS = {
    "0": ["███", "█ █", "█ █", "█ █", "███"],
    "1": ["  █", "  █", "  █", "  █", "  █"],
    "2": ["███", "  █", "███", "█  ", "███"],
    "3": ["███", "  █", "███", "  █", "███"],
    "4": ["█ █", "█ █", "███", "  █", "  █"],
    "5": ["███", "█  ", "███", "  █", "███"],
    "6": ["███", "█  ", "███", "█ █", "███"],
    "7": ["███", "  █", "  █", "  █", "  █"],
    "8": ["███", "█ █", "███", "█ █", "███"],
    "9": ["███", "█ █", "███", "  █", "███"],
    ":": [" ", "█", " ", "█", " "],
    " ": [" ", " ", " ", " ", " "],
}


def big_digits(text: str) -> list[str]:
    """Render a string of digits / colons as 5 rows of block art."""
    glyphs = [_DIGITS.get(ch, _DIGITS[" "]) for ch in text]
    return ["  ".join(g[row] for g in glyphs) for row in range(5)]


def col_headers(labels, numeric):
    """DataTable column labels with numeric ones right-justified."""
    return [Text(c, justify="right") if c in numeric else c for c in labels]


POSITION_COLUMNS_FULL = ["TICKER", "NAME", "QTY", "AVG", "NOW", "VALUE", "P&L", "P&L%", "FX", "WEIGHT"]
POSITION_COLUMNS_COMPACT = ["TICKER", "QTY", "VALUE", "P&L%"]


def columns_for_width(full, compact, width: int):
    return full if width >= 100 else compact

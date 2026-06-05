from __future__ import annotations
import time

WINDOWS = [("1D", 86_400), ("7D", 604_800), ("30D", 2_592_000), ("ALL", 0)]


def window_series(series: list[tuple[int, float]], window_seconds: int, *, now: int | None = None):
    if window_seconds <= 0:
        return series
    cutoff = (now if now is not None else int(time.time())) - window_seconds
    return [(ts, v) for ts, v in series if ts >= cutoff]

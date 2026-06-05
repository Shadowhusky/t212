from t212.charts import window_series, WINDOWS


def test_windows_defined():
    assert [w[0] for w in WINDOWS] == ["1D", "7D", "30D", "ALL"]


def test_window_series_filters_by_seconds():
    series = [(100, 1.0), (200, 2.0), (10_000, 3.0)]
    out = window_series(series, 9_000, now=10_000)   # keep ts >= 1000
    assert out == [(10_000, 3.0)]
    assert window_series(series, 0, now=10_000) == series   # ALL

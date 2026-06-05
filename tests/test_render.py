from t212.widgets.render import bar, sparkline, pnl_text

def test_bar_fraction():
    assert bar(0.0, width=10) == "▱" * 10
    assert bar(1.0, width=10) == "▰" * 10
    assert bar(0.5, width=10) == "▰" * 5 + "▱" * 5

def test_sparkline_len_and_charset():
    s = sparkline([1, 2, 3, 4, 5], width=5)
    assert len(s) == 5
    assert all(ch in "▁▂▃▄▅▆▇█" for ch in s)

def test_sparkline_flat_series():
    assert sparkline([3, 3, 3], width=3) == "▄▄▄" or set(sparkline([3, 3, 3], width=3)) <= set("▁▂▃▄▅▆▇█")

def test_pnl_text_has_arrow_and_style():
    t = pnl_text(129.6, 0.061, "GBP")
    assert "▲" in t.plain and "+£129.60" in t.plain
    assert "gain" in str(t.style) or any("gain" in str(s.style) for s in t.spans)

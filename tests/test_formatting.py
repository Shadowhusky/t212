from t212 import formatting as f

def test_symbol():
    assert f.symbol("GBP") == "£" and f.symbol("USD") == "$" and f.symbol("EUR") == "€"

def test_money():
    assert f.money(24813.07, "GBP") == "£24,813.07"
    assert f.money(1000, "USD") == "$1,000.00"

def test_money_privacy_blur():
    assert f.money(24813.07, "GBP", blur=True) == "••••••"

def test_compact_money():
    assert f.compact_money(24813.07, "GBP") == "£24.8k"
    assert f.compact_money(2_500_000, "GBP") == "£2.5M"
    assert f.compact_money(312, "GBP") == "£312"

def test_percent():
    assert f.percent(0.0512) == "+5.12%"
    assert f.percent(-0.018) == "−1.80%"
    assert f.percent(0.0512, dp=1) == "+5.1%"

def test_arrow():
    assert f.arrow(3) == "▲" and f.arrow(-1) == "▼" and f.arrow(0) == "–"

def test_signed_money():
    assert f.signed_money(129.60, "GBP") == "+£129.60"
    assert f.signed_money(-34.40, "GBP") == "−£34.40"
    assert f.signed_money(-34.40, "GBP", blur=True) == "••••"

def test_pnl_class():
    assert f.pnl_class(1) == "gain" and f.pnl_class(-1) == "loss" and f.pnl_class(0) == "flat"

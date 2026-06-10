from t212.api.limits import RATE_LIMITS, LIVE_URL, DEMO_URL

def test_limits_cover_all_endpoints():
    for key in ("summary", "positions", "orders", "pies", "pie",
                "history_orders", "dividends", "transactions", "instruments", "exchanges"):
        assert key in RATE_LIMITS
        cap, per = RATE_LIMITS[key]
        assert cap >= 1 and per > 0

def test_base_urls():
    assert LIVE_URL.startswith("https://live.")
    assert DEMO_URL.startswith("https://demo.")

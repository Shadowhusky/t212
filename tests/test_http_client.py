import base64
import time
import httpx, pytest
from t212.api.http import HttpT212Client
from t212.api.ratelimit import RateLimitGovernor
from t212.api.base import RateLimited, AuthError, ScopeError
from t212.api.limits import RATE_LIMITS

SUMMARY = {"id": 1, "currency": "GBP", "totalValue": 2.0,
           "cash": {"availableToTrade": 1.0},
           "investments": {"totalCost": 1.0, "unrealizedProfitLoss": 0.5}}


def make_client(handler, governor=None):
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(base_url="https://live.trading212.com",
                             headers={"Authorization": "KEY"}, transport=transport)
    gov = governor or RateLimitGovernor(RATE_LIMITS)
    return HttpT212Client(api_key="KEY", base_url="https://live.trading212.com",
                          governor=gov, client=http), gov

async def test_summary_parsed_and_auth_header_sent():
    seen = {}
    def handler(req):
        seen["auth"] = req.headers.get("Authorization")
        seen["path"] = req.url.path
        return httpx.Response(200, json=SUMMARY)
    c, _ = make_client(handler)
    s = await c.summary()
    assert s.total_value == 2.0 and s.cash.available_to_trade == 1.0
    assert seen["auth"] == "KEY"
    assert seen["path"] == "/api/v0/equity/account/summary"

async def test_positions_path():
    seen = {}
    def handler(req):
        seen["path"] = req.url.path
        return httpx.Response(200, json=[])
    c, _ = make_client(handler)
    assert await c.positions() == []
    assert seen["path"] == "/api/v0/equity/positions"

async def test_history_paths_under_equity_and_limit_50():
    seen = []
    def handler(req):
        seen.append((req.url.path, dict(req.url.params)))
        return httpx.Response(200, json={"items": [], "nextPagePath": None})
    c, _ = make_client(handler)
    await c.history_orders()
    await c.dividends()
    await c.transactions()
    paths = [p for p, _ in seen]
    assert paths == ["/api/v0/equity/history/orders",
                     "/api/v0/equity/history/dividends",
                     "/api/v0/equity/history/transactions"]
    assert all(params["limit"] == "50" for _, params in seen)

async def test_429_seconds_value_sets_reset_and_raises():
    def handler(req):
        return httpx.Response(429, headers={"x-ratelimit-reset": "9"}, json={})
    c, _ = make_client(handler)
    with pytest.raises(RateLimited) as ei:
        await c.positions()
    assert ei.value.retry_after == 9.0

async def test_429_unix_timestamp_converted_to_seconds():
    def handler(req):
        return httpx.Response(429, headers={"x-ratelimit-reset": str(time.time() + 9)}, json={})
    c, gov = make_client(handler)
    with pytest.raises(RateLimited) as ei:
        await c.positions()
    assert 1.0 <= ei.value.retry_after <= 30.0
    # governor got the converted value, not the raw timestamp
    assert gov._reset_until["positions"] - gov._clock() <= 30.0

async def test_401_raises_auth_error():
    def handler(req):
        return httpx.Response(401, json={})
    c, _ = make_client(handler)
    with pytest.raises(AuthError):
        await c.summary()

async def test_403_raises_scope_error():
    def handler(req):
        return httpx.Response(403, json={})
    c, _ = make_client(handler)
    with pytest.raises(ScopeError):
        await c.orders()

async def test_keyid_secret_uses_basic_auth():
    c = HttpT212Client(api_key="myid:mysecret", base_url="https://live.trading212.com",
                       governor=RateLimitGovernor(RATE_LIMITS))
    auth = c._client.auth
    assert isinstance(auth, httpx.BasicAuth)
    request = httpx.Request("GET", "https://live.trading212.com/x")
    signed = next(auth.auth_flow(request))
    expected = "Basic " + base64.b64encode(b"myid:mysecret").decode()
    assert signed.headers["Authorization"] == expected

async def test_legacy_single_key_uses_raw_header():
    c = HttpT212Client(api_key="LEGACYKEY", base_url="https://live.trading212.com",
                       governor=RateLimitGovernor(RATE_LIMITS))
    assert c._client.headers.get("Authorization") == "LEGACYKEY"

async def test_history_orders_parses_cursor_and_path():
    def handler(req):
        return httpx.Response(200, json={"items": [
            {"order": {"ticker": "AAPL_US_EQ", "filledValue": 10.0}}],
            "nextPagePath": "/api/v0/equity/history/orders?cursor=77&limit=50"})
    c, _ = make_client(handler)
    page = await c.history_orders()
    assert page.items[0].order.filled_value == 10.0
    assert page.next_cursor == "77"
    assert page.next_path == "/api/v0/equity/history/orders?cursor=77&limit=50"

async def test_get_page_follows_raw_path():
    seen = {}
    def handler(req):
        seen["path"] = req.url.path
        seen["params"] = dict(req.url.params)
        return httpx.Response(200, json={"items": [], "nextPagePath": None})
    c, _ = make_client(handler)
    raw = await c.get_page("/api/v0/equity/history/orders?cursor=77&limit=50")
    assert raw == {"items": [], "nextPagePath": None}
    assert seen["path"] == "/api/v0/equity/history/orders"
    assert seen["params"] == {"cursor": "77", "limit": "50"}

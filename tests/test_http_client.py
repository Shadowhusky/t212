import httpx, pytest
from t212.api.http import HttpT212Client
from t212.api.ratelimit import RateLimitGovernor
from t212.api.base import RateLimited, AuthError
from t212.api.limits import RATE_LIMITS

def make_client(handler):
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(base_url="https://live.trading212.com",
                             headers={"Authorization": "KEY"}, transport=transport)
    gov = RateLimitGovernor(RATE_LIMITS)
    return HttpT212Client(api_key="KEY", base_url="https://live.trading212.com",
                          governor=gov, client=http)

async def test_cash_parsed_and_auth_header_sent():
    seen = {}
    def handler(req):
        seen["auth"] = req.headers.get("Authorization")
        seen["path"] = req.url.path
        return httpx.Response(200, json={"free": 1.0, "total": 2.0, "invested": 1.0,
                                         "ppl": 0.5, "result": 0.0})
    c = make_client(handler)
    cash = await c.cash()
    assert cash.total == 2.0
    assert seen["auth"] == "KEY"
    assert seen["path"] == "/api/v0/equity/account/cash"

async def test_429_sets_reset_and_raises():
    def handler(req):
        return httpx.Response(429, headers={"x-ratelimit-reset": "9"}, json={})
    c = make_client(handler)
    with pytest.raises(RateLimited) as ei:
        await c.portfolio()
    assert ei.value.retry_after == 9.0

async def test_401_raises_auth_error():
    def handler(req):
        return httpx.Response(401, json={})
    c = make_client(handler)
    with pytest.raises(AuthError):
        await c.account_info()

async def test_history_orders_parses_cursor():
    def handler(req):
        return httpx.Response(200, json={"items": [
            {"ticker": "AAPL_US_EQ", "fillCost": 10.0}],
            "nextPagePath": "/x?cursor=77&limit=20"})
    c = make_client(handler)
    page = await c.history_orders()
    assert page.items[0].fill_cost == 10.0 and page.next_cursor == "77"

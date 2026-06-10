import pathlib
from t212.api.mock import MockT212Client

FIX = pathlib.Path(__file__).parent / "fixtures"

async def test_mock_returns_parsed_models():
    c = MockT212Client(FIX)
    s = await c.summary()
    assert s.currency == "GBP" and s.total_value == 24813.07
    pos = await c.positions()
    assert pos[0].ticker == "AAPL_US_EQ" and round(pos[0].market_value, 2) == 2248.80
    orders = await c.orders()
    assert orders[0].side == "BUY" and orders[0].limit_price == 180.00
    assert (await c.instruments())[0].short_name == "AAPL"
    assert (await c.exchanges())[0].name == "NASDAQ"
    assert (await c.pies())[0].result.result == 612.40
    assert (await c.pie(42)).settings.name == "Growth Pie"

async def test_mock_history_pages():
    c = MockT212Client(FIX)
    page = await c.history_orders()
    assert page.items[0].fill.price == 187.10
    assert page.next_cursor == "1760346100000"
    assert page.next_path == "/api/v0/equity/history/orders?limit=50&cursor=1760346100000"
    assert (await c.dividends()).items[0].amount == 4.20
    assert (await c.transactions()).items[2].type == "WITHDRAW"

async def test_mock_get_page_is_empty():
    c = MockT212Client(FIX)
    assert await c.get_page("/api/v0/equity/history/orders?cursor=1") == {
        "items": [], "nextPagePath": None}

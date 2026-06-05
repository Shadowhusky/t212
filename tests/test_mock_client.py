import pathlib
from t212.api.mock import MockT212Client

FIX = pathlib.Path(__file__).parent / "fixtures"

async def test_mock_returns_parsed_models():
    c = MockT212Client(FIX)
    assert (await c.account_info()).currency_code == "GBP"
    assert (await c.cash()).total == 24813.07
    pos = await c.portfolio()
    assert pos[0].ticker == "AAPL_US_EQ" and round(pos[0].market_value, 2) == 2248.80
    assert (await c.instruments())[0].short_name == "AAPL"
    assert (await c.exchanges())[0].name == "NASDAQ"
    assert (await c.pies())[0].result.result == 612.40
    assert (await c.pie(42)).settings.name == "Growth Pie"

async def test_mock_history_pages():
    c = MockT212Client(FIX)
    page = await c.history_orders()
    assert page.items[0].fill_cost == 374.20
    assert page.next_cursor == "8999"
    assert (await c.dividends()).items[0].amount == 4.20
    assert (await c.transactions()).items[1].type == "WITHDRAW"

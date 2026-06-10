import pathlib
from t212.app import T212App
from t212.api.mock import MockT212Client
from textual.widgets import DataTable

FIX = pathlib.Path(__file__).parent / "fixtures"

async def test_search_filters_universe():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await app.do_refresh()                       # builds resolver
        search = app.query_one("#search")
        search.set_universe(await app.client.instruments())
        search.set_query("apple")
        await pilot.pause()
        table = app.query_one("#search-table", DataTable)
        assert table.row_count == 1
        assert "AAPL" in str(table.get_row_at(0)[0])

async def test_instrument_detail_market_hours():
    import datetime
    from t212.screens.instrument_detail import market_line, today_hours
    from t212.resolve import Resolver
    client = MockT212Client(FIX)
    r = Resolver(await client.instruments(), await client.exchanges())
    day = datetime.date(2026, 6, 10)
    line = market_line(r, "AAPL_US_EQ", day)
    assert line == "Market: NASDAQ · opens 13:30 / closes 20:00 UTC"
    # no events for another day → dim no-session line
    assert "no session today" in market_line(r, "AAPL_US_EQ", datetime.date(2026, 6, 11))
    opens, closes = today_hours(r.schedule("VUSA_GB_EQ").time_events, day)
    assert opens.hour == 7 and closes.hour == 15

async def test_instrument_detail_rows():
    app = T212App(client=MockT212Client(FIX), environment="demo", currency="GBP")
    async with app.run_test() as pilot:
        await app.do_refresh()
        search = app.query_one("#search")
        search.set_universe(await app.client.instruments())
        search.set_query("apple")
        await pilot.pause()
        table = app.query_one("#search-table", DataTable)
        table.focus()
        table.move_cursor(row=0)
        await pilot.press("enter")
        await pilot.pause()
        from textual.widgets import Static
        text = app.screen.query_one(Static).visual.plain
        assert "Max qty" in text and "25000" in text
        assert "Ext. hours" in text and "Yes" in text
        assert "Market: NASDAQ" in text

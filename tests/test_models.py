import json, pathlib
from t212.models import (AccountSummary, Position, TradableInstrument, Exchange,
                         Pie, PieDetail, PendingOrder, HistoricalOrder, Dividend, Transaction)

FIX = pathlib.Path(__file__).parent / "fixtures"
def load(name): return json.loads((FIX / f"{name}.json").read_text())

def test_account_summary():
    s = AccountSummary.model_validate(load("summary"))
    assert s.id == 1234567 and s.currency == "GBP"
    assert s.total_value == 24813.07
    assert s.cash.available_to_trade == 312.40 and s.cash.in_pies == 105.50
    assert s.investments.total_cost == 23190.84
    assert s.investments.unrealized_pnl == 1204.33
    assert s.investments.realized_pnl == 430.11

def test_position_computed():
    p = Position.model_validate(load("positions")[0])
    assert p.ticker == "AAPL_US_EQ" and p.name == "Apple Inc."
    assert round(p.market_value, 2) == 2248.80
    assert round(p.cost_basis, 2) == 2119.20
    assert round(p.pnl_pct, 4) == round(129.60 / 2119.20, 4)
    assert p.fx_ppl == -2.10
    assert p.quantity_available == 12.0

def test_position_ignores_unknown_fields():
    raw = dict(load("positions")[0], somethingNew="x")
    p = Position.model_validate(raw)
    assert p.ticker == "AAPL_US_EQ"

def test_pending_order():
    orders = [PendingOrder.model_validate(x) for x in load("orders")]
    assert orders[0].side == "BUY" and orders[0].limit_price == 180.00
    assert orders[0].time_in_force == "GOOD_TILL_CANCEL"
    assert orders[1].type == "STOP" and orders[1].stop_price == 220.00
    assert orders[1].instrument.ticker == "TSLA_US_EQ"

def test_pie_and_detail():
    pies = [Pie.model_validate(x) for x in load("pies")]
    assert pies[0].result.result == 612.40 and pies[0].progress == 0.78
    assert pies[0].dividend_details.gained == 42.18
    assert pies[1].progress is None and pies[1].status is None
    det = PieDetail.model_validate(load("pie_detail"))
    assert det.settings.name == "Growth Pie" and len(det.instruments) == 2
    assert det.settings.dividend_cash_action == "REINVEST"
    assert det.instruments[0].current_share == 0.241
    assert det.instruments[1].issues[0].name == "APPROACHING_MAX_POSITION_SIZE"

def test_historical_order():
    items = [HistoricalOrder.model_validate(x) for x in load("history_orders")["items"]]
    assert items[0].ticker == "AAPL_US_EQ"
    assert items[0].order.filled_value == 374.20
    assert items[0].fill.price == 187.10
    assert round(items[0].total_taxes, 2) == 0.56
    assert items[1].realized_pnl == 18.40

def test_historical_order_empty_defaults():
    h = HistoricalOrder.model_validate({})
    assert h.ticker == "" and h.total_taxes == 0.0 and h.realized_pnl == 0.0

def test_dividend_and_interest():
    items = [Dividend.model_validate(x) for x in load("dividends")["items"]]
    assert items[0].amount == 4.20 and items[0].instrument.name == "Apple Inc."
    assert items[0].is_interest is False
    assert items[2].is_interest is True and items[2].ticker is None

def test_transaction():
    t = Transaction.model_validate(load("transactions")["items"][2])
    assert t.type == "WITHDRAW" and t.amount == -200.0 and t.currency == "GBP"

def test_tradable_instrument():
    i = TradableInstrument.model_validate(load("instruments")[0])
    assert i.short_name == "AAPL" and i.extended_hours is True
    assert i.max_open_quantity == 25000.0 and i.added_on is not None

def test_exchange():
    ex = Exchange.model_validate(load("exchanges")[0])
    assert ex.name == "NASDAQ" and ex.working_schedules[0].id == 1
    events = ex.working_schedules[0].time_events
    assert events[0].type == "OPEN" and events[1].type == "CLOSE"

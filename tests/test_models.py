import json, pathlib
from t212.models import (AccountInfo, Cash, Position, Instrument, Exchange,
                         Pie, PieDetail, HistoryOrder, Dividend, Transaction)

FIX = pathlib.Path(__file__).parent / "fixtures"
def load(name): return json.loads((FIX / f"{name}.json").read_text())

def test_account_info():
    a = AccountInfo.model_validate(load("account_info"))
    assert a.currency_code == "GBP" and a.id == 1234567

def test_cash():
    c = Cash.model_validate(load("cash"))
    assert c.total == 24813.07 and c.ppl == 1204.33 and c.pie_cash == 3.10

def test_position_computed():
    p = Position.model_validate(load("portfolio")[0])
    assert p.ticker == "AAPL_US_EQ"
    assert round(p.market_value, 2) == 2248.80
    assert round(p.cost_basis, 2) == 2119.20
    assert round(p.pnl_pct, 4) == round(129.60 / 2119.20, 4)

def test_position_ignores_unknown_fields():
    raw = dict(load("portfolio")[0], somethingNew="x")
    p = Position.model_validate(raw)
    assert p.ticker == "AAPL_US_EQ"

def test_pie_and_detail():
    pie = Pie.model_validate(load("pies")[0])
    assert pie.result.result == 612.40 and pie.progress == 0.78
    det = PieDetail.model_validate(load("pie_detail"))
    assert det.settings.name == "Growth Pie" and len(det.instruments) == 2
    assert det.instruments[0].current_share == 0.241

def test_history_models():
    o = HistoryOrder.model_validate(load("history_orders")["items"][0])
    assert o.fill_cost == 374.20
    d = Dividend.model_validate(load("dividends")["items"][0])
    assert d.amount == 4.20
    t = Transaction.model_validate(load("transactions")["items"][1])
    assert t.type == "WITHDRAW" and t.amount == -200.0

def test_exchange():
    ex = Exchange.model_validate(load("exchanges")[0])
    assert ex.name == "NASDAQ" and ex.working_schedules[0].id == 1

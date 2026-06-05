import json, pathlib
from t212.models import Instrument, Exchange
from t212.resolve import Resolver

FIX = pathlib.Path(__file__).parent / "fixtures"

def build():
    inst = [Instrument.model_validate(x) for x in json.loads((FIX / "instruments.json").read_text())]
    exch = [Exchange.model_validate(x) for x in json.loads((FIX / "exchanges.json").read_text())]
    return Resolver(inst, exch)

def test_name_and_exchange():
    r = build()
    assert r.short_name("AAPL_US_EQ") == "AAPL"
    assert r.long_name("AAPL_US_EQ") == "Apple Inc."
    assert r.exchange("AAPL_US_EQ") == "NASDAQ"
    assert r.exchange("VUSA_GB_EQ") == "LSE"

def test_unknown_ticker_falls_back():
    r = build()
    assert r.short_name("WAT_US_EQ") == "WAT_US_EQ"
    assert r.exchange("WAT_US_EQ") is None
    assert r.instrument("WAT_US_EQ") is None

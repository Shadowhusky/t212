import pathlib
from t212.api.mock import MockT212Client
from t212.summary import build_summary, render_summary_text

FIX = pathlib.Path(__file__).parent / "fixtures"

async def test_build_summary():
    c = MockT212Client(FIX)
    s = await build_summary(c)
    assert s.currency == "GBP"
    assert s.total == 24813.07
    assert s.open_pnl == 1204.33
    assert s.in_pies == 105.50
    assert len(s.positions) == 3
    assert s.positions[0].ticker == "VUSA_GB_EQ"   # sorted by market value desc

async def test_render_text_contains_key_numbers():
    c = MockT212Client(FIX)
    s = await build_summary(c)
    text = render_summary_text(s)
    assert "£24,813.07" in text
    assert "Apple" in text or "AAPL" in text
    assert "+£1,204.33" in text
    assert "In pies" in text and "£105.50" in text

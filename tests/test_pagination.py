from t212.pagination import Page, parse_cursor

def test_parse_cursor_extracts_param():
    assert parse_cursor("/api/v0/equity/history/orders?cursor=8999&limit=20") == "8999"

def test_parse_cursor_none_when_absent():
    assert parse_cursor(None) is None
    assert parse_cursor("/api/v0/x?limit=20") is None

def test_page_holds_items():
    p = Page(items=[1, 2, 3], next_cursor="8999")
    assert p.items == [1, 2, 3] and p.next_cursor == "8999"
    assert p.has_more is True
    assert Page(items=[]).has_more is False

from t212.widgets.render import columns_for_width, POSITION_COLUMNS_FULL, POSITION_COLUMNS_COMPACT


def test_compact_drops_columns_under_100():
    assert columns_for_width(POSITION_COLUMNS_FULL, POSITION_COLUMNS_COMPACT, 120) == POSITION_COLUMNS_FULL
    assert columns_for_width(POSITION_COLUMNS_FULL, POSITION_COLUMNS_COMPACT, 80) == POSITION_COLUMNS_COMPACT

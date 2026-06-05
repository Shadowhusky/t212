from t212.theming import THEMES, theme_names

def test_three_themes_present():
    assert set(theme_names()) >= {"t212-dark", "t212-light", "t212-contrast"}

def test_dark_theme_has_semantic_colors():
    dark = THEMES["t212-dark"]
    assert dark.dark is True
    assert dark.success and dark.error and dark.accent

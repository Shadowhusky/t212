from __future__ import annotations
from textual.theme import Theme

THEMES: dict[str, Theme] = {
    "t212-dark": Theme(
        name="t212-dark", primary="#58a6ff", dark=True,
        background="#0d1117", surface="#161b22", panel="#21262d",
        accent="#58a6ff", foreground="#e6edf3",
        success="#3fb950", error="#f85149", warning="#d29922", secondary="#8b949e",
    ),
    "t212-light": Theme(
        name="t212-light", primary="#0969da", dark=False,
        background="#ffffff", surface="#f6f8fa", panel="#eaeef2",
        accent="#0969da", foreground="#1f2328",
        success="#1a7f37", error="#cf222e", warning="#9a6700", secondary="#656d76",
    ),
    "t212-contrast": Theme(
        name="t212-contrast", primary="#58a6ff", dark=True,
        background="#000000", surface="#0a0a0a", panel="#141414",
        accent="#58a6ff", foreground="#ffffff",
        success="#1f6feb", error="#e8590c", warning="#d29922", secondary="#c9d1d9",
    ),
}


def theme_names() -> list[str]:
    return list(THEMES)

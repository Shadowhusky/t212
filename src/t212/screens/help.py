from __future__ import annotations
from textual.binding import Binding
from textual.content import Content
from textual.screen import ModalScreen
from textual.widgets import Static

_SECTIONS = [
    ("Navigation", "1–5 tabs · ↑↓/jk move · ⏎ detail · Esc back"),
    ("History", "←/→ section · m load more"),
    ("Positions", "s sort · ◔ = quantity in pies"),
    ("Display", "z privacy blur · t theme · r refresh now"),
    ("Other", "? this help · ^p command palette · q quit"),
]


class HelpScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "dismiss", "Back"),
        Binding("question_mark", "dismiss", "Close", show=False),
    ]
    DEFAULT_CSS = """
    HelpScreen { align: center middle; }
    HelpScreen > Static {
        width: auto; height: auto; padding: 1 2;
        background: $panel; border: round $accent;
    }
    """

    def compose(self):
        lines = ["[b]Keys[/b]", ""]
        for name, keys in _SECTIONS:
            lines.append(f"[$accent]{name:<12}[/$accent]{keys}")
        lines.append("")
        lines.append("[dim]read-only — t212 can never place or cancel orders[/dim]")
        yield Static(Content.from_markup("\n".join(lines)), id="help-body")

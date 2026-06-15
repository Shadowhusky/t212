from __future__ import annotations
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static


class DetailModal(ModalScreen):
    """Centered, bordered, scrollable modal whose body always holds focus."""
    DEFAULT_CSS = """
    DetailModal { align: center middle; }
    DetailModal > #modal-frame {
        width: 78; max-width: 96%;
        height: auto; max-height: 90%;
        padding: 1 2; background: $panel; border: round $accent;
    }
    DetailModal #modal-hint { color: $text-muted; margin-top: 1; }
    """
    BINDINGS = [Binding("escape", "dismiss", "Back")]
    HINT = "esc back · ↑↓ scroll"

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="modal-frame"):
            yield from self.compose_body()
            yield Static(self.HINT, id="modal-hint")

    def compose_body(self) -> ComposeResult:
        return iter(())

    def on_mount(self) -> None:
        frame = self.query_one("#modal-frame", VerticalScroll)
        frame.can_focus = True
        frame.focus()
        self.populate()

    def populate(self) -> None:
        """Subclasses fill their body widgets here (called after mount)."""

from __future__ import annotations
from datetime import datetime
from textual.app import ComposeResult
from textual.binding import Binding
from textual.content import Content
from textual.screen import ModalScreen
from textual.widgets import Static
from t212.widgets.render import big_digits


class FocusScreen(ModalScreen):
    """A calm, glanceable overlay for when you're heads-down coding.

    Hides every live figure — no colour, no moving numbers — leaving just the
    time and a quiet "still running" dot. Data keeps polling behind it.
    """

    BINDINGS = [
        Binding("f", "app.toggle_focus", "Resume", show=False),
        Binding("escape", "app.toggle_focus", "Resume", show=False),
        Binding("q", "app.quit", "Quit", show=False),
    ]
    DEFAULT_CSS = """
    FocusScreen { align: center middle; background: $background; }
    FocusScreen > #focus-body { width: auto; height: auto; text-align: center; }
    """

    def compose(self) -> ComposeResult:
        yield Static(self._content(), id="focus-body")

    def on_mount(self) -> None:
        self.set_interval(10, self._update_clock)

    def _update_clock(self) -> None:
        try:
            self.query_one("#focus-body", Static).update(self._content())
        except Exception:
            pass

    def _content(self) -> Content:
        now = datetime.now()
        clock = "\n".join(f"[$text-muted]{row}[/$text-muted]"
                          for row in big_digits(now.strftime("%H:%M")))
        date = now.strftime("%A %-d %B")
        body = (
            clock
            + f"\n\n[dim]{date}[/dim]"
            + "\n\n[$success]●[/$success][dim]  t212 · still tracking[/dim]"
            + "\n\n[dim]focus mode · f to resume[/dim]"
        )
        return Content.from_markup(body)

from __future__ import annotations
from dataclasses import dataclass
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.content import Content
from textual.screen import ModalScreen
from textual.widgets import Button, Input, RadioButton, RadioSet, Static
from t212 import config
from t212.api.base import AuthError, ScopeError

_TIPS = "\n".join([
    "[dim]Get a key: Trading 212 app → ⚙ Settings → API (Beta) → Generate key[/dim]",
    "[dim]Scopes: enable the read scopes — Account, Portfolio, Pies, Metadata,",
    "History. 'Orders read' is optional (powers the pending-orders panel).",
    "t212 is read-only and can never trade.[/dim]",
    "[dim]Keys are per-environment: a live key won't work on demo and vice-versa.[/dim]",
    "[dim]Stored locally at ~/.config/t212/config.toml (chmod 600).",
    "Sent only to trading212.com.[/dim]",
])


@dataclass
class SetupResult:
    api_key: str | None
    environment: str | None
    summary: object | None

    @property
    def is_mock(self) -> bool:
        return self.api_key == "mock"


class SetupScreen(ModalScreen):
    BINDINGS = [Binding("escape", "cancel_setup", "Back", show=False)]
    DEFAULT_CSS = """
    SetupScreen { align: center middle; }
    SetupScreen > Vertical {
        width: 76; height: auto; max-height: 100%; overflow-y: auto; padding: 1 2;
        background: $panel; border: round $accent;
    }
    SetupScreen RadioSet { layout: horizontal; height: auto; margin: 1 0; }
    SetupScreen Input { margin-bottom: 1; }
    SetupScreen #setup-status { height: auto; min-height: 1; margin-bottom: 1; }
    SetupScreen #setup-buttons { height: auto; }
    SetupScreen Button { margin-right: 2; }
    """

    def __init__(self, *, validator, required: bool = False, status: str = ""):
        super().__init__()
        self._validator = validator
        self._required = required
        self._initial_status = status

    def compose(self):
        with Vertical():
            yield Static(Content.from_markup(
                "[b]t212 · connect your Trading 212 account[/b]"))
            yield Static(Content.from_markup(_TIPS), id="setup-tips")
            with RadioSet(id="setup-env"):
                yield RadioButton("Live", value=True, id="env-live")
                yield RadioButton("Demo (practice)", id="env-demo")
            yield Input(placeholder="API key ID", id="setup-key-id")
            yield Input(placeholder="API secret", password=True, id="setup-secret")
            yield Static(Content.from_markup(self._initial_status), id="setup-status")
            with Horizontal(id="setup-buttons"):
                yield Button("Validate & save", variant="primary", id="setup-validate")
                yield Button("Browse sample data", id="setup-mock")

    def on_mount(self) -> None:
        self.query_one("#setup-key-id", Input).focus()

    def _environment(self) -> str:
        return "demo" if self.query_one("#env-demo", RadioButton).value else "live"

    def _set_status(self, markup: str) -> None:
        self.query_one("#setup-status", Static).update(Content.from_markup(markup))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "setup-validate":
            await self._submit()
        elif event.button.id == "setup-mock":
            self.dismiss(SetupResult("mock", None, None))

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "setup-key-id":
            self.query_one("#setup-secret", Input).focus()
        elif event.input.id == "setup-secret":
            await self._submit()

    def action_cancel_setup(self) -> None:
        if self._required:
            self._set_status("[dim]no account connected yet — q quits[/dim]")
        else:
            self.dismiss(None)

    async def _submit(self) -> None:
        key_id = self.query_one("#setup-key-id", Input).value.strip()
        secret = self.query_one("#setup-secret", Input).value.strip()
        if not key_id or not secret:
            self._set_status("[$error]enter both the API key ID and the secret[/$error]")
            return
        environment = self._environment()
        api_key = f"{key_id}:{secret}"
        self._set_status("[dim]validating…[/dim]")
        try:
            summary = await self._validator(api_key, environment)
        except AuthError:
            self._set_status("[$error]rejected — check key ID & secret, "
                             "and that the environment matches[/$error]")
            return
        except ScopeError:
            self._set_status("[$error]key valid but missing the Account scope — "
                             "enable read scopes[/$error]")
            return
        except Exception as e:
            self._set_status(f"[$warning]could not reach Trading 212 — {str(e)[:80]}[/$warning]")
            return
        config.save_key(config.DEFAULT_CONFIG_PATH, environment, api_key)
        self._set_status(f"[$success]connected — account {summary.id} · "
                         f"{summary.currency}[/$success]")
        self.dismiss(SetupResult(api_key, environment, summary))

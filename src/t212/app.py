from __future__ import annotations
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Footer, ContentSwitcher
from t212.theming import THEMES, theme_names
from t212.widgets.summary_header import SummaryHeader

TABS = [("dashboard", "Dashboard"), ("positions", "Positions"),
        ("pies", "Pies"), ("history", "History"), ("search", "Search")]


class T212App(App):
    CSS_PATH = "widgets/styles.tcss"
    BINDINGS = [
        Binding("1", "tab('dashboard')", "Dashboard"),
        Binding("2", "tab('positions')", "Positions"),
        Binding("3", "tab('pies')", "Pies"),
        Binding("4", "tab('history')", "History"),
        Binding("5", "tab('search')", "Search"),
        Binding("z", "privacy", "Privacy"),
        Binding("t", "cycle_theme", "Theme"),
        Binding("r", "refresh_now", "Refresh"),
        Binding("question_mark", "help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    active_tab: reactive[str] = reactive("dashboard")
    privacy: reactive[bool] = reactive(False)

    def __init__(self, *, client, environment: str, currency: str,
                 store=None, resolver=None, scheduler=None):
        super().__init__()
        from t212.scheduler import RefreshScheduler
        from t212.store import Store
        self.client = client
        self.environment = environment
        self.currency = currency
        self.store = store or Store(":memory:", throttle_seconds=0)
        self.resolver = resolver
        self.scheduler = scheduler or RefreshScheduler(client)
        self._theme_idx = 0

    def on_mount(self) -> None:
        for th in THEMES.values():
            self.register_theme(th)
        self.theme = "t212-dark"

    def compose(self) -> ComposeResult:
        yield SummaryHeader(self.environment, self.currency)
        with ContentSwitcher(initial="dashboard", id="body"):
            from textual.widgets import Static
            for tab_id, label in TABS:
                yield Static(label, id=tab_id)
        yield Footer()

    def watch_active_tab(self, tab: str) -> None:
        switcher = self.query_one("#body", ContentSwitcher)
        switcher.current = tab
        if self.scheduler:
            self.scheduler.set_active(tab)

    def action_tab(self, tab: str) -> None:
        self.active_tab = tab

    def action_privacy(self) -> None:
        self.privacy = not self.privacy

    def action_cycle_theme(self) -> None:
        names = theme_names()
        self._theme_idx = (self._theme_idx + 1) % len(names)
        self.theme = names[self._theme_idx]

    def action_refresh_now(self) -> None:
        if self.scheduler:
            self.scheduler.refresh_now()

    def action_help(self) -> None:
        self.notify("1-5 tabs · ↑↓ move · ⏎ detail · z privacy · t theme · r refresh · q quit",
                    title="Keys", timeout=6)


def run_app(*, environment, mock, fixtures, refresh, api_key):
    import pathlib
    from t212.api.limits import RATE_LIMITS
    if mock:
        from t212.api.mock import MockT212Client
        client = MockT212Client(fixtures or (pathlib.Path(__file__).parent.parent.parent / "tests" / "fixtures"))
        currency = "GBP"
    else:
        from t212.api.http import HttpT212Client
        from t212.api.ratelimit import RateLimitGovernor
        from t212.config import resolve_settings
        settings = resolve_settings(environment=environment, api_key=api_key, refresh=refresh)
        client = HttpT212Client(api_key=settings.api_key, base_url=settings.base_url,
                                governor=RateLimitGovernor(RATE_LIMITS))
        currency = "GBP"
    T212App(client=client, environment=environment, currency=currency).run()

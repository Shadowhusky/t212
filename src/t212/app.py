from __future__ import annotations
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import ContentSwitcher
from t212.theming import THEMES, theme_names
from t212.widgets.hintbar import HintBar
from t212.widgets.summary_header import SummaryHeader
from t212.widgets.tabbar import TabBar

TABS = [("dashboard", "Dashboard"), ("positions", "Positions"),
        ("pies", "Pies"), ("history", "History"), ("search", "Search")]


class T212App(App):
    CSS_PATH = "widgets/styles.tcss"
    BINDINGS = [
        Binding("1", "tab('dashboard')", "Dashboard", show=False),
        Binding("2", "tab('positions')", "Positions", show=False),
        Binding("3", "tab('pies')", "Pies", show=False),
        Binding("4", "tab('history')", "History", show=False),
        Binding("5", "tab('search')", "Search", show=False),
        Binding("z", "privacy", "Privacy"),
        Binding("t", "cycle_theme", "Theme"),
        Binding("r", "refresh_now", "Refresh"),
        Binding("s", "sort", "Sort"),
        Binding("left", "history_section(-1)", "Prev section", show=False),
        Binding("right", "history_section(1)", "Next section", show=False),
        Binding("m", "history_more", "More"),
        Binding("j", "move_cursor(1)", "Down", show=False),
        Binding("k", "move_cursor(-1)", "Up", show=False),
        Binding("question_mark", "help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    active_tab: reactive[str] = reactive("dashboard")
    privacy: reactive[bool] = reactive(False)

    def __init__(self, *, client=None, environment: str, currency: str,
                 store=None, resolver=None, scheduler=None, refresh_seconds: float = 10.0,
                 persist: bool = False):
        super().__init__()
        from t212.scheduler import RefreshScheduler
        from t212.store import Store
        self.client = client
        self.environment = environment
        self.currency = currency
        self.store = store or Store(":memory:", throttle_seconds=0)
        self._store_is_default = store is None
        self._persist = persist
        self.resolver = resolver
        self.scheduler = scheduler or (RefreshScheduler(client) if client is not None else None)
        self._polling = False
        self._pending_client = None
        self._reauth_prompted = False
        self._theme_idx = 0
        self._positions = []
        self._free = 0.0
        self._refresh = refresh_seconds
        self._summary = None
        self._today = 0.0
        self._orders = None
        self._pies = []
        self._pie_names: dict[int, str] = {}
        self._pie_names_loading = False
        self._income: dict | None = None
        self._net_deposits: float | None = None
        self._history_loaded = False
        self._initial_focus_done = False

    def on_mount(self) -> None:
        for th in THEMES.values():
            self.register_theme(th)
        self.theme = "t212-dark"
        if self.client is None:
            from t212.screens.setup import SetupScreen
            self.push_screen(SetupScreen(validator=self._validate_key, required=True),
                             callback=self._setup_done)
        else:
            self._start_polling()

    def _start_polling(self) -> None:
        if not self._polling:
            self._polling = True
            self.set_interval(self._refresh_seconds(), self.do_refresh)
        self.run_worker(self.do_refresh())

    async def _validate_key(self, api_key: str, environment: str):
        from t212.api.http import HttpT212Client
        from t212.api.limits import LIVE_URL, DEMO_URL, RATE_LIMITS
        from t212.api.ratelimit import RateLimitGovernor
        base = LIVE_URL if environment == "live" else DEMO_URL
        client = HttpT212Client(api_key=api_key, base_url=base,
                                governor=RateLimitGovernor(RATE_LIMITS))
        try:
            summary = await client.summary()
        except Exception:
            await client.aclose()
            raise
        self._pending_client = client
        return summary

    def _setup_done(self, result) -> None:
        if result is None:
            return
        from t212.scheduler import RefreshScheduler
        if result.is_mock:
            import pathlib
            from t212.api.mock import MockT212Client
            self.client = MockT212Client(
                pathlib.Path(__file__).parent.parent.parent / "tests" / "fixtures")
            self.currency = "GBP"
        else:
            from t212.store import Store, default_db_path
            self.client = self._pending_client or self.client
            self._pending_client = None
            self.environment = result.environment
            self.currency = result.summary.currency
            self.store = Store(default_db_path(result.environment, result.summary.id))
            self._store_is_default = False
            self._reauth_prompted = False
        self.scheduler = RefreshScheduler(self.client)
        header = self.query_one(SummaryHeader)
        header.environment = self.environment
        header.currency = self.currency
        history = self.query_one("#history")
        history.client = self.client
        history.currency = self.currency
        self._start_polling()

    def _refresh_seconds(self) -> float:
        return self._refresh

    def compose(self) -> ComposeResult:
        yield SummaryHeader(self.environment, self.currency)
        yield TabBar(TABS)
        with ContentSwitcher(initial="dashboard", id="body"):
            from t212.screens.dashboard import Dashboard
            from t212.screens.positions import Positions
            from t212.screens.pies import Pies
            from t212.screens.history import History
            from t212.screens.search import Search
            yield Dashboard()
            yield Positions()
            yield Pies()
            yield History(self.client, self.currency)
            yield Search()
        yield HintBar()

    async def do_refresh(self) -> None:
        data = await self.scheduler.poll_once()
        summary = data.get("summary")
        if summary is not None:
            self.currency = summary.currency
        if summary is not None and self._persist and self._store_is_default:
            from t212.store import Store, default_db_path
            self.store = Store(default_db_path(self.environment, summary.id))
            self._store_is_default = False
        from t212.api.base import AuthError
        if isinstance(self.scheduler.last_error, AuthError) and not self._reauth_prompted:
            from t212.screens.setup import SetupScreen
            if not isinstance(self.screen, SetupScreen):
                self._reauth_prompted = True
                self.push_screen(
                    SetupScreen(validator=self._validate_key, required=True,
                                status="[$error]saved key was rejected — "
                                       "re-enter your credentials[/$error]"),
                    callback=self._setup_done)
        if self.resolver is None:
            from t212.resolve import Resolver
            try:
                self.resolver = Resolver(await self.client.instruments(),
                                         await self.client.exchanges())
            except Exception:
                self.resolver = Resolver([], [])
        positions = data.get("positions", [])
        if summary is not None:
            self.store.record(summary, positions, self.currency)
        today = 0.0
        if summary is not None:
            base = self.store.today_baseline()
            today = (summary.total_value - base) if base is not None else 0.0
        status = "● live" if self.scheduler.last_error is None else "◐ reconnecting"
        self.query_one(SummaryHeader).update_data(
            total=summary.total_value if summary else 0.0, today=today,
            free=summary.cash.available_to_trade if summary else 0.0,
            invested=summary.investments.total_cost if summary else 0.0,
            status=status, privacy=self.privacy)
        self._summary = summary
        self._today = today
        self._orders = data.get("orders")
        pies = data.get("pies")
        if pies is not None:
            self._pies = pies
        self._render_dashboard()
        self._positions = positions
        self._free = summary.cash.available_to_trade if summary else 0.0
        if summary is not None:
            total_value = sum(p.market_value for p in positions) + summary.cash.available_to_trade
            self.query_one("#positions").update_data(
                positions=positions, resolver=self.resolver, currency=self.currency,
                total_value=total_value, privacy=self.privacy)
        if pies is not None:
            self._dispatch_pies()
            self._ensure_pie_names()
        if summary is not None and not self._history_loaded:
            self._history_loaded = True
            self.run_worker(self.load_history_caches())
        if not self._initial_focus_done:
            self._initial_focus_done = True
            self._focus_primary(self.active_tab)

    def _render_dashboard(self) -> None:
        if self._summary is None:
            return
        self.query_one("#dashboard").update_data(
            summary=self._summary, positions=self._positions, resolver=self.resolver,
            currency=self.currency, today=self._today,
            series=self.store.equity_series(), privacy=self.privacy,
            orders=self._orders, pies=self._pies, pie_names=self._pie_names,
            scope_errors=self.scheduler.scope_errors,
            income=self._income, net_deposits=self._net_deposits)

    def _dispatch_pies(self) -> None:
        self.query_one("#pies").update_data(
            pies=self._pies, names=self._pie_names,
            currency=self.currency, privacy=self.privacy)

    def _ensure_pie_names(self) -> None:
        missing = [p.id for p in self._pies if p.id not in self._pie_names]
        if not missing or self._pie_names_loading:
            return
        self._pie_names_loading = True
        self.run_worker(self.load_pie_names(missing))

    async def load_pie_names(self, ids: list[int]) -> None:
        try:
            for pid in ids:
                try:
                    detail = await self.client.pie(pid)
                    self._pie_names[pid] = detail.settings.name or f"Pie {pid}"
                except Exception:
                    continue
        finally:
            self._pie_names_loading = False
        self._dispatch_pies()
        self._render_dashboard()

    async def _all_history_pages(self, fetch, model, max_pages: int = 10) -> list:
        page = await fetch()
        items = list(page.items)
        next_path = page.next_path
        pages = 1
        while next_path and pages < max_pages:
            raw = await self.client.get_page(next_path)
            items.extend(model.model_validate(x) for x in raw.get("items", []))
            next_path = raw.get("nextPagePath")
            pages += 1
        return items

    async def load_history_caches(self) -> None:
        from datetime import datetime, timedelta, timezone
        from t212.models import Dividend, Transaction
        try:
            divs = await self._all_history_pages(self.client.dividends, Dividend)
        except Exception:
            divs = None
        try:
            txs = await self._all_history_pages(self.client.transactions, Transaction)
        except Exception:
            txs = None
        if divs is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=365)
            def recent(d):
                dt = d.paid_on
                if dt is None:
                    return False
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt >= cutoff
            self._income = {
                "dividends": sum(d.amount for d in divs if not d.is_interest),
                "interest": sum(d.amount for d in divs if d.is_interest),
                "last12m_total": sum(d.amount for d in divs if recent(d)),
            }
        if txs is not None:
            self._net_deposits = sum(
                t.amount for t in txs if t.type in ("DEPOSIT", "WITHDRAW", "WITHDRAWAL"))
        self._render_dashboard()

    def watch_active_tab(self, tab: str) -> None:
        switcher = self.query_one("#body", ContentSwitcher)
        switcher.current = tab
        self.query_one(TabBar).set_active(tab)
        if self.scheduler is not None:
            self.scheduler.set_active(tab)
        if tab == "history":
            hist = self.query_one("#history")
            self.run_worker(self._load_history_section(hist, hist.section))
        elif tab == "search":
            search = self.query_one("#search")
            search.held = {p.ticker: p.quantity for p in self._positions}
            if self.resolver is not None:
                search.set_universe(self.resolver.all_instruments())
        self._focus_primary(tab)
        self._update_hintbar()

    async def _load_history_section(self, hist, section: str) -> None:
        await hist.load_section(section)
        self._update_hintbar()

    def _update_hintbar(self) -> None:
        try:
            bar = self.query_one(HintBar)
            has_more = self.query_one("#history").has_more
        except Exception:
            return
        width = (self.size.width or 82) - 2  # HintBar horizontal padding
        bar.set_context(self.active_tab, width, has_more=has_more)

    def on_resize(self, event) -> None:
        self._update_hintbar()

    _FOCUS_TARGETS = {"positions": "#positions-table", "pies": "#pies-table",
                      "history": "#history-table", "search": "#search-input"}

    def _focus_primary(self, tab: str) -> None:
        target = self._FOCUS_TARGETS.get(tab)
        if target is None:
            return
        try:
            self.query_one(target).focus()
        except Exception:
            pass

    def action_tab(self, tab: str) -> None:
        self.active_tab = tab

    def action_privacy(self) -> None:
        self.privacy = not self.privacy

    def watch_privacy(self, privacy: bool) -> None:
        if self._summary is None:
            return
        status = "● live" if self.scheduler.last_error is None else "◐ reconnecting"
        self.query_one(SummaryHeader).update_data(
            total=self._summary.total_value, today=self._today, free=self._free,
            invested=self._summary.investments.total_cost, status=status, privacy=privacy)
        self._render_dashboard()
        total_value = sum(p.market_value for p in self._positions) + self._free
        self.query_one("#positions").update_data(
            positions=self._positions, resolver=self.resolver, currency=self.currency,
            total_value=total_value, privacy=privacy)
        self._dispatch_pies()

    def action_cycle_theme(self) -> None:
        names = theme_names()
        self._theme_idx = (self._theme_idx + 1) % len(names)
        self.theme = names[self._theme_idx]

    def action_refresh_now(self) -> None:
        if self.scheduler is None:
            return
        self.scheduler.refresh_now()
        self.notify("Refreshing…", timeout=1.5)
        self.query_one(SummaryHeader).set_status("⟳ refreshing")

        async def _manual_refresh() -> None:
            await self.do_refresh()
            self.notify("Refreshed", severity="information", timeout=2)

        self.run_worker(_manual_refresh())

    def action_help(self) -> None:
        from t212.screens.help import HelpScreen
        if isinstance(self.screen, HelpScreen):
            self.screen.dismiss()
            return
        self.push_screen(HelpScreen())

    def action_move_cursor(self, delta: int) -> None:
        from textual.widgets import DataTable
        if isinstance(self.focused, DataTable):
            if delta > 0:
                self.focused.action_cursor_down()
            else:
                self.focused.action_cursor_up()

    async def on_data_table_row_selected(self, event) -> None:
        tid = event.data_table.id
        if tid == "positions-table":
            ticker = event.row_key.value
            pos = next((p for p in self._positions if p.ticker == ticker), None)
            if pos is not None:
                from t212.screens.position_detail import PositionDetail
                self.push_screen(PositionDetail(
                    pos, self.resolver, self.currency,
                    self.store.position_series(ticker), self.privacy))
        elif tid == "pies-table":
            from t212.screens.pie_detail import PieDetailScreen
            pie_id = int(event.row_key.value)
            detail = await self.client.pie(pie_id)
            pie = next((p for p in self._pies if p.id == pie_id), None)
            self.push_screen(PieDetailScreen(detail, self.resolver, self.currency,
                                             self.privacy, pie=pie))
        elif tid == "search-table":
            from t212.screens.instrument_detail import InstrumentDetail
            ticker = event.row_key.value
            inst = self.resolver.instrument(ticker) if self.resolver else None
            if inst is None:
                inst = next((x for x in self.query_one("#search")._instruments
                             if x.ticker == ticker), None)
            if inst is not None:
                held = next((p.quantity for p in self._positions if p.ticker == ticker), None)
                self.push_screen(InstrumentDetail(inst, self.resolver, held))

    def action_history_section(self, delta: int) -> None:
        if self.active_tab != "history":
            return
        from t212.screens.history import SECTIONS
        hist = self.query_one("#history")
        i = (SECTIONS.index(hist.section) + delta) % len(SECTIONS)
        self.run_worker(self._load_history_section(hist, SECTIONS[i]))

    def action_history_more(self) -> None:
        if self.active_tab != "history":
            self.notify("Load more works on the History tab (4)", severity="warning", timeout=2)
            return
        hist = self.query_one("#history")

        async def _more() -> None:
            n = await hist.load_more()
            if n:
                self.notify(f"Loaded {n} more", timeout=2)
            else:
                self.notify("No more pages", timeout=2)
            self._update_hintbar()

        self.run_worker(_more())

    def action_sort(self) -> None:
        if self.active_tab != "positions":
            self.notify("Sort works on the Positions tab (2)", severity="warning", timeout=2)
            return
        positions_widget = self.query_one("#positions")
        positions_widget.cycle_sort()
        if self._positions:
            total_value = sum(p.market_value for p in self._positions) + self._free
            positions_widget.update_data(
                positions=self._positions, resolver=self.resolver, currency=self.currency,
                total_value=total_value, privacy=self.privacy)
        self.notify(f"Sorted by {positions_widget.sort_label}", timeout=1.5)


def run_app(*, environment, mock, fixtures, refresh, api_key):
    import pathlib
    from t212.api.limits import RATE_LIMITS
    rs = float(refresh) if refresh else 10.0
    if mock:
        from t212.api.mock import MockT212Client
        client = MockT212Client(fixtures or (pathlib.Path(__file__).parent.parent.parent / "tests" / "fixtures"))
        T212App(client=client, environment=environment, currency="GBP", refresh_seconds=rs).run()
        return
    from t212.api.http import HttpT212Client
    from t212.api.ratelimit import RateLimitGovernor
    from t212.config import MissingKeyError, resolve_settings
    try:
        settings = resolve_settings(environment=environment, api_key=api_key, refresh=refresh)
    except MissingKeyError:
        T212App(client=None, environment=environment, currency="", refresh_seconds=rs).run()
        return
    client = HttpT212Client(api_key=settings.api_key, base_url=settings.base_url,
                            governor=RateLimitGovernor(RATE_LIMITS))
    T212App(client=client, environment=environment, currency="GBP",
            refresh_seconds=rs, persist=True).run()

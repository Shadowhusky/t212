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
        Binding("s", "sort", "Sort"),
        Binding("left", "history_section(-1)", "Prev section", show=False),
        Binding("right", "history_section(1)", "Next section", show=False),
        Binding("m", "history_more", "More", show=False),
        Binding("question_mark", "help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    active_tab: reactive[str] = reactive("dashboard")
    privacy: reactive[bool] = reactive(False)

    def __init__(self, *, client, environment: str, currency: str,
                 store=None, resolver=None, scheduler=None, refresh_seconds: float = 10.0):
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

    def on_mount(self) -> None:
        for th in THEMES.values():
            self.register_theme(th)
        self.theme = "t212-dark"
        self.set_interval(self._refresh_seconds(), self.do_refresh)
        self.run_worker(self.do_refresh())

    def _refresh_seconds(self) -> float:
        return self._refresh

    def compose(self) -> ComposeResult:
        yield SummaryHeader(self.environment, self.currency)
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
        yield Footer()

    async def do_refresh(self) -> None:
        data = await self.scheduler.poll_once()
        summary = data.get("summary")
        if summary is not None:
            self.currency = summary.currency
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
        self.scheduler.set_active(tab)
        if tab == "history":
            hist = self.query_one("#history")
            self.run_worker(hist.load_section(hist.section))
        elif tab == "search":
            search = self.query_one("#search")
            search.held = {p.ticker: p.quantity for p in self._positions}
            if self.resolver is not None:
                search.set_universe(self.resolver.all_instruments())

    def action_tab(self, tab: str) -> None:
        self.active_tab = tab

    def action_privacy(self) -> None:
        self.privacy = not self.privacy

    def action_cycle_theme(self) -> None:
        names = theme_names()
        self._theme_idx = (self._theme_idx + 1) % len(names)
        self.theme = names[self._theme_idx]

    def action_refresh_now(self) -> None:
        self.scheduler.refresh_now()
        self.run_worker(self.do_refresh())

    def action_help(self) -> None:
        self.notify("1-5 tabs · ↑↓ move · ⏎ detail · z privacy · t theme · r refresh · q quit",
                    title="Keys", timeout=6)

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
        self.run_worker(hist.load_section(SECTIONS[i]))

    def action_history_more(self) -> None:
        if self.active_tab != "history":
            return
        self.run_worker(self.query_one("#history").load_more())

    def action_sort(self) -> None:
        if self.active_tab != "positions":
            return
        positions_widget = self.query_one("#positions")
        positions_widget.cycle_sort()
        if self._positions:
            total_value = sum(p.market_value for p in self._positions) + self._free
            positions_widget.update_data(
                positions=self._positions, resolver=self.resolver, currency=self.currency,
                total_value=total_value, privacy=self.privacy)


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
    rs = float(refresh) if refresh else 10.0
    T212App(client=client, environment=environment, currency=currency, refresh_seconds=rs).run()

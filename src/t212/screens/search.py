from __future__ import annotations
from textual import events
from textual.app import ComposeResult
from textual.content import Content
from textual.widgets import DataTable, Input, Static
from t212.models import Instrument
from t212.resolve import Resolver

COLUMNS = ["TICKER", "NAME", "TYPE", "EXCHANGE", "CURRENCY", "HELD"]


class Search(Static):
    def __init__(self):
        super().__init__(id="search")
        self.held: dict[str, float] = {}
        self._instruments: list[Instrument] = []

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search ticker / name / ISIN…", id="search-input",
                    select_on_focus=False)
        yield Static("", id="search-hint")
        table = DataTable(id="search-table", cursor_type="row", zebra_stripes=False)
        table.add_columns(*COLUMNS)
        yield table

    def _resolver(self) -> Resolver:
        return getattr(self.app, "resolver", None) or Resolver([], [])

    def set_universe(self, instruments: list[Instrument]) -> None:
        self._instruments = instruments
        self._render_hint()

    def _render_hint(self, shown: int | None = None) -> None:
        n = len(self._instruments)
        if shown is None:
            msg = (f"Type to search {n:,} instruments · holdings are marked ✓"
                   if n else "Loading instruments…")
        elif shown == 0:
            msg = "No matches"
        else:
            msg = f"{shown} match{'es' if shown != 1 else ''}" + (" · showing first 200" if shown >= 200 else "")
        self.query_one("#search-hint", Static).update(Content.from_markup(f"[dim]{msg}[/dim]"))

    async def on_input_changed(self, event: Input.Changed) -> None:
        self.set_query(event.value)

    def on_key(self, event: events.Key) -> None:
        inp = self.query_one("#search-input", Input)
        # Escape moves focus from the filter input to the results, freeing 1-5 etc.
        if event.key == "escape" and inp.has_focus:
            self.query_one("#search-table", DataTable).focus()
            event.stop()
            return
        # Typing a letter while the results have focus starts filtering;
        # digits stay free for tab switching until a query is underway.
        ch = event.character
        if not inp.has_focus and ch and ch.isalpha() and len(ch) == 1 and not event.key.startswith("ctrl"):
            inp.focus()
            inp.value += ch
            inp.cursor_position = len(inp.value)
            event.stop()
            event.prevent_default()

    def set_query(self, query: str) -> None:
        q = query.strip().lower()
        r = self._resolver()
        table = self.query_one("#search-table", DataTable)
        table.clear()
        if not q:
            self._render_hint()
            return
        matches = [i for i in self._instruments
                   if q in (i.ticker or "").lower()
                   or q in (i.name or "").lower()
                   or q in (i.short_name or "").lower()
                   or q in (i.isin or "").lower()][:200]
        for i in matches:
            held = self.held.get(i.ticker)
            table.add_row(
                i.short_name or i.ticker, (i.name or "")[:24], i.type,
                r.exchange(i.ticker) or "—", i.currency_code or "—",
                f"✓ {held:g}" if held else "—", key=i.ticker)
        self._render_hint(len(matches))

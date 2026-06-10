from __future__ import annotations
from textual import events
from textual.app import ComposeResult
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
        table = DataTable(id="search-table", cursor_type="row", zebra_stripes=False)
        table.add_columns(*COLUMNS)
        yield table

    def _resolver(self) -> Resolver:
        return getattr(self.app, "resolver", None) or Resolver([], [])

    def set_universe(self, instruments: list[Instrument]) -> None:
        self._instruments = instruments

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

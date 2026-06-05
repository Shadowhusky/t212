from __future__ import annotations
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.content import Content
from textual.binding import Binding


class InstrumentDetail(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Back")]

    def __init__(self, instrument, resolver, held_qty):
        super().__init__()
        self.instrument = instrument
        self.resolver = resolver
        self.held_qty = held_qty

    def compose(self):
        i = self.instrument
        rows = [("Ticker", i.ticker), ("Type", i.type), ("ISIN", i.isin or "—"),
                ("Currency", i.currency_code or "—"),
                ("Exchange", self.resolver.exchange(i.ticker) or "—"),
                ("You hold", f"{self.held_qty:g}" if self.held_qty else "—")]
        body = f"[b]‹ {i.short_name or i.ticker} · {i.name or ''}[/b]\n\n"
        body += "\n".join(f"[dim]{k:<10}[/dim]{v}" for k, v in rows)
        yield Static(Content.from_markup(body))

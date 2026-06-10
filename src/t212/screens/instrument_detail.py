from __future__ import annotations
from datetime import date, datetime, timezone
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.content import Content
from textual.binding import Binding


def today_hours(events, day: date) -> tuple[datetime | None, datetime | None]:
    def find(kind):
        return next((e.date for e in events
                     if e.type == kind and e.date and e.date.date() == day), None)
    return find("OPEN"), find("CLOSE")


def market_line(resolver, ticker: str, day: date | None = None) -> str:
    name = resolver.exchange(ticker)
    if not name:
        return "[dim]Market: unknown[/dim]"
    schedule = resolver.schedule(ticker)
    day = day or datetime.now(timezone.utc).date()
    opens, closes = today_hours(schedule.time_events if schedule else [], day)
    if opens and closes:
        return (f"Market: {name} · opens {opens:%H:%M} / closes {closes:%H:%M} UTC")
    return f"[dim]Market: {name} · no session today[/dim]"


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
                ("Max qty", f"{i.max_open_quantity:g}" if i.max_open_quantity else "—"),
                ("Added", i.added_on.date() if i.added_on else "—"),
                ("Ext. hours", "Yes" if i.extended_hours else "No"),
                ("You hold", f"{self.held_qty:g}" if self.held_qty else "—")]
        body = f"[b]‹ {i.short_name or i.ticker} · {i.name or ''}[/b]\n\n"
        body += "\n".join(f"[dim]{k:<10}[/dim]{v}" for k, v in rows)
        body += "\n\n" + market_line(self.resolver, i.ticker)
        yield Static(Content.from_markup(body))

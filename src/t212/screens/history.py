from __future__ import annotations
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from textual.content import Content
from t212 import formatting as f
from t212.models import Dividend, HistoricalOrder, Transaction
from t212.widgets.render import pnl_cell, num, col_headers

SECTIONS = ["orders", "dividends", "transactions"]
HEADERS = {
    "orders": ["DATE", "TICKER", "SIDE", "TYPE", "QTY", "FILL", "VALUE",
               "REAL.P&L", "FEES", "STATUS"],
    "dividends": ["DATE", "NAME", "TYPE", "QTY", "PER SHARE", "AMOUNT", "TOTAL"],
    "transactions": ["DATE", "TYPE", "AMOUNT", "BALANCE"],
}
NUMERIC = {"QTY", "FILL", "VALUE", "REAL.P&L", "FEES", "PER SHARE", "AMOUNT",
           "TOTAL", "BALANCE"}
_MODELS = {"orders": HistoricalOrder, "dividends": Dividend, "transactions": Transaction}
_DIV_TYPES = {"ORDINARY": "Ord", "INTEREST": "Int", "DIVIDEND": "Div"}


def _div_type(t: str | None) -> str:
    if not t:
        return "—"
    return _DIV_TYPES.get(t, t[:8].title())


class History(Static):
    def __init__(self, client, currency: str):
        super().__init__(id="history")
        self.client = client
        self.currency = currency
        self.section = "orders"
        self._next_path: str | None = None
        self._count = 0
        self._fees = 0.0
        self._div_total = 0.0
        self._balance = 0.0
        self._net_deposits = 0.0

    @property
    def has_more(self) -> bool:
        return bool(self._next_path)

    def compose(self) -> ComposeResult:
        yield Static("‹ Orders ›  Dividends  Transactions", id="history-tabs")
        yield Static("", id="history-stats")
        yield DataTable(id="history-table", cursor_type="row", zebra_stripes=False)
        yield Static("", id="history-more")

    async def load_section(self, section: str) -> None:
        self.section = section
        fetch = {"orders": self.client.history_orders,
                 "dividends": self.client.dividends,
                 "transactions": self.client.transactions}[section]
        table = self.query_one("#history-table", DataTable)
        try:
            page = await fetch()
        except Exception:
            self._next_path = None
            table.clear(columns=True)
            table.add_columns(*col_headers(HEADERS[section], NUMERIC))
            table.add_row("couldn't load — press r to retry",
                          *[""] * (len(HEADERS[section]) - 1))
            self._render_chrome()
            return
        self._next_path = None
        self._count = 0
        self._fees = self._div_total = self._balance = self._net_deposits = 0.0
        table.clear(columns=True)
        table.add_columns(*col_headers(HEADERS[section], NUMERIC))
        self._add_items(page.items)
        self._next_path = page.next_path
        if table.row_count == 0:
            table.add_row("(none)", *[""] * (len(HEADERS[section]) - 1))
        self._render_chrome()

    async def load_more(self) -> int | None:
        if not self._next_path:
            return None
        try:
            raw = await self.client.get_page(self._next_path)
            model = _MODELS[self.section]
            items = [model.model_validate(x) for x in raw.get("items", [])]
            self._add_items(items)
            self._next_path = raw.get("nextPagePath")
            self._render_chrome()
            return len(items)
        except Exception:
            return None

    def _add_items(self, items) -> None:
        cur = self.currency
        table = self.query_one("#history-table", DataTable)
        if self.section == "orders":
            for h in items:
                o = h.order
                fill_price = h.fill.price if h.fill else None
                self._count += 1
                self._fees += h.total_taxes
                side = (o.side if o else None) or "—"
                side_cell = Text(side, style="green" if side == "BUY" else
                                 "red" if side == "SELL" else "dim")
                table.add_row(
                    o.created_at.strftime("%m-%d %H:%M") if o and o.created_at else "—",
                    f.display_ticker(h.ticker) or "—",
                    side_cell,
                    (o.type if o else None) or "—",
                    num(f"{o.filled_quantity:g}" if o and o.filled_quantity else "—"),
                    num(f"{fill_price:,.2f}" if fill_price else "—"),
                    num(f.money(o.filled_value, cur) if o and o.filled_value else "—"),
                    pnl_cell(h.realized_pnl, cur),
                    Text(f.money(h.total_taxes, cur), style="dim", justify="right"),
                    (o.status if o else None) or "—")
        elif self.section == "dividends":
            for d in items:
                self._div_total += d.amount
                name = "Cash interest" if d.is_interest else (
                    (d.instrument.name if d.instrument else None) or d.ticker or "—")
                table.add_row(
                    d.paid_on.strftime("%Y-%m-%d") if d.paid_on else "—",
                    name[:24],
                    _div_type(d.type),
                    num(f"{d.quantity:g}" if d.quantity else "—"),
                    num(f"{d.gross_per_share:,.4f}" if d.gross_per_share else "—"),
                    num(f.money(d.amount, cur)), num(f.money(self._div_total, cur)))
        else:
            for tx in items:
                self._balance += tx.amount
                if tx.type in ("DEPOSIT", "WITHDRAW", "WITHDRAWAL"):
                    self._net_deposits += tx.amount
                table.add_row(
                    tx.date_time.strftime("%Y-%m-%d") if tx.date_time else "—",
                    tx.type, num(f.signed_money(tx.amount, cur)),
                    num(f.money(self._balance, cur)))

    def _render_chrome(self) -> None:
        cur = self.currency
        titles = {"orders": "Orders", "dividends": "Dividends", "transactions": "Transactions"}
        tabs = "  ".join(f"‹ {titles[s]} ›" if s == self.section else titles[s]
                         for s in SECTIONS)
        self.query_one("#history-tabs", Static).update(tabs)
        stats = {
            "orders": f"{self._count} orders · fees {f.money(self._fees, cur)}",
            "dividends": f"total received {f.money(self._div_total, cur)}",
            "transactions": f"net deposits {f.money(self._net_deposits, cur)}",
        }[self.section]
        self.query_one("#history-stats", Static).update(
            Content.from_markup(f"[dim]{stats}[/dim]"))
        more = "[dim]▾ m: load more[/dim]" if self._next_path else ""
        self.query_one("#history-more", Static).update(Content.from_markup(more))

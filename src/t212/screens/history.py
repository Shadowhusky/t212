from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from t212.resolve import Resolver
from t212 import formatting as f

SECTIONS = ["orders", "dividends", "transactions"]
HEADERS = {
    "orders": ["DATE", "TICKER", "TYPE", "QTY", "FILL", "VALUE", "STATUS"],
    "dividends": ["DATE", "TICKER", "QTY", "PER SHARE", "AMOUNT", "TOTAL"],
    "transactions": ["DATE", "TYPE", "AMOUNT", "BALANCE"],
}


class History(Static):
    def __init__(self, client, currency: str):
        super().__init__(id="history")
        self.client = client
        self.currency = currency
        self.section = "orders"

    def compose(self) -> ComposeResult:
        yield Static("‹ Orders ›  Dividends  Transactions", id="history-tabs")
        yield DataTable(id="history-table", cursor_type="row")

    def _resolver(self) -> Resolver:
        return getattr(self.app, "resolver", None) or Resolver([], [])

    async def load_section(self, section: str) -> None:
        self.section = section
        r = self._resolver()
        cur = self.currency
        table = self.query_one("#history-table", DataTable)
        table.clear(columns=True)
        table.add_columns(*HEADERS[section])
        if section == "orders":
            page = await self.client.history_orders()
            for o in page.items:
                table.add_row(
                    o.date_created.strftime("%m-%d %H:%M") if o.date_created else "—",
                    r.short_name(o.ticker), o.type or "—",
                    f"{o.filled_quantity:g}" if o.filled_quantity else "—",
                    f"{o.fill_price:,.2f}" if o.fill_price else "—",
                    f.money(o.fill_cost, cur) if o.fill_cost else "—",
                    o.status or "—")
        elif section == "dividends":
            page = await self.client.dividends()
            running = 0.0
            for d in page.items:
                running += d.amount
                table.add_row(
                    d.paid_on.strftime("%Y-%m-%d") if d.paid_on else "—",
                    r.short_name(d.ticker),
                    f"{d.quantity:g}" if d.quantity else "—",
                    f.money(d.gross_per_share, cur) if d.gross_per_share else "—",
                    f.money(d.amount, cur), f.money(running, cur))
        else:
            page = await self.client.transactions()
            balance = 0.0
            for tx in page.items:
                balance += tx.amount
                table.add_row(
                    tx.date_time.strftime("%Y-%m-%d") if tx.date_time else "—",
                    tx.type, f.signed_money(tx.amount, cur), f.money(balance, cur))

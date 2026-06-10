from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from t212 import formatting as f

SECTIONS = ["orders", "dividends", "transactions"]
HEADERS = {
    "orders": ["DATE", "TICKER", "SIDE", "TYPE", "QTY", "FILL", "VALUE", "STATUS"],
    "dividends": ["DATE", "NAME", "TYPE", "AMOUNT", "TOTAL"],
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

    async def load_section(self, section: str) -> None:
        self.section = section
        cur = self.currency
        table = self.query_one("#history-table", DataTable)
        table.clear(columns=True)
        table.add_columns(*HEADERS[section])
        if section == "orders":
            page = await self.client.history_orders()
            for h in page.items:
                o = h.order
                fill_price = h.fill.price if h.fill else None
                table.add_row(
                    o.created_at.strftime("%m-%d %H:%M") if o and o.created_at else "—",
                    f.display_ticker(h.ticker) or "—",
                    (o.side if o else None) or "—",
                    (o.type if o else None) or "—",
                    f"{o.filled_quantity:g}" if o and o.filled_quantity else "—",
                    f"{fill_price:,.2f}" if fill_price else "—",
                    f.money(o.filled_value, cur) if o and o.filled_value else "—",
                    (o.status if o else None) or "—")
        elif section == "dividends":
            page = await self.client.dividends()
            running = 0.0
            for d in page.items:
                running += d.amount
                name = "Cash interest" if d.is_interest else (
                    (d.instrument.name if d.instrument else None) or d.ticker or "—")
                table.add_row(
                    d.paid_on.strftime("%Y-%m-%d") if d.paid_on else "—",
                    name[:24],
                    (d.type or "—")[:12],
                    f.money(d.amount, cur), f.money(running, cur))
        else:
            page = await self.client.transactions()
            balance = 0.0
            for tx in page.items:
                balance += tx.amount
                table.add_row(
                    tx.date_time.strftime("%Y-%m-%d") if tx.date_time else "—",
                    tx.type, f.signed_money(tx.amount, cur), f.money(balance, cur))
        if table.row_count == 0:
            ncols = len(HEADERS[section])
            table.add_row("(none)", *[""] * (ncols - 1))

from __future__ import annotations
from textual.content import Content
from textual.widgets import Static
from t212 import formatting as f

_PNL_TAG = {"gain": "$success", "loss": "$error", "flat": "$text-muted"}


class SummaryHeader(Static):
    DEFAULT_CSS = "SummaryHeader { height: 3; padding: 0 1; }"

    def __init__(self, environment: str, currency: str):
        super().__init__()
        self.environment = environment
        self.currency = currency
        self._total = 0.0
        self._today = 0.0
        self._free = 0.0
        self._invested = 0.0
        self._open_pnl = 0.0
        self._open_pnl_pct = 0.0
        self._privacy = False
        self._status = "○ connecting"

    def update_data(self, *, total, today, free, invested, status, privacy,
                    open_pnl: float = 0.0, open_pnl_pct: float = 0.0):
        self._total, self._today = total, today
        self._free, self._invested = free, invested
        self._open_pnl, self._open_pnl_pct = open_pnl, open_pnl_pct
        self._status, self._privacy = status, privacy
        self.update(self._render())

    def set_status(self, status: str) -> None:
        self._status = status
        self.update(self._render())

    def _render(self) -> Content:
        cur = self.currency
        today_tag = _PNL_TAG[f.pnl_class(self._today)]
        today_txt = f"{f.arrow(self._today)} {f.signed_money(self._today, cur, blur=self._privacy)}"
        pnl_tag = _PNL_TAG[f.pnl_class(self._open_pnl)]
        pnl_txt = (f"{f.arrow(self._open_pnl)} "
                   f"{f.signed_money(self._open_pnl, cur, blur=self._privacy)} "
                   f"{f.percent(self._open_pnl_pct)}")
        st_tag = "$warning" if "reconnect" in self._status.lower() else "$success"
        private = "  [$warning]◌ private[/$warning]" if self._privacy else ""
        markup = (
            f"[b] t212  [/b][{st_tag}]{self._status}[/{st_tag}]"
            f"[b] · {self.environment.upper()} · {cur}[/b]{private}\n"
            f"[dim] Portfolio value  [/dim]"
            f"[b]{f.money(self._total, cur, blur=self._privacy)}[/b]"
            f"[dim]   P&L [/dim]"
            f"[{pnl_tag}]{pnl_txt}[/{pnl_tag}]"
            f"[dim]   Today [/dim]"
            f"[{today_tag}]{today_txt}[/{today_tag}]"
            f"[dim]   Free {f.money(self._free, cur, blur=self._privacy)}[/dim]"
        )
        return Content.from_markup(markup)

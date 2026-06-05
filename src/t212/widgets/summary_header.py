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
        self._privacy = False
        self._status = "○ connecting"

    def update_data(self, *, total, today, free, invested, status, privacy):
        self._total, self._today = total, today
        self._free, self._invested = free, invested
        self._status, self._privacy = status, privacy
        self.update(self._render())

    def _render(self) -> Content:
        cur = self.currency
        pnl_tag = _PNL_TAG[f.pnl_class(self._today)]
        today_txt = f"{f.arrow(self._today)} {f.signed_money(self._today, cur, blur=self._privacy)}"
        markup = (
            f"[b] t212  {self._status} · {self.environment.upper()} · {cur}[/b]\n"
            f"[dim] Portfolio value  [/dim]"
            f"[b]{f.money(self._total, cur, blur=self._privacy)}[/b]"
            f"[dim]   Today [/dim]"
            f"[{pnl_tag}]{today_txt}[/{pnl_tag}]"
            f"[dim]   Free {f.money(self._free, cur, blur=self._privacy)}[/dim]"
        )
        return Content.from_markup(markup)

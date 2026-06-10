from __future__ import annotations
from textual.content import Content
from textual.widgets import Static


class TabBar(Static):
    DEFAULT_CSS = "TabBar { height: 1; padding: 0 1; }"

    def __init__(self, tabs: list[tuple[str, str]]):
        super().__init__()
        self._tabs = tabs
        self._active = tabs[0][0] if tabs else ""

    def on_mount(self) -> None:
        self._render_tabs()

    def set_active(self, tab_id: str) -> None:
        self._active = tab_id
        self._render_tabs()

    def _render_tabs(self) -> None:
        parts = []
        for n, (tab_id, label) in enumerate(self._tabs, start=1):
            if tab_id == self._active:
                parts.append(f"[b][$accent] {n} {label} [/$accent][/b]")
            else:
                parts.append(f"[dim] {n} {label} [/dim]")
        self.update(Content.from_markup(" ".join(parts)))

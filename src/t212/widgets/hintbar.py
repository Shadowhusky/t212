from __future__ import annotations
from textual.content import Content
from textual.widgets import Static

COMMON = "1-5 tabs · ⏎ detail · ? help · q quit"
TAB_HINTS = {"positions": ["s sort"], "search": ["type to filter", "esc → results"]}
EXTRA = ["/ find", "z privacy", "f focus", "t theme", "r refresh", "j/k move"]


class HintBar(Static):
    DEFAULT_CSS = "HintBar { dock: bottom; height: auto; padding: 0 1; color: $text-muted; }"

    def set_context(self, tab: str, width: int, has_more: bool = False) -> None:
        segments = [COMMON, *TAB_HINTS.get(tab, [])]
        if tab == "history":
            segments.append("←→ section")
            if has_more:
                segments.append("m more")
        extra = list(EXTRA)
        line = " · ".join(segments + extra)
        while extra and len(line) > width:
            extra.pop()
            line = " · ".join(segments + extra)
        self.update(Content.from_markup(f"[dim]{line}[/dim]"))

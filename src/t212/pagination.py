from __future__ import annotations
from dataclasses import dataclass, field
from typing import Generic, TypeVar
from urllib.parse import urlsplit, parse_qs

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    items: list[T] = field(default_factory=list)
    next_cursor: str | None = None
    next_path: str | None = None

    @property
    def has_more(self) -> bool:
        return self.next_cursor is not None or self.next_path is not None


def parse_cursor(next_page_path: str | None) -> str | None:
    if not next_page_path:
        return None
    qs = parse_qs(urlsplit(next_page_path).query)
    values = qs.get("cursor")
    return values[0] if values else None

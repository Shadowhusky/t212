from __future__ import annotations
from t212.models import Instrument, Exchange, WorkingSchedule


class Resolver:
    def __init__(self, instruments: list[Instrument], exchanges: list[Exchange]):
        self._by_ticker = {i.ticker: i for i in instruments}
        self._exchange_by_schedule: dict[int, str] = {}
        self._schedule_by_id: dict[int, WorkingSchedule] = {}
        for ex in exchanges:
            for ws in ex.working_schedules:
                self._exchange_by_schedule[ws.id] = ex.name
                self._schedule_by_id[ws.id] = ws

    def instrument(self, ticker: str) -> Instrument | None:
        return self._by_ticker.get(ticker)

    def short_name(self, ticker: str) -> str:
        inst = self._by_ticker.get(ticker)
        return (inst.short_name or inst.name) if inst and (inst.short_name or inst.name) else ticker

    def long_name(self, ticker: str) -> str:
        inst = self._by_ticker.get(ticker)
        return (inst.name or inst.short_name) if inst and (inst.name or inst.short_name) else ticker

    def exchange(self, ticker: str) -> str | None:
        inst = self._by_ticker.get(ticker)
        if not inst or inst.working_schedule_id is None:
            return None
        return self._exchange_by_schedule.get(inst.working_schedule_id)

    def schedule(self, ticker: str) -> WorkingSchedule | None:
        inst = self._by_ticker.get(ticker)
        if not inst or inst.working_schedule_id is None:
            return None
        return self._schedule_by_id.get(inst.working_schedule_id)

    def all_instruments(self) -> list[Instrument]:
        return list(self._by_ticker.values())

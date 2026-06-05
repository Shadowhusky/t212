from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class AccountInfo(_Base):
    currency_code: str = Field(alias="currencyCode")
    id: int


class Cash(_Base):
    free: float
    total: float
    invested: float
    ppl: float
    result: float
    pie_cash: float = Field(alias="pieCash", default=0.0)
    blocked: float | None = None


class Position(_Base):
    ticker: str
    quantity: float
    average_price: float = Field(alias="averagePrice")
    current_price: float = Field(alias="currentPrice")
    ppl: float
    fx_ppl: float | None = Field(alias="fxPpl", default=None)
    initial_fill_date: datetime | None = Field(alias="initialFillDate", default=None)
    max_buy: float | None = Field(alias="maxBuy", default=None)
    max_sell: float | None = Field(alias="maxSell", default=None)
    pie_quantity: float | None = Field(alias="pieQuantity", default=None)

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.average_price

    @property
    def pnl_pct(self) -> float | None:
        return self.ppl / self.cost_basis if self.cost_basis else None


class Instrument(_Base):
    ticker: str
    type: str
    isin: str | None = None
    currency_code: str | None = Field(alias="currencyCode", default=None)
    name: str | None = None
    short_name: str | None = Field(alias="shortName", default=None)
    working_schedule_id: int | None = Field(alias="workingScheduleId", default=None)


class WorkingSchedule(_Base):
    id: int


class Exchange(_Base):
    id: int
    name: str
    working_schedules: list[WorkingSchedule] = Field(alias="workingSchedules", default_factory=list)


class PieResult(_Base):
    invested: float = Field(alias="priceAvgInvestedValue")
    value: float = Field(alias="priceAvgValue")
    result: float = Field(alias="priceAvgResult")
    result_coef: float = Field(alias="priceAvgResultCoef")


class Pie(_Base):
    id: int
    cash: float = 0.0
    result: PieResult
    progress: float | None = None
    status: str | None = None
    dividend_details: dict | None = Field(alias="dividendDetails", default=None)


class PieInstrument(_Base):
    ticker: str
    current_share: float = Field(alias="currentShare")
    expected_share: float = Field(alias="expectedShare")
    owned_quantity: float = Field(alias="ownedQuantity")
    result: PieResult


class PieSettings(_Base):
    id: int
    name: str | None = None
    goal: float | None = None
    icon: str | None = None


class PieDetail(_Base):
    settings: PieSettings
    instruments: list[PieInstrument] = Field(default_factory=list)


class Order(_Base):
    id: int
    ticker: str
    type: str | None = None
    quantity: float | None = None
    limit_price: float | None = Field(alias="limitPrice", default=None)
    stop_price: float | None = Field(alias="stopPrice", default=None)
    status: str | None = None


class HistoryOrder(_Base):
    ticker: str
    type: str | None = None
    status: str | None = None
    filled_quantity: float | None = Field(alias="filledQuantity", default=None)
    fill_price: float | None = Field(alias="fillPrice", default=None)
    fill_cost: float | None = Field(alias="fillCost", default=None)
    date_created: datetime | None = Field(alias="dateCreated", default=None)


class Dividend(_Base):
    ticker: str
    quantity: float | None = None
    amount: float
    gross_per_share: float | None = Field(alias="grossAmountPerShare", default=None)
    paid_on: datetime | None = Field(alias="paidOn", default=None)
    type: str | None = None


class Transaction(_Base):
    type: str
    amount: float
    reference: str | None = None
    date_time: datetime | None = Field(alias="dateTime", default=None)

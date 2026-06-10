from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class InstrumentRef(_Base):
    ticker: str
    currency: str | None = None
    isin: str | None = None
    name: str | None = None


class CashBreakdown(_Base):
    available_to_trade: float = Field(alias="availableToTrade", default=0.0)
    in_pies: float = Field(alias="inPies", default=0.0)
    reserved_for_orders: float = Field(alias="reservedForOrders", default=0.0)


class Investments(_Base):
    current_value: float = Field(alias="currentValue", default=0.0)
    total_cost: float = Field(alias="totalCost", default=0.0)
    realized_pnl: float = Field(alias="realizedProfitLoss", default=0.0)
    unrealized_pnl: float = Field(alias="unrealizedProfitLoss", default=0.0)


class AccountSummary(_Base):
    id: int
    currency: str
    total_value: float = Field(alias="totalValue", default=0.0)
    cash: CashBreakdown = Field(default_factory=CashBreakdown)
    investments: Investments = Field(default_factory=Investments)


class PositionWalletImpact(_Base):
    currency: str | None = None
    current_value: float = Field(alias="currentValue", default=0.0)
    fx_impact: float = Field(alias="fxImpact", default=0.0)
    total_cost: float = Field(alias="totalCost", default=0.0)
    unrealized_pnl: float = Field(alias="unrealizedProfitLoss", default=0.0)


class Position(_Base):
    instrument: InstrumentRef
    quantity: float = 0.0
    average_price: float = Field(alias="averagePricePaid", default=0.0)
    current_price: float = Field(alias="currentPrice", default=0.0)
    created_at: datetime | None = Field(alias="createdAt", default=None)
    quantity_available: float = Field(alias="quantityAvailableForTrading", default=0.0)
    quantity_in_pies: float = Field(alias="quantityInPies", default=0.0)
    wallet: PositionWalletImpact = Field(alias="walletImpact", default_factory=PositionWalletImpact)

    @property
    def ticker(self) -> str:
        return self.instrument.ticker

    @property
    def name(self) -> str:
        return self.instrument.name or self.ticker

    @property
    def market_value(self) -> float:
        return self.wallet.current_value

    @property
    def ppl(self) -> float:
        return self.wallet.unrealized_pnl

    @property
    def cost_basis(self) -> float:
        return self.wallet.total_cost

    @property
    def pnl_pct(self) -> float | None:
        return self.ppl / self.cost_basis if self.cost_basis else None

    @property
    def fx_ppl(self) -> float:
        return self.wallet.fx_impact


class Tax(_Base):
    charged_at: datetime | None = Field(alias="chargedAt", default=None)
    currency: str | None = None
    name: str | None = None
    quantity: float = 0.0


class FillWalletImpact(_Base):
    currency: str | None = None
    fx_rate: float | None = Field(alias="fxRate", default=None)
    net_value: float = Field(alias="netValue", default=0.0)
    realized_pnl: float = Field(alias="realisedProfitLoss", default=0.0)
    taxes: list[Tax] = Field(default_factory=list)


class Fill(_Base):
    filled_at: datetime | None = Field(alias="filledAt", default=None)
    id: int | None = None
    price: float = 0.0
    quantity: float = 0.0
    trading_method: str | None = Field(alias="tradingMethod", default=None)
    type: str | None = None
    wallet: FillWalletImpact | None = Field(alias="walletImpact", default=None)


class PendingOrder(_Base):
    created_at: datetime | None = Field(alias="createdAt", default=None)
    currency: str | None = None
    extended_hours: bool = Field(alias="extendedHours", default=False)
    filled_quantity: float = Field(alias="filledQuantity", default=0.0)
    filled_value: float = Field(alias="filledValue", default=0.0)
    id: int | None = None
    initiated_from: str | None = Field(alias="initiatedFrom", default=None)
    instrument: InstrumentRef | None = None
    limit_price: float | None = Field(alias="limitPrice", default=None)
    quantity: float = 0.0
    side: str | None = None
    status: str | None = None
    stop_price: float | None = Field(alias="stopPrice", default=None)
    strategy: str | None = None
    ticker: str | None = None
    time_in_force: str | None = Field(alias="timeInForce", default=None)
    type: str | None = None
    value: float = 0.0


class HistoricalOrder(_Base):
    fill: Fill | None = None
    order: PendingOrder | None = None

    @property
    def ticker(self) -> str:
        if self.order is not None:
            if self.order.ticker:
                return self.order.ticker
            if self.order.instrument is not None and self.order.instrument.ticker:
                return self.order.instrument.ticker
        return ""

    @property
    def total_taxes(self) -> float:
        if self.fill is not None and self.fill.wallet is not None:
            return sum(t.quantity for t in self.fill.wallet.taxes)
        return 0.0

    @property
    def realized_pnl(self) -> float:
        if self.fill is not None and self.fill.wallet is not None:
            return self.fill.wallet.realized_pnl
        return 0.0


class Dividend(_Base):
    amount: float = 0.0
    amount_eur: float | None = Field(alias="amountInEuro", default=None)
    currency: str | None = None
    gross_per_share: float | None = Field(alias="grossAmountPerShare", default=None)
    instrument: InstrumentRef | None = None
    paid_on: datetime | None = Field(alias="paidOn", default=None)
    quantity: float | None = None
    reference: str | None = None
    ticker: str | None = None
    type: str | None = None

    @property
    def is_interest(self) -> bool:
        return "INTEREST" in (self.type or "")


class Transaction(_Base):
    type: str
    amount: float = 0.0
    currency: str | None = None
    date_time: datetime | None = Field(alias="dateTime", default=None)
    reference: str | None = None


class TradableInstrument(_Base):
    ticker: str
    added_on: datetime | None = Field(alias="addedOn", default=None)
    currency_code: str | None = Field(alias="currencyCode", default=None)
    extended_hours: bool = Field(alias="extendedHours", default=False)
    isin: str | None = None
    max_open_quantity: float | None = Field(alias="maxOpenQuantity", default=None)
    name: str | None = None
    short_name: str | None = Field(alias="shortName", default=None)
    type: str = "STOCK"
    working_schedule_id: int | None = Field(alias="workingScheduleId", default=None)


Instrument = TradableInstrument


class TimeEvent(_Base):
    date: datetime | None = None
    type: str | None = None


class WorkingSchedule(_Base):
    id: int
    time_events: list[TimeEvent] = Field(alias="timeEvents", default_factory=list)


class Exchange(_Base):
    id: int
    name: str
    working_schedules: list[WorkingSchedule] = Field(alias="workingSchedules", default_factory=list)


class DividendDetails(_Base):
    gained: float = 0.0
    in_cash: float = Field(alias="inCash", default=0.0)
    reinvested: float = 0.0


class InvestmentResult(_Base):
    invested: float = Field(alias="priceAvgInvestedValue", default=0.0)
    value: float = Field(alias="priceAvgValue", default=0.0)
    result: float = Field(alias="priceAvgResult", default=0.0)
    result_coef: float = Field(alias="priceAvgResultCoef", default=0.0)


class Pie(_Base):
    id: int
    cash: float = 0.0
    dividend_details: DividendDetails = Field(alias="dividendDetails", default_factory=DividendDetails)
    result: InvestmentResult = Field(default_factory=InvestmentResult)
    progress: float | None = None
    status: str | None = None


class InstrumentIssue(_Base):
    name: str | None = None
    severity: str | None = None


class PieInstrument(_Base):
    ticker: str
    current_share: float = Field(alias="currentShare", default=0.0)
    expected_share: float = Field(alias="expectedShare", default=0.0)
    owned_quantity: float = Field(alias="ownedQuantity", default=0.0)
    issues: list[InstrumentIssue] = Field(default_factory=list)
    result: InvestmentResult = Field(default_factory=InvestmentResult)


class PieSettings(_Base):
    id: int
    name: str | None = None
    goal: float | None = None
    icon: str | None = None
    creation_date: datetime | None = Field(alias="creationDate", default=None)
    dividend_cash_action: str | None = Field(alias="dividendCashAction", default=None)
    end_date: datetime | None = Field(alias="endDate", default=None)
    initial_investment: float | None = Field(alias="initialInvestment", default=None)
    instrument_shares: dict | None = Field(alias="instrumentShares", default=None)
    public_url: str | None = Field(alias="publicUrl", default=None)


class PieDetail(_Base):
    settings: PieSettings
    instruments: list[PieInstrument] = Field(default_factory=list)

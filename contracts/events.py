from dataclasses import dataclass


@dataclass(frozen=True)
class MeterReading:
    meter_id: str
    timestamp: str  # ISO format, e.g. "2026-10-07T09:00:00"
    kwh: float


@dataclass(frozen=True)
class TradeMatched:
    event_id: str
    trade_id: str
    seller_id: str
    buyer_id: str
    kwh: float
    price_per_kwh: float


@dataclass(frozen=True)
class EnergyDeliveryVerified:
    event_id: str
    trade_id: str
    delivered_kwh: float

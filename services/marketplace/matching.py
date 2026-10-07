"""Marketplace context (Member 1): match a buyer's bid to the cheapest suitable offer."""
import uuid
from dataclasses import dataclass

from contracts.events import TradeMatched


@dataclass
class Offer:
    seller_id: str
    kwh: float
    price_per_kwh: float


@dataclass
class Bid:
    buyer_id: str
    kwh: float
    max_price_per_kwh: float


def match(bid: Bid, offers: list[Offer]) -> TradeMatched | None:
    """Return a TradeMatched event for the cheapest offer that covers the bid, or None."""
    suitable = [
        o for o in offers
        if o.kwh >= bid.kwh and o.price_per_kwh <= bid.max_price_per_kwh
    ]
    if not suitable:
        return None
    best = min(suitable, key=lambda o: o.price_per_kwh)
    best.kwh -= bid.kwh                      # reduce the seller's remaining energy
    return TradeMatched(
        event_id=str(uuid.uuid4()),
        trade_id=str(uuid.uuid4()),
        seller_id=best.seller_id,
        buyer_id=bid.buyer_id,
        kwh=bid.kwh,
        price_per_kwh=best.price_per_kwh,
    )

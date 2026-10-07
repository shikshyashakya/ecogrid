# an orchestrated saga with idempotent event handling
# and a double-entry ledger. Steps: reserve funds -> verify delivery -> charge (pro-rata) -> release rest
from dataclasses import dataclass, field

from contracts.events import EnergyDeliveryVerified, TradeMatched


@dataclass
class LedgerEntry:
    trade_id: str
    debit_account: str
    credit_account: str
    amount: float


@dataclass
class SettlementService:
    balances: dict[str, float] = field(default_factory=dict)
    reserved: dict[str, float] = field(default_factory=dict)  # trade_id -> amount held
    trades: dict[str, TradeMatched] = field(default_factory=dict)
    status: dict[str, str] = field(default_factory=dict)  # trade_id -> saga state
    ledger: list[LedgerEntry] = field(default_factory=list)
    processed_events: set[str] = field(default_factory=set)

    def _already_processed(self, event_id: str) -> bool:
        """Idempotency: the same event delivered twice is handled only once."""
        if event_id in self.processed_events:
            return True
        self.processed_events.add(event_id)
        return False

    def on_trade_matched(self, e: TradeMatched) -> None:
        if self._already_processed(e.event_id):
            return
        cost = round(e.kwh * e.price_per_kwh, 2)
        if self.balances.get(e.buyer_id, 0.0) < cost:
            self.status[e.trade_id] = "REJECTED_INSUFFICIENT_FUNDS"
            return
        self.balances[e.buyer_id] -= cost  # step 2: hold funds (not yet paid)
        self.reserved[e.trade_id] = cost
        self.trades[e.trade_id] = e
        self.status[e.trade_id] = "FUNDS_RESERVED"

    def on_delivery_verified(self, e: EnergyDeliveryVerified) -> None:
        if self._already_processed(e.event_id):
            return
        trade = self.trades.get(e.trade_id)
        if trade is None or self.status.get(e.trade_id) != "FUNDS_RESERVED":
            return
        held = self.reserved.pop(e.trade_id)
        delivered = min(e.delivered_kwh, trade.kwh)
        charge = round(delivered * trade.price_per_kwh, 2)  # pro-rata if short
        refund = round(held - charge, 2)
        self.balances[trade.seller_id] = (
            self.balances.get(trade.seller_id, 0.0) + charge
        )
        self.balances[trade.buyer_id] += refund
        self.ledger.append(
            LedgerEntry(e.trade_id, trade.buyer_id, trade.seller_id, charge)
        )
        self.status[e.trade_id] = "SETTLED"

    def cancel(self, trade_id: str) -> None:
        """Compensation: release the hold if verification never arrives (e.g. timeout)."""
        if self.status.get(trade_id) != "FUNDS_RESERVED":
            return
        buyer = self.trades[trade_id].buyer_id
        self.balances[buyer] += self.reserved.pop(trade_id)
        self.status[trade_id] = "CANCELLED"

    def total_money(self) -> float:
        """All money in wallets plus money on hold. A saga must never create or lose money."""
        return round(sum(self.balances.values()) + sum(self.reserved.values()), 2)

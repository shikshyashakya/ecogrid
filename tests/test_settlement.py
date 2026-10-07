from contracts.events import EnergyDeliveryVerified, TradeMatched
from services.settlement.saga import SettlementService


def make_service():
    return SettlementService(balances={"buyer": 10.0, "seller": 0.0})


TRADE = TradeMatched("e1", "t1", "seller", "buyer", kwh=2.0, price_per_kwh=0.25)


def test_full_saga_settles_trade():
    s = make_service()
    s.on_trade_matched(TRADE)
    s.on_delivery_verified(EnergyDeliveryVerified("e2", "t1", 2.0))
    assert s.status["t1"] == "SETTLED"
    assert s.balances == {"buyer": 9.5, "seller": 0.5}


def test_duplicate_event_does_not_charge_twice():
    s = make_service()
    s.on_trade_matched(TRADE)
    s.on_trade_matched(TRADE)                 # same event delivered again
    assert s.balances["buyer"] == 9.5


def test_short_delivery_charges_pro_rata():
    s = make_service()
    s.on_trade_matched(TRADE)
    s.on_delivery_verified(EnergyDeliveryVerified("e2", "t1", 1.0))   # only half delivered
    assert s.balances == {"buyer": 9.75, "seller": 0.25}


def test_insufficient_funds_rejected():
    s = SettlementService(balances={"buyer": 0.1})
    s.on_trade_matched(TRADE)
    assert s.status["t1"] == "REJECTED_INSUFFICIENT_FUNDS"


def test_cancel_releases_hold():
    s = make_service()
    s.on_trade_matched(TRADE)
    s.cancel("t1")                            # compensation, e.g. verification timed out
    assert s.status["t1"] == "CANCELLED"
    assert s.balances["buyer"] == 10.0


def test_money_is_never_created_or_lost():
    s = make_service()
    s.on_trade_matched(TRADE)
    assert s.total_money() == 10.0
    s.on_delivery_verified(EnergyDeliveryVerified("e2", "t1", 1.5))
    assert s.total_money() == 10.0

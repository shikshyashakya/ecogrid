from fastapi.testclient import TestClient

from services.marketplace.api import app, offers

client = TestClient(app)


def test_offer_then_bid_matches():
    offers.clear()
    client.post("/offers", json={"seller_id": "s1", "kwh": 5, "price_per_kwh": 0.25})
    response = client.post("/bids", json={"buyer_id": "b1", "kwh": 2, "max_price_per_kwh": 0.30})
    assert response.status_code == 200
    assert response.json()["status"] == "matched"

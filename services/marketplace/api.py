"""Marketplace HTTP API (Member 1). Run with: uvicorn services.marketplace.api:app --reload"""
from dataclasses import asdict

from fastapi import FastAPI
from pydantic import BaseModel

from services.marketplace.matching import Bid, Offer, match

app = FastAPI(title="EcoGrid Marketplace")
offers: list[Offer] = []


class OfferIn(BaseModel):
    seller_id: str
    kwh: float
    price_per_kwh: float


class BidIn(BaseModel):
    buyer_id: str
    kwh: float
    max_price_per_kwh: float


@app.post("/offers")
def create_offer(body: OfferIn) -> dict:
    offers.append(Offer(**body.model_dump()))
    return {"status": "listed", "open_offers": len(offers)}


@app.post("/bids")
def create_bid(body: BidIn) -> dict:
    trade = match(Bid(**body.model_dump()), offers)
    if trade is None:
        return {"status": "no_match"}
    return {"status": "matched", "trade": asdict(trade)}

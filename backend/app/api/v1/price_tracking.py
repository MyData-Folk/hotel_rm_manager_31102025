from __future__ import annotations

from fastapi import APIRouter, Body

from ...services.price_tracking import generate_price_scenarios

router = APIRouter(prefix="/price-tracking", tags=["Price Tracking"])


@router.post("/simulate")
async def simulate_price(payload: dict = Body(default_factory=dict)):
    return generate_price_scenarios(payload)

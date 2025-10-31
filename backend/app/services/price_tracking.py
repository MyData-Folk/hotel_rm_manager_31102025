from __future__ import annotations

import io
import logging
import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def calculate_commission(price: float, partner: str = "OTA") -> float:
    commission_rates = {
        "Booking.com": 0.18,
        "Expedia": 0.15,
        "Airbnb": 0.15,
        "Direct": 0.0,
        "OTA": 0.16,
        "OTA RO FLEX": 0.16,
    }
    rate = commission_rates.get(partner, 0.15)
    return round(price * rate, 2)


def calculate_final_price(base_price: float, commission: float, discount: float = 0) -> float:
    return round(base_price + commission - discount, 2)


def simulate_price_evolution(base_price: float, room_type: str, plan_name: str, days: int) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    room_multipliers = {
        "Double Classique": 1.0,
        "Suite Junior": 1.5,
        "Suite Deluxe": 2.0,
        "Suite Présidentielle": 3.2,
    }
    plan_multipliers = {
        "OTA RO FLEX": 1.0,
        "Direct Flexible": 0.9,
        "Non-Refundable": 0.85,
        "Early Bird": 0.8,
        "Last Minute": 1.1,
    }
    room_mult = room_multipliers.get(room_type, 1.0)
    plan_mult = plan_multipliers.get(plan_name, 1.0)
    for offset in range(days):
        seasonal_factor = 1 + 0.1 * math.sin(2 * math.pi * offset / 7)
        random_factor = 1 + random.uniform(-0.05, 0.08)
        trend_factor = 1 + (offset * 0.001)
        daily_price = base_price * room_mult * plan_mult * seasonal_factor * random_factor * trend_factor
        commission = calculate_commission(daily_price, plan_name)
        final_price = calculate_final_price(daily_price, commission)
        data.append(
            {
                "date": (datetime.utcnow() + timedelta(days=offset)).strftime("%Y-%m-%d"),
                "room_type": room_type,
                "plan_name": plan_name,
                "base_price": round(daily_price, 2),
                "commission": commission,
                "final_price": final_price,
                "is_available": random.random() > 0.1,
                "partner": plan_name,
                "currency": "EUR",
            }
        )
    return data


def compute_analytics(price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not price_data:
        return {
            "period": "",
            "average_price": 0.0,
            "min_price": 0.0,
            "max_price": 0.0,
            "price_variance": 0.0,
            "availability_rate": 0.0,
            "trend": "stable",
        }
    prices = [item["final_price"] for item in price_data]
    availability_rate = sum(1 for item in price_data if item["is_available"]) / len(price_data) * 100
    trend = "stable"
    if prices[-1] > prices[0] * 1.05:
        trend = "increasing"
    elif prices[-1] < prices[0] * 0.95:
        trend = "decreasing"
    return {
        "period": f"{price_data[0]['date']} → {price_data[-1]['date']}",
        "average_price": round(sum(prices) / len(prices), 2),
        "min_price": round(min(prices), 2),
        "max_price": round(max(prices), 2),
        "price_variance": round(max(prices) - min(prices), 2),
        "availability_rate": round(availability_rate, 2),
        "trend": trend,
    }


def generate_price_scenarios(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        base_price = float(payload.get("base_price", 120.0))
        room_type = payload.get("room_type", "Double Classique")
        plan_name = payload.get("plan_name", "OTA RO FLEX")
        days = int(payload.get("days", 14))
    except (ValueError, TypeError) as exc:  # pragma: no cover - defensive
        logger.error("Invalid payload received for price scenario generation: %s", exc)
        raise HTTPException(status_code=400, detail="Payload invalide") from exc
    data = simulate_price_evolution(base_price, room_type, plan_name, days)
    return {
        "success": True,
        "message": "Séries tarifaires générées",
        "price_data": data,
        "analytics": compute_analytics(data),
    }


def export_price_report(price_data: List[Dict[str, Any]]) -> bytes:
    try:
        import pandas as pd

        output = io.BytesIO()
        pd.DataFrame(price_data).to_excel(output, index=False)
        output.seek(0)
        return output.read()
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to export price report")
        raise HTTPException(status_code=500, detail="Erreur export suivi des tarifs") from exc

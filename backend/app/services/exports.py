from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Dict

import pandas as pd
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


def _build_simulation_dataframe(data: Dict) -> pd.ExcelWriter:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1 - Details
        detail_rows = []
        for day in data.get("results", []):
            gross_price = day.get("gross_price", 0) or 0
            net_price = day.get("net_price", 0) or 0
            partner_discount = (gross_price - (day.get("price_after_partner_discount", 0) or 0))
            promo_discount = ((day.get("price_after_partner_discount", 0) or 0) - (day.get("price_after_promo", 0) or 0))
            stock = day.get("stock", 0)
            detail_rows.append(
                {
                    "Date": day.get("date_display", day.get("date")),
                    "Prix brut (€)": round(gross_price, 2),
                    "Remise partenaire (€)": round(partner_discount, 2),
                    "Remise promo (€)": round(promo_discount, 2),
                    "Prix après remises (€)": round(day.get("price_after_promo", 0) or 0, 2),
                    "Commission (€)": round(day.get("commission", 0) or 0, 2),
                    "Prix net (€)": round(net_price, 2),
                    "Stock": stock,
                    "Revenue potentiel (€)": round(gross_price * stock, 2),
                }
            )
        pd.DataFrame(detail_rows).to_excel(writer, sheet_name="Détail quotidien", index=False)

        summary = data.get("summary", {})
        sim_info = data.get("simulation_info", {})
        total_days = len(data.get("results", [])) or 1
        available_days = len([row for row in data.get("results", []) if row.get("stock", 0) > 0])
        occupancy_rate = (available_days / total_days) * 100 if total_days else 0
        avg_daily_revenue = (summary.get("total_net", 0) / max(available_days, 1)) if available_days else 0
        summary_rows = {
            "Métrique": [
                "Hôtel",
                "Chambre",
                "Plan tarifaire",
                "Partenaire",
                "Période",
                "Nombre de nuits",
                "Taux d'occupation (%)",
                "Sous-total brut (€)",
                "Total remises partenaire (€)",
                "Total remises promo (€)",
                "Total commissions (€)",
                "Total net (€)",
                "Revenue moyen / nuit (€)",
                "Jours disponibles",
                "Jours complets",
            ],
            "Valeur": [
                sim_info.get("hotel_id", ""),
                sim_info.get("room", ""),
                sim_info.get("plan", ""),
                sim_info.get("partner", "Direct"),
                f"{sim_info.get('start_date', '')} au {sim_info.get('end_date', '')}",
                sim_info.get("nights", total_days),
                round(occupancy_rate, 2),
                round(summary.get("subtotal_brut", 0), 2),
                round(summary.get("total_partner_discount", 0), 2),
                round(summary.get("total_promo_discount", 0), 2),
                round(summary.get("total_commission", 0), 2),
                round(summary.get("total_net", 0), 2),
                round(avg_daily_revenue, 2),
                available_days,
                total_days - available_days,
            ],
        }
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Résumé exécutif", index=False)

        partner = sim_info.get("partner")
        if partner and partner.lower() != "direct":
            partner_rows = {
                "Métrique partenaire": [
                    "Nom partenaire",
                    "Commission (%)",
                    "Remise partenaire (%)",
                    "Commission totale (€)",
                    "Économie partenaire (€)",
                ],
                "Valeur": [
                    partner,
                    sim_info.get("partner_commission", 0),
                    sim_info.get("partner_discount", 0),
                    round(summary.get("total_commission", 0), 2),
                    round(summary.get("total_partner_discount", 0), 2),
                ],
            }
            pd.DataFrame(partner_rows).to_excel(writer, sheet_name="Analyse partenaire", index=False)

        availability_rows = []
        for day in data.get("results", []):
            stock = day.get("stock", 0)
            if stock:
                price = day.get("gross_price", 0) or 0
                availability_rows.append(
                    {
                        "Date": day.get("date_display", day.get("date")),
                        "Stock": stock,
                        "Prix/nuit (€)": round(price, 2),
                        "Revenue potentiel (€)": round(price * stock, 2),
                    }
                )
        if availability_rows:
            pd.DataFrame(availability_rows).to_excel(writer, sheet_name="Analyse disponibilité", index=False)
    output.seek(0)
    return output


def export_simulation(data: Dict, filename_prefix: str = "simulation") -> StreamingResponse:
    try:
        output = _build_simulation_dataframe(data)
        hotel_id = data.get("simulation_info", {}).get("hotel_id", "hotel")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{hotel_id}_{timestamp}.xlsx"
        logger.info("Excel simulation export generated", extra={"filename": filename})
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to export simulation")
        raise HTTPException(status_code=500, detail=f"Erreur export simulation: {exc}") from exc


def export_reservation_simulation(data: Dict) -> StreamingResponse:
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            rows = []
            total_revenue = 0.0
            total_nights = 0
            for day in data.get("results", []):
                stock = day.get("stock", 0)
                net_price = day.get("net_price", 0) or 0
                booking_rate = 0.5 if stock else 0
                reservations = round(stock * booking_rate, 0)
                revenue = reservations * net_price
                total_revenue += revenue
                if stock:
                    total_nights += 1
                rows.append(
                    {
                        "Date": day.get("date_display", day.get("date")),
                        "Stock disponible": stock,
                        "Prix net (€)": round(net_price, 2),
                        "Taux réservation estimé (%)": round(booking_rate * 100, 1),
                        "Réservations prévues": int(reservations),
                        "Revenue prévu (€)": round(revenue, 2),
                    }
                )
            pd.DataFrame(rows).to_excel(writer, sheet_name="Prévisions réservation", index=False)
            resume = {
                "Métrique": ["Total revenu prévu (€)", "Nuits disponibles", "Revenue moyen par nuit (€)"],
                "Valeur": [round(total_revenue, 2), total_nights, round(total_revenue / max(total_nights, 1), 2)],
            }
            pd.DataFrame(resume).to_excel(writer, sheet_name="Résumé financier", index=False)
        output.seek(0)
        filename = f"reservation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to export reservation simulation")
        raise HTTPException(status_code=500, detail=f"Erreur export réservation: {exc}") from exc

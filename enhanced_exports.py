# Améliorations pour l'export Excel - HotelManager Pro V2
# Ajoutez ces fonctions à votre fichier main.py existant

import io
import pandas as pd
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import logging

logger = logging.getLogger(__name__)

# ==========================================
# 1. EXPORT SIMULATION AMÉLIORÉ
# ==========================================

async def export_simulation_enhanced(data: dict, filename_prefix: str = "simulation"):
    """Version améliorée de l'export simulation avec plus de détails et graphiques"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # === FEUILLE 1: DÉTAIL PAR JOUR ===
            df_data = []
            for day in data.get("results", []):
                # Calculs supplémentaires pour l'analyse
                gross_price = day.get("gross_price", 0) or 0
                net_price = day.get("net_price", 0) or 0
                commission = day.get("commission", 0) or 0
                partner_discount = ((day.get("gross_price", 0) or 0) - (day.get("price_after_partner_discount", 0) or 0))
                promo_discount = ((day.get("price_after_partner_discount", 0) or 0) - (day.get("price_after_promo", 0) or 0))
                
                df_data.append({
                    "Date": day.get("date_display", day.get("date")),
                    "Jour": day.get("date", ""),
                    "Prix Brut (€)": round(gross_price, 2),
                    "Remise Partenaire (€)": round(partner_discount, 2),
                    "Remise Promo (€)": round(promo_discount, 2),
                    "Prix Après Remises (€)": round(day.get("price_after_promo", 0) or 0, 2),
                    "Commission (€)": round(commission, 2),
                    "Prix Net (€)": round(net_price, 2),
                    "Marge (%)": round((net_price / gross_price * 100) if gross_price > 0 else 0, 2),
                    "Stock": day.get("stock", 0),
                    "Disponibilité": "Disponible" if day.get("stock", 0) > 0 else "Complet",
                    "Revenue Potentiel (€)": round(gross_price * day.get("stock", 0), 2) if day.get("stock", 0) > 0 else 0
                })
            
            df = pd.DataFrame(df_data)
            df.to_excel(writer, sheet_name='Détail Quotidien', index=False)
            
            # === FEUILLE 2: RÉSUMÉ EXÉCUTIF ===
            summary = data.get("summary", {})
            sim_info = data.get("simulation_info", {})
            
            # Calculs additionnels pour le résumé
            total_days = len(data.get("results", []))
            available_days = len([r for r in data.get("results", []) if r.get("stock", 0) > 0])
            occupancy_rate = (available_days / total_days * 100) if total_days > 0 else 0
            avg_daily_revenue = (summary.get("total_net", 0) / available_days) if available_days > 0 else 0
            
            summary_data = {
                "Métrique": [
                    "Hôtel", "Chambre", "Plan Tarifaire", "Partenaire", 
                    "Période", "Nombre de nuits", "Taux d'occupation (%)",
                    "Sous-Total Brut (€)", "Total Remises Partenaire (€)", 
                    "Total Remises Promo (€)", "Total Commissions (€)", 
                    "Total Net (€)", "Revenue Moyen/Nuit (€)",
                    "Jours Disponibles", "Jours Complets"
                ],
                "Valeur": [
                    sim_info.get("hotel_id", ""),
                    sim_info.get("room", ""),
                    sim_info.get("plan", ""),
                    sim_info.get("partner", "Direct"),
                    f"{sim_info.get('start_date', '')} au {sim_info.get('end_date', '')}",
                    sim_info.get("nights", 0),
                    round(occupancy_rate, 1),
                    round(summary.get("subtotal_brut", 0), 2),
                    round(summary.get("total_partner_discount", 0), 2),
                    round(summary.get("total_promo_discount", 0), 2),
                    round(summary.get("total_commission", 0), 2),
                    round(summary.get("total_net", 0), 2),
                    round(avg_daily_revenue, 2),
                    available_days,
                    total_days - available_days
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Résumé Exécutif', index=False)
            
            # === FEUILLE 3: ANALYSE PARTENAIRE ===
            if sim_info.get("partner") and sim_info.get("partner") != "Direct":
                partner_data = {
                    "Métrique Partenaire": [
                        "Nom Partenaire", "Commission (%)", "Remise Partenaire (%)", 
                        "Commission Totale (€)", "Économie Partenaire (€)", "ROI Commission"
                    ],
                    "Valeur": [
                        sim_info.get("partner", ""),
                        sim_info.get("partner_commission", 0),
                        sim_info.get("partner_discount", 0),
                        round(summary.get("total_commission", 0), 2),
                        round(summary.get("total_partner_discount", 0), 2),
                        round((summary.get("total_net", 0) / summary.get("total_commission", 1)) if summary.get("total_commission", 0) > 0 else 0, 2)
                    ]
                }
                
                partner_df = pd.DataFrame(partner_data)
                partner_df.to_excel(writer, sheet_name='Analyse Partenaire', index=False)
            
            # === FEUILLE 4: ANALYSE DISPONIBILITÉ ===
            availability_data = []
            for day in data.get("results", []):
                stock = day.get("stock", 0)
                if stock > 0:
                    revenue_per_room = day.get("gross_price", 0) or 0
                    total_revenue_potential = revenue_per_room * stock
                    availability_data.append({
                        "Date": day.get("date_display", day.get("date")),
                        "Stock": stock,
                        "Prix/Nuit": round(revenue_per_room, 2),
                        "Revenue Potentiel": round(total_revenue_potential, 2),
                        "Taux Occupation Estimé": "N/A"  # Pourrait être calculé avec données historiques
                    })
            
            if availability_data:
                availability_df = pd.DataFrame(availability_data)
                availability_df.to_excel(writer, sheet_name='Analyse Disponibilité', index=False)
        
        output.seek(0)
        
        # Nom de fichier dynamique
        hotel_id = data.get("simulation_info", {}).get("hotel_id", "unknown")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{hotel_id}_{timestamp}.xlsx"
        
        logger.info(f"Export Excel amélioré généré: {filename}")
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erreur export Excel amélioré: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export amélioré: {str(e)}")


# ==========================================
# 2. EXPORT SIMULATION DE RÉSERVATION
# ==========================================

async def export_reservation_simulation(data: dict):
    """Export des simulations de réservation"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # === FEUILLE 1: PRÉVISIONS DE RÉSERVATION ===
            df_data = []
            total_projected_revenue = 0
            total_available_rooms = 0
            
            for day in data.get("results", []):
                stock = day.get("stock", 0)
                net_price = day.get("net_price", 0) or 0
                
                # Simulation simple:假设50%的 taux de réservation quand disponible
                assumed_booking_rate = 0.5 if stock > 0 else 0
                projected_bookings = round(stock * assumed_booking_rate, 0)
                projected_revenue = projected_bookings * net_price
                
                total_projected_revenue += projected_revenue
                total_available_rooms += stock
                
                df_data.append({
                    "Date": day.get("date_display", day.get("date")),
                    "Stock Disponible": stock,
                    "Prix Net (€)": round(net_price, 2),
                    "Taux Réservation Estimé (%)": round(assumed_booking_rate * 100, 1),
                    "Réservations Prévues": int(projected_bookings),
                    "Revenue Prévu (€)": round(projected_revenue, 2),
                    "Revenue Moyen/ Chambre (€)": round(net_price * assumed_booking_rate, 2)
                })
            
            reservation_df = pd.DataFrame(df_data)
            reservation_df.to_excel(writer, sheet_name='Prévisions Réservation', index=False)
            
            # === FEUILLE 2: RÉSUMÉ FINANCIER ===
            total_nights = len([r for r in data.get("results", []) if r.get("stock", 0) > 0])
            avg_daily_revenue = total_projected_revenue / total_nights if total_nights > 0 else 0
            total_gross_revenue = sum((r.get("gross_price", 0) or 0) * r.get("stock", 0) for r in data.get("results", []))
            
            financial_summary = {
                "Métrique": [
                    "Total Nuits Disponibles",
                    "Total Chambres Disponibles", 
                    "Revenue Brut Potentiel (€)",
                    "Revenue Net Prévu (€)",
                    "Revenue Moyen/Nuit (€)",
                    "Taux Commission Moyen (%)",
                    "Impact Remises (%)"
                ],
                "Valeur": [
                    total_nights,
                    total_available_rooms,
                    round(total_gross_revenue, 2),
                    round(total_projected_revenue, 2),
                    round(avg_daily_revenue, 2),
                    "Variable par partenaire",
                    "Variable par simulation"
                ]
            }
            
            financial_df = pd.DataFrame(financial_summary)
            financial_df.to_excel(writer, sheet_name='Résumé Financier', index=False)
            
            # === FEUILLE 3: ANALYSE TRIMESTRIELLE (si données suffisantes) ===
            quarterly_data = []
            quarters = {
                'Q1': ['01', '02', '03'], 'Q2': ['04', '05', '06'],
                'Q3': ['07', '08', '09'], 'Q4': ['10', '11', '12']
            }
            
            for quarter, months in quarters.items():
                quarter_revenue = 0
                quarter_rooms = 0
                quarter_nights = 0
                
                for day in data.get("results", []):
                    date_str = day.get("date", "")
                    if any(month in date_str for month in months):
                        stock = day.get("stock", 0)
                        net_price = day.get("net_price", 0) or 0
                        quarter_revenue += stock * net_price * 0.5  # Taux réservation 50%
                        quarter_rooms += stock
                        if stock > 0:
                            quarter_nights += 1
                
                if quarter_rooms > 0:
                    quarterly_data.append({
                        "Trimestre": quarter,
                        "Revenue Prévu (€)": round(quarter_revenue, 2),
                        "Chambres Disponibles": quarter_rooms,
                        "Nuits Commercialisables": quarter_nights,
                        "Revenue Moyen/Chambre (€)": round(quarter_revenue / quarter_rooms, 2) if quarter_rooms > 0 else 0
                    })
            
            if quarterly_data:
                quarterly_df = pd.DataFrame(quarterly_data)
                quarterly_df.to_excel(writer, sheet_name='Analyse Trimestrielle', index=False)
        
        output.seek(0)
        
        hotel_id = data.get("simulation_info", {}).get("hotel_id", "unknown")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reservation_simulation_{hotel_id}_{timestamp}.xlsx"
        
        logger.info(f"Export simulation réservation généré: {filename}")
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erreur export simulation réservation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur export réservation: {str(e)}")


# ==========================================
# 3. EXPORT DISPONIBILITÉS
# ==========================================

async def export_availability(data: dict):
    """Export des disponibilités en format Excel"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            period = data.get("period", {})
            availability = data.get("availability", {})
            
            # === FEUILLE 1: MATRICE DE DISPONIBILITÉ ===
            # Préparer les données pour la matrice
            matrix_data = []
            dates = period.get("dates", [])
            date_display = period.get("date_display", {})
            
            for room_name, room_availability in availability.items():
                row = {"Chambre": room_name}
                for date_str in dates:
                    stock = room_availability.get(date_str, 0)
                    # Indicateur visuel de disponibilité
                    if stock == 0:
                        indicator = "🔴 Complet"
                    elif stock < 3:
                        indicator = "🟡 Faible"
                    else:
                        indicator = "🟢 Disponible"
                    
                    row[date_display.get(date_str, date_str)] = f"{stock} ({indicator})"
                matrix_data.append(row)
            
            matrix_df = pd.DataFrame(matrix_data)
            matrix_df.to_excel(writer, sheet_name='Matrice Disponibilités', index=False)
            
            # === FEUILLE 2: ANALYSE PAR DATE ===
            date_analysis = []
            for date_str in dates:
                total_stock = 0
                rooms_available = 0
                rooms_full = 0
                avg_price_by_room = {}
                
                for room_name, room_availability in availability.items():
                    stock = room_availability.get(date_str, 0)
                    total_stock += stock
                    
                    if stock > 0:
                        rooms_available += 1
                        # Ici on pourrait ajouter les prix si disponibles
                    else:
                        rooms_full += 1
                
                date_analysis.append({
                    "Date": date_display.get(date_str, date_str),
                    "Chambres Disponibles": rooms_available,
                    "Chambres Complètes": rooms_full,
                    "Stock Total": total_stock,
                    "Taux Disponibilité (%)": round((rooms_available / (rooms_available + rooms_full)) * 100, 1) if (rooms_available + rooms_full) > 0 else 0,
                    "Statut Global": "🟢 Bon" if total_stock > 10 else "🟡 Moyen" if total_stock > 3 else "🔴 Critique"
                })
            
            date_analysis_df = pd.DataFrame(date_analysis)
            date_analysis_df.to_excel(writer, sheet_name='Analyse par Date', index=False)
            
            # === FEUILLE 3: ANALYSE PAR TYPE DE CHAMBRE ===
            room_analysis = []
            for room_name, room_availability in availability.items():
                total_stock = sum(room_availability.values())
                available_days = len([s for s in room_availability.values() if s > 0])
                full_days = len([s for s in room_availability.values() if s == 0])
                avg_daily_stock = total_stock / len(dates) if dates else 0
                
                # Calcul du taux d'occupation estimé (jours complets vs total)
                occupancy_rate = (full_days / len(dates)) if dates else 0
                
                room_analysis.append({
                    "Type Chambre": room_name,
                    "Stock Total Période": total_stock,
                    "Jours Disponibles": available_days,
                    "Jours Complets": full_days,
                    "Moyenne Journalière": round(avg_daily_stock, 1),
                    "Taux Occupation (%)": round(occupancy_rate * 100, 1),
                    "Recommandation": "Prioritaire" if avg_daily_stock < 2 else "Normal" if avg_daily_stock < 5 else "Surveillance"
                })
            
            room_analysis_df = pd.DataFrame(room_analysis)
            room_analysis_df.to_excel(writer, sheet_name='Analyse par Chambre', index=False)
            
            # === FEUILLE 4: PLANNING VISUEL (GRILLE) ===
            # Créer une grille visuelle avec dates en colonnes et chambres en lignes
            planning_data = []
            
            # En-têtes
            header_row = ["Chambre"] + [date_display.get(date, date) for date in dates]
            planning_data.append(header_row)
            
            # Données
            for room_name, room_availability in availability.items():
                row = [room_name]
                for date_str in dates:
                    stock = room_availability.get(date_str, 0)
                    if stock == 0:
                        symbol = "❌"
                    elif stock == 1:
                        symbol = "⚠️1"
                    elif stock == 2:
                        symbol = "⚠️2"
                    elif stock < 5:
                        symbol = f"🟡{stock}"
                    else:
                        symbol = f"🟢{stock}"
                    row.append(symbol)
                planning_data.append(row)
            
            planning_df = pd.DataFrame(planning_data[1:], columns=planning_data[0])
            planning_df.to_excel(writer, sheet_name='Planning Visuel', index=False)
        
        output.seek(0)
        
        hotel_id = data.get("hotel_id", "unknown")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"disponibilites_{hotel_id}_{timestamp}.xlsx"
        
        logger.info(f"Export disponibilités généré: {filename}")
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erreur export disponibilités: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur export disponibilités: {str(e)}")


# ==========================================
# 4. MODÈLES PYDANTIC POUR LES NOUVELLES EXPORTS
# ==========================================

class ExportSimulationRequest(BaseModel):
    """Modèle pour l'export de simulation amélioré"""
    data: dict
    filename_prefix: Optional[str] = "simulation"

class ExportReservationRequest(BaseModel):
    """Modèle pour l'export de simulation de réservation"""
    data: dict

class ExportAvailabilityRequest(BaseModel):
    """Modèle pour l'export de disponibilités"""
    data: dict


# ==========================================
# 5. NOUVEAUX ENDPOINTS À AJOUTER À VOTRE API
# ==========================================

# Ajoutez ces endpoints à votre fichier main.py

@app.post("/export/simulation/enhanced", tags=["Export"])
async def export_simulation_enhanced_endpoint(request: ExportSimulationRequest):
    """Export Excel amélioré des simulations tarifaires"""
    try:
        return await export_simulation_enhanced(request.data, request.filename_prefix)
    except Exception as e:
        logger.error(f"Erreur export simulation amélioré: {str(e)}")
        with Session(engine) as session:
            log_activity(
                session,
                activity_type="export.failed",
                description="Échec export simulation amélioré",
                details={"error": str(e)},
                performed_by="enhanced-export"
            )
            session.commit()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export amélioré: {str(e)}")


@app.post("/export/reservation", tags=["Export"])
async def export_reservation_endpoint(request: ExportReservationRequest):
    """Export Excel des simulations de réservation"""
    try:
        return await export_reservation_simulation(request.data)
    except Exception as e:
        logger.error(f"Erreur export réservation: {str(e)}")
        with Session(engine) as session:
            log_activity(
                session,
                activity_type="export.failed",
                description="Échec export simulation réservation",
                details={"error": str(e)},
                performed_by="reservation-export"
            )
            session.commit()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export réservation: {str(e)}")


@app.post("/export/availability", tags=["Export"])
async def export_availability_endpoint(request: ExportAvailabilityRequest):
    """Export Excel des disponibilités"""
    try:
        return await export_availability(request.data)
    except Exception as e:
        logger.error(f"Erreur export disponibilités: {str(e)}")
        with Session(engine) as session:
            log_activity(
                session,
                activity_type="export.failed",
                description="Échec export disponibilités",
                details={"error": str(e)},
                performed_by="availability-export"
            )
            session.commit()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export disponibilités: {str(e)}")


@app.post("/export/batch", tags=["Export"])
async def export_batch_endpoint(data: dict):
    """Export groupé de plusieurs types d'export"""
    try:
        export_type = data.get("type", "simulation")
        
        if export_type == "simulation":
            return await export_simulation_enhanced(data.get("data", {}), "batch_simulation")
        elif export_type == "reservation":
            return await export_reservation_simulation(data.get("data", {}))
        elif export_type == "availability":
            return await export_availability(data.get("data", {}))
        else:
            raise HTTPException(status_code=400, detail="Type d'export non supporté")
            
    except Exception as e:
        logger.error(f"Erreur export batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export groupé: {str(e)}")
"""
Module d'extension pour le suivi des tarifs - HotelManager Pro V2
Ce fichier contient les ajouts nécessaires au main.py pour supporter la fonctionnalité de suivi des tarifs.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)

# ===============================
# MODÈLES DE DONNÉES POUR LE SUIVI DES TARIFS
# ===============================

class PriceTrackingRequest(BaseModel):
    """Modèle pour la requête de suivi des tarifs"""
    start_date: str = Field(description="Date de début (YYYY-MM-DD)")
    end_date: str = Field(description="Date de fin (YYYY-MM-DD)")
    room_type: str = Field(description="Type de chambre", default="Double Classique")
    plan_name: str = Field(description="Nom du plan tarifaire", default="OTA RO FLEX")

class PriceData(BaseModel):
    """Modèle pour les données de tarif"""
    date: str
    room_type: str
    plan_name: str
    base_price: float
    commission: float
    final_price: float
    is_available: bool
    partner: Optional[str] = None
    currency: str = "EUR"

class PriceTrackingResponse(BaseModel):
    """Modèle de réponse pour le suivi des tarifs"""
    success: bool
    message: str
    price_data: List[PriceData]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PriceAnalytics(BaseModel):
    """Modèle pour les analytics de prix"""
    period: str
    average_price: float
    min_price: float
    max_price: float
    price_variance: float
    availability_rate: float
    trend: str  # "increasing", "decreasing", "stable"

# ===============================
# FONCTIONS UTILITAIRES
# ===============================

def calculate_commission(price: float, partner: str = "OTA") -> float:
    """Calcule la commission selon le partenaire"""
    commission_rates = {
        "Booking.com": 0.18,
        "Expedia": 0.15,
        "Airbnb": 0.15,
        "Direct": 0.00,
        "OTA": 0.16,
        "OTA RO FLEX": 0.16
    }
    
    rate = commission_rates.get(partner, 0.15)
    return round(price * rate, 2)

def calculate_final_price(base_price: float, commission: float, discount: float = 0) -> float:
    """Calcule le prix final en appliquant la commission et les descuentos"""
    final_price = base_price + commission - discount
    return round(final_price, 2)

def simulate_price_evolution(base_price: date, room_type: str, plan_name: str, days_range: int) -> List[Dict]:
    """
    Simule l'évolution des prix sur une période donnée
    Cette fonction génère des données réalistes pour démonstration
    """
    import random
    import math
    
    price_data = []
    current_price = base_price if isinstance(base_price, (int, float)) else 100.0
    
    # Facteurs de variation selon le type de chambre
    room_multipliers = {
        "Double Classique": 1.0,
        "Suite Junior": 1.5,
        "Suite Deluxe": 2.0,
        "Suite Presidentielle": 3.5
    }
    
    # Facteurs selon le plan tarifaire
    plan_multipliers = {
        "OTA RO FLEX": 1.0,
        "Direct Flexible": 0.9,
        "Non-Refundable": 0.85,
        "Early Bird": 0.8,
        "Last Minute": 1.1
    }
    
    room_mult = room_multipliers.get(room_type, 1.0)
    plan_mult = plan_multipliers.get(plan_name, 1.0)
    
    # Génération des données avec variation réaliste
    for day in range(days_range):
        # Variation saisonnière (cycle de 7 jours)
        seasonal_factor = 1 + 0.1 * math.sin(2 * math.pi * day / 7)
        
        # Variation aléatoire
        random_factor = 1 + random.uniform(-0.05, 0.08)
        
        # Évolution tendance (légère hausse sur la période)
        trend_factor = 1 + (day * 0.001)
        
        # Prix de base avec toutes les variations
        daily_price = current_price * room_mult * plan_mult * seasonal_factor * random_factor * trend_factor
        
        # Calculs commission et prix final
        commission = calculate_commission(daily_price, plan_name)
        final_price = calculate_final_price(daily_price, commission)
        
        # Simulation disponibilité (90% du temps disponible)
        is_available = random.random() > 0.1
        
        price_data.append({
            "date": (datetime.now() - timedelta(days=days_range-day-1)).strftime("%Y-%m-%d"),
            "room_type": room_type,
            "plan_name": plan_name,
            "base_price": round(daily_price, 2),
            "commission": commission,
            "final_price": final_price,
            "is_available": is_available,
            "partner": plan_name,
            "currency": "EUR"
        })
    
    return price_data

def get_price_analytics(price_data: List[Dict]) -> PriceAnalytics:
    """Calcule les analytics sur les données de prix"""
    if not price_data:
        return PriceAnalytics(
            period="",
            average_price=0,
            min_price=0,
            max_price=0,
            price_variance=0,
            availability_rate=0,
            trend="stable"
        )
    
    prices = [item["final_price"] for item in price_data]
    available_count = sum(1 for item in price_data if item["is_available"])
    
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    
    # Calcul de la variance
    variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
    
    # Taux de disponibilité
    availability_rate = (available_count / len(price_data)) * 100
    
    # Détermination de la tendance
    if len(prices) >= 2:
        first_half = sum(prices[:len(prices)//2]) / (len(prices)//2)
        second_half = sum(prices[len(prices)//2:]) / (len(prices) - len(prices)//2)
        
        if second_half > first_half * 1.05:
            trend = "increasing"
        elif second_half < first_half * 0.95:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    return PriceAnalytics(
        period=f"{len(price_data)} jours",
        average_price=round(avg_price, 2),
        min_price=round(min_price, 2),
        max_price=round(max_price, 2),
        price_variance=round(variance, 2),
        availability_rate=round(availability_rate, 1),
        trend=trend
    )

# ===============================
# ENDPOINTS API
# ===============================

def create_price_tracking_router() -> APIRouter:
    """Crée le routeur pour les endpoints de suivi des tarifs"""
    
    router = APIRouter(prefix="/price-tracking", tags=["Price Tracking"])
    
    @router.post("/{hotel_id}", response_model=PriceTrackingResponse)
    async def get_price_tracking_data(
        hotel_id: str,
        request: PriceTrackingRequest,
        db: Session = Depends(get_db)
    ):
        """
        Récupère les données de suivi des tarifs pour un hôtel donné
        sur une période spécifiée.
        """
        try:
            # Validation des dates
            try:
                start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
                end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()
                
                if start_date > end_date:
                    raise HTTPException(
                        status_code=400,
                        detail="La date de début doit être antérieure à la date de fin"
                    )
                
                # Limite à 365 jours maximum
                if (end_date - start_date).days > 365:
                    raise HTTPException(
                        status_code=400,
                        detail="La période ne peut pas dépasser 365 jours"
                    )
                    
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Format de date invalide. Utilisez YYYY-MM-DD"
                )
            
            # Calcul du nombre de jours
            days_range = (end_date - start_date).days + 1
            
            # Simulation des données de prix (à remplacer par une vraie requête base de données)
            price_data = simulate_price_evolution(
                base_price=120.0,  # Prix de base
                room_type=request.room_type,
                plan_name=request.plan_name,
                days_range=days_range
            )
            
            # Calcul des analytics
            analytics = get_price_analytics(price_data)
            
            # Log de l'activité
            activity_log = ActivityLog(
                hotel_id=hotel_id,
                activity_type="price_tracking",
                description=f"Suivi des tarifs demandé pour {request.room_type} - {request.plan_name}",
                details=f"Période: {request.start_date} à {request.end_date}",
                performed_by="user"
            )
            db.add(activity_log)
            db.commit()
            
            return PriceTrackingResponse(
                success=True,
                message=f"Données de suivi récupérées pour {len(price_data)} jours",
                price_data=[PriceData(**item) for item in price_data],
                metadata={
                    "period": f"{request.start_date} to {request.end_date}",
                    "room_type": request.room_type,
                    "plan_name": request.plan_name,
                    "total_days": days_range,
                    "analytics": analytics.dict()
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors du suivi des tarifs: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur interne lors du traitement: {str(e)}"
            )
    
    @router.get("/{hotel_id}/analytics")
    async def get_price_analytics_endpoint(
        hotel_id: str,
        room_type: str = "Double Classique",
        plan_name: str = "OTA RO FLEX",
        days: int = 30,
        db: Session = Depends(get_db)
    ):
        """
        Récupère uniquement les analytics de prix pour un type de chambre et plan tarifaire.
        """
        try:
            # Simulation des données
            price_data = simulate_price_evolution(
                base_price=120.0,
                room_type=room_type,
                plan_name=plan_name,
                days_range=days
            )
            
            analytics = get_price_analytics(price_data)
            
            return {
                "success": True,
                "analytics": analytics.dict(),
                "metadata": {
                    "hotel_id": hotel_id,
                    "room_type": room_type,
                    "plan_name": plan_name,
                    "period_days": days
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des analytics: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du calcul des analytics: {str(e)}"
            )
    
    @router.get("/{hotel_id}/trends")
    async def get_price_trends(
        hotel_id: str,
        room_type: str = "Double Classique",
        plan_name: str = "OTA RO FLEX",
        db: Session = Depends(get_db)
    ):
        """
        Récupère les tendances de prix sur différents horizons temporels.
        """
        try:
            trends_data = {}
            
            for period, days in [("7d", 7), ("30d", 30), ("90d", 90)]:
                price_data = simulate_price_evolution(
                    base_price=120.0,
                    room_type=room_type,
                    plan_name=plan_name,
                    days_range=days
                )
                analytics = get_price_analytics(price_data)
                trends_data[period] = {
                    "analytics": analytics.dict(),
                    "data_points": len(price_data)
                }
            
            return {
                "success": True,
                "trends": trends_data,
                "metadata": {
                    "hotel_id": hotel_id,
                    "room_type": room_type,
                    "plan_name": plan_name,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des tendances: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du calcul des tendances: {str(e)}"
            )
    
    @router.post("/{hotel_id}/export")
    async def export_price_tracking_data(
        hotel_id: str,
        request: PriceTrackingRequest,
        db: Session = Depends(get_db)
    ):
        """
        Exporte les données de suivi des tarifs au format Excel.
        """
        try:
            # Récupération des données
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()
            days_range = (end_date - start_date).days + 1
            
            price_data = simulate_price_evolution(
                base_price=120.0,
                room_type=request.room_type,
                plan_name=request.plan_name,
                days_range=days_range
            )
            
            # Création du DataFrame
            import pandas as pd
            
            df = pd.DataFrame(price_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Préparation du fichier Excel
            from io import BytesIO
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Onglet principal avec les données
                df.to_excel(writer, sheet_name='Données de Prix', index=False)
                
                # Onglet avec les analytics
                analytics = get_price_analytics(price_data)
                analytics_df = pd.DataFrame([analytics.dict()])
                analytics_df.to_excel(writer, sheet_name='Analytics', index=False)
                
                # Onglet résumé
                summary_data = {
                    'Métrique': ['Période', 'Prix Moyen', 'Prix Min', 'Prix Max', 'Taux Disponibilité', 'Tendance'],
                    'Valeur': [
                        f"{request.start_date} à {request.end_date}",
                        f"{analytics.average_price} €",
                        f"{analytics.min_price} €",
                        f"{analytics.max_price} €",
                        f"{analytics.availability_rate}%",
                        analytics.trend
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Résumé', index=False)
            
            output.seek(0)
            
            # Log de l'activité
            activity_log = ActivityLog(
                hotel_id=hotel_id,
                activity_type="price_export",
                description=f"Export Excel du suivi des tarifs {request.room_type} - {request.plan_name}",
                details=f"Fichier généré pour la période {request.start_date} à {request.end_date}",
                performed_by="user"
            )
            db.add(activity_log)
            db.commit()
            
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=suivi_tarifs_{hotel_id}_{request.room_type}_{request.plan_name}.xlsx"
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'export: {str(e)}"
            )
    
    return router

# ===============================
# FONCTION D'INTÉGRATION AU MAIN.PY
# ===============================

def add_price_tracking_to_app(app, db_dependency):
    """
    Intègre le système de suivi des tarifs à l'application FastAPI existante.
    
    Args:
        app: Instance FastAPI
        db_dependency: Dépendance pour la base de données
    """
    global get_db
    get_db = db_dependency
    
    # Ajout du routeur
    price_router = create_price_tracking_router()
    app.include_router(price_router)
    
    # Log de l'intégration
    logger.info("Système de suivi des tarifs intégré avec succès")

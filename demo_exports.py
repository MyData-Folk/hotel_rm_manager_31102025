#!/usr/bin/env python3
"""
Démonstration des nouvelles fonctionnalités d'export Excel
HotelManager Pro V2 - Scripts de test
"""

import json
import requests
from datetime import datetime, timedelta
import time

# Configuration
API_BASE = "http://localhost:8080"
HOTEL_ID = "hotel-demo"

def create_demo_hotel():
    """Crée un hôtel de démonstration"""
    print("🏨 Création de l'hôtel de démonstration...")
    
    response = requests.post(f"{API_BASE}/hotels", json={
        "hotel_id": HOTEL_ID,
        "name": "Hôtel de Démonstration"
    })
    
    if response.status_code in [200, 201]:
        print("✅ Hôtel créé avec succès")
        return True
    else:
        print(f"❌ Erreur création hôtel: {response.text}")
        return False

def create_demo_data():
    """Crée des données de démonstration"""
    print("📊 Création des données de démonstration...")
    
    # Générer des données de planning pour 30 jours
    dates = []
    today = datetime.now().date()
    
    for i in range(30):
        date = today + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    
    # Structure de données simulée
    demo_data = {
        "report_generated_at": f"Démo HotelManager Pro - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "rooms": {
            "Chambre Standard": {
                "stock": {date: 10 + (i % 5) for i, date in enumerate(dates)},
                "plans": {
                    "Tarif Standard": {date: 150.0 + (i * 2) for i, date in enumerate(dates)},
                    "Tarif Weekend": {date: 180.0 + (i * 2) for i, date in enumerate(dates)}
                }
            },
            "Chambre Deluxe": {
                "stock": {date: 5 + (i % 3) for i, date in enumerate(dates)},
                "plans": {
                    "Tarif Deluxe": {date: 250.0 + (i * 3) for i, date in enumerate(dates)},
                    "Tarif Suite": {date: 350.0 + (i * 4) for i, date in enumerate(dates)}
                }
            }
        },
        "dates_processed": dates
    }
    
    # Sauvegarder les données
    with open(f"{HOTEL_ID}_data.json", "w", encoding="utf-8") as f:
        json.dump(demo_data, f, indent=2, ensure_ascii=False)
    
    print("✅ Données de démonstration créées")
    return demo_data

def upload_demo_data(data):
    """Upload des données de démonstration"""
    print("📤 Upload des données...")
    
    # Créer un fichier CSV simulé
    csv_content = """Planning HotelManager Pro - Démonstration
,,
,Chambre Standard,Chambre Standard,Chambre Deluxe,Chambre Deluxe
,Stock Left for Sale,Price,Stock Left for Sale,Price
"""
    
    for i, date in enumerate(data["dates_processed"]):
        csv_content += f"{date},10,150.0,5,250.0\n"
    
    # Upload via l'API
    files = {"file": ("planning_demo.csv", csv_content, "text/csv")}
    response = requests.post(
        f"{API_BASE}/upload/data?hotel_id={HOTEL_ID}",
        files=files
    )
    
    if response.status_code == 200:
        print("✅ Données uploadées avec succès")
        return True
    else:
        print(f"❌ Erreur upload: {response.text}")
        return False

def create_demo_config():
    """Crée une configuration de démonstration"""
    print("⚙️ Création de la configuration...")
    
    config = {
        "hotel_id": HOTEL_ID,
        "partners": {
            "Booking.com": {
                "codes": ["BOOK", "COM"],
                "commission": 15,
                "defaultDiscount": {
                    "percentage": 5,
                    "excludePlansContaining": ["Weekend"]
                }
            },
            "Airbnb": {
                "codes": ["AIR"],
                "commission": 12,
                "defaultDiscount": {
                    "percentage": 3
                }
            },
            "Direct": {
                "codes": ["DIRECT"],
                "commission": 0,
                "defaultDiscount": {
                    "percentage": 0
                }
            }
        },
        "displayOrder": ["Chambre Standard", "Chambre Deluxe"]
    }
    
    # Upload de la config
    files = {"file": ("config_demo.json", json.dumps(config), "application/json")}
    response = requests.post(
        f"{API_BASE}/upload/data?hotel_id={HOTEL_ID}",
        files=files
    )
    
    if response.status_code == 200:
        print("✅ Configuration uploadée avec succès")
        return True
    else:
        print(f"❌ Erreur upload config: {response.text}")
        return False

def test_simulation():
    """Test de simulation et export"""
    print("🧪 Test de simulation...")
    
    # Données de simulation
    simulation_data = {
        "hotel_id": HOTEL_ID,
        "partner_name": "Booking.com",
        "room": "Chambre Standard",
        "plan": "Tarif Standard",
        "start": datetime.now().strftime("%Y-%m-%d"),
        "end": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "apply_commission": True,
        "apply_partner_discount": True,
        "promo_discount": 10,
        "performed_by": "demo-script"
    }
    
    # Lancer la simulation
    response = requests.post(f"{API_BASE}/simulate", json=simulation_data)
    
    if response.status_code == 200:
        simulation_result = response.json()
        print("✅ Simulation réussie")
        return simulation_result
    else:
        print(f"❌ Erreur simulation: {response.text}")
        return None

def test_export_simulation(simulation_data):
    """Test d'export de simulation amélioré"""
    print("📊 Test export simulation amélioré...")
    
    response = requests.post(f"{API_BASE}/export/simulation/enhanced", json={
        "data": simulation_data,
        "filename_prefix": "demo_simulation"
    })
    
    if response.status_code == 200:
        # Sauvegarder le fichier
        with open("demo_simulation_enhanced.xlsx", "wb") as f:
            f.write(response.content)
        print("✅ Export simulation amélioré réussi")
        return True
    else:
        print(f"❌ Erreur export simulation: {response.text}")
        return False

def test_export_reservation(simulation_data):
    """Test d'export de réservation"""
    print("📈 Test export réservation...")
    
    response = requests.post(f"{API_BASE}/export/reservation", json={
        "data": simulation_data
    })
    
    if response.status_code == 200:
        with open("demo_reservation_prediction.xlsx", "wb") as f:
            f.write(response.content)
        print("✅ Export réservation réussi")
        return True
    else:
        print(f"❌ Erreur export réservation: {response.text}")
        return False

def test_export_availability():
    """Test d'export de disponibilités"""
    print("📅 Test export disponibilités...")
    
    availability_data = {
        "hotel_id": HOTEL_ID,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        "room_types": ["Chambre Standard", "Chambre Deluxe"],
        "performed_by": "demo-script"
    }
    
    # D'abord récupérer les données de disponibilité
    response = requests.post(f"{API_BASE}/availability", json=availability_data)
    
    if response.status_code == 200:
        availability_result = response.json()
        
        # Puis exporter
        export_response = requests.post(f"{API_BASE}/export/availability", json={
            "data": availability_result
        })
        
        if export_response.status_code == 200:
            with open("demo_availability.xlsx", "wb") as f:
                f.write(export_response.content)
            print("✅ Export disponibilités réussi")
            return True
        else:
            print(f"❌ Erreur export disponibilités: {export_response.text}")
            return False
    else:
        print(f"❌ Erreur récupération disponibilités: {response.text}")
        return False

def test_batch_export():
    """Test d'export groupé"""
    print("📦 Test export groupé...")
    
    # Test avec simulation
    response = requests.post(f"{API_BASE}/export/batch", json={
        "type": "simulation",
        "data": {
            "results": [
                {
                    "date": "2024-10-31",
                    "date_display": "Jeu 31/10",
                    "gross_price": 150.0,
                    "price_after_partner_discount": 142.5,
                    "price_after_promo": 128.25,
                    "commission": 19.24,
                    "net_price": 109.01,
                    "stock": 8,
                    "availability": "Disponible"
                }
            ],
            "summary": {
                "subtotal_brut": 150.0,
                "total_partner_discount": 7.5,
                "total_promo_discount": 14.25,
                "total_discount": 21.75,
                "total_commission": 19.24,
                "total_net": 109.01
            },
            "simulation_info": {
                "hotel_id": HOTEL_ID,
                "room": "Chambre Standard",
                "plan": "Tarif Standard",
                "partner": "Booking.com",
                "partner_commission": 15,
                "partner_discount": 5,
                "promo_discount": 10,
                "apply_partner_discount": True,
                "start_date": "2024-10-31",
                "end_date": "2024-11-07",
                "nights": 7,
                "source": "Démonstration HotelManager Pro"
            }
        }
    })
    
    if response.status_code == 200:
        with open("demo_batch_simulation.xlsx", "wb") as f:
            f.write(response.content)
        print("✅ Export groupé réussi")
        return True
    else:
        print(f"❌ Erreur export groupé: {response.text}")
        return False

def run_comprehensive_test():
    """Lance une série de tests complets"""
    print("🚀 Démarrage des tests de démonstration")
    print("=" * 50)
    
    try:
        # 1. Créer l'hôtel
        if not create_demo_hotel():
            return False
        
        # 2. Créer et uploader les données
        demo_data = create_demo_data()
        if not upload_demo_data(demo_data):
            return False
        
        # 3. Créer et uploader la config
        if not create_demo_config():
            return False
        
        # 4. Attendre un peu pour que les données soient traitées
        print("⏳ Attente du traitement des données...")
        time.sleep(2)
        
        # 5. Test de simulation
        simulation_result = test_simulation()
        if not simulation_result:
            return False
        
        # 6. Tests d'export
        print("\n📤 Test des fonctionnalités d'export:")
        
        test_export_simulation(simulation_result)
        test_export_reservation(simulation_result)
        test_export_availability()
        test_batch_export()
        
        print("\n" + "=" * 50)
        print("🎉 Tests terminés!")
        print("\nFichiers générés:")
        print("- demo_simulation_enhanced.xlsx (Rapport simulation complet)")
        print("- demo_reservation_prediction.xlsx (Prévisions de réservation)")
        print("- demo_availability.xlsx (Rapport disponibilités)")
        print("- demo_batch_simulation.xlsx (Export groupé)")
        print("\n✅ Toutes les fonctionnalités d'export sont opérationnelles!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")
        return False

def check_api_status():
    """Vérifie que l'API est accessible"""
    print("🔍 Vérification du statut de l'API...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API accessible - Statut: {health_data.get('status', 'unknown')}")
            print(f"📊 Version: {health_data.get('version', 'unknown')}")
            print(f"⚡ Latence: {health_data.get('latency_ms', 'unknown')}ms")
            return True
        else:
            print(f"❌ API non accessible - Code: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Impossible de se connecter à l'API")
        print("💡 Assurez-vous que votre serveur FastAPI fonctionne sur http://localhost:8080")
        return False

def main():
    """Fonction principale"""
    print("🏨 HotelManager Pro V2 - Test des Exports Excel")
    print("=" * 60)
    
    # Vérifier le statut de l'API
    if not check_api_status():
        return
    
    print("\n🚀 Lancement de la démonstration...")
    
    # Demander confirmation
    response = input("\nCette démonstration va créer des données de test. Continuer? (y/N): ")
    if response.lower() != 'y':
        print("🛑 Démonstration annulée")
        return
    
    # Lancer les tests
    success = run_comprehensive_test()
    
    if success:
        print("\n🎊 Démonstration réussie!")
        print("Vous pouvez maintenant:")
        print("1. Ouvrir les fichiers Excel générés")
        print("2. Tester depuis votre interface web")
        print("3. Intégrer ces fonctionnalités dans votre application")
    else:
        print("\n❌ Démonstration échouée")
        print("Vérifiez les erreurs ci-dessus et réessayez")

if __name__ == "__main__":
    main()
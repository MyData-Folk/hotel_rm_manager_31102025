#!/usr/bin/env python3
"""
Script de démonstration pour le module de suivi des tarifs
HotelManager Pro V2 - Suivi des Tarifs Demo

Ce script teste la nouvelle fonctionnalité de suivi des tarifs
en simulant des requêtes vers l'API et en validant les réponses.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class PriceTrackingDemo:
    """Classe de démonstration pour le suivi des tarifs"""
    
    def __init__(self, api_base: str = "http://localhost:8080"):
        self.api_base = api_base
        self.hotel_id = "demo_hotel_001"
        
    def test_connection(self) -> bool:
        """Test de connexion à l'API"""
        print("🔗 Test de connexion à l'API...")
        
        try:
            # Test d'un endpoint existant (liste des hôtels)
            response = requests.get(f"{self.api_base}/hotels", timeout=5)
            
            if response.status_code == 200:
                print("✅ Connexion API réussie")
                return True
            else:
                print(f"⚠️  Réponse inattendue: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Impossible de se connecter à l'API")
            print("   Assurez-vous que votre serveur FastAPI est démarré")
            print(f"   URL attendue: {self.api_base}")
            return False
        except requests.exceptions.Timeout:
            print("⏰ Timeout de connexion")
            return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_price_tracking_endpoint(self) -> Dict[str, Any]:
        """Test de l'endpoint principal de suivi des tarifs"""
        print("\n📊 Test de l'endpoint de suivi des tarifs...")
        
        # Configuration des données de test
        test_data = {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "room_type": "Double Classique",
            "plan_name": "OTA RO FLEX"
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/price-tracking/{self.hotel_id}",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Endpoint de suivi des tarifs fonctionnel")
                
                # Analyse de la réponse
                if result.get("success"):
                    price_data = result.get("price_data", [])
                    print(f"   📈 {len(price_data)} données de prix récupérées")
                    
                    if price_data:
                        print(f"   📅 Période: {price_data[0]['date']} à {price_data[-1]['date']}")
                        print(f"   💰 Prix moyen: {sum(item['final_price'] for item in price_data) / len(price_data):.2f}€")
                        
                        # Analytics
                        metadata = result.get("metadata", {})
                        analytics = metadata.get("analytics", {})
                        if analytics:
                            print(f"   📊 Tendance: {analytics.get('trend', 'N/A')}")
                            print(f"   📋 Taux disponibilité: {analytics.get('availability_rate', 0)}%")
                    
                    return result
                else:
                    print(f"❌ Erreur dans la réponse: {result.get('error', 'Inconnue')}")
                    return {}
                    
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return {}
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout lors de la requête")
            return {}
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            return {}
    
    def test_analytics_endpoint(self) -> Dict[str, Any]:
        """Test de l'endpoint d'analytics"""
        print("\n📈 Test de l'endpoint d'analytics...")
        
        try:
            response = requests.get(
                f"{self.api_base}/price-tracking/{self.hotel_id}/analytics",
                params={
                    "room_type": "Suite Deluxe",
                    "plan_name": "Direct Flexible",
                    "days": 7
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Endpoint d'analytics fonctionnel")
                
                analytics = result.get("analytics", {})
                if analytics:
                    print(f"   📊 Prix moyen: {analytics.get('average_price', 0)}€")
                    print(f"   📊 Prix min/max: {analytics.get('min_price', 0)}€ / {analytics.get('max_price', 0)}€")
                    print(f"   📊 Variance: {analytics.get('price_variance', 0)}")
                    print(f"   📊 Tendance: {analytics.get('trend', 'N/A')}")
                
                return result
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Erreur lors du test analytics: {e}")
            return {}
    
    def test_trends_endpoint(self) -> Dict[str, Any]:
        """Test de l'endpoint des tendances"""
        print("\n📉 Test de l'endpoint des tendances...")
        
        try:
            response = requests.get(
                f"{self.api_base}/price-tracking/{self.hotel_id}/trends",
                params={
                    "room_type": "Double Classique",
                    "plan_name": "OTA RO FLEX"
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Endpoint des tendances fonctionnel")
                
                trends = result.get("trends", {})
                for period, data in trends.items():
                    analytics = data.get("analytics", {})
                    if analytics:
                        print(f"   📊 {period}: {analytics.get('average_price', 0)}€ (tendance: {analytics.get('trend', 'N/A')})")
                
                return result
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Erreur lors du test des tendances: {e}")
            return {}
    
    def test_export_endpoint(self) -> bool:
        """Test de l'endpoint d'export"""
        print("\n📄 Test de l'endpoint d'export...")
        
        test_data = {
            "start_date": "2025-01-15",
            "end_date": "2025-01-20",
            "room_type": "Double Classique",
            "plan_name": "OTA RO FLEX"
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/price-tracking/{self.hotel_id}/export",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Endpoint d'export fonctionnel")
                print(f"   📄 Taille du fichier: {len(response.content)} bytes")
                
                # Sauvegarde du fichier de test
                filename = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"   💾 Fichier sauvegardé: {filename}")
                
                return True
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du test d'export: {e}")
            return False
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Lance tous les tests de manière séquentielle"""
        print("🚀 Démarrage des tests de démonstration - Suivi des Tarifs")
        print("=" * 60)
        
        results = {
            "connection": False,
            "price_tracking": {},
            "analytics": {},
            "trends": {},
            "export": False,
            "overall_success": False
        }
        
        # Test de connexion
        results["connection"] = self.test_connection()
        
        if not results["connection"]:
            print("\n❌ Tests interrompus - API non accessible")
            return results
        
        # Tests des endpoints
        results["price_tracking"] = self.test_price_tracking_endpoint()
        results["analytics"] = self.test_analytics_endpoint()
        results["trends"] = self.test_trends_endpoint()
        results["export"] = self.test_export_endpoint()
        
        # Évaluation globale
        endpoints_working = (
            bool(results["price_tracking"]) and
            bool(results["analytics"]) and
            bool(results["trends"]) and
            results["export"]
        )
        
        results["overall_success"] = endpoints_working
        
        # Résumé final
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        tests = [
            ("Connexion API", results["connection"]),
            ("Suivi des tarifs", bool(results["price_tracking"])),
            ("Analytics", bool(results["analytics"])),
            ("Tendances", bool(results["trends"])),
            ("Export Excel", results["export"])
        ]
        
        for test_name, success in tests:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        overall = "✅ SUCCÈS GLOBAL" if results["overall_success"] else "❌ ÉCHEC GLOBAL"
        print(f"\n{overall}")
        
        if results["overall_success"]:
            print("\n🎉 Tous les tests sont passés avec succès!")
            print("   La fonctionnalité de suivi des tarifs est opérationnelle.")
        else:
            print("\n⚠️  Certains tests ont échoué.")
            print("   Vérifiez la configuration et les logs du serveur.")
        
        return results

def interactive_demo():
    """Mode de démonstration interactif"""
    print("🎭 Mode démonstration interactive")
    print("Choisissez un test à lancer:")
    print("1. Test complet de tous les endpoints")
    print("2. Test de connexion seulement")
    print("3. Test du suivi des tarifs seulement")
    print("4. Test des analytics seulement")
    print("5. Test des tendances seulement")
    print("6. Test d'export seulement")
    print("0. Quitter")
    
    while True:
        try:
            choice = input("\nVotre choix (0-6): ").strip()
            
            if choice == "0":
                print("👋 Au revoir!")
                break
            elif choice == "1":
                demo = PriceTrackingDemo()
                demo.run_comprehensive_test()
                break
            elif choice == "2":
                demo = PriceTrackingDemo()
                demo.test_connection()
                break
            elif choice == "3":
                demo = PriceTrackingDemo()
                demo.test_price_tracking_endpoint()
                break
            elif choice == "4":
                demo = PriceTrackingDemo()
                demo.test_analytics_endpoint()
                break
            elif choice == "5":
                demo = PriceTrackingDemo()
                demo.test_trends_endpoint()
                break
            elif choice == "6":
                demo = PriceTrackingDemo()
                demo.test_export_endpoint()
                break
            else:
                print("❌ Choix invalide. Veuillez choisir entre 0 et 6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interruption utilisateur. Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    import sys
    
    print("🎯 HotelManager Pro V2 - Démonstration Suivi des Tarifs")
    print("=" * 50)
    
    # Vérification des arguments en ligne de commande
    if len(sys.argv) > 1:
        api_base = sys.argv[1]
    else:
        api_base = input("URL de l'API (défaut: http://localhost:8080): ").strip()
        if not api_base:
            api_base = "http://localhost:8080"
    
    print(f"🔗 Utilisation de l'API: {api_base}")
    
    # Mode interactif ou test direct
    if len(sys.argv) > 2 and sys.argv[2] == "--interactive":
        interactive_demo()
    else:
        # Test automatique
        demo = PriceTrackingDemo(api_base)
        results = demo.run_comprehensive_test()
        
        # Code de sortie
        sys.exit(0 if results["overall_success"] else 1)

if __name__ == "__main__":
    main()

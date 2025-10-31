# Guide d'Intégration - Suivi des Tarifs

## Vue d'ensemble

Ce guide vous accompagne pour intégrer la fonctionnalité de **Suivi des Tarifs** dans votre application HotelManager Pro V2 existante. Cette nouvelle fonctionnalité permet de visualiser l'évolution des tarifs sur une période donnée avec un tableau et un graphique interactif.

## 📁 Fichiers à créer/modifier

### 1. Fichier backend - `price_tracking_module.py`

**Action** : Copiez le fichier `price_tracking_module.py` dans le même répertoire que votre `main.py`.

### 2. Modification du fichier `main.py`

Ajoutez les imports suivants au début de votre fichier `main.py` :

```python
# Ajouter après les imports existants
from datetime import timedelta  # Déjà présent normalement
import random
import math
```

**Puis, à la fin de votre fichier `main.py` (avant `if __name__ == "__main__"`), ajoutez :**

```python
# ===============================
# INTÉGRATION DU SUIVI DES TARIFS
# ===============================

def get_db():
    """Dépendance de base de données pour le suivi des tarifs"""
    with Session(engine) as session:
        yield session

# Import du module de suivi des tarifs
try:
    from price_tracking_module import add_price_tracking_to_app
    
    # Intégration du système de suivi des tarifs
    add_price_tracking_to_app(app, get_db)
    print("✅ Système de suivi des tarifs intégré avec succès")
    
except ImportError as e:
    print(f"⚠️  Impossible d'importer le module de suivi des tarifs: {e}")
except Exception as e:
    print(f"⚠️  Erreur lors de l'intégration du suivi des tarifs: {e}")
```

### 3. Remplacement du fichier frontend

**Action** : Remplacez votre fichier `index.html` existant par le contenu du fichier `index_suivi_tarifs.html`.

## 🚀 Fonctionnalités intégrées

### Interface utilisateur

1. **Nouvel onglet** : "Suivi des tarifs" avec icône trending-up
2. **Formulaire de recherche** :
   - Sélection de période (date début/fin)
   - Type de chambre (par défaut "Double Classique")
   - Plan tarifaire (par défaut "OTA RO FLEX")
3. **Tableau de résultats** avec :
   - Date, type de chambre, plan tarifaire
   - Prix de base, commission, prix final
   - Statut de disponibilité avec indicateurs visuels
4. **Graphique interactif** utilisant Chart.js pour visualiser l'évolution

### Backend API

Nouveaux endpoints disponibles :

1. **`POST /price-tracking/{hotel_id}`**
   - Récupère les données de tarifs pour une période donnée
   - Paramètres : `start_date`, `end_date`, `room_type`, `plan_name`

2. **`GET /price-tracking/{hotel_id}/analytics`**
   - Analytics rapides sur les tarifs
   - Paramètres : `room_type`, `plan_name`, `days`

3. **`GET /price-tracking/{hotel_id}/trends`**
   - Tendances sur plusieurs périodes (7d, 30d, 90d)

4. **`POST /price-tracking/{hotel_id}/export`**
   - Export Excel des données de suivi

## 🔧 Configuration et test

### 1. Installation des dépendances

Ajoutez ces packages à votre `requirements.txt` ou installez-les :

```bash
pip install pandas openpyxl
```

### 2. Test de l'intégration

**Test du backend :**

```python
# Test rapide dans un shell Python
import requests

# Configuration
api_base = "http://localhost:8080"
hotel_id = "hotel_test"

# Test de l'endpoint
response = requests.post(f"{api_base}/price-tracking/{hotel_id}", json={
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "room_type": "Double Classique",
    "plan_name": "OTA RO FLEX"
})

print(response.status_code)
print(response.json())
```

**Test du frontend :**

1. Démarrez votre serveur FastAPI
2. Ouvrez votre navigateur sur `http://localhost:8000` (ou votre port)
3. Naviguez vers l'onglet "Suivi des tarifs"
4. Configurez les paramètres et lancez une recherche

### 3. Configuration de l'endpoint API

Dans l'interface frontend, n'oubliez pas de configurer votre endpoint API :

1. Dans l'en-tête de la page, saisissez votre URL backend (ex: `http://localhost:8080`)
2. Cliquez sur "Sauvegarder & synchroniser"
3. Sélectionnez un hôtel et chargez les données

## 📊 Structure des données

### Modèle de réponse API

```json
{
  "success": true,
  "message": "Données de suivi récupérées pour 30 jours",
  "price_data": [
    {
      "date": "2025-01-01",
      "room_type": "Double Classique",
      "plan_name": "OTA RO FLEX",
      "base_price": 125.50,
      "commission": 20.08,
      "final_price": 145.58,
      "is_available": true,
      "partner": "OTA RO FLEX",
      "currency": "EUR"
    }
  ],
  "metadata": {
    "period": "2025-01-01 to 2025-01-31",
    "room_type": "Double Classique",
    "plan_name": "OTA RO FLEX",
    "total_days": 31,
    "analytics": {
      "period": "31 jours",
      "average_price": 145.23,
      "min_price": 120.00,
      "max_price": 180.50,
      "price_variance": 245.67,
      "availability_rate": 89.5,
      "trend": "increasing"
    }
  }
}
```

## 🎨 Personnalisation

### Modification des types de chambres

Dans le fichier `index_suivi_tarifs.html`, modifiez la section `<select id="trackRoom">` :

```html
<select id="trackRoom" class="form-control">
    <option value="Double Classique">Double Classique</option>
    <option value="Suite Junior">Suite Junior</option>
    <option value="Suite Deluxe">Suite Deluxe</option>
    <option value="Suite Presidentielle">Suite Presidentielle</option>
</select>
```

### Modification des plans tarifaires

De même pour les plans tarifaires :

```html
<select id="trackPlan" class="form-control">
    <option value="OTA RO FLEX">OTA RO FLEX</option>
    <option value="Direct Flexible">Direct Flexible</option>
    <option value="Non-Refundable">Non-Refundable</option>
    <option value="Early Bird">Early Bird</option>
    <option value="Last Minute">Last Minute</option>
</select>
```

### Couleurs du graphique

Dans la fonction `updatePriceChart()`, modifiez les couleurs :

```javascript
priceChart = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: [{
            borderColor: '#6366f1',        // Couleur de la ligne
            backgroundColor: 'rgba(99, 102, 241, 0.1)',  // Couleur de remplissage
            pointBackgroundColor: '#6366f1'  // Couleur des points
        }]
    }
});
```

## 🐛 Dépannage

### Erreurs courantes

1. **"ModuleNotFoundError: No module named 'pandas'"**
   - Solution : `pip install pandas openpyxl`

2. **"CORS error"**
   - Vérifiez que votre backend autorise les requêtes depuis votre frontend
   - Dans `main.py`, vérifiez la configuration CORS

3. **"Chart.js not loaded"**
   - Vérifiez que la CDN Chart.js est bien chargée dans le HTML

4. **"No data found"**
   - Le système génère actuellement des données simulées
   - Vérifiez que les dates sont valides et dans le bon format

### Debug du backend

Ajoutez des logs temporaires pour debug :

```python
# Dans price_tracking_module.py, fonction get_price_tracking_data
logger.info(f"Requête reçue pour hôtel {hotel_id}")
logger.info(f"Paramètres: {request.dict()}")
```

## 🔮 Évolutions futures

### 1. Connexion à une vraie base de données

Remplacez la fonction `simulate_price_evolution()` par de vraies requêtes SQL :

```python
def get_real_price_data(hotel_id: str, start_date: date, end_date: date, room_type: str, plan_name: str, db: Session):
    """Récupère les vraies données de prix depuis la base de données"""
    query = select(PriceHistory).where(
        and_(
            PriceHistory.hotel_id == hotel_id,
            PriceHistory.date >= start_date,
            PriceHistory.date <= end_date,
            PriceHistory.room_type == room_type,
            PriceHistory.plan_name == plan_name
        )
    )
    return db.exec(query).all()
```

### 2. Ajout de filtres avancés

- Filtre par partenaire spécifique
- Filtre par taux d'occupation
- Comparaison entre plusieurs plans tarifaires

### 3. Alertes et notifications

- Alertes sur les variations de prix
- Notifications pour les tarifs optimaux
- Intégration avec le système d'activité existant

## 📞 Support

Pour toute question ou problème d'intégration :

1. Vérifiez que tous les fichiers sont bien en place
2. Testez les endpoints avec un client REST (Postman, Insomnia)
3. Consultez les logs de votre serveur FastAPI
4. Vérifiez la console navigateur pour les erreurs JavaScript

---

**Version** : 1.0  
**Compatibilité** : HotelManager Pro V2  
**Auteur** : MiniMax Agent  
**Date** : 2025-10-31
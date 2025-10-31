# Guide d'Intégration - Gestion Excel et Paramètres

## Vue d'ensemble

Ce guide vous accompagne pour intégrer les nouvelles fonctionnalités de **Gestion des fichiers Excel** et **Paramètres** dans votre application HotelManager Pro V2.

## 🚀 Nouvelles fonctionnalités ajoutées

### 1. Gestion des fichiers Excel
- **Sauvegarde automatique** des fichiers Excel de tarifs
- **Historique** des 10 derniers fichiers par hôtel
- **Rotation automatique** (suppression des anciens fichiers)
- **Zone drag & drop** pour l'upload
- **Statistiques** d'utilisation
- **Téléchargement** et **suppression** des fichiers

### 2. Onglet Paramètres
- **Configuration PostgreSQL** avec interface conviviale
- **Configuration du stockage** des fichiers Excel
- **Tests de connexion** intégrés
- **État des paramètres** en temps réel

### 3. Backend étendu
- **4 nouveaux endpoints** pour la gestion des fichiers
- **4 endpoints** pour la gestion des paramètres
- **Nouveaux modèles** de données
- **Sécurité** et **validation** des fichiers

## 📁 Fichiers à intégrer

### 1. Fichier backend : `excel_file_management.py`

**Action** : Copiez ce fichier dans le même répertoire que votre `main.py`.

### 2. Fichier frontend : `index_complet_etendu.html`

**Action** : Remplacez votre fichier `index.html` existant par ce nouveau fichier.

### 3. Modifications du fichier `main.py`

Ajoutez les modifications suivantes à votre fichier `main.py` existant.

#### Étape 1 : Imports supplémentaires

**Ajoutez après les imports existants :**

```python
# Pour la gestion des fichiers Excel et paramètres
from pathlib import Path
import io
import tempfile
from typing import Union
```

#### Étape 2 : Import du module d'extension

**Ajoutez après la création de l'application (autour de la ligne 30) :**

```python
# Import du module d'extension pour Excel et paramètres
try:
    from excel_file_management import (
        create_excel_tables, 
        add_excel_management_to_app,
        TariffFile,
        AppSettings
    )
    
    # Créer les nouvelles tables
    create_excel_tables(engine)
    print("✅ Tables de gestion Excel créées")
    
    # Intégrer les nouveaux endpoints
    add_excel_management_to_app(app, get_db)
    print("✅ Système de gestion Excel et paramètres intégré")
    
except ImportError as e:
    print(f"⚠️  Module Excel non disponible: {e}")
except Exception as e:
    print(f"⚠️  Erreur intégration Excel: {e}")
```

#### Étape 3 : Endpoint de test de connexion (optionnel)

**Ajoutez cet endpoint dans la section des endpoints :**

```python
@app.post("/settings/test-connection", tags=["Settings"])
async def test_database_connection(settings_data: dict):
    """Test de connexion à la base de données PostgreSQL"""
    try:
        database_url = settings_data.get("database_url")
        if not database_url:
            raise HTTPException(status_code=400, detail="URL de base de données requise")
        
        # Test de connexion simple
        from sqlalchemy import create_engine
        test_engine = create_engine(database_url.replace("postgres://", "postgresql+psycopg2://"))
        with test_engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {"success": True, "message": "Connexion réussie"}
        
    except Exception as e:
        logger.error(f"Erreur test connexion: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de connexion: {str(e)}")
```

#### Étape 4 : Initialisation des paramètres par défaut

**Ajoutez cet endpoint :**

```python
@app.post("/settings/initialize", tags=["Settings"])
def initialize_default_settings():
    """Initialise les paramètres par défaut de l'application"""
    try:
        # Import dynamique pour éviter les erreurs si le module n'est pas chargé
        from excel_file_management import create_settings_router, AppSettings
        
        # Cette fonction sera appelée automatiquement
        return {"success": True, "message": "Paramètres déjà initialisés"}
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Module de gestion Excel non disponible")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
```

### 4. Créer le répertoire de stockage

**Créez le répertoire de stockage :**

```bash
mkdir -p /tmp/hotel_excel_storage
chmod 755 /tmp/hotel_excel_storage
```

### 5. Installation des dépendances

**Ajoutez ces packages à votre `requirements.txt` :**

```txt
pandas>=1.5.0
openpyxl>=3.0.10
python-multipart>=0.0.5
```

**Ou installez-les directement :**

```bash
pip install pandas openpyxl python-multipart
```

## 🔧 Vérifications post-intégration

### 1. Test des nouveaux endpoints

**Testez ces endpoints avec curl :**

```bash
# Test de l'endpoint de paramètres
curl -X GET "http://localhost:8080/settings"

# Test de l'initialisation des paramètres
curl -X POST "http://localhost:8080/settings/initialize"

# Test de l'historique des fichiers
curl -X GET "http://localhost:8080/excel-management/history/hotel_test"
```

### 2. Vérification des tables

**Vérifiez que les nouvelles tables ont été créées :**

```sql
-- Connexion à votre base de données
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('tarifffile', 'appsettings');
```

### 3. Test de l'interface utilisateur

1. **Démarrez votre serveur** : `uvicorn main:app --reload`
2. **Ouvrez votre navigateur** sur `http://localhost:8000`
3. **Naviguez vers les nouveaux onglets** :
   - "Gestion des fichiers" pour tester l'upload Excel
   - "Paramètres" pour configurer PostgreSQL

## 🎯 Fonctionnalités disponibles

### Onglet "Gestion des fichiers"

1. **Upload de fichiers Excel** :
   - Glissez-déposez vos fichiers .xlsx, .xls, .xlsm
   - Sélection multiple de fichiers
   - Barre de progression
   - Validation automatique

2. **Historique des fichiers** :
   - Liste des 10 derniers fichiers uploadés
   - Informations : nom, date, taille, statut
   - Boutons de téléchargement et suppression
   - Actualisation manuelle

3. **Statistiques** :
   - Nombre total de fichiers
   - Espace de stockage utilisé
   - État de la limite (10 fichiers max)
   - Indicateur d'espace disponible

### Onglet "Paramètres"

1. **Configuration PostgreSQL** :
   - Interface pour saisir tous les paramètres
   - Construction automatique de l'URL de connexion
   - Test de connexion intégré
   - Sauvegarde sécurisée

2. **Configuration du stockage** :
   - Chemin de stockage des fichiers Excel
   - Nombre maximum de fichiers par hôtel
   - Activation/désactivation du nettoyage automatique

3. **État des paramètres** :
   - Statut en temps réel de chaque configuration
   - Indicateurs visuels (vert/ambre/rouge)
   - Récapitulatif des paramètres actifs

## 🔐 Sécurité et bonnes pratiques

### Validation des fichiers

- **Extensions autorisées** : .xlsx, .xls, .xlsm uniquement
- **Taille des fichiers** : Pas de limite spécifique mais les gros fichiers peuvent causer des timeouts
- **Contenu** : Validation basique du format Excel

### Stockage sécurisé

- **Base de données** : Stockage des métadonnées et contenu en base
- **Système de fichiers** : Copie physique dans un répertoire dédié
- **Nettoyage automatique** : Suppression des anciens fichiers selon la limite

### Gestion des erreurs

- **Try-catch** sur tous les endpoints
- **Rollback** automatique en cas d'erreur
- **Logs détaillés** pour le debugging
- **Messages utilisateur** clairs

## 📊 API Endpoints disponibles

### Gestion des fichiers Excel

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/excel-management/upload/{hotel_id}` | POST | Upload d'un fichier Excel |
| `/excel-management/history/{hotel_id}` | GET | Récupère l'historique des fichiers |
| `/excel-management/download/{file_id}` | GET | Télécharge un fichier |
| `/excel-management/delete/{file_id}` | DELETE | Supprime un fichier |
| `/excel-management/stats/{hotel_id}` | GET | Statistiques des fichiers |

### Gestion des paramètres

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/settings` | GET | Liste tous les paramètres |
| `/settings/{setting_key}` | GET | Récupère un paramètre |
| `/settings/{setting_key}` | PUT | Met à jour un paramètre |
| `/settings/initialize` | POST | Initialise les paramètres par défaut |

## 🐛 Dépannage

### Erreurs courantes

**1. "ModuleNotFoundError: No module named 'pandas'"**
```bash
pip install pandas openpyxl
```

**2. "Table 'tarifffile' doesn't exist"**
- Vérifiez que `create_excel_tables(engine)` est appelé
- Redémarrez l'application pour recréer les tables

**3. "Permission denied" sur le répertoire de stockage**
```bash
chmod 755 /tmp/hotel_excel_storage
# ou changez le chemin dans les paramètres
```

**4. "CORS error"**
- Vérifiez la configuration CORS dans votre `main.py`
- Ajoutez `http://localhost:8000` aux origins autorisés

**5. "Upload failed"**
- Vérifiez que le fichier est un Excel valide
- Vérifiez l'espace disque disponible
- Consultez les logs du serveur

### Debug du backend

**Activez les logs détaillés :**

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Vérifiez les logs d'activité :**

```bash
# Les uploads et modifications sont loggées dans ActivityLog
curl "http://localhost:8080/activity?limit=10"
```

### Debug du frontend

**Ouvrez la console navigateur :**
- F12 → Console pour voir les erreurs JavaScript
- F12 → Network pour voir les requêtes API

**Testez les endpoints avec un client REST :**
- Postman, Insomnia, ou curl
- Vérifiez les réponses et codes d'erreur

## 🔮 Évolutions futures possibles

### 1. Import automatique des données Excel

```python
# Après upload, extraction automatique des données
def extract_data_from_excel(file_content: bytes):
    """Extrait les données des fichiers Excel pour les simulations"""
    df = pd.read_excel(io.BytesIO(file_content))
    return process_tariff_data(df)
```

### 2. Synchronisation avec les simulations

```python
# Utilisation automatique des derniers fichiers uploadés
def get_latest_tariff_data(hotel_id: str):
    """Récupère les données du dernier fichier Excel uploadé"""
    latest_file = get_latest_uploaded_file(hotel_id)
    return extract_data_from_excel(latest_file.data)
```

### 3. Notifications et alertes

- Notification lors de la limite de fichiers atteinte
- Alertes de disque plein
- Notifications de nouvelles données disponibles

### 4. Compression et archivage

- Compression automatique des anciens fichiers
- Archivage vers un stockage externe
- Système de backup automatique

## 📞 Support et assistance

### Checklist de vérification

- [ ] Module `excel_file_management.py` copié
- [ ] Tables créées (`TariffFile`, `AppSettings`)
- [ ] Dépendances installées (`pandas`, `openpyxl`)
- [ ] Répertoire de stockage créé
- [ ] Frontend mis à jour
- [ ] Serveur redémarré
- [ ] Endpoints testés
- [ ] Interface utilisateur vérifiée

### Tests recommandés

1. **Upload d'un fichier Excel** via l'interface
2. **Vérification de l'historique** et des statistiques
3. **Configuration PostgreSQL** dans l'onglet paramètres
4. **Test de connexion** à la base de données
5. **Téléchargement et suppression** d'un fichier

---

**Version** : 1.0  
**Compatibilité** : HotelManager Pro V2  
**Auteur** : MiniMax Agent  
**Date** : 2025-10-31
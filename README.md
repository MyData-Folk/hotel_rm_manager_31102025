# HotelManager Pro Codex

Suite complète de revenue management combinant API FastAPI, base de données SQLModel et front-end moderne. Ce projet fournit une application fonctionnelle prête à être déployée pour piloter exports Excel avancés, simulations de tarifs et gestion documentaire.

## Architecture

```
.
├── backend
│   ├── app
│   │   ├── api/v1
│   │   │   ├── excel_management.py
│   │   │   ├── exports.py
│   │   │   └── price_tracking.py
│   │   ├── core/config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models/entities.py
│   │   ├── services
│   │   │   ├── excel_management.py
│   │   │   ├── exports.py
│   │   │   └── price_tracking.py
│   │   └── utils/logging.py
│   └── requirements.txt
├── frontend
│   ├── assets
│   │   ├── main.js
│   │   └── styles.css
│   └── index.html
└── storage
    └── app.db (créé au premier démarrage)
```

## Prérequis

- Python 3.10+
- Node.js (optionnel si vous souhaitez servir le front autrement qu'en fichier statique)

## Démarrage backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

L'API expose un point de santé (`GET /health`) et les routes de production sous `http://localhost:8000/api/v1`.

## Démarrage frontend

Les fichiers front-end sont statiques. Pour les servir rapidement :

```bash
cd frontend
python -m http.server 5173
```

Puis ouvrez <http://localhost:5173>. L'interface détecte automatiquement l'API exécutée sur `localhost:8000`.

## Fonctionnalités principales

### Exports Excel
- `POST /api/v1/exports/simulation` : génère un classeur Excel multi-feuilles pour une simulation tarifaire complète.
- `POST /api/v1/exports/reservation` : produit un rapport de prévision de réservation.

### Suivi des tarifs
- `POST /api/v1/price-tracking/simulate` : crée une série temporelle synthétique et des analytics (prix moyen, variance, tendance, disponibilité).

### Gestion documentaire
- `POST /api/v1/excel/upload` : téléverse un fichier Excel et enregistre ses métadonnées.
- `GET /api/v1/excel/history` : liste les fichiers stockés.
- `GET /api/v1/excel/{id}/download` : télécharge un fichier.
- `DELETE /api/v1/excel/{id}` : supprime un fichier et ses traces.
- `GET /api/v1/excel/settings` / `PUT /api/v1/excel/settings` : consulte et modifie les paramètres globaux.

## Base de données

Le service utilise SQLite (fichier `storage/app.db`) via SQLModel. Les tables sont créées au démarrage (`ActivityLog`, `UploadedExcelFile`, `AppSettings`).

## Design & expérience

Le front-end adopte une esthétique premium :
- Hero gradient moderne, composants arrondis et ombres douces.
- Sections modulaires pour exports, suivi des tarifs et gestion documentaire.
- Notifications toast et mises à jour en temps réel via l'API.

## Tests rapides

1. Démarrer l'API (`uvicorn app.main:app --reload`).
2. Servir le front (`python -m http.server 5173`).
3. Accéder à l'interface, lancer une simulation et téléverser un fichier Excel de test.

L'application est prête à être étendue (authentification, rôles, connecteurs PMS) selon vos besoins.

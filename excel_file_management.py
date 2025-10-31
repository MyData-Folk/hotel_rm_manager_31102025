"""
Module d'extension pour la gestion des fichiers Excel et paramètres
HotelManager Pro V2 - Excel File Management & Settings

Ce module ajoute :
- Sauvegarde automatique des fichiers Excel de tarifs
- Historique des 10 derniers fichiers par hôtel  
- Gestion des paramètres (connexion PostgreSQL)
- Interface d'administration des fichiers
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlmodel import SQLModel, Field as SQLField, select, and_, func, desc
import json
import os
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

# ===============================
# MODÈLES DE DONNÉES
# ===============================

class TariffFile(SQLModel, table=True):
    """Modèle pour stocker les fichiers Excel de tarifs"""
    id: Optional[int] = SQLField(default=None, primary_key=True)
    hotel_id: str = SQLField(index=True)
    filename: str = SQLField(index=True)
    original_filename: str
    file_type: str = SQLField(default="tariff_excel", index=True)  #区分文件类型
    file_size: int = SQLField(default=0)
    content_type: Optional[str] = SQLField(default=None)
    
    # Métadonnées
    sheet_count: Optional[int] = SQLField(default=None)
    data_range: Optional[str] = SQLField(default=None)  # 如 "2025-01-01 to 2025-01-31"
    uploaded_by: str = SQLField(default="user")
    
    # Timestamps
    uploaded_at: datetime = SQLField(default_factory=datetime.utcnow, index=True)
    processed_at: Optional[datetime] = SQLField(default=None)
    
    # Statut
    status: str = SQLField(default="uploaded", index=True)  # uploaded, processed, error
    error_message: Optional[str] = SQLField(default=None)
    
    # Data storage
    stored_path: Optional[str] = SQLField(default=None)
    data: bytes = SQLField(sa_column=SQLField(sa_column=None), default=b"")

class AppSettings(SQLModel, table=True):
    """Modèle pour stocker les paramètres de l'application"""
    id: Optional[int] = SQLField(default=None, primary_key=True)
    setting_key: str = SQLField(unique=True, index=True)
    setting_value: str
    setting_type: str = SQLField(default="string")  # string, integer, boolean, json
    description: Optional[str] = SQLField(default=None)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow, index=True)
    updated_by: str = SQLField(default="system")

class TariffFileOut(BaseModel):
    """Modèle de sortie pour les fichiers de tarifs"""
    id: int
    hotel_id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    content_type: Optional[str]
    sheet_count: Optional[int]
    data_range: Optional[str]
    uploaded_by: str
    uploaded_at: datetime
    processed_at: Optional[datetime]
    status: str
    error_message: Optional[str]

class SettingsOut(BaseModel):
    """Modèle de sortie pour les paramètres"""
    id: int
    setting_key: str
    setting_value: str
    setting_type: str
    description: Optional[str]
    updated_at: datetime
    updated_by: str

class SettingsUpdate(BaseModel):
    """Modèle pour mettre à jour les paramètres"""
    setting_key: str
    setting_value: str
    setting_type: Optional[str] = "string"
    description: Optional[str] = None
    updated_by: str = Field(default="user")

class ExcelUploadResponse(BaseModel):
    """Modèle de réponse pour l'upload Excel"""
    success: bool
    message: str
    file_id: Optional[int] = None
    file_info: Optional[TariffFileOut] = None
    history_count: Optional[int] = None
    cleaned_files: Optional[int] = None

class FileHistoryResponse(BaseModel):
    """Modèle de réponse pour l'historique des fichiers"""
    success: bool
    hotel_id: str
    files: List[TariffFileOut]
    total_files: int
    oldest_file: Optional[datetime] = None
    newest_file: Optional[datetime] = None

# ===============================
# FONCTIONS UTILITAIRES
# ===============================

def get_file_extension(filename: str) -> str:
    """Récupère l'extension d'un fichier"""
    return Path(filename).suffix.lower()

def validate_excel_file(file: UploadFile) -> bool:
    """Valide qu'un fichier est un Excel valide"""
    allowed_extensions = ['.xlsx', '.xls', '.xlsm']
    file_ext = get_file_extension(file.filename)
    return file_ext in allowed_extensions

def clean_old_files(session: Session, hotel_id: str, max_files: int = 10):
    """
    Nettoie les anciens fichiers en gardant seulement les max_files plus récents
    Retourne le nombre de fichiers supprimés
    """
    try:
        # Compter les fichiers existants
        count_query = select(func.count(TariffFile.id)).where(TariffFile.hotel_id == hotel_id)
        total_files = session.exec(count_query).one()
        
        if total_files <= max_files:
            return 0
        
        # Récupérer les IDs des fichiers à supprimer (les plus anciens)
        files_to_delete_query = (
            select(TariffFile.id)
            .where(TariffFile.hotel_id == hotel_id)
            .order_by(desc(TariffFile.uploaded_at))
            .offset(max_files)
        )
        
        files_to_delete = session.exec(files_to_delete_query).all()
        
        # Supprimer les fichiers
        for file_id in files_to_delete:
            file_record = session.get(TariffFile, file_id[0])
            if file_record:
                # Supprimer le fichier physique si il existe
                if file_record.stored_path and os.path.exists(file_record.stored_path):
                    try:
                        os.remove(file_record.stored_path)
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer le fichier physique: {e}")
                
                session.delete(file_record)
        
        session.commit()
        return len(files_to_delete)
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des fichiers: {e}")
        session.rollback()
        return 0

def extract_excel_metadata(file_content: bytes) -> Dict[str, Any]:
    """Extrait les métadonnées d'un fichier Excel"""
    try:
        import pandas as pd
        import io
        
        # Lire le fichier Excel
        excel_file = io.BytesIO(file_content)
        
        # Récupérer les noms des feuilles
        xl = pd.ExcelFile(excel_file)
        sheet_names = xl.sheet_names
        
        metadata = {
            "sheet_count": len(sheet_names),
            "sheet_names": sheet_names[:10],  # Limiter à 10 feuilles
            "sheets_summary": []
        }
        
        # Analyser chaque feuille (juste les premières lignes pour les métadonnées)
        for sheet_name in sheet_names[:5]:  # Analyser seulement 5 premières feuilles
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=5)
                metadata["sheets_summary"].append({
                    "name": sheet_name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist()[:10]  # 10 premières colonnes
                })
            except Exception as e:
                logger.warning(f"Erreur lors de l'analyse de la feuille {sheet_name}: {e}")
                metadata["sheets_summary"].append({
                    "name": sheet_name,
                    "error": str(e)
                })
        
        return metadata
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des métadonnées: {e}")
        return {
            "sheet_count": 0,
            "sheet_names": [],
            "sheets_summary": [],
            "error": str(e)
        }

def create_hotel_directory(hotel_id: str, base_path: str = "/tmp/hotel_excel_storage") -> str:
    """Crée le répertoire de stockage pour un hôtel"""
    hotel_dir = os.path.join(base_path, f"hotel_{hotel_id}")
    os.makedirs(hotel_dir, exist_ok=True)
    return hotel_dir

# ===============================
# ENDPOINTS API
# ===============================

def create_excel_management_router() -> APIRouter:
    """Crée le routeur pour la gestion des fichiers Excel et paramètres"""
    
    router = APIRouter(prefix="/excel-management", tags=["Excel Management"])
    
    @router.post("/upload/{hotel_id}", response_model=ExcelUploadResponse)
    async def upload_tariff_excel(
        hotel_id: str,
        file: UploadFile = File(...),
        uploaded_by: str = Query("user", description="Utilisateur qui uploade"),
        db: Session = Depends(get_db)
    ):
        """Upload et sauvegarde d'un fichier Excel de tarifs"""
        try:
            # Validation du fichier
            if not validate_excel_file(file):
                raise HTTPException(
                    status_code=400,
                    detail="Format de fichier non supporté. Utilisez .xlsx, .xls ou .xlsm"
                )
            
            # Lire le contenu du fichier
            file_content = await file.read()
            
            if len(file_content) == 0:
                raise HTTPException(status_code=400, detail="Fichier vide")
            
            # Créer le répertoire de l'hôtel
            hotel_dir = create_hotel_directory(hotel_id)
            
            # Générer un nom de fichier unique
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = get_file_extension(file.filename)
            unique_filename = f"tariff_{hotel_id}_{timestamp}{file_extension}"
            stored_path = os.path.join(hotel_dir, unique_filename)
            
            # Sauvegarder le fichier physique
            with open(stored_path, 'wb') as f:
                f.write(file_content)
            
            # Extraire les métadonnées
            metadata = extract_excel_metadata(file_content)
            
            # Créer l'enregistrement en base
            file_record = TariffFile(
                hotel_id=hotel_id,
                filename=unique_filename,
                original_filename=file.filename,
                file_type="tariff_excel",
                file_size=len(file_content),
                content_type=file.content_type,
                sheet_count=metadata.get("sheet_count"),
                uploaded_by=uploaded_by,
                processed_at=datetime.utcnow(),
                status="processed",
                stored_path=stored_path,
                data=file_content  # Sauvegarde en base aussi
            )
            
            # Détecter la plage de données (si possible)
            # Ici on peut ajouter une logique pour analyser le contenu
            file_record.data_range = "Auto-détecté lors du traitement"
            
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            
            # Nettoyer les anciens fichiers (garder seulement les 10 derniers)
            cleaned_count = clean_old_files(db, hotel_id)
            
            # Log de l'activité
            activity_log = ActivityLog(
                hotel_id=hotel_id,
                activity_type="excel_upload",
                description=f"Fichier Excel uploadé: {file.filename}",
                details=f"ID: {file_record.id}, Taille: {len(file_content)} bytes",
                performed_by=uploaded_by
            )
            db.add(activity_log)
            db.commit()
            
            return ExcelUploadResponse(
                success=True,
                message=f"Fichier {file.filename} sauvegardé avec succès",
                file_id=file_record.id,
                file_info=TariffFileOut(**file_record.dict()),
                history_count=clean_old_files(db, hotel_id) + 1,
                cleaned_files=cleaned_count
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'upload Excel: {e}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du traitement du fichier: {str(e)}"
            )
    
    @router.get("/history/{hotel_id}", response_model=FileHistoryResponse)
    def get_file_history(
        hotel_id: str,
        limit: int = Query(10, ge=1, le=50, description="Nombre maximum de fichiers à retourner"),
        db: Session = Depends(get_db)
    ):
        """Récupère l'historique des fichiers Excel d'un hôtel"""
        try:
            # Récupérer les fichiers triés par date de téléchargement
            files_query = (
                select(TariffFile)
                .where(and_(TariffFile.hotel_id == hotel_id, TariffFile.file_type == "tariff_excel"))
                .order_by(desc(TariffFile.uploaded_at))
                .limit(limit)
            )
            
            files = db.exec(files_query).all()
            
            # Convertir en modèles de sortie
            files_out = [TariffFileOut(**file.dict()) for file in files]
            
            # Calculer les statistiques
            total_query = (
                select(func.count(TariffFile.id))
                .where(and_(TariffFile.hotel_id == hotel_id, TariffFile.file_type == "tariff_excel"))
            )
            total_files = db.exec(total_query).one()
            
            oldest_file = None
            newest_file = None
            if files:
                oldest_file = min(file.uploaded_at for file in files)
                newest_file = max(file.uploaded_at for file in files)
            
            return FileHistoryResponse(
                success=True,
                hotel_id=hotel_id,
                files=files_out,
                total_files=total_files,
                oldest_file=oldest_file,
                newest_file=newest_file
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
            )
    
    @router.get("/download/{file_id}")
    def download_excel_file(file_id: int, db: Session = Depends(get_db)):
        """Télécharge un fichier Excel depuis l'historique"""
        try:
            file_record = db.get(TariffFile, file_id)
            
            if not file_record:
                raise HTTPException(status_code=404, detail="Fichier non trouvé")
            
            if file_record.file_type != "tariff_excel":
                raise HTTPException(status_code=400, detail="Type de fichier non supporté")
            
            # Log de l'activité
            activity_log = ActivityLog(
                hotel_id=file_record.hotel_id,
                activity_type="excel_download",
                description=f"Téléchargement du fichier: {file_record.original_filename}",
                details=f"ID: {file_id}",
                performed_by="user"
            )
            db.add(activity_log)
            db.commit()
            
            return StreamingResponse(
                io.BytesIO(file_record.data),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={file_record.original_filename}"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du téléchargement: {str(e)}"
            )
    
    @router.delete("/delete/{file_id}")
    def delete_excel_file(file_id: int, db: Session = Depends(get_db)):
        """Supprime un fichier de l'historique"""
        try:
            file_record = db.get(TariffFile, file_id)
            
            if not file_record:
                raise HTTPException(status_code=404, detail="Fichier non trouvé")
            
            hotel_id = file_record.hotel_id
            
            # Supprimer le fichier physique
            if file_record.stored_path and os.path.exists(file_record.stored_path):
                try:
                    os.remove(file_record.stored_path)
                except Exception as e:
                    logger.warning(f"Impossible de supprimer le fichier physique: {e}")
            
            # Supprimer de la base de données
            db.delete(file_record)
            db.commit()
            
            # Log de l'activité
            activity_log = ActivityLog(
                hotel_id=hotel_id,
                activity_type="excel_delete",
                description=f"Fichier supprimé: {file_record.original_filename}",
                details=f"ID: {file_id}",
                performed_by="user"
            )
            db.add(activity_log)
            db.commit()
            
            return {"success": True, "message": "Fichier supprimé avec succès"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la suppression: {str(e)}"
            )
    
    @router.get("/stats/{hotel_id}")
    def get_file_stats(hotel_id: str, db: Session = Depends(get_db)):
        """Récupère les statistiques des fichiers d'un hôtel"""
        try:
            # Statistiques générales
            total_query = (
                select(func.count(TariffFile.id))
                .where(and_(TariffFile.hotel_id == hotel_id, TariffFile.file_type == "tariff_excel"))
            )
            total_files = db.exec(total_query).one()
            
            # Taille totale
            size_query = (
                select(func.sum(TariffFile.file_size))
                .where(and_(TariffFile.hotel_id == hotel_id, TariffFile.file_type == "tariff_excel"))
            )
            total_size = db.exec(size_query).one() or 0
            
            # Dernier upload
            last_upload_query = (
                select(TariffFile.uploaded_at)
                .where(and_(TariffFile.hotel_id == hotel_id, TariffFile.file_type == "tariff_excel"))
                .order_by(desc(TariffFile.uploaded_at))
                .limit(1)
            )
            last_upload = db.exec(last_upload_query).first()
            
            # Répartition par statut
            status_query = (
                select(TariffFile.status, func.count(TariffFile.id))
                .where(and_(TariffFile.hotel_id == hotel_id, TariffFile.file_type == "tariff_excel"))
                .group_by(TariffFile.status)
            )
            status_stats = dict(db.exec(status_query).all())
            
            return {
                "success": True,
                "hotel_id": hotel_id,
                "stats": {
                    "total_files": total_files,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "last_upload": last_upload,
                    "status_distribution": status_stats,
                    "limit": 10,
                    "can_upload": total_files < 10
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du calcul des statistiques: {str(e)}"
            )
    
    return router

def create_settings_router() -> APIRouter:
    """Crée le routeur pour la gestion des paramètres"""
    
    router = APIRouter(prefix="/settings", tags=["Settings"])
    
    @router.get("", response_model=List[SettingsOut])
    def get_all_settings(db: Session = Depends(get_db)):
        """Récupère tous les paramètres de l'application"""
        try:
            settings = db.exec(select(AppSettings).order_by(AppSettings.setting_key)).all()
            return [SettingsOut(**setting.dict()) for setting in settings]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des paramètres: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la récupération des paramètres: {str(e)}"
            )
    
    @router.get("/{setting_key}", response_model=SettingsOut)
    def get_setting(setting_key: str, db: Session = Depends(get_db)):
        """Récupère un paramètre spécifique"""
        try:
            setting = db.exec(select(AppSettings).where(AppSettings.setting_key == setting_key)).first()
            
            if not setting:
                raise HTTPException(status_code=404, detail="Paramètre non trouvé")
            
            return SettingsOut(**setting.dict())
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du paramètre: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la récupération du paramètre: {str(e)}"
            )
    
    @router.put("/{setting_key}", response_model=SettingsOut)
    def update_setting(
        setting_key: str,
        payload: SettingsUpdate,
        db: Session = Depends(get_db)
    ):
        """Met à jour un paramètre"""
        try:
            # Récupérer le paramètre existant
            setting = db.exec(select(AppSettings).where(AppSettings.setting_key == setting_key)).first()
            
            if setting:
                # Mise à jour
                setting.setting_value = payload.setting_value
                setting.setting_type = payload.setting_type or setting.setting_type
                setting.description = payload.description or setting.description
                setting.updated_at = datetime.utcnow()
                setting.updated_by = payload.updated_by
            else:
                # Création
                setting = AppSettings(
                    setting_key=setting_key,
                    setting_value=payload.setting_value,
                    setting_type=payload.setting_type,
                    description=payload.description,
                    updated_by=payload.updated_by
                )
                db.add(setting)
            
            db.commit()
            db.refresh(setting)
            
            # Log de l'activité
            activity_log = ActivityLog(
                activity_type="setting_update",
                description=f"Paramètre mis à jour: {setting_key}",
                details=f"Nouvelle valeur: {payload.setting_value}",
                performed_by=payload.updated_by
            )
            db.add(activity_log)
            db.commit()
            
            return SettingsOut(**setting.dict())
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du paramètre: {e}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la mise à jour du paramètre: {str(e)}"
            )
    
    @router.post("/initialize")
    def initialize_default_settings(db: Session = Depends(get_db)):
        """Initialise les paramètres par défaut"""
        try:
            default_settings = [
                {
                    "setting_key": "database_url",
                    "setting_value": "postgresql://user:password@localhost:5432/hotelmanager",
                    "setting_type": "string",
                    "description": "URL de connexion à la base de données PostgreSQL",
                    "updated_by": "system"
                },
                {
                    "setting_key": "excel_storage_path",
                    "setting_value": "/tmp/hotel_excel_storage",
                    "setting_type": "string", 
                    "description": "Chemin de stockage des fichiers Excel",
                    "updated_by": "system"
                },
                {
                    "setting_key": "max_files_per_hotel",
                    "setting_value": "10",
                    "setting_type": "integer",
                    "description": "Nombre maximum de fichiers Excel à conserver par hôtel",
                    "updated_by": "system"
                },
                {
                    "setting_key": "auto_cleanup_enabled",
                    "setting_value": "true",
                    "setting_type": "boolean",
                    "description": "Nettoyage automatique des anciens fichiers activé",
                    "updated_by": "system"
                }
            ]
            
            for setting_data in default_settings:
                # Vérifier si le paramètre existe déjà
                existing = db.exec(
                    select(AppSettings).where(AppSettings.setting_key == setting_data["setting_key"])
                ).first()
                
                if not existing:
                    setting = AppSettings(**setting_data)
                    db.add(setting)
            
            db.commit()
            
            return {"success": True, "message": "Paramètres par défaut initialisés"}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des paramètres: {e}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'initialisation: {str(e)}"
            )
    
    return router

# ===============================
# FONCTION D'INTÉGRATION
# ===============================

def add_excel_management_to_app(app, db_dependency):
    """
    Intègre le système de gestion des fichiers Excel et paramètres à l'application FastAPI existante.
    
    Args:
        app: Instance FastAPI
        db_dependency: Dépendance pour la base de données
    """
    global get_db
    get_db = db_dependency
    
    # Créer les tables si elles n'existent pas
    # (Ces lignes seront exécutées dans le main.py lors de l'initialisation)
    
    # Ajout des routeurs
    excel_router = create_excel_management_router()
    settings_router = create_settings_router()
    
    app.include_router(excel_router)
    app.include_router(settings_router)
    
    # Log de l'intégration
    logger.info("Système de gestion des fichiers Excel et paramètres intégré avec succès")

def create_excel_tables(engine):
    """Crée les tables nécessaires pour la gestion des fichiers Excel"""
    # Cette fonction sera appelée depuis main.py
    TariffFile.metadata.create_all(engine)
    AppSettings.metadata.create_all(engine)

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlmodel import Session, select

from ..core.config import get_settings
from ..models.entities import AppSettings, UploadedExcelFile
from ..utils.logging import log_activity

logger = logging.getLogger(__name__)
settings = get_settings()


def _ensure_storage_dir(hotel_id: str) -> Path:
    root = Path(settings.storage_dir) / hotel_id
    root.mkdir(parents=True, exist_ok=True)
    return root


def _read_excel_preview(path: Path) -> Dict[str, Optional[str]]:
    try:
        xls = pd.ExcelFile(path)
        sheet_names = xls.sheet_names
        preview_data = {}
        for sheet in sheet_names[:2]:
            df = xls.parse(sheet, nrows=5)
            preview_data[sheet] = df.to_json(orient="split")
        return {"sheet_names": sheet_names, "preview": json.dumps(preview_data)}
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Unable to build Excel preview: %s", exc)
        return {"sheet_names": [], "preview": None}


def store_excel_file(session: Session, hotel_id: str, upload: UploadFile) -> UploadedExcelFile:
    if not upload.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    storage_dir = _ensure_storage_dir(hotel_id)
    stored_name = f"{hotel_id}_{upload.filename}"
    destination = storage_dir / stored_name
    content = upload.file.read()
    destination.write_bytes(content)
    metadata = _read_excel_preview(destination)
    record = UploadedExcelFile(
        hotel_id=hotel_id,
        filename=upload.filename,
        stored_name=stored_name,
        file_size=len(content),
        sheet_names=", ".join(metadata.get("sheet_names", [])),
        preview=metadata.get("preview"),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    log_activity(
        session,
        action="upload",
        entity="excel_file",
        metadata={"hotel_id": hotel_id, "filename": upload.filename},
    )
    return record


def list_excel_files(session: Session, hotel_id: Optional[str] = None) -> List[UploadedExcelFile]:
    statement = select(UploadedExcelFile)
    if hotel_id:
        statement = statement.where(UploadedExcelFile.hotel_id == hotel_id)
    results = session.exec(statement.order_by(UploadedExcelFile.uploaded_at.desc())).all()
    return list(results)


def get_excel_file(session: Session, file_id: int) -> UploadedExcelFile:
    file = session.get(UploadedExcelFile, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return file


def delete_excel_file(session: Session, file_id: int) -> None:
    file = get_excel_file(session, file_id)
    path = Path(settings.storage_dir) / file.hotel_id / file.stored_name
    if path.exists():
        path.unlink()
    session.delete(file)
    session.commit()
    log_activity(
        session,
        action="delete",
        entity="excel_file",
        metadata={"hotel_id": file.hotel_id, "filename": file.filename},
    )


def get_settings_record(session: Session) -> AppSettings:
    settings_record = session.exec(select(AppSettings)).first()
    if not settings_record:
        settings_record = AppSettings()
        session.add(settings_record)
        session.commit()
        session.refresh(settings_record)
    return settings_record


def update_settings(session: Session, payload: Dict[str, str]) -> AppSettings:
    record = get_settings_record(session)
    for key, value in payload.items():
        if hasattr(record, key):
            setattr(record, key, value)
    record.updated_at = datetime.utcnow()
    session.add(record)
    session.commit()
    session.refresh(record)
    log_activity(session, action="update", entity="settings", metadata=payload)
    return record

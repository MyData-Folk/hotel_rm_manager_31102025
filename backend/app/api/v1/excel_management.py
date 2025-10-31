from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from ...core.config import get_settings
from ...database import get_session
from ...services import excel_management as service

router = APIRouter(prefix="/excel", tags=["Excel Management"])
settings = get_settings()


@router.post("/upload")
async def upload_excel(
    hotel_id: str = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    return service.store_excel_file(session, hotel_id, file)


@router.get("/history")
async def history(hotel_id: Optional[str] = None, session: Session = Depends(get_session)):
    return service.list_excel_files(session, hotel_id)


@router.get("/{file_id}/download")
async def download(file_id: int, session: Session = Depends(get_session)):
    record = service.get_excel_file(session, file_id)
    path = Path(settings.storage_dir) / record.hotel_id / record.stored_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable sur le disque")
    return FileResponse(path, filename=record.filename)


@router.delete("/{file_id}")
async def remove(file_id: int, session: Session = Depends(get_session)):
    service.delete_excel_file(session, file_id)
    return {"success": True}


@router.get("/settings")
async def get_settings(session: Session = Depends(get_session)):
    return service.get_settings_record(session)


@router.put("/settings")
async def update_settings(payload: dict, session: Session = Depends(get_session)):
    return service.update_settings(session, payload)

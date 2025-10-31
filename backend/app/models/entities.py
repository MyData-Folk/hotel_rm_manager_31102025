from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ActivityLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action: str = Field(index=True)
    entity: str = Field(index=True)
    metadata: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UploadedExcelFile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: str = Field(index=True)
    filename: str
    stored_name: str
    file_size: int
    sheet_names: Optional[str] = None
    preview: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class AppSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_name: str = Field(default="HotelManager Pro")
    currency: str = Field(default="EUR")
    locale: str = Field(default="fr-FR")
    default_partner: str = Field(default="Direct")
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

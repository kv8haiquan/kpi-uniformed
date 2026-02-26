"""Pydantic schemas cho tra loi / binh luan."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from forum_service.schemas.chu_de import UserBrief


class TraLoiCreate(BaseModel):
    noi_dung: str = Field(..., min_length=1)
    parent_id: Optional[UUID] = None
    can_cu_phap_ly: Optional[list[Any]] = None


class TraLoiUpdate(BaseModel):
    noi_dung: Optional[str] = Field(None, min_length=1)
    can_cu_phap_ly: Optional[list[Any]] = None


class TraLoiResponse(BaseModel):
    """Response tra loi."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    chu_de_id: UUID
    parent_id: Optional[UUID] = None
    noi_dung: str
    tac_gia: Optional[UserBrief] = None
    is_dap_an_chuan: bool = False
    is_an: bool = False
    so_upvote: int = 0
    can_cu_phap_ly: Optional[list[Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

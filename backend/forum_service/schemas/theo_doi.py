"""Pydantic schemas cho theo doi chu de."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TheoDoiResponse(BaseModel):
    """Response theo doi."""
    model_config = ConfigDict(from_attributes=True)
    cong_chuc_id: UUID
    chu_de_id: UUID
    created_at: Optional[datetime] = None

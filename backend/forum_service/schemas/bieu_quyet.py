"""Pydantic schemas cho bieu quyet (vote)."""
from uuid import UUID
from pydantic import BaseModel, Field


class BieuQuyetCreate(BaseModel):
    doi_tuong_type: str = Field(..., pattern="^(CHU_DE|TRA_LOI)$")
    doi_tuong_id: UUID
    loai: str = Field(..., pattern="^(UP|DOWN)$")


class BieuQuyetDelete(BaseModel):
    doi_tuong_type: str = Field(..., pattern="^(CHU_DE|TRA_LOI)$")
    doi_tuong_id: UUID


class BieuQuyetResponse(BaseModel):
    """Response sau khi vote."""
    hanh_dong: str  # "CREATED", "TOGGLED_OFF", "CHANGED"
    loai: str | None = None  # UP, DOWN, None (neu toggled off)
    so_upvote_moi: int  # so_upvote moi cua doi tuong

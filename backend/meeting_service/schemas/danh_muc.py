"""Schemas cho danh mục dùng chung của Lịch công tác (G4.11)."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DanhMucItem(BaseModel):
    """Một mục danh mục trả về cho giao diện."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nhom: str
    ma: str
    nhan: str
    thu_tu: int
    is_active: bool
    he_thong: bool
    mo_ta: Optional[str] = None
    # Chỉ màn hình quản trị mới xin số này (đếm tốn một truy vấn mỗi mục),
    # nên để None ở các đường đọc thường.
    dang_su_dung: Optional[int] = None


class DanhMucCreate(BaseModel):
    nhom: str
    ma: str = Field(max_length=50)
    nhan: str = Field(max_length=150)
    thu_tu: Optional[int] = None
    mo_ta: Optional[str] = None


class DanhMucUpdate(BaseModel):
    """Chỉ gửi trường muốn đổi.

    Cố tình KHÔNG có `ma`: mã là khoá dữ liệu đã ghi tham chiếu tới. Nếu
    giao diện vẫn gửi lên thì tầng dịch vụ chối bằng `DM_KHONG_DOI_MA`.
    """

    nhan: Optional[str] = Field(default=None, max_length=150)
    thu_tu: Optional[int] = None
    is_active: Optional[bool] = None
    mo_ta: Optional[str] = None


class DongSapXep(BaseModel):
    id: UUID
    thu_tu: int


class DanhMucSapXep(BaseModel):
    thu_tu: list[DongSapXep]

"""
notification_service.py
========================
Wrapper INSERT trực tiếp vào common.thong_bao với loai='MEETING'.

Schema thật (verify P0):
  nguoi_nhan_id, tieu_de, noi_dung, loai (VARCHAR), link_url,
  doi_tuong_type, doi_tuong_id, da_doc, ngay_doc, muc_do
"""

from typing import Iterable, Optional
from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


LOAI = "MEETING"


async def gui_thong_bao(
    db: AsyncSession,
    *,
    nguoi_nhan_id: UUID,
    tieu_de: str,
    noi_dung: Optional[str] = None,
    sub_loai: Optional[str] = None,
    link_url: Optional[str] = None,
    doi_tuong_id: Optional[UUID] = None,
    muc_do: str = "BINH_THUONG",
) -> None:
    """1 notification. `sub_loai` lưu vào doi_tuong_type (vd: GIAY_MOI_HOP)."""
    await db.execute(
        sa_text("""
            INSERT INTO common.thong_bao
                (nguoi_nhan_id, tieu_de, noi_dung, loai, link_url,
                 doi_tuong_type, doi_tuong_id, muc_do)
            VALUES
                (:nguoi_nhan_id, :tieu_de, :noi_dung, :loai, :link_url,
                 :doi_tuong_type, :doi_tuong_id, :muc_do)
        """),
        {
            "nguoi_nhan_id": str(nguoi_nhan_id),
            "tieu_de": tieu_de[:300],
            "noi_dung": noi_dung,
            "loai": LOAI,
            "link_url": link_url,
            "doi_tuong_type": sub_loai,
            "doi_tuong_id": str(doi_tuong_id) if doi_tuong_id else None,
            "muc_do": muc_do,
        },
    )


async def gui_thong_bao_bulk(
    db: AsyncSession,
    *,
    nguoi_nhan_ids: Iterable[UUID],
    tieu_de: str,
    noi_dung: Optional[str] = None,
    sub_loai: Optional[str] = None,
    link_url: Optional[str] = None,
    doi_tuong_id: Optional[UUID] = None,
    muc_do: str = "BINH_THUONG",
) -> int:
    """Gửi nhiều notification cùng lúc. Trả về số lượng gửi."""
    count = 0
    for nn_id in nguoi_nhan_ids:
        await gui_thong_bao(
            db,
            nguoi_nhan_id=nn_id,
            tieu_de=tieu_de,
            noi_dung=noi_dung,
            sub_loai=sub_loai,
            link_url=link_url,
            doi_tuong_id=doi_tuong_id,
            muc_do=muc_do,
        )
        count += 1
    return count

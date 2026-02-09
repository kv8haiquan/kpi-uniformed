#!/usr/bin/env python3
"""
scripts/verify_import.py
========================
Script kiểm tra dữ liệu sau khi import.

Chạy:
    python scripts/verify_import.py
"""

import asyncio
import sys
from pathlib import Path

# Setup path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models import DonVi, VaiTro, CongChuc, CapBacVaiTro


async def main():
    """Kiểm tra và hiển thị thống kê dữ liệu."""
    
    print("=" * 60)
    print("KIỂM TRA DỮ LIỆU SAU IMPORT")
    print("=" * 60)
    
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Thống kê vai trò
        print("\n📋 VAI TRÒ:")
        result = await session.execute(
            select(VaiTro).order_by(VaiTro.cap_bac)
        )
        for vt in result.scalars().all():
            print(f"   - {vt.ma_vai_tro}: {vt.ten_vai_tro} ({vt.cap_bac.value})")
        
        # 2. Thống kê đơn vị
        print("\n🏢 ĐƠN VỊ:")
        result = await session.execute(
            select(DonVi).order_by(DonVi.thu_tu_hien_thi)
        )
        for dv in result.scalars().all():
            # Đếm số CC trong đơn vị
            cc_count = await session.execute(
                select(func.count()).select_from(CongChuc).where(CongChuc.don_vi_id == dv.id)
            )
            print(f"   - {dv.ma_don_vi}: {dv.ten_don_vi} ({dv.loai_don_vi.value}) - {cc_count.scalar()} CC")
        
        # 3. Thống kê công chức theo vai trò
        print("\n👥 CÔNG CHỨC THEO VAI TRÒ:")
        result = await session.execute(
            select(VaiTro.ten_vai_tro, func.count(CongChuc.id))
            .join(CongChuc, CongChuc.vai_tro_id == VaiTro.id)
            .group_by(VaiTro.ten_vai_tro)
        )
        for row in result.fetchall():
            print(f"   - {row[0]}: {row[1]} người")
        
        # 4. Tổng số
        total_cc = await session.execute(select(func.count()).select_from(CongChuc))
        total_dv = await session.execute(select(func.count()).select_from(DonVi))
        total_ld = await session.execute(
            select(func.count()).select_from(CongChuc).where(CongChuc.is_lanh_dao == True)
        )
        
        print("\n📊 TỔNG KẾT:")
        print(f"   - Tổng công chức: {total_cc.scalar()}")
        print(f"   - Tổng đơn vị: {total_dv.scalar()}")
        print(f"   - Số lãnh đạo: {total_ld.scalar()}")
        
        # 5. Mẫu dữ liệu
        print("\n📝 MẪU DỮ LIỆU (5 công chức đầu):")
        result = await session.execute(
            select(CongChuc)
            .options()
            .limit(5)
        )
        for cc in result.scalars().all():
            print(f"   - {cc.ma_cc}: {cc.ho_ten} | {cc.chuc_vu} | Username: {cc.username}")
    
    await engine.dispose()
    print("\n✅ KIỂM TRA HOÀN TẤT!")


if __name__ == "__main__":
    asyncio.run(main())

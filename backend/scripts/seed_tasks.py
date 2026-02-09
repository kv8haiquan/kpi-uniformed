#!/usr/bin/env python3
"""
scripts/seed_tasks.py
=====================
Script import danh mục sản phẩm/công việc chi tiết vào database.

Chạy:
    python scripts/seed_tasks.py

Tạo dữ liệu:
1. SP Chuẩn: SP1 (Tờ khai), SP2 (Văn bản), SP3 (Giờ trực), SP4 (Chống buôn lậu)
2. Danh mục công việc: 46 mục với mã DM-001 đến DM-046

⚠️ LƯU Ý:
- Script này IDEMPOTENT: chạy nhiều lần không gây lỗi
- Kiểm tra tồn tại trước khi tạo mới
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from decimal import Decimal

# =============================================================================
# SETUP PATH
# =============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models import SpCongViecChuan, DanhMucSpCongViec


# =============================================================================
# CONSTANTS - Dữ liệu SP Chuẩn
# =============================================================================

SP_CHUAN_DATA = [
    {
        "ma_sp": "SP1",
        "ten_sp": "Tờ khai HQ được kiểm tra chi tiết hồ sơ",
        "mo_ta": "Sản phẩm gốc - Mỗi tờ khai mất 5 phút xử lý",
        "thoi_gian_phut": 5,
        "he_so_quy_doi_sp1": Decimal("1"),
        "is_sp_goc": True,
    },
    {
        "ma_sp": "SP2",
        "ten_sp": "Văn bản hành chính",
        "mo_ta": "Văn bản, công văn, báo cáo - Mỗi văn bản mất 60 phút",
        "thoi_gian_phut": 60,
        "he_so_quy_doi_sp1": Decimal("12"),
        "is_sp_goc": False,
    },
    {
        "ma_sp": "SP3",
        "ten_sp": "Giờ trực làm việc",
        "mo_ta": "Giờ trực, họp, công tác - Mỗi giờ = 12 SP gốc",
        "thoi_gian_phut": 60,
        "he_so_quy_doi_sp1": Decimal("12"),
        "is_sp_goc": False,
    },
    {
        "ma_sp": "SP4",
        "ten_sp": "Giờ tuần tra kiểm soát",
        "mo_ta": "Tuần tra, trinh sát, chống buôn lậu - Mỗi giờ = 12 SP gốc",
        "thoi_gian_phut": 60,
        "he_so_quy_doi_sp1": Decimal("12"),
        "is_sp_goc": False,
    },
]


# =============================================================================
# CONSTANTS - Danh mục Công việc chi tiết (46 mục)
# =============================================================================

# Nhóm SP1 - Nghiệp vụ Hải quan (21 mục)
NHOM_SP1 = [
    "Kiểm tra hồ sơ hải quan đơn giản",
    "Kiểm tra thực tế hàng hóa",
    "Thủ tục hủy tờ khai",
    "Thủ tục sửa đổi bổ sung tờ khai",
    "Rà soát tờ khai luồng xanh",
    "Thủ tục qua Hệ thống dịch vụ công trực tuyến",
    "Thủ tục phương tiện xuất cảnh",
    "Thủ tục phương tiện nhập cảnh",
    "Thủ tục phương tiện quá cảnh",
    "Tiếp nhận tờ khai giám sát",
    "Xác nhận qua khu vực giám sát",
    "Kiểm tra tờ khai giám sát",
    "Lấy mẫu",
    "Rà soát các tờ khai quá thời hạn",
    "Cập nhật sổ theo dõi",
    "Phúc tập hồ sơ",
    "Sắp xếp, quản lý, bàn giao, lưu trữ hồ sơ nghiệp vụ",
    "Nghiệp vụ kế toán",
    "Cập nhật Hệ thống",
    "Cân ô tô điện tử",
    "Máy phát hiện ma túy",
]

# Nhóm SP2 - Hành chính - Tổng hợp (11 mục)
NHOM_SP2 = [
    "Báo cáo định kỳ",
    "Báo cáo đột xuất",
    "Kế hoạch, chương trình",
    "Tờ trình",
    "Công văn báo cáo",
    "Công văn triển khai",
    "Biên bản",
    "Quyết định",
    "Quy chế, quy trình",
    "Dự toán thu",
    "Sắp xếp, quản lý, lưu trữ văn bản",
]

# Nhóm SP3 - Trực ban & Công vụ (8 mục)
NHOM_SP3 = [
    "Họp",
    "Đi công tác",
    "Trực giám sát trực tuyến",
    "Hợp đồng lao động làm công việc hỗ trợ phục vụ",
    "Giờ làm việc công vụ",
    "Học, tập huấn",
    "Tổ chức học, tập huấn",
    "Phục vụ thanh tra, kiểm tra",
]

# Nhóm SP4 - Kiểm soát & Chống buôn lậu (6 mục)
NHOM_SP4 = [
    "Tuần tra",
    "Trinh sát",
    "Nắm tình hình",
    "Phục vụ chuyên án",
    "Huấn luyện chó nghiệp vụ",
    "Công việc thuyền viên",
]

# Tổng hợp với thông tin nhóm
DANH_MUC_CONG_VIEC = []

# SP1: Mục 1-21
for i, ten in enumerate(NHOM_SP1, start=1):
    DANH_MUC_CONG_VIEC.append({
        "stt": i,
        "ma_danh_muc": f"DM-{i:03d}",
        "ten_cong_viec": ten,
        "ma_sp": "SP1",
        "nhom_cong_viec": "Nghiệp vụ Hải quan",
    })

# SP2: Mục 22-32
for i, ten in enumerate(NHOM_SP2, start=22):
    DANH_MUC_CONG_VIEC.append({
        "stt": i,
        "ma_danh_muc": f"DM-{i:03d}",
        "ten_cong_viec": ten,
        "ma_sp": "SP2",
        "nhom_cong_viec": "Hành chính - Tổng hợp",
    })

# SP3: Mục 33-40
for i, ten in enumerate(NHOM_SP3, start=33):
    DANH_MUC_CONG_VIEC.append({
        "stt": i,
        "ma_danh_muc": f"DM-{i:03d}",
        "ten_cong_viec": ten,
        "ma_sp": "SP3",
        "nhom_cong_viec": "Trực ban & Công vụ",
    })

# SP4: Mục 41-46
for i, ten in enumerate(NHOM_SP4, start=41):
    DANH_MUC_CONG_VIEC.append({
        "stt": i,
        "ma_danh_muc": f"DM-{i:03d}",
        "ten_cong_viec": ten,
        "ma_sp": "SP4",
        "nhom_cong_viec": "Kiểm soát & Chống buôn lậu",
    })


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

async def ensure_sp_chuan(session: AsyncSession) -> dict[str, str]:
    """
    Đảm bảo bảng sp_cong_viec_chuan có đủ 4 loại SP.
    
    Returns:
        dict: Mapping mã SP -> UUID (VD: {"SP1": "uuid-1", ...})
    """
    print("\n" + "=" * 60)
    print("BƯỚC 1: KIỂM TRA/TẠO SP CHUẨN")
    print("=" * 60)
    
    sp_map = {}
    created_count = 0
    
    for sp_data in SP_CHUAN_DATA:
        ma_sp = sp_data["ma_sp"]
        
        # Kiểm tra tồn tại
        result = await session.execute(
            select(SpCongViecChuan).where(SpCongViecChuan.ma_sp == ma_sp)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            sp_map[ma_sp] = str(existing.id)
            print(f"  [SKIP] {ma_sp}: {existing.ten_sp} (đã tồn tại)")
        else:
            # Tạo mới
            new_sp = SpCongViecChuan(**sp_data)
            session.add(new_sp)
            await session.flush()
            
            sp_map[ma_sp] = str(new_sp.id)
            created_count += 1
            print(f"  [CREATE] {ma_sp}: {new_sp.ten_sp}")
            print(f"           Thời gian: {new_sp.thoi_gian_phut} phút, Hệ số: {new_sp.he_so_quy_doi_sp1}")
    
    await session.commit()
    print(f"\n✅ SP Chuẩn: {created_count} mới, {len(SP_CHUAN_DATA) - created_count} đã có")
    
    return sp_map


async def seed_danh_muc_cong_viec(
    session: AsyncSession,
    sp_map: dict[str, str]
) -> tuple[int, int]:
    """
    Import danh mục công việc chi tiết.
    
    Args:
        session: Database session
        sp_map: Mapping mã SP -> UUID
        
    Returns:
        tuple: (số tạo mới, số đã tồn tại)
    """
    print("\n" + "=" * 60)
    print("BƯỚC 2: IMPORT DANH MỤC CÔNG VIỆC")
    print("=" * 60)
    
    total = len(DANH_MUC_CONG_VIEC)
    created_count = 0
    skipped_count = 0
    
    # Lấy danh sách mã danh mục đã tồn tại
    result = await session.execute(
        select(DanhMucSpCongViec.ma_danh_muc)
    )
    existing_codes = {row[0] for row in result.fetchall()}
    print(f"Đã có {len(existing_codes)} danh mục trong database\n")
    
    current_nhom = None
    
    for item in DANH_MUC_CONG_VIEC:
        ma_danh_muc = item["ma_danh_muc"]
        ten_cong_viec = item["ten_cong_viec"]
        ma_sp = item["ma_sp"]
        nhom_cong_viec = item["nhom_cong_viec"]
        
        # In header nhóm mới
        if current_nhom != nhom_cong_viec:
            current_nhom = nhom_cong_viec
            print(f"\n📁 {nhom_cong_viec} ({ma_sp}):")
        
        # Kiểm tra tồn tại
        if ma_danh_muc in existing_codes:
            skipped_count += 1
            print(f"  [SKIP] {ma_danh_muc}: {ten_cong_viec[:40]}...")
            continue
        
        # Lấy SP chuẩn ID
        sp_chuan_id = sp_map.get(ma_sp)
        if not sp_chuan_id:
            print(f"  [ERROR] {ma_danh_muc}: Không tìm thấy SP chuẩn {ma_sp}")
            continue
        
        # Tạo danh mục mới
        new_danh_muc = DanhMucSpCongViec(
            ma_danh_muc=ma_danh_muc,
            ten_cong_viec=ten_cong_viec,
            sp_chuan_id=sp_chuan_id,
            nhom_cong_viec=nhom_cong_viec,
            don_vi_ap_dung_id=None,  # Áp dụng toàn Chi cục
            is_active=True,
        )
        
        session.add(new_danh_muc)
        created_count += 1
        print(f"  [CREATE] {ma_danh_muc}: {ten_cong_viec[:50]}{'...' if len(ten_cong_viec) > 50 else ''}")
    
    await session.commit()
    
    return created_count, skipped_count


async def print_summary(session: AsyncSession):
    """In thống kê sau khi import."""
    
    print("\n" + "=" * 60)
    print("THỐNG KÊ DANH MỤC CÔNG VIỆC")
    print("=" * 60)
    
    # Đếm theo SP chuẩn
    result = await session.execute(
        select(
            SpCongViecChuan.ma_sp,
            SpCongViecChuan.ten_sp,
            func.count(DanhMucSpCongViec.id)
        )
        .outerjoin(DanhMucSpCongViec, DanhMucSpCongViec.sp_chuan_id == SpCongViecChuan.id)
        .group_by(SpCongViecChuan.ma_sp, SpCongViecChuan.ten_sp)
        .order_by(SpCongViecChuan.ma_sp)
    )
    
    print("\n📊 Phân bố theo SP Chuẩn:")
    print("-" * 50)
    total_dm = 0
    for row in result.fetchall():
        ma_sp, ten_sp, count = row
        total_dm += count
        print(f"  {ma_sp}: {ten_sp[:35]:<35} │ {count:>3} mục")
    print("-" * 50)
    print(f"  {'TỔNG CỘNG':<40} │ {total_dm:>3} mục")
    
    # Đếm theo nhóm công việc
    result = await session.execute(
        select(
            DanhMucSpCongViec.nhom_cong_viec,
            func.count(DanhMucSpCongViec.id)
        )
        .where(DanhMucSpCongViec.is_deleted == False)
        .group_by(DanhMucSpCongViec.nhom_cong_viec)
    )
    
    print("\n📁 Phân bố theo Nhóm công việc:")
    print("-" * 50)
    for row in result.fetchall():
        nhom, count = row
        if nhom:
            print(f"  {nhom:<40} │ {count:>3} mục")


# =============================================================================
# MAIN FUNCTION
# =============================================================================

async def main():
    """Entry point chính của script."""
    
    print("=" * 60)
    print("SCRIPT IMPORT DANH MỤC CÔNG VIỆC - HẢI QUAN KV8")
    print("=" * 60)
    print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print(f"Tổng số danh mục cần import: {len(DANH_MUC_CONG_VIEC)}")
    
    # Tạo async engine và session
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Bước 1: Đảm bảo có SP Chuẩn
            sp_map = await ensure_sp_chuan(session)
            
            if len(sp_map) < 4:
                print("\n❌ ERROR: Không đủ SP Chuẩn trong database!")
                return
            
            # Bước 2: Import danh mục công việc
            created, skipped = await seed_danh_muc_cong_viec(session, sp_map)
            
            # Bước 3: In thống kê
            await print_summary(session)
            
            # Kết quả
            print("\n" + "=" * 60)
            print("KẾT QUẢ IMPORT")
            print("=" * 60)
            print(f"✅ Tạo mới: {created}")
            print(f"⏭️ Bỏ qua (đã tồn tại): {skipped}")
            print(f"📊 Tổng cộng: {created + skipped}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await session.rollback()
            raise
        
        finally:
            await engine.dispose()
    
    print("\n✅ HOÀN THÀNH!")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    asyncio.run(main())

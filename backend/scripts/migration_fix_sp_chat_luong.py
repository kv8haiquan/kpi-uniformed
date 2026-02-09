#!/usr/bin/env python3
"""
scripts/migration_fix_sp_chat_luong.py
======================================
Script sửa dữ liệu SP Chất lượng và Tiến độ cho các bản kê khai đã duyệt.

HOTFIX v2.5.7 (27/01/2026)

VẤN ĐỀ:
- Các bản kê khai đã phê duyệt (DA_PHE_DUYET) thiếu giá trị so_sp_chat_luong và so_sp_tien_do
- Do bug trong code phê duyệt cũ không tính các trường này

CÔNG THỨC:
- so_sp_chat_luong = so_sp_goc_quy_doi - so_loi_chat_luong (min = 0)
- so_sp_tien_do = so_sp_goc_quy_doi - so_loi_tien_do (min = 0)

CÁCH DÙNG:
    # Xem preview (không thực sự update)
    python scripts/migration_fix_sp_chat_luong.py --dry-run
    
    # Chạy thật
    python scripts/migration_fix_sp_chat_luong.py

LƯU Ý:
- Script này chỉ update dữ liệu HIỆN CÓ
- Không tạo dữ liệu mới
- Chạy trong transaction, có rollback nếu lỗi
"""

import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime

# Thêm path để import được app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func, update, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings


# =============================================================================
# CONFIGURATION
# =============================================================================

# Màu sắc cho terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_database_url() -> str:
    """Lấy database URL từ settings."""
    return settings.database_url


async def get_async_session() -> AsyncSession:
    """Tạo async database session."""
    engine = create_async_engine(
        get_database_url(),
        echo=False,
        pool_size=5,
        max_overflow=10,
    )
    
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    return async_session()


# =============================================================================
# MIGRATION FUNCTIONS
# =============================================================================

async def count_records_to_update(session: AsyncSession) -> int:
    """Đếm số bản ghi cần update."""
    query = text("""
        SELECT COUNT(*) as total
        FROM ke_khai_cong_viec
        WHERE 
            trang_thai = 'DA_PHE_DUYET'
            AND is_deleted = FALSE
            AND (so_sp_chat_luong IS NULL OR so_sp_tien_do IS NULL)
    """)
    
    result = await session.execute(query)
    row = result.fetchone()
    return row[0] if row else 0


async def preview_records(session: AsyncSession, limit: int = 10) -> list:
    """Xem preview các bản ghi sẽ được update."""
    query = text("""
        SELECT 
            id,
            thang,
            nam,
            so_sp_goc_quy_doi,
            so_loi_chat_luong,
            so_loi_tien_do,
            so_sp_chat_luong AS sp_cl_hien_tai,
            so_sp_tien_do AS sp_td_hien_tai,
            GREATEST(COALESCE(so_sp_goc_quy_doi, 0) - COALESCE(so_loi_chat_luong, 0), 0) AS sp_cl_sau_update,
            GREATEST(COALESCE(so_sp_goc_quy_doi, 0) - COALESCE(so_loi_tien_do, 0), 0) AS sp_td_sau_update
        FROM ke_khai_cong_viec
        WHERE 
            trang_thai = 'DA_PHE_DUYET'
            AND is_deleted = FALSE
            AND (so_sp_chat_luong IS NULL OR so_sp_tien_do IS NULL)
        LIMIT :limit
    """)
    
    result = await session.execute(query, {"limit": limit})
    return result.fetchall()


async def execute_update(session: AsyncSession) -> int:
    """Thực hiện update dữ liệu."""
    query = text("""
        UPDATE ke_khai_cong_viec 
        SET 
            so_sp_chat_luong = GREATEST(COALESCE(so_sp_goc_quy_doi, 0) - COALESCE(so_loi_chat_luong, 0), 0),
            so_sp_tien_do = GREATEST(COALESCE(so_sp_goc_quy_doi, 0) - COALESCE(so_loi_tien_do, 0), 0),
            updated_at = NOW()
        WHERE 
            trang_thai = 'DA_PHE_DUYET'
            AND is_deleted = FALSE
            AND (so_sp_chat_luong IS NULL OR so_sp_tien_do IS NULL)
    """)
    
    result = await session.execute(query)
    return result.rowcount


async def verify_no_nulls(session: AsyncSession) -> int:
    """Kiểm tra không còn NULL sau khi update."""
    query = text("""
        SELECT COUNT(*) as remaining
        FROM ke_khai_cong_viec
        WHERE 
            trang_thai = 'DA_PHE_DUYET'
            AND is_deleted = FALSE
            AND (so_sp_chat_luong IS NULL OR so_sp_tien_do IS NULL)
    """)
    
    result = await session.execute(query)
    row = result.fetchone()
    return row[0] if row else 0


async def get_summary_by_month(session: AsyncSession) -> list:
    """Thống kê dữ liệu theo tháng sau khi update."""
    query = text("""
        SELECT 
            thang,
            nam,
            COUNT(*) as so_ke_khai,
            COALESCE(SUM(so_sp_goc_quy_doi), 0) as tong_sp_goc,
            COALESCE(SUM(so_sp_chat_luong), 0) as tong_sp_chat_luong,
            COALESCE(SUM(so_sp_tien_do), 0) as tong_sp_tien_do,
            COALESCE(SUM(so_loi_chat_luong), 0) as tong_loi_cl,
            COALESCE(SUM(so_loi_tien_do), 0) as tong_loi_td
        FROM ke_khai_cong_viec
        WHERE 
            trang_thai = 'DA_PHE_DUYET'
            AND is_deleted = FALSE
        GROUP BY thang, nam
        ORDER BY nam DESC, thang DESC
    """)
    
    result = await session.execute(query)
    return result.fetchall()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def run_migration(dry_run: bool = False):
    """
    Chạy migration.
    
    Args:
        dry_run: True = chỉ preview, không thực sự update
    """
    print_header("MIGRATION: Fix SP Chất lượng & Tiến độ")
    print_info(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Chế độ: {'DRY-RUN (chỉ xem preview)' if dry_run else 'THỰC THI'}")
    
    session = await get_async_session()
    
    try:
        # Bước 1: Đếm số bản ghi cần update
        print(f"\n{Colors.BOLD}[BƯỚC 1] Kiểm tra số bản ghi cần update...{Colors.ENDC}")
        total_to_update = await count_records_to_update(session)
        
        if total_to_update == 0:
            print_success("Không có bản ghi nào cần update!")
            print_info("Dữ liệu đã đầy đủ so_sp_chat_luong và so_sp_tien_do.")
            return
        
        print_warning(f"Tìm thấy {total_to_update} bản ghi cần update")
        
        # Bước 2: Preview dữ liệu
        print(f"\n{Colors.BOLD}[BƯỚC 2] Preview dữ liệu (tối đa 10 bản ghi)...{Colors.ENDC}")
        preview = await preview_records(session, limit=10)
        
        print(f"\n{'ID':<40} {'Tháng':<6} {'SP Gốc':<10} {'Lỗi CL':<8} {'Lỗi TĐ':<8} {'SP CL (sau)':<12} {'SP TĐ (sau)':<12}")
        print("-" * 120)
        
        for row in preview:
            print(f"{str(row[0]):<40} {row[1]}/{row[2]:<4} {float(row[3] or 0):<10.2f} {row[4] or 0:<8} {row[5] or 0:<8} {float(row[8]):<12.2f} {float(row[9]):<12.2f}")
        
        if dry_run:
            print_warning("\n[DRY-RUN] Không thực hiện update. Chạy lại không có --dry-run để update thật.")
            return
        
        # Bước 3: Xác nhận
        print(f"\n{Colors.BOLD}[BƯỚC 3] Xác nhận...{Colors.ENDC}")
        confirm = input(f"{Colors.WARNING}Bạn có chắc muốn update {total_to_update} bản ghi? (yes/no): {Colors.ENDC}")
        
        if confirm.lower() not in ['yes', 'y']:
            print_warning("Đã hủy migration.")
            return
        
        # Bước 4: Thực hiện update
        print(f"\n{Colors.BOLD}[BƯỚC 4] Thực hiện UPDATE...{Colors.ENDC}")
        updated_count = await execute_update(session)
        print_success(f"Đã update {updated_count} bản ghi")
        
        # Bước 5: Verify
        print(f"\n{Colors.BOLD}[BƯỚC 5] Kiểm tra kết quả...{Colors.ENDC}")
        remaining = await verify_no_nulls(session)
        
        if remaining == 0:
            print_success("Không còn bản ghi NULL nào!")
        else:
            print_error(f"Vẫn còn {remaining} bản ghi NULL - cần kiểm tra lại!")
            await session.rollback()
            return
        
        # Bước 6: Commit
        print(f"\n{Colors.BOLD}[BƯỚC 6] Commit transaction...{Colors.ENDC}")
        await session.commit()
        print_success("Đã commit thành công!")
        
        # Bước 7: Thống kê sau migration
        print(f"\n{Colors.BOLD}[BƯỚC 7] Thống kê sau migration...{Colors.ENDC}")
        summary = await get_summary_by_month(session)
        
        print(f"\n{'Tháng':<10} {'Số KK':<10} {'SP Gốc':<15} {'SP CL':<15} {'SP TĐ':<15} {'Lỗi CL':<10} {'Lỗi TĐ':<10}")
        print("-" * 90)
        
        for row in summary:
            print(f"{row[0]}/{row[1]:<8} {row[2]:<10} {float(row[3]):<15.2f} {float(row[4]):<15.2f} {float(row[5]):<15.2f} {int(row[6]):<10} {int(row[7]):<10}")
        
        print_header("MIGRATION HOÀN THÀNH")
        
    except Exception as e:
        print_error(f"Lỗi: {str(e)}")
        await session.rollback()
        raise
    finally:
        await session.close()


def main():
    """Entry point."""
    # Parse arguments
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        sys.exit(0)
    
    # Run migration
    asyncio.run(run_migration(dry_run=dry_run))


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
scripts/clear_data_nhap_vao.py
==============================
Script xóa sạch dữ liệu nhập vào để test clean.

CẢNH BÁO: Script này sẽ XÓA dữ liệu!
         Tuy nhiên, dữ liệu sẽ được BACKUP trước khi xóa.

DỮ LIỆU SẼ BỊ XÓA (có backup):
- ke_khai_cong_viec: Tất cả kê khai công việc
- danh_gia_thang: Tất cả đánh giá tháng
- tieu_chi_chung_danh_gia: Tất cả kết quả chấm tiêu chí
- nghi_phep: Tất cả đơn nghỉ phép

DỮ LIỆU ĐƯỢC GIỮ LẠI (Master Data):
- cong_chuc: 548 công chức đã seed
- don_vi: Cơ cấu tổ chức
- vai_tro: Phân quyền
- danh_muc_san_pham: Danh mục sản phẩm
- cap_do: Cấp độ công việc
- sp_chuan: SP chuẩn
- tieu_chi_chung: 31 tiêu chí master
- audit_log: Log hệ thống (được giữ)

BACKUP:
- Tự động tạo file backup JSON trước khi xóa
- Lưu tại: scripts/backups/backup_YYYYMMDD_HHMMSS/
- Có thể restore lại nếu cần

CÁCH DÙNG:
    # Xem preview (không thực sự xóa)
    python scripts/clear_data_nhap_vao.py --dry-run
    
    # Chạy thật (TỰ ĐỘNG BACKUP + YÊU CẦU CONFIRM)
    python scripts/clear_data_nhap_vao.py
    
    # Chạy không backup (không khuyến nghị)
    python scripts/clear_data_nhap_vao.py --no-backup

LƯU Ý:
- Chạy script này CHỈ khi muốn reset toàn bộ dữ liệu test
- Backup được tạo tự động, có thể restore lại
- Script chạy trong transaction, có rollback nếu lỗi
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID
from decimal import Decimal

# Thêm path để import được app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings


# =============================================================================
# BACKUP CONFIGURATION
# =============================================================================

BACKUP_DIR = Path(__file__).parent / "backups"


# =============================================================================
# CONFIGURATION
# =============================================================================

# Danh sách bảng sẽ XÓA DỮ LIỆU (theo thứ tự FK dependency)
TABLES_TO_CLEAR = [
    # Xóa con trước
    "tieu_chi_chung_danh_gia",  # FK -> danh_gia_thang, tieu_chi_chung
    "ke_khai_cong_viec",         # FK -> cong_chuc, danh_muc_sp
    "danh_gia_thang",            # FK -> cong_chuc
    "nghi_phep",                 # FK -> cong_chuc
]

# Danh sách bảng GIỮ NGUYÊN (Master Data)
TABLES_TO_KEEP = [
    "cong_chuc",
    "don_vi", 
    "vai_tro",
    "danh_muc_san_pham",
    "cap_do",
    "sp_chuan",
    "tieu_chi_chung",
    "audit_log",
    "alembic_version",
]


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


def print_danger(text: str):
    print(f"{Colors.FAIL}{Colors.BOLD}🚨 {text}{Colors.ENDC}")


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
# JSON ENCODER FOR SPECIAL TYPES
# =============================================================================

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder để xử lý UUID, Decimal, datetime, etc."""
    
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


# =============================================================================
# BACKUP FUNCTIONS
# =============================================================================

async def backup_table(session: AsyncSession, table_name: str, backup_dir: Path) -> int:
    """
    Backup toàn bộ dữ liệu của một bảng ra file JSON.
    
    Args:
        session: Database session
        table_name: Tên bảng cần backup
        backup_dir: Thư mục lưu backup
        
    Returns:
        Số bản ghi đã backup
    """
    try:
        # Lấy tất cả dữ liệu từ bảng
        query = text(f"SELECT * FROM {table_name}")
        result = await session.execute(query)
        
        # Lấy tên cột
        columns = result.keys()
        
        # Chuyển thành list of dict
        rows = []
        for row in result.fetchall():
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Chuyển đổi các kiểu đặc biệt
                if isinstance(value, UUID):
                    value = str(value)
                elif isinstance(value, Decimal):
                    value = float(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()
                elif hasattr(value, 'value'):  # Enum
                    value = value.value
                row_dict[col] = value
            rows.append(row_dict)
        
        # Lưu ra file JSON
        backup_file = backup_dir / f"{table_name}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({
                "table": table_name,
                "backup_time": datetime.now().isoformat(),
                "record_count": len(rows),
                "columns": list(columns),
                "data": rows
            }, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
        
        return len(rows)
        
    except Exception as e:
        print_error(f"Lỗi backup bảng {table_name}: {str(e)}")
        raise


async def create_backup(session: AsyncSession, tables: list, skip_backup: bool = False) -> tuple[Path, dict]:
    """
    Tạo backup cho tất cả các bảng.
    
    Args:
        session: Database session
        tables: Danh sách bảng cần backup
        skip_backup: True = bỏ qua backup
        
    Returns:
        Tuple (backup_dir, backup_summary)
    """
    if skip_backup:
        return None, {}
    
    # Tạo thư mục backup với timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUP_DIR / f"backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backup_summary = {}
    
    print(f"\n{Colors.BOLD}📦 Đang tạo backup...{Colors.ENDC}")
    print(f"   Thư mục: {backup_dir}")
    
    for table in tables:
        try:
            # Kiểm tra bảng có tồn tại không
            exists_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                )
            """)
            result = await session.execute(exists_query, {"table_name": table})
            exists = result.fetchone()[0]
            
            if not exists:
                print_info(f"   Bỏ qua {table} (không tồn tại)")
                continue
            
            # Đếm số bản ghi
            count_query = text(f"SELECT COUNT(*) FROM {table}")
            count_result = await session.execute(count_query)
            count = count_result.fetchone()[0]
            
            if count == 0:
                print_info(f"   Bỏ qua {table} (không có dữ liệu)")
                backup_summary[table] = 0
                continue
            
            # Backup
            backed_up = await backup_table(session, table, backup_dir)
            backup_summary[table] = backed_up
            print_success(f"   Đã backup {backed_up} bản ghi từ {table}")
            
        except Exception as e:
            print_error(f"   Lỗi backup {table}: {str(e)}")
            raise
    
    # Tạo file metadata
    metadata = {
        "backup_time": datetime.now().isoformat(),
        "tables": backup_summary,
        "total_records": sum(backup_summary.values()),
    }
    
    metadata_file = backup_dir / "_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return backup_dir, backup_summary


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def check_table_exists(session: AsyncSession, table_name: str) -> bool:
    """Kiểm tra bảng có tồn tại không."""
    query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        )
    """)
    result = await session.execute(query, {"table_name": table_name})
    row = result.fetchone()
    return row[0] if row else False


async def count_records(session: AsyncSession, table_name: str) -> int:
    """Đếm số bản ghi trong bảng."""
    try:
        query = text(f"SELECT COUNT(*) FROM {table_name}")
        result = await session.execute(query)
        row = result.fetchone()
        return row[0] if row else 0
    except Exception:
        return -1  # Bảng không tồn tại hoặc lỗi


async def delete_all_from_table(session: AsyncSession, table_name: str) -> int:
    """Xóa tất cả dữ liệu trong bảng."""
    query = text(f"DELETE FROM {table_name}")
    result = await session.execute(query)
    return result.rowcount


async def get_table_summary(session: AsyncSession) -> dict:
    """Lấy tổng quan số bản ghi trong các bảng."""
    summary = {}
    
    all_tables = TABLES_TO_CLEAR + TABLES_TO_KEEP
    
    for table in all_tables:
        exists = await check_table_exists(session, table)
        if exists:
            count = await count_records(session, table)
            summary[table] = {"exists": True, "count": count}
        else:
            summary[table] = {"exists": False, "count": 0}
    
    return summary


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def run_clear_data(dry_run: bool = False, skip_backup: bool = False):
    """
    Chạy xóa dữ liệu.
    
    Args:
        dry_run: True = chỉ preview, không thực sự xóa
        skip_backup: True = không tạo backup (không khuyến nghị)
    """
    print_header("CLEAR DATA - Xóa dữ liệu nhập vào")
    print_info(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Chế độ: {'DRY-RUN (chỉ xem preview)' if dry_run else 'THỰC THI'}")
    print_info(f"Backup: {'TẮT (không khuyến nghị)' if skip_backup else 'BẬT'}")
    
    # Cảnh báo
    if not skip_backup:
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Dữ liệu sẽ được BACKUP trước khi xóa{Colors.ENDC}")
        print(f"{Colors.GREEN}{Colors.BOLD}   Bạn có thể restore lại nếu cần{Colors.ENDC}")
        print(f"{Colors.GREEN}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    else:
        print_danger("\n" + "="*60)
        print_danger("CẢNH BÁO: BACKUP ĐÃ TẮT!")
        print_danger("         Dữ liệu sẽ KHÔNG THỂ khôi phục!")
        print_danger("="*60 + "\n")
    
    session = await get_async_session()
    
    try:
        # Bước 1: Lấy tổng quan dữ liệu hiện tại
        print(f"\n{Colors.BOLD}[BƯỚC 1] Tổng quan dữ liệu hiện tại...{Colors.ENDC}")
        summary = await get_table_summary(session)
        
        # Hiển thị bảng sẽ XÓA
        print(f"\n{Colors.FAIL}{Colors.BOLD}📋 BẢNG SẼ BỊ XÓA DỮ LIỆU:{Colors.ENDC}")
        print(f"{'Tên bảng':<35} {'Số bản ghi':<15} {'Trạng thái':<15}")
        print("-" * 65)
        
        total_to_delete = 0
        for table in TABLES_TO_CLEAR:
            info = summary.get(table, {"exists": False, "count": 0})
            status = "✓ Tồn tại" if info["exists"] else "✗ Không có"
            count = info["count"] if info["count"] >= 0 else "N/A"
            print(f"{table:<35} {count:<15} {status:<15}")
            if info["count"] > 0:
                total_to_delete += info["count"]
        
        print(f"\n{Colors.BOLD}Tổng số bản ghi sẽ xóa: {total_to_delete}{Colors.ENDC}")
        
        # Hiển thị bảng sẽ GIỮ
        print(f"\n{Colors.GREEN}{Colors.BOLD}📋 BẢNG SẼ ĐƯỢC GIỮ NGUYÊN:{Colors.ENDC}")
        print(f"{'Tên bảng':<35} {'Số bản ghi':<15} {'Trạng thái':<15}")
        print("-" * 65)
        
        for table in TABLES_TO_KEEP:
            info = summary.get(table, {"exists": False, "count": 0})
            status = "✓ Tồn tại" if info["exists"] else "✗ Không có"
            count = info["count"] if info["count"] >= 0 else "N/A"
            print(f"{table:<35} {count:<15} {status:<15}")
        
        if total_to_delete == 0:
            print_success("\nKhông có dữ liệu để xóa. Database đã clean!")
            return
        
        if dry_run:
            print_warning("\n[DRY-RUN] Không thực hiện xóa. Chạy lại không có --dry-run để xóa thật.")
            return
        
        # Bước 2: Tạo BACKUP
        print(f"\n{Colors.BOLD}[BƯỚC 2] Tạo backup...{Colors.ENDC}")
        backup_dir, backup_summary = await create_backup(session, TABLES_TO_CLEAR, skip_backup)
        
        if backup_dir:
            total_backed_up = sum(backup_summary.values())
            print_success(f"Đã backup {total_backed_up} bản ghi vào {backup_dir}")
        
        # Bước 3: Xác nhận
        print(f"\n{Colors.BOLD}[BƯỚC 3] Xác nhận...{Colors.ENDC}")
        
        if backup_dir:
            print_info(f"Backup đã được tạo tại: {backup_dir}")
        
        confirm = input(f"{Colors.WARNING}Bạn có chắc muốn xóa {total_to_delete} bản ghi? (yes/no): {Colors.ENDC}")
        
        if confirm.lower() not in ['yes', 'y']:
            print_warning("Đã hủy.")
            return
        
        # Bước 4: Thực hiện xóa
        print(f"\n{Colors.BOLD}[BƯỚC 4] Thực hiện XÓA DỮ LIỆU...{Colors.ENDC}")
        
        deleted_counts = {}
        for table in TABLES_TO_CLEAR:
            info = summary.get(table, {"exists": False, "count": 0})
            if not info["exists"]:
                print_info(f"  Bỏ qua {table} (không tồn tại)")
                continue
            
            if info["count"] == 0:
                print_info(f"  Bỏ qua {table} (đã trống)")
                continue
            
            try:
                deleted = await delete_all_from_table(session, table)
                deleted_counts[table] = deleted
                print_success(f"  Đã xóa {deleted} bản ghi từ {table}")
            except Exception as e:
                print_error(f"  Lỗi khi xóa {table}: {str(e)}")
                raise
        
        # Bước 5: Verify
        print(f"\n{Colors.BOLD}[BƯỚC 5] Kiểm tra kết quả...{Colors.ENDC}")
        
        all_empty = True
        for table in TABLES_TO_CLEAR:
            exists = await check_table_exists(session, table)
            if exists:
                count = await count_records(session, table)
                if count > 0:
                    print_error(f"  {table}: Vẫn còn {count} bản ghi!")
                    all_empty = False
                else:
                    print_success(f"  {table}: Đã xóa sạch")
        
        if not all_empty:
            print_error("Có lỗi! Rollback...")
            await session.rollback()
            return
        
        # Bước 6: Commit
        print(f"\n{Colors.BOLD}[BƯỚC 6] Commit transaction...{Colors.ENDC}")
        await session.commit()
        print_success("Đã commit thành công!")
        
        # Bước 7: Tổng kết
        print_header("XÓA DỮ LIỆU HOÀN THÀNH")
        
        total_deleted = sum(deleted_counts.values())
        print(f"\n📊 Tổng kết:")
        print(f"   - Tổng số bản ghi đã xóa: {total_deleted}")
        print(f"   - Số bảng đã xử lý: {len(deleted_counts)}")
        
        if backup_dir:
            print(f"   - Backup lưu tại: {backup_dir}")
            print(f"\n💡 Để restore, sử dụng file JSON trong thư mục backup.")
        
        print(f"\n✅ Database đã sẵn sàng cho clean test!")
        
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
    skip_backup = '--no-backup' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        sys.exit(0)
    
    # Run
    asyncio.run(run_clear_data(dry_run=dry_run, skip_backup=skip_backup))


if __name__ == "__main__":
    main()
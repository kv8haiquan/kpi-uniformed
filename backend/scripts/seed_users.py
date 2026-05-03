#!/usr/bin/env python3
"""
scripts/seed_users.py
=====================
Script import danh sách công chức từ file Excel vào database.

Chạy:
    python scripts/seed_users.py

Yêu cầu:
    - Database đã được migrate (alembic upgrade head)
    - File data/danh_sach_cong_chuc.xlsx tồn tại
    - Các vai trò đã được seed (trong migration)

Quy trình:
    1. Đọc file Excel, bỏ qua dòng đánh số (dòng 2)
    2. Tạo các đơn vị từ cột "ĐƠN VỊ"
    3. Import công chức với mapping vai trò và đơn vị
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import re

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# =============================================================================
# SETUP PATH - Thêm project root vào sys.path
# =============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import sau khi thêm path
from app.config import settings
from app.models import DonVi, VaiTro, CongChuc, LoaiDonVi, CapBacVaiTro
from app.core.security import hash_password, DEFAULT_PASSWORD


# =============================================================================
# CONSTANTS
# =============================================================================

# Đường dẫn file Excel
EXCEL_FILE = PROJECT_ROOT / "data" / "danh_sach_cong_chuc.xlsx"

# Mapping chức vụ trong Excel -> mã vai trò trong DB
# Key: tên chức vụ (lowercase, stripped)
# Value: mã vai trò
CHUC_VU_TO_VAI_TRO = {
    # Cấp 1 - Chi cục trưởng
    "chi cục trưởng": "CCT",
    
    # Cấp 2 - Phó Chi cục trưởng
    "phó chi cục trưởng": "PCCT",
    
    # Cấp 3 - Trưởng đơn vị (Trưởng phòng, Đội trưởng, Chánh VP)
    "chánh văn phòng": "TDV",
    "trưởng phòng": "TDV",
    "đội trưởng": "TDV",
    
    # Cấp 4 - Phó đơn vị
    "phó văn phòng": "TDV",  # Phó VP coi như Trưởng ĐV (theo cơ cấu)
    "phó trưởng phòng": "PDV",
    "phó đội trưởng": "PDV",
    
    # Cấp 5 - Công chức
    "công chức": "CC",
    # HĐ 111 dùng vai trò riêng (29/04/2026): form lãnh đạo, không d/đ/e
    "hợp đồng 111": "HD_111",
}

# Mapping tên đơn vị -> loại đơn vị
DON_VI_LOAI_MAP = {
    "lãnh đạo chi cục": LoaiDonVi.LANH_DAO_CHI_CUC,
    "văn phòng": LoaiDonVi.PHONG,
    "phòng tổ chức cán bộ": LoaiDonVi.PHONG,
    "phòng nghiệp vụ hải quan": LoaiDonVi.PHONG,
    "phòng quản lý rủi ro": LoaiDonVi.PHONG,
    "phòng công nghệ thông tin": LoaiDonVi.PHONG,
    "đội phúc tập và kiểm tra sau thông quan": LoaiDonVi.DOI,
    "đội kiểm soát hải quan": LoaiDonVi.DOI,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_string(s: str) -> str:
    """Chuẩn hóa string: strip, lowercase, loại bỏ khoảng trắng thừa."""
    if pd.isna(s):
        return ""
    return " ".join(str(s).strip().split()).lower()


def get_vai_tro_code(chuc_vu: str) -> str:
    """
    Map chức vụ sang mã vai trò.
    
    Args:
        chuc_vu: Tên chức vụ từ Excel
        
    Returns:
        str: Mã vai trò (CCT, PCCT, TDV, PDV, CC)
    """
    normalized = normalize_string(chuc_vu)
    
    # Tìm trong mapping
    if normalized in CHUC_VU_TO_VAI_TRO:
        return CHUC_VU_TO_VAI_TRO[normalized]
    
    # Kiểm tra pattern đặc biệt
    if "trưởng" in normalized and "phó" not in normalized:
        return "TDV"  # Trưởng đơn vị
    if "phó" in normalized:
        return "PDV"  # Phó đơn vị
    
    # Mặc định là công chức
    return "CC"


def get_loai_don_vi(ten_don_vi: str) -> LoaiDonVi:
    """
    Xác định loại đơn vị từ tên.
    
    Args:
        ten_don_vi: Tên đơn vị từ Excel
        
    Returns:
        LoaiDonVi: Loại đơn vị (PHONG, DOI, HAI_QUAN_CUA_KHAU, ...)
    """
    normalized = normalize_string(ten_don_vi)
    
    # Tìm trong mapping
    if normalized in DON_VI_LOAI_MAP:
        return DON_VI_LOAI_MAP[normalized]
    
    # Pattern matching
    if "hqck" in normalized or "cửa khẩu" in normalized or "cảng" in normalized:
        return LoaiDonVi.HAI_QUAN_CUA_KHAU
    if "phòng" in normalized:
        return LoaiDonVi.PHONG
    if "đội" in normalized:
        return LoaiDonVi.DOI
    
    # Mặc định
    return LoaiDonVi.PHONG


def generate_ma_don_vi(ten_don_vi: str, index: int) -> str:
    """
    Tạo mã đơn vị từ tên.
    
    Args:
        ten_don_vi: Tên đơn vị
        index: Số thứ tự
        
    Returns:
        str: Mã đơn vị (VD: DV01, HQCK01)
    """
    normalized = normalize_string(ten_don_vi)
    
    if "lãnh đạo" in normalized:
        return "LDCC"
    if "văn phòng" in normalized and "phòng" not in normalized.replace("văn phòng", ""):
        return "VP"
    if "tổ chức cán bộ" in normalized:
        return "TCCB"
    if "nghiệp vụ" in normalized:
        return "NVHQ"
    if "rủi ro" in normalized:
        return "QLRR"
    if "công nghệ" in normalized:
        return "CNTT"
    if "phúc tập" in normalized:
        return "PTSTQ"
    if "kiểm soát" in normalized:
        return "KSHQ"
    if "hòn gai" in normalized:
        return "HQCK-HG"
    if "cẩm phả" in normalized:
        return "HQCK-CP"
    if "móng cái" in normalized:
        return "HQCK-MC"
    if "hoành mô" in normalized:
        return "HQCK-HM"
    if "bắc phong sinh" in normalized:
        return "HQCK-BPS"
    if "vạn gia" in normalized:
        return "HQCK-VG"
    
    # Default
    return f"DV{index:02d}"


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse ngày sinh từ nhiều format khác nhau.
    
    Args:
        date_str: Chuỗi ngày (VD: "29/10/1973", "1973-10-29")
        
    Returns:
        datetime hoặc None nếu không parse được
    """
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    # Các format có thể có
    formats = [
        "%d/%m/%Y",    # 29/10/1973
        "%d-%m-%Y",    # 29-10-1973
        "%Y-%m-%d",    # 1973-10-29
        "%d/%m/%y",    # 29/10/73
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def is_lanh_dao(vai_tro_code: str) -> bool:
    """Kiểm tra vai trò có phải lãnh đạo không."""
    return vai_tro_code in ["CCT", "PCCT", "TDV", "PDV"]


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

async def get_or_create_vai_tro_map(session: AsyncSession) -> dict[str, str]:
    """
    Lấy mapping mã vai trò -> UUID từ database.
    
    Returns:
        dict: {"CCT": "uuid-1", "PCCT": "uuid-2", ...}
    """
    result = await session.execute(select(VaiTro))
    vai_tros = result.scalars().all()
    
    return {vt.ma_vai_tro: str(vt.id) for vt in vai_tros}


async def create_don_vi_from_excel(
    session: AsyncSession,
    df: pd.DataFrame
) -> dict[str, str]:
    """
    Tạo các đơn vị từ cột ĐƠN VỊ trong Excel.
    
    Args:
        session: Database session
        df: DataFrame chứa dữ liệu
        
    Returns:
        dict: Mapping tên đơn vị -> UUID
    """
    print("\n" + "=" * 60)
    print("BƯỚC 1: TẠO ĐƠN VỊ")
    print("=" * 60)
    
    # Lấy danh sách đơn vị unique
    don_vi_list = df["ĐƠN VỊ"].dropna().unique()
    print(f"Tìm thấy {len(don_vi_list)} đơn vị trong Excel")
    
    # Kiểm tra đơn vị đã tồn tại
    existing_result = await session.execute(select(DonVi))
    existing_don_vi = {dv.ten_don_vi.strip().lower(): str(dv.id) for dv in existing_result.scalars().all()}
    
    don_vi_map = {}
    created_count = 0
    
    for idx, ten_don_vi in enumerate(don_vi_list, 1):
        ten_clean = str(ten_don_vi).strip()
        ten_lower = ten_clean.lower()
        
        # Kiểm tra đã tồn tại chưa
        if ten_lower in existing_don_vi:
            don_vi_map[ten_clean] = existing_don_vi[ten_lower]
            print(f"  [SKIP] {ten_clean} - đã tồn tại")
            continue
        
        # Tạo mới
        ma_don_vi = generate_ma_don_vi(ten_don_vi, idx)
        loai_don_vi = get_loai_don_vi(ten_don_vi)
        
        new_don_vi = DonVi(
            ma_don_vi=ma_don_vi,
            ten_don_vi=ten_clean,
            loai_don_vi=loai_don_vi,
            thu_tu_hien_thi=idx,
            is_active=True,
        )
        
        session.add(new_don_vi)
        
        try:
            await session.flush()  # Để lấy ID
            don_vi_map[ten_clean] = str(new_don_vi.id)
            print(f"  [CREATE] {ten_clean} ({ma_don_vi}) - {loai_don_vi.value}")
            created_count += 1
        except Exception as e:
            print(f"  [ERROR] {ten_clean}: {e}")
            await session.rollback()
    
    await session.commit()
    print(f"\n✅ Đã tạo {created_count} đơn vị mới")
    
    # Cập nhật lại map với tất cả đơn vị
    final_result = await session.execute(select(DonVi))
    return {dv.ten_don_vi.strip(): str(dv.id) for dv in final_result.scalars().all()}


async def import_cong_chuc(
    session: AsyncSession,
    df: pd.DataFrame,
    vai_tro_map: dict[str, str],
    don_vi_map: dict[str, str],
) -> tuple[int, int]:
    """
    Import danh sách công chức từ DataFrame.
    
    Args:
        session: Database session
        df: DataFrame chứa dữ liệu
        vai_tro_map: Mapping mã vai trò -> UUID
        don_vi_map: Mapping tên đơn vị -> UUID
        
    Returns:
        tuple: (số thành công, số thất bại)
    """
    print("\n" + "=" * 60)
    print("BƯỚC 2: IMPORT CÔNG CHỨC")
    print("=" * 60)
    
    total = len(df)
    success_count = 0
    fail_count = 0
    errors = []
    
    # Hash password mặc định một lần
    default_password_hash = hash_password(DEFAULT_PASSWORD)
    
    # Lấy danh sách mã CC đã tồn tại
    existing_result = await session.execute(
        select(CongChuc.ma_cc)
    )
    existing_ma_cc = {row[0] for row in existing_result.fetchall()}
    print(f"Đã có {len(existing_ma_cc)} công chức trong database")
    
    # Batch size cho commit
    BATCH_SIZE = 50
    batch_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Lấy dữ liệu từ row
            ma_cc = str(row["MÃ CC"]).strip()
            ho_ten = str(row["HỌ VÀ TÊN"]).strip()
            chuc_vu = str(row["CHỨC VỤ"]).strip() if pd.notna(row["CHỨC VỤ"]) else ""
            don_vi_name = str(row["ĐƠN VỊ"]).strip() if pd.notna(row["ĐƠN VỊ"]) else ""
            nam_sinh_str = row.get("NĂM SINH", "")
            
            # Validate dữ liệu bắt buộc
            if not ma_cc or not ho_ten:
                raise ValueError(f"Thiếu mã CC hoặc họ tên")
            
            # Skip nếu đã tồn tại
            if ma_cc in existing_ma_cc:
                print(f"  [{idx + 1}/{total}] SKIP: {ma_cc} - {ho_ten} (đã tồn tại)")
                success_count += 1  # Coi như thành công vì đã có
                continue
            
            # Parse ngày sinh
            ngay_sinh = parse_date(nam_sinh_str)
            
            # Map vai trò
            vai_tro_code = get_vai_tro_code(chuc_vu)
            vai_tro_id = vai_tro_map.get(vai_tro_code)
            
            if not vai_tro_id:
                raise ValueError(f"Không tìm thấy vai trò: {vai_tro_code}")
            
            # Map đơn vị
            don_vi_id = None
            for key in don_vi_map:
                if key.strip().lower() == don_vi_name.strip().lower():
                    don_vi_id = don_vi_map[key]
                    break
            
            if not don_vi_id:
                raise ValueError(f"Không tìm thấy đơn vị: {don_vi_name}")
            
            # Tạo công chức mới
            new_cc = CongChuc(
                ma_cc=ma_cc,
                ho_ten=ho_ten,
                ngay_sinh=ngay_sinh.date() if ngay_sinh else None,
                chuc_vu=chuc_vu if chuc_vu else None,
                don_vi_id=don_vi_id,
                vai_tro_id=vai_tro_id,
                is_lanh_dao=is_lanh_dao(vai_tro_code),
                username=ma_cc,  # Username = Mã CC
                password_hash=default_password_hash,
                is_active=True,
            )
            
            session.add(new_cc)
            batch_count += 1
            
            # Commit theo batch
            if batch_count >= BATCH_SIZE:
                await session.commit()
                batch_count = 0
            
            success_count += 1
            
            # Progress
            if (idx + 1) % 50 == 0 or (idx + 1) == total:
                print(f"  Processing {idx + 1}/{total}... (✓ {success_count}, ✗ {fail_count})")
                
        except Exception as e:
            fail_count += 1
            error_msg = f"Row {idx + 1} ({row.get('MÃ CC', 'N/A')}): {str(e)}"
            errors.append(error_msg)
            
            # Rollback row lỗi
            await session.rollback()
    
    # Commit batch cuối
    if batch_count > 0:
        await session.commit()
    
    # In lỗi nếu có
    if errors:
        print("\n⚠️ DANH SÁCH LỖI:")
        for err in errors[:10]:  # Chỉ hiện 10 lỗi đầu
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... và {len(errors) - 10} lỗi khác")
    
    return success_count, fail_count


# =============================================================================
# MAIN FUNCTION
# =============================================================================

async def main():
    """Entry point chính của script."""
    
    print("=" * 60)
    print("SCRIPT IMPORT CÔNG CHỨC - HẢI QUAN KV8")
    print("=" * 60)
    print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    
    # Kiểm tra file Excel
    if not EXCEL_FILE.exists():
        print(f"\n❌ ERROR: Không tìm thấy file {EXCEL_FILE}")
        print("Hãy đảm bảo file danh_sach_cong_chuc.xlsx nằm trong thư mục data/")
        return
    
    # Đọc file Excel
    print(f"\n📖 Đọc file: {EXCEL_FILE.name}")
    
    try:
        # Đọc với header ở dòng 1 (index 0), skip dòng 2 (index 1)
        df = pd.read_excel(
            EXCEL_FILE,
            header=0,        # Header ở dòng đầu tiên
            skiprows=[1],    # Bỏ qua dòng thứ 2 (đánh số cột)
        )
        
        # Clean column names
        df.columns = [col.strip() for col in df.columns]
        
        print(f"✅ Đọc thành công: {len(df)} dòng dữ liệu")
        print(f"   Các cột: {list(df.columns)}")
        
    except Exception as e:
        print(f"❌ ERROR khi đọc file Excel: {e}")
        return
    
    # Tạo async engine và session
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Lấy mapping vai trò
            vai_tro_map = await get_or_create_vai_tro_map(session)
            print(f"\n📋 Vai trò trong DB: {list(vai_tro_map.keys())}")
            
            if not vai_tro_map:
                print("❌ ERROR: Không có vai trò trong database!")
                print("Hãy chạy migration trước: alembic upgrade head")
                return
            
            # Tạo đơn vị
            don_vi_map = await create_don_vi_from_excel(session, df)
            
            # Import công chức
            success, fail = await import_cong_chuc(
                session, df, vai_tro_map, don_vi_map
            )
            
            # Kết quả cuối cùng
            print("\n" + "=" * 60)
            print("KẾT QUẢ IMPORT")
            print("=" * 60)
            print(f"✅ Thành công: {success}")
            print(f"❌ Thất bại: {fail}")
            print(f"📊 Tổng cộng: {success + fail}")
            
            # Thống kê trong DB
            total_cc = await session.execute(
                select(func.count()).select_from(CongChuc)
            )
            total_dv = await session.execute(
                select(func.count()).select_from(DonVi)
            )
            
            print(f"\n📈 Thống kê Database:")
            print(f"   - Tổng công chức: {total_cc.scalar()}")
            print(f"   - Tổng đơn vị: {total_dv.scalar()}")
            
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

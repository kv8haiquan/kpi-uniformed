#!/usr/bin/env python3
"""
scripts/seed_admin.py
=====================
Script tạo tài khoản Super Admin cho hệ thống.

Chạy:
    python scripts/seed_admin.py

Tạo các dữ liệu:
1. Đơn vị Admin: DEPT-ADMIN (Phòng Quản trị Hệ thống)
2. Vai trò Admin: ADMIN (Quản trị hệ thống, cấp SUPER_ADMIN)
3. User Admin: ADMIN-001 (admin/123456)

⚠️ LƯU Ý:
- Script này IDEMPOTENT: chạy nhiều lần không gây lỗi
- Admin KHÔNG tham gia quy trình nghiệp vụ (không phê duyệt, không chấm điểm)
- Admin chỉ quản lý User, Danh mục, xem dữ liệu
"""

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime

# =============================================================================
# SETUP PATH - Thêm project root vào sys.path
# =============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import sau khi thêm path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models import DonVi, VaiTro, CongChuc, LoaiDonVi, CapBacVaiTro
from app.core.security import hash_password, DEFAULT_PASSWORD


# =============================================================================
# CONSTANTS - Dữ liệu Admin cố định
# =============================================================================

# UUID cố định để dễ quản lý và tham chiếu
ADMIN_DON_VI_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")
ADMIN_VAI_TRO_ID = uuid.UUID("a0000000-0000-0000-0000-000000000003")  # Khác với vai trò khác
ADMIN_USER_ID = uuid.UUID("a0000000-0000-0000-0000-000000000002")

# Thông tin Đơn vị Admin
ADMIN_DON_VI = {
    "id": ADMIN_DON_VI_ID,
    "ma_don_vi": "DEPT-ADMIN",
    "ten_don_vi": "Phòng Quản trị Hệ thống",
    "ten_viet_tat": "Admin",
    "loai_don_vi": LoaiDonVi.PHONG,
    "thu_tu_hien_thi": 0,  # Hiển thị đầu tiên
    "is_active": True,
}

# Thông tin Vai trò Admin
ADMIN_VAI_TRO = {
    "id": ADMIN_VAI_TRO_ID,
    "ma_vai_tro": "ADMIN",
    "ten_vai_tro": "Quản trị hệ thống",
    "cap_bac": CapBacVaiTro.SUPER_ADMIN,
    "mo_ta": "Quản trị viên hệ thống - Không tham gia quy trình nghiệp vụ",
    "is_lanh_dao": False,
    "is_system_admin": True,
    "is_active": True,
}

# Thông tin User Admin
ADMIN_USER = {
    "id": ADMIN_USER_ID,
    "ma_cc": "ADMIN-001",
    "ho_ten": "Quản trị viên",
    "email": "admin@chicuchaiuan.gov.vn",
    "chuc_vu": "Quản trị viên hệ thống",
    "is_lanh_dao": True,  # TRUE để truy cập menu (theo yêu cầu)
    "is_active": True,
    "username": "admin",
}


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

async def create_admin_don_vi(session: AsyncSession) -> DonVi:
    """
    Tạo hoặc lấy Đơn vị Admin (DEPT-ADMIN).
    
    Returns:
        DonVi: Đơn vị Admin
    """
    print("\n" + "=" * 50)
    print("BƯỚC 1: TẠO ĐƠN VỊ ADMIN")
    print("=" * 50)
    
    # Kiểm tra đã tồn tại chưa
    result = await session.execute(
        select(DonVi).where(DonVi.ma_don_vi == ADMIN_DON_VI["ma_don_vi"])
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        print(f"  [SKIP] Đơn vị '{ADMIN_DON_VI['ma_don_vi']}' đã tồn tại")
        print(f"         ID: {existing.id}")
        return existing
    
    # Tạo mới
    don_vi = DonVi(**ADMIN_DON_VI)
    session.add(don_vi)
    await session.flush()
    
    print(f"  [CREATE] Đơn vị '{don_vi.ma_don_vi}' - {don_vi.ten_don_vi}")
    print(f"           ID: {don_vi.id}")
    
    return don_vi


async def create_admin_vai_tro(session: AsyncSession) -> VaiTro:
    """
    Tạo hoặc lấy Vai trò Admin (SUPER_ADMIN).
    
    Returns:
        VaiTro: Vai trò Admin
    """
    print("\n" + "=" * 50)
    print("BƯỚC 2: TẠO VAI TRÒ ADMIN")
    print("=" * 50)
    
    # Kiểm tra đã tồn tại chưa
    result = await session.execute(
        select(VaiTro).where(VaiTro.ma_vai_tro == ADMIN_VAI_TRO["ma_vai_tro"])
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        print(f"  [SKIP] Vai trò '{ADMIN_VAI_TRO['ma_vai_tro']}' đã tồn tại")
        print(f"         ID: {existing.id}")
        print(f"         Cấp bậc: {existing.cap_bac.value}")
        return existing
    
    # Tạo mới
    vai_tro = VaiTro(**ADMIN_VAI_TRO)
    session.add(vai_tro)
    await session.flush()
    
    print(f"  [CREATE] Vai trò '{vai_tro.ma_vai_tro}' - {vai_tro.ten_vai_tro}")
    print(f"           ID: {vai_tro.id}")
    print(f"           Cấp bậc: {vai_tro.cap_bac.value}")
    print(f"           is_system_admin: {vai_tro.is_system_admin}")
    
    return vai_tro


async def create_admin_user(
    session: AsyncSession,
    don_vi: DonVi,
    vai_tro: VaiTro
) -> CongChuc:
    """
    Tạo hoặc lấy User Admin (ADMIN-001).
    
    Args:
        session: Database session
        don_vi: Đơn vị Admin
        vai_tro: Vai trò Admin
        
    Returns:
        CongChuc: User Admin
    """
    print("\n" + "=" * 50)
    print("BƯỚC 3: TẠO USER ADMIN")
    print("=" * 50)
    
    # Kiểm tra đã tồn tại chưa (theo ma_cc)
    result = await session.execute(
        select(CongChuc).where(CongChuc.ma_cc == ADMIN_USER["ma_cc"])
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        print(f"  [SKIP] User '{ADMIN_USER['ma_cc']}' đã tồn tại")
        print(f"         ID: {existing.id}")
        print(f"         Username: {existing.username}")
        return existing
    
    # Kiểm tra username đã tồn tại chưa
    result = await session.execute(
        select(CongChuc).where(CongChuc.username == ADMIN_USER["username"])
    )
    existing_username = result.scalar_one_or_none()
    
    if existing_username:
        print(f"  ⚠️ [WARNING] Username '{ADMIN_USER['username']}' đã được sử dụng bởi: {existing_username.ma_cc}")
        print(f"         Sẽ sử dụng username = '{ADMIN_USER['ma_cc'].lower()}'")
        username = ADMIN_USER["ma_cc"].lower()
    else:
        username = ADMIN_USER["username"]
    
    # Hash password
    password_hash = hash_password(DEFAULT_PASSWORD)
    
    # Tạo user
    admin_user = CongChuc(
        id=ADMIN_USER["id"],
        ma_cc=ADMIN_USER["ma_cc"],
        ho_ten=ADMIN_USER["ho_ten"],
        email=ADMIN_USER["email"],
        chuc_vu=ADMIN_USER["chuc_vu"],
        don_vi_id=don_vi.id,
        vai_tro_id=vai_tro.id,
        is_lanh_dao=ADMIN_USER["is_lanh_dao"],
        is_active=ADMIN_USER["is_active"],
        username=username,
        password_hash=password_hash,
    )
    
    session.add(admin_user)
    await session.flush()
    
    print(f"  [CREATE] User Admin")
    print(f"           ID: {admin_user.id}")
    print(f"           Mã CC: {admin_user.ma_cc}")
    print(f"           Họ tên: {admin_user.ho_ten}")
    print(f"           Username: {admin_user.username}")
    print(f"           Password: {DEFAULT_PASSWORD} (đã hash)")
    print(f"           Đơn vị: {don_vi.ten_don_vi}")
    print(f"           Vai trò: {vai_tro.ten_vai_tro}")
    print(f"           is_lanh_dao: {admin_user.is_lanh_dao}")
    
    return admin_user


# =============================================================================
# MAIN FUNCTION
# =============================================================================

async def main():
    """Entry point chính của script."""
    
    print("=" * 60)
    print("SCRIPT TẠO TÀI KHOẢN SUPER ADMIN - HẢI QUAN KV8")
    print("=" * 60)
    print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    
    # Tạo async engine và session
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Bước 1: Tạo Đơn vị Admin
            don_vi = await create_admin_don_vi(session)
            
            # Bước 2: Tạo Vai trò Admin
            vai_tro = await create_admin_vai_tro(session)
            
            # Bước 3: Tạo User Admin
            admin_user = await create_admin_user(session, don_vi, vai_tro)
            
            # Commit tất cả
            await session.commit()
            
            # Kết quả
            print("\n" + "=" * 60)
            print("✅ TẠO TÀI KHOẢN ADMIN THÀNH CÔNG!")
            print("=" * 60)
            print(f"""
╔══════════════════════════════════════════════════════════╗
║               THÔNG TIN ĐĂNG NHẬP ADMIN                  ║
╠══════════════════════════════════════════════════════════╣
║  Username : {admin_user.username:<44} ║
║  Password : {DEFAULT_PASSWORD:<44} ║
╠══════════════════════════════════════════════════════════╣
║  Mã CC    : {admin_user.ma_cc:<44} ║
║  Họ tên   : {admin_user.ho_ten:<44} ║
║  Email    : {admin_user.email or 'N/A':<44} ║
║  Đơn vị   : {don_vi.ten_don_vi:<44} ║
║  Vai trò  : {vai_tro.ten_vai_tro:<44} ║
╚══════════════════════════════════════════════════════════╝
""")
            print("⚠️ LƯU Ý:")
            print("   - Admin KHÔNG tham gia quy trình nghiệp vụ")
            print("   - Admin chỉ quản lý User, Danh mục, xem dữ liệu")
            print("   - Hãy đổi mật khẩu sau khi đăng nhập lần đầu!")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await session.rollback()
            raise
        
        finally:
            await engine.dispose()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
scripts/seed_tieu_chi.py
========================
Script nạp dữ liệu Master Data tiêu chí chung vào bảng tieu_chi_chung.

CÁCH CHẠY:
    cd haiquan_kv8_backend
    python scripts/seed_tieu_chi.py

YÊU CẦU:
    - Database đã được migrate: alembic upgrade head
    - Bảng tieu_chi_chung đã được tạo (migration 004)
    - File .env có DATABASE_URL hợp lệ

DỮ LIỆU NẠP (Master Data v2.5.0):
    - 10 tiêu chí LỚN (1.1, 1.2, 2.1-2.4, 3.1-3.4) - có điểm
    - 21 tiêu chí CON (a1-a8, b1-b4, ...) - không điểm
    - Tổng cộng: 31 dòng

PHÂN BỐ ĐIỂM:
    - Nhóm 1: 10đ = 1.1 (5đ) + 1.2 (5đ)
    - Nhóm 2: 10đ = 2.1 + 2.2 + 2.3 + 2.4 (mỗi cái 2.5đ)
    - Nhóm 3: 10đ = 3.1 + 3.2 + 3.3 + 3.4 (mỗi cái 2.5đ)
    - TỔNG: 30 điểm

TÍNH NĂNG:
    - IDEMPOTENT: Chạy nhiều lần không gây lỗi (skip nếu đã tồn tại)
    - Async: Sử dụng asyncio + SQLAlchemy async
    - Auto-config: Đọc DATABASE_URL từ settings

Phiên bản: 2.5.0 (26/01/2026)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Optional

# =============================================================================
# SETUP PATH - Thêm project root vào sys.path
# =============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import sau khi thêm path
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models import TieuChiChung


# =============================================================================
# CONSTANTS - Dữ liệu Tiêu chí chung (31 dòng)
# =============================================================================

"""
CẤU TRÚC DỮ LIỆU KHỚP 100% VỚI MODEL TieuChiChung:
- ma_tieu_chi: String(10) - UNIQUE, NOT NULL
- ma_tieu_chi_con: String(10) - NULL nếu là TC lớn
- nhom_tieu_chi: Integer (1, 2, 3)
- ten_tieu_chi: Text - NOT NULL
- mo_ta: Text - NULL
- diem_toi_da: Decimal(4,2) - 5.0, 2.5, hoặc 0
- gia_tri_mac_dinh: Boolean - TRUE (nhóm 1,2), FALSE (nhóm 3)
- loai_logic: String(20) - 'ALL_OR_NOTHING' hoặc 'BONUS'
- parent_ma_tieu_chi: String(10) - NULL nếu là TC lớn
- thu_tu: Integer (1-31)
"""

TIEU_CHI_DATA = [
    # =========================================================================
    # NHÓM 1: PHẨM CHẤT CHÍNH TRỊ, ĐẠO ĐỨC, VĂN HÓA (10 điểm)
    # Logic: ALL_OR_NOTHING - vi phạm 1 TC con => 0 điểm TC lớn
    # Mặc định: TRUE (đạt)
    # =========================================================================
    
    # 1.1: Phẩm chất chính trị, đạo đức (5 điểm)
    {
        "ma_tieu_chi": "1.1",
        "ma_tieu_chi_con": None,
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Phẩm chất chính trị, phẩm chất đạo đức, văn hóa thực thi công vụ",
        "mo_ta": "Đánh giá về chính trị, đạo đức, văn hóa ứng xử trong công việc",
        "diem_toi_da": Decimal("5.00"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": None,
        "thu_tu": 1
    },
    {
        "ma_tieu_chi": "1.1a1",
        "ma_tieu_chi_con": "a1",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Chấp hành nghiêm túc đường lối, chủ trương của Đảng, chính sách pháp luật của Nhà nước",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.1",
        "thu_tu": 2
    },
    {
        "ma_tieu_chi": "1.1a2",
        "ma_tieu_chi_con": "a2",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Có quan điểm, bản lĩnh chính trị vững vàng; kiên định lập trường",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.1",
        "thu_tu": 3
    },
    {
        "ma_tieu_chi": "1.1a3",
        "ma_tieu_chi_con": "a3",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Có ý thức nghiên cứu, học tập, vận dụng chủ nghĩa Mác - Lênin, tư tưởng Hồ Chí Minh",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.1",
        "thu_tu": 4
    },
    {
        "ma_tieu_chi": "1.1a4",
        "ma_tieu_chi_con": "a4",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Giữ gìn phẩm chất đạo đức, lối sống trong sáng, trung thực",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.1",
        "thu_tu": 5
    },
    {
        "ma_tieu_chi": "1.1a5",
        "ma_tieu_chi_con": "a5",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Không tham ô, tham nhũng, lãng phí, tiêu cực",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.1",
        "thu_tu": 6
    },
    {
        "ma_tieu_chi": "1.1a6",
        "ma_tieu_chi_con": "a6",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Có tinh thần đoàn kết, ý thức xây dựng cơ quan",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.1",
        "thu_tu": 7
    },
    {
        "ma_tieu_chi": "1.1a7",
        "ma_tieu_chi_con": "a7",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Thực hiện văn hóa công vụ",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.1",
        "thu_tu": 8
    },
    {
        "ma_tieu_chi": "1.1a8",
        "ma_tieu_chi_con": "a8",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Tinh thần tự phê bình, tự soi, tự sửa",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.1",
        "thu_tu": 9
    },
    
    # 1.2: Ý thức kỷ luật, kỷ cương (5 điểm)
    {
        "ma_tieu_chi": "1.2",
        "ma_tieu_chi_con": None,
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Ý thức kỷ luật, kỷ cương trong thực thi công vụ",
        "mo_ta": "Đánh giá về ý thức chấp hành quy định, kỷ luật lao động",
        "diem_toi_da": Decimal("5.00"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": None,
        "thu_tu": 10
    },
    {
        "ma_tieu_chi": "1.2b1",
        "ma_tieu_chi_con": "b1",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Chấp hành sự phân công của tổ chức",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.2",
        "thu_tu": 11
    },
    {
        "ma_tieu_chi": "1.2b2",
        "ma_tieu_chi_con": "b2",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Thực hiện các quy định, quy chế, nội quy của cơ quan",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.2",
        "thu_tu": 12
    },
    {
        "ma_tieu_chi": "1.2b3",
        "ma_tieu_chi_con": "b3",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Thực hiện việc kê khai và công khai tài sản, thu nhập",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.2",
        "thu_tu": 13
    },
    {
        "ma_tieu_chi": "1.2b4",
        "ma_tieu_chi_con": "b4",
        "nhom_tieu_chi": 1,
        "ten_tieu_chi": "Báo cáo đầy đủ, trung thực, cung cấp thông tin chính xác",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "1.2",
        "thu_tu": 14
    },
    
    # =========================================================================
    # NHÓM 2: NĂNG LỰC CHUYÊN MÔN, NGHIỆP VỤ (10 điểm)
    # Logic: ALL_OR_NOTHING
    # Mặc định: TRUE (đạt)
    # =========================================================================
    
    # 2.1: Năng lực chuyên môn (2.5 điểm)
    {
        "ma_tieu_chi": "2.1",
        "ma_tieu_chi_con": None,
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Năng lực chuyên môn, nghiệp vụ theo yêu cầu của vị trí việc làm",
        "mo_ta": "Đánh giá về kiến thức, kỹ năng chuyên môn",
        "diem_toi_da": Decimal("2.50"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": None,
        "thu_tu": 15
    },
    {
        "ma_tieu_chi": "2.1a1",
        "ma_tieu_chi_con": "a1",
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Có kiến thức chuyên sâu, toàn diện về lĩnh vực công tác",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "2.1",
        "thu_tu": 16
    },
    {
        "ma_tieu_chi": "2.1a2",
        "ma_tieu_chi_con": "a2",
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Thường xuyên cập nhật kiến thức mới",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "2.1",
        "thu_tu": 17
    },
    {
        "ma_tieu_chi": "2.1a3",
        "ma_tieu_chi_con": "a3",
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Có kỹ năng xử lý công việc độc lập, làm việc nhóm hiệu quả",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "2.1",
        "thu_tu": 18
    },
    
    # 2.2: Khả năng đáp ứng (2.5 điểm)
    {
        "ma_tieu_chi": "2.2",
        "ma_tieu_chi_con": None,
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Khả năng đáp ứng yêu cầu thực thi nhiệm vụ được giao",
        "mo_ta": "Đánh giá khả năng hoàn thành nhiệm vụ thường xuyên và đột xuất",
        "diem_toi_da": Decimal("2.50"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": None,
        "thu_tu": 19
    },
    {
        "ma_tieu_chi": "2.2b1",
        "ma_tieu_chi_con": "b1",
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Nhiệm vụ thường xuyên: Xử lý công việc theo kế hoạch định kỳ",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "2.2",
        "thu_tu": 20
    },
    {
        "ma_tieu_chi": "2.2b2",
        "ma_tieu_chi_con": "b2",
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Nhiệm vụ đột xuất: Chủ động đề xuất giải pháp, phản ứng nhanh",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "2.2",
        "thu_tu": 21
    },
    
    # 2.3: Tinh thần trách nhiệm (2.5 điểm)
    {
        "ma_tieu_chi": "2.3",
        "ma_tieu_chi_con": None,
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Tinh thần trách nhiệm trong thực thi công vụ",
        "mo_ta": "Đánh giá về trách nhiệm, chủ động trong công việc",
        "diem_toi_da": Decimal("2.50"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": None,
        "thu_tu": 22
    },
    {
        "ma_tieu_chi": "2.3c1",
        "ma_tieu_chi_con": "c1",
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Có tinh thần trách nhiệm trong nghiên cứu, đề xuất, tham mưu",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "2.3",
        "thu_tu": 23
    },
    {
        "ma_tieu_chi": "2.3c2",
        "ma_tieu_chi_con": "c2",
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Tích cực cập nhật, ứng dụng kiến thức, công nghệ mới",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "2.3",
        "thu_tu": 24
    },
    
    # 2.4: Thái độ phục vụ (2.5 điểm)
    {
        "ma_tieu_chi": "2.4",
        "ma_tieu_chi_con": None,
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Thái độ phục vụ Nhân dân, doanh nghiệp và khả năng phối hợp",
        "mo_ta": "Đánh giá về thái độ phục vụ, hợp tác với đồng nghiệp",
        "diem_toi_da": Decimal("2.50"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": None,
        "thu_tu": 25
    },
    {
        "ma_tieu_chi": "2.4d1",
        "ma_tieu_chi_con": "d1",
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Được người dân, doanh nghiệp đánh giá tích cực (nếu có tiếp xúc)",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "2.4",
        "thu_tu": 26
    },
    {
        "ma_tieu_chi": "2.4d2",
        "ma_tieu_chi_con": "d2",
        "nhom_tieu_chi": 2,
        "ten_tieu_chi": "Có tinh thần trách nhiệm, hợp tác trong chuyên môn",
        "mo_ta": None,
        "diem_toi_da": Decimal("0"),
        "gia_tri_mac_dinh": True,
        "loai_logic": "ALL_OR_NOTHING",
        "parent_ma_tieu_chi": "2.4",
        "thu_tu": 27
    },
    
    # =========================================================================
    # NHÓM 3: NĂNG LỰC ĐỔI MỚI, SÁNG TẠO (10 điểm)
    # Logic: BONUS - mỗi TC đạt => +2.5 điểm
    # Mặc định: FALSE (không đạt) - phải tick nếu có thành tích
    # =========================================================================
    
    {
        "ma_tieu_chi": "3.1",
        "ma_tieu_chi_con": None,
        "nhom_tieu_chi": 3,
        "ten_tieu_chi": "Có sản phẩm, giải pháp đột phá, sáng tạo đem lại giá trị thiết thực",
        "mo_ta": "Có sáng kiến, cải tiến được công nhận và mang lại hiệu quả",
        "diem_toi_da": Decimal("2.50"),
        "gia_tri_mac_dinh": False,
        "loai_logic": "BONUS",
        "parent_ma_tieu_chi": None,
        "thu_tu": 28
    },
    {
        "ma_tieu_chi": "3.2",
        "ma_tieu_chi_con": None,
        "nhom_tieu_chi": 3,
        "ten_tieu_chi": "Sẵn sàng tham gia nhiệm vụ chính trị đặc biệt quan trọng",
        "mo_ta": "Tham gia công tác đột xuất, nhiệm vụ đặc biệt khi được điều động",
        "diem_toi_da": Decimal("2.50"),
        "gia_tri_mac_dinh": False,
        "loai_logic": "BONUS",
        "parent_ma_tieu_chi": None,
        "thu_tu": 29
    },
    {
        "ma_tieu_chi": "3.3",
        "ma_tieu_chi_con": None,
        "nhom_tieu_chi": 3,
        "ten_tieu_chi": "Có tinh thần chịu trách nhiệm trước kết quả công việc",
        "mo_ta": "Dám nghĩ, dám làm, dám chịu trách nhiệm với quyết định của mình",
        "diem_toi_da": Decimal("2.50"),
        "gia_tri_mac_dinh": False,
        "loai_logic": "BONUS",
        "parent_ma_tieu_chi": None,
        "thu_tu": 30
    },
    {
        "ma_tieu_chi": "3.4",
        "ma_tieu_chi_con": None,
        "nhom_tieu_chi": 3,
        "ten_tieu_chi": "Chủ động đưa ra quyết định trong phạm vi thẩm quyền",
        "mo_ta": "Chủ động giải quyết công việc, không đùn đẩy, trì hoãn",
        "diem_toi_da": Decimal("2.50"),
        "gia_tri_mac_dinh": False,
        "loai_logic": "BONUS",
        "parent_ma_tieu_chi": None,
        "thu_tu": 31
    },
]


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

async def get_existing_ma_tieu_chi(session: AsyncSession) -> set[str]:
    """
    Lấy danh sách mã tiêu chí đã tồn tại trong database.
    
    Returns:
        set: Tập hợp các mã tiêu chí đã có
    """
    result = await session.execute(
        select(TieuChiChung.ma_tieu_chi)
    )
    return {row[0] for row in result.fetchall()}


async def seed_tieu_chi_chung(session: AsyncSession) -> tuple[int, int]:
    """
    Nạp dữ liệu tiêu chí chung vào database.
    
    Args:
        session: Database session
        
    Returns:
        tuple: (số tạo mới, số bỏ qua)
    """
    print("\n" + "=" * 60)
    print("NẠP DỮ LIỆU TIÊU CHÍ CHUNG")
    print("=" * 60)
    
    total = len(TIEU_CHI_DATA)
    created_count = 0
    skipped_count = 0
    
    # Lấy danh sách đã tồn tại (IDEMPOTENT check)
    existing_codes = await get_existing_ma_tieu_chi(session)
    print(f"Đã có {len(existing_codes)} tiêu chí trong database\n")
    
    current_nhom = None
    
    for tc_data in TIEU_CHI_DATA:
        ma_tieu_chi = tc_data["ma_tieu_chi"]
        ten_tieu_chi = tc_data["ten_tieu_chi"]
        nhom = tc_data["nhom_tieu_chi"]
        ma_con = tc_data["ma_tieu_chi_con"]
        
        # In header nhóm mới
        if current_nhom != nhom:
            current_nhom = nhom
            nhom_ten = {
                1: "NHÓM 1: Phẩm chất chính trị, đạo đức (10đ)",
                2: "NHÓM 2: Năng lực chuyên môn (10đ)",
                3: "NHÓM 3: Năng lực đổi mới, sáng tạo (10đ)",
            }
            print(f"\n📋 {nhom_ten.get(nhom, f'Nhóm {nhom}')}:")
        
        # Kiểm tra tồn tại (IDEMPOTENT)
        if ma_tieu_chi in existing_codes:
            skipped_count += 1
            if ma_con is None:  # Chỉ log tiêu chí lớn
                print(f"  [SKIP] {ma_tieu_chi}: {ten_tieu_chi[:45]}... (đã tồn tại)")
            continue
        
        # Tạo tiêu chí mới sử dụng model SQLAlchemy
        new_tieu_chi = TieuChiChung(**tc_data)
        session.add(new_tieu_chi)
        created_count += 1
        
        # Log
        if ma_con is None:  # Tiêu chí lớn (có điểm)
            diem = tc_data["diem_toi_da"]
            logic = tc_data["loai_logic"]
            default = "ĐẠT" if tc_data["gia_tri_mac_dinh"] else "KHÔNG"
            print(f"  [CREATE] {ma_tieu_chi}: {ten_tieu_chi[:40]}... ({diem}đ, {logic}, mặc định={default})")
        else:  # Tiêu chí con
            print(f"    └─ [CREATE] {ma_tieu_chi}: {ten_tieu_chi[:35]}...")
    
    # Commit tất cả
    await session.commit()
    
    return created_count, skipped_count


async def print_summary(session: AsyncSession):
    """In thống kê sau khi nạp dữ liệu."""
    
    print("\n" + "=" * 60)
    print("THỐNG KÊ TIÊU CHÍ CHUNG")
    print("=" * 60)
    
    # Đếm theo nhóm (chỉ tiêu chí lớn - có điểm > 0)
    result = await session.execute(
        select(
            TieuChiChung.nhom_tieu_chi,
            func.count(TieuChiChung.id),
            func.sum(TieuChiChung.diem_toi_da)
        )
        .where(TieuChiChung.ma_tieu_chi_con.is_(None))
        .group_by(TieuChiChung.nhom_tieu_chi)
        .order_by(TieuChiChung.nhom_tieu_chi)
    )
    
    print("\n📊 Phân bố theo Nhóm (chỉ tiêu chí lớn):")
    print("-" * 55)
    print(f"{'Nhóm':<8} {'Số TC lớn':<15} {'Tổng điểm':<10}")
    print("-" * 55)
    
    total_tc = 0
    total_diem = Decimal("0")
    
    for row in result.fetchall():
        nhom, count, diem = row
        total_tc += count
        total_diem += diem or Decimal("0")
        print(f"  {nhom:<6} {count:<15} {diem or 0:<10}")
    
    print("-" * 55)
    print(f"  {'TỔNG':<6} {total_tc:<15} {total_diem:<10}")
    
    # Đếm tổng (cả tiêu chí con)
    result = await session.execute(
        select(func.count(TieuChiChung.id))
    )
    total_all = result.scalar() or 0
    
    result = await session.execute(
        select(func.count(TieuChiChung.id))
        .where(TieuChiChung.ma_tieu_chi_con.isnot(None))
    )
    total_con = result.scalar() or 0
    
    print(f"\n📈 Tổng cộng:")
    print(f"   - Tiêu chí lớn: {total_tc}")
    print(f"   - Tiêu chí con: {total_con}")
    print(f"   - Tổng số dòng: {total_all}")


async def verify_data(session: AsyncSession) -> bool:
    """
    Kiểm tra dữ liệu sau khi nạp.
    
    Returns:
        bool: True nếu dữ liệu đầy đủ và hợp lệ
    """
    print("\n" + "=" * 60)
    print("KIỂM TRA DỮ LIỆU")
    print("=" * 60)
    
    errors = []
    
    # Test 1: Kiểm tra số lượng tiêu chí lớn (phải = 10)
    result = await session.execute(
        select(func.count(TieuChiChung.id))
        .where(TieuChiChung.ma_tieu_chi_con.is_(None))
    )
    tc_lon = result.scalar() or 0
    
    if tc_lon != 10:
        errors.append(f"❌ Số tiêu chí lớn sai: có {tc_lon}, cần 10")
    else:
        print(f"✅ Tiêu chí lớn: {tc_lon}/10")
    
    # Test 2: Kiểm tra tổng điểm (phải = 30)
    result = await session.execute(
        select(func.sum(TieuChiChung.diem_toi_da))
        .where(TieuChiChung.ma_tieu_chi_con.is_(None))
    )
    tong_diem = result.scalar() or Decimal("0")
    
    if tong_diem != Decimal("30"):
        errors.append(f"❌ Tổng điểm sai: có {tong_diem}, cần 30")
    else:
        print(f"✅ Tổng điểm tối đa: {tong_diem}/30")
    
    # Test 3: Kiểm tra nhóm 3 có đúng 4 TC với logic BONUS
    result = await session.execute(
        select(func.count(TieuChiChung.id))
        .where(
            TieuChiChung.nhom_tieu_chi == 3,
            TieuChiChung.loai_logic == "BONUS"
        )
    )
    nhom3_bonus = result.scalar() or 0
    
    if nhom3_bonus != 4:
        errors.append(f"❌ Nhóm 3 BONUS sai: có {nhom3_bonus}, cần 4")
    else:
        print(f"✅ Nhóm 3 (BONUS): {nhom3_bonus}/4")
    
    # Test 4: Kiểm tra tổng số dòng (phải = 31)
    result = await session.execute(
        select(func.count(TieuChiChung.id))
    )
    total_rows = result.scalar() or 0
    
    if total_rows != 31:
        errors.append(f"❌ Tổng số dòng sai: có {total_rows}, cần 31")
    else:
        print(f"✅ Tổng số dòng: {total_rows}/31")
    
    # Kết quả
    if errors:
        print("\n⚠️ CÓ LỖI:")
        for err in errors:
            print(f"  {err}")
        return False
    
    print("\n✅ DỮ LIỆU HỢP LỆ - KHỚP 100% VỚI MODEL!")
    return True


# =============================================================================
# MAIN FUNCTION
# =============================================================================

async def main():
    """Entry point chính của script."""
    
    print("=" * 60)
    print("SCRIPT NẠP TIÊU CHÍ CHUNG - HẢI QUAN KV8")
    print("=" * 60)
    print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print(f"Tổng số tiêu chí cần nạp: {len(TIEU_CHI_DATA)}")
    
    # Tạo async engine và session (sử dụng settings.database_url)
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Bước 1: Nạp dữ liệu
            created, skipped = await seed_tieu_chi_chung(session)
            
            # Bước 2: In thống kê
            await print_summary(session)
            
            # Bước 3: Kiểm tra dữ liệu
            is_valid = await verify_data(session)
            
            # Kết quả
            print("\n" + "=" * 60)
            print("KẾT QUẢ NẠP DỮ LIỆU")
            print("=" * 60)
            print(f"✅ Tạo mới: {created}")
            print(f"⏭️ Bỏ qua (đã tồn tại): {skipped}")
            print(f"📊 Tổng xử lý: {created + skipped}")
            
            if not is_valid:
                print("\n⚠️ CẢNH BÁO: Dữ liệu chưa đầy đủ!")
                print("Vui lòng kiểm tra lại migration và chạy script một lần nữa.")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
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
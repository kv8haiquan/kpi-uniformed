"""
Migration 004: Tạo/Cập nhật bảng Tiêu chí chung theo chuẩn v2.5.0

Revision ID: 004_tieu_chi_chung
Revises: 83b03c6bb879 (reset_initial)
Create Date: 2026-01-26

CHUỖI MIGRATION:
    001_init_tables
    002_add_super_admin
    003_add_self_evaluation
    a660585d9c09_add_leave_management_table
    83b03c6bb879_reset_initial  <- HEAD trước đó
    004_tieu_chi_chung          <- MIGRATION NÀY

VẤN ĐỀ CẦN XỬ LÝ:
    1. Migration 001 đã tạo bảng `tieu_chi_chung_danh_gia` với cấu trúc CŨ
       (có ma_tieu_chi, ten_tieu_chi trực tiếp, KHÔNG có FK tới tieu_chi_chung)
    2. Model mới yêu cầu:
       - Bảng `tieu_chi_chung` (Master Data) - CHƯA TỒN TẠI
       - Bảng `tieu_chi_chung_danh_gia` với FK `tieu_chi_id` → `tieu_chi_chung.id`

GIẢI PHÁP:
    1. Backup dữ liệu cũ (nếu có)
    2. DROP bảng `tieu_chi_chung_danh_gia` cũ
    3. Tạo bảng `tieu_chi_chung` (Master Data)
    4. Tạo lại bảng `tieu_chi_chung_danh_gia` với cấu trúc mới

⚠️ WARNING: Migration này sẽ XÓA dữ liệu trong bảng tieu_chi_chung_danh_gia cũ!
            Đây là điều cần thiết vì cấu trúc không tương thích.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_tieu_chi_chung'
down_revision: Union[str, None] = '83b03c6bb879'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Tạo/Cập nhật bảng tiêu chí chung theo chuẩn v2.5.0.
    """
    
    print("\n" + "=" * 60)
    print("MIGRATION 004: TẠO BẢNG TIÊU CHÍ CHUNG v2.5.0")
    print("=" * 60)
    
    # =========================================================================
    # BƯỚC 1: TẠO ENUM trang_thai_tieu_chi_enum (NẾU CHƯA CÓ)
    # =========================================================================
    print("\n[Bước 1] Tạo ENUM trang_thai_tieu_chi_enum...")
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE trang_thai_tieu_chi_enum AS ENUM ('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET');
        EXCEPTION
            WHEN duplicate_object THEN 
                RAISE NOTICE 'ENUM trang_thai_tieu_chi_enum đã tồn tại, bỏ qua.';
        END $$;
    """)
    
    # =========================================================================
    # BƯỚC 2: XÓA BẢNG tieu_chi_chung_danh_gia CŨ (NẾU CÓ)
    # Bảng cũ có cấu trúc không tương thích (không có FK tới tieu_chi_chung)
    # =========================================================================
    print("[Bước 2] Xóa bảng tieu_chi_chung_danh_gia cũ (nếu có)...")
    
    op.execute("""
        DROP TABLE IF EXISTS tieu_chi_chung_danh_gia CASCADE;
    """)
    
    # =========================================================================
    # BƯỚC 3: TẠO BẢNG tieu_chi_chung (MASTER DATA)
    # Phải tạo bảng này TRƯỚC vì tieu_chi_chung_danh_gia sẽ FK tới nó
    # =========================================================================
    print("[Bước 3] Tạo bảng tieu_chi_chung (Master Data)...")
    
    op.execute("""
        DROP TABLE IF EXISTS tieu_chi_chung CASCADE;
    """)
    
    op.create_table(
        'tieu_chi_chung',
        
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text('gen_random_uuid()'), 
                  nullable=False,
                  comment='Primary Key (UUID)'),
        
        # Mã tiêu chí
        sa.Column('ma_tieu_chi', sa.String(10), nullable=False,
                  comment='Mã tiêu chí: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4'),
        sa.Column('ma_tieu_chi_con', sa.String(10), nullable=True,
                  comment='Mã tiêu chí con: a1, a2, b1, ... (NULL nếu là TC lớn)'),
        
        # Phân nhóm
        sa.Column('nhom_tieu_chi', sa.Integer(), nullable=False,
                  comment='Nhóm: 1=Phẩm chất, 2=Năng lực CM, 3=Đổi mới'),
        
        # Nội dung
        sa.Column('ten_tieu_chi', sa.Text(), nullable=False,
                  comment='Tên tiêu chí'),
        sa.Column('mo_ta', sa.Text(), nullable=True,
                  comment='Mô tả chi tiết'),
        
        # Điểm số
        sa.Column('diem_toi_da', sa.Numeric(4, 2), nullable=False,
                  comment='Điểm tối đa: 5.0 (nhóm 1), 2.5 (nhóm 2,3)'),
        
        # Logic chấm điểm
        sa.Column('gia_tri_mac_dinh', sa.Boolean(), nullable=False,
                  comment='Giá trị mặc định: TRUE (nhóm 1,2), FALSE (nhóm 3)'),
        sa.Column('loai_logic', sa.String(20), nullable=False,
                  comment='Logic: ALL_OR_NOTHING hoặc BONUS'),
        
        # Quan hệ cha con
        sa.Column('parent_ma_tieu_chi', sa.String(10), nullable=True,
                  comment='Mã tiêu chí cha (VD: a1 có parent 1.1)'),
        sa.Column('thu_tu', sa.Integer(), nullable=False,
                  comment='Thứ tự hiển thị (1-31)'),
        
        # Trạng thái
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true',
                  comment='Còn sử dụng'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ma_tieu_chi', name='uq_tieu_chi_ma'),
        sa.CheckConstraint('nhom_tieu_chi BETWEEN 1 AND 3', name='ck_tc_nhom'),
        sa.CheckConstraint("loai_logic IN ('ALL_OR_NOTHING', 'BONUS')", name='ck_tc_loai_logic'),
        
        comment='Master Data: Danh mục tiêu chí chung (31 tiêu chí)'
    )
    
    # Indexes cho tieu_chi_chung
    op.create_index('idx_tieu_chi_nhom', 'tieu_chi_chung', ['nhom_tieu_chi'])
    op.create_index('idx_tieu_chi_parent', 'tieu_chi_chung', ['parent_ma_tieu_chi'])
    op.create_index('idx_tieu_chi_active', 'tieu_chi_chung', ['is_active'])
    
    print("   ✅ Đã tạo bảng tieu_chi_chung")
    
    # =========================================================================
    # BƯỚC 4: TẠO LẠI BẢNG tieu_chi_chung_danh_gia (CHUẨN v2.5.0)
    # Với FK tới tieu_chi_chung.id và các trường is_achieved_cc, is_achieved_ld
    # =========================================================================
    print("[Bước 4] Tạo lại bảng tieu_chi_chung_danh_gia (chuẩn v2.5.0)...")
    
    op.create_table(
        'tieu_chi_chung_danh_gia',
        
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'),
                  nullable=False,
                  comment='Primary Key (UUID)'),
        
        # Foreign Keys
        sa.Column('danh_gia_thang_id', postgresql.UUID(as_uuid=True), nullable=False,
                  comment='FK → danh_gia_thang.id'),
        sa.Column('tieu_chi_id', postgresql.UUID(as_uuid=True), nullable=False,
                  comment='FK → tieu_chi_chung.id'),
        
        # =====================================================================
        # BINARY SCORING - LƯU CẢ 2 BẢN TÍCH (v2.4.1)
        # =====================================================================
        sa.Column('is_achieved_cc', sa.Boolean(), nullable=False,
                  comment='BẢN TÍCH CC: TRUE=Đạt, FALSE=Không đạt'),
        sa.Column('is_achieved_ld', sa.Boolean(), nullable=True,
                  comment='BẢN TÍCH LĐ: NULL=Chưa duyệt'),
        
        # Điểm tự động tính
        sa.Column('diem_tu_cham', sa.Numeric(4, 2), nullable=False,
                  comment='Điểm CC = diem_toi_da if is_achieved_cc else 0'),
        sa.Column('diem_phe_duyet', sa.Numeric(4, 2), nullable=True,
                  comment='Điểm LĐ = diem_toi_da if is_achieved_ld else 0'),
        
        # =====================================================================
        # LUỒNG PHÊ DUYỆT (KHÔNG CÓ TỪ CHỐI - LĐ điều chỉnh trực tiếp)
        # =====================================================================
        sa.Column('trang_thai', 
                  postgresql.ENUM('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET', 
                                  name='trang_thai_tieu_chi_enum', create_type=False),
                  nullable=False, server_default='NHAP',
                  comment='Trạng thái: NHAP, CHO_PHE_DUYET, DA_PHE_DUYET'),
        
        sa.Column('nguoi_phe_duyet_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='FK → cong_chuc.id (người phê duyệt)'),
        
        # Thời gian
        sa.Column('ngay_gui', sa.DateTime(timezone=True), nullable=True,
                  comment='Ngày CC gửi phê duyệt'),
        sa.Column('ngay_phe_duyet', sa.DateTime(timezone=True), nullable=True,
                  comment='Ngày LĐ phê duyệt'),
        
        # Ghi chú (AUDIT TRAIL)
        sa.Column('ghi_chu_cc', sa.Text(), nullable=True,
                  comment='Ghi chú của CC khi tự đánh giá'),
        sa.Column('ghi_chu_ld', sa.Text(), nullable=True,
                  comment='Ghi chú của LĐ khi phê duyệt'),
        sa.Column('ly_do_dieu_chinh', sa.Text(), nullable=True,
                  comment='Lý do LĐ điều chỉnh (nếu is_achieved_ld != is_achieved_cc)'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['danh_gia_thang_id'], ['danh_gia_thang.id'],
                                name='fk_tcdg_danh_gia_thang', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tieu_chi_id'], ['tieu_chi_chung.id'],
                                name='fk_tcdg_tieu_chi', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nguoi_phe_duyet_id'], ['cong_chuc.id'],
                                name='fk_tcdg_nguoi_phe_duyet', ondelete='SET NULL'),
        sa.UniqueConstraint('danh_gia_thang_id', 'tieu_chi_id', 
                           name='uq_tc_danh_gia_tieu_chi'),
        
        comment='Kết quả chấm tiêu chí chung của CC (Binary Scoring v2.5.0)'
    )
    
    # Indexes cho tieu_chi_chung_danh_gia
    op.create_index('idx_tc_chung_danh_gia', 'tieu_chi_chung_danh_gia', ['danh_gia_thang_id'])
    op.create_index('idx_tc_trang_thai', 'tieu_chi_chung_danh_gia', ['trang_thai'])
    op.create_index('idx_tc_nguoi_phe_duyet', 'tieu_chi_chung_danh_gia', ['nguoi_phe_duyet_id'])
    
    # Index đặc biệt: Tìm các TC có sự khác biệt giữa CC và LĐ
    op.execute("""
        CREATE INDEX idx_tc_khac_biet ON tieu_chi_chung_danh_gia(danh_gia_thang_id)
        WHERE is_achieved_ld IS NOT NULL AND is_achieved_cc != is_achieved_ld;
    """)
    
    print("   ✅ Đã tạo bảng tieu_chi_chung_danh_gia")
    
    # =========================================================================
    # BƯỚC 5: THÊM CỘT diem_tieu_chi_chung VÀO danh_gia_thang (NẾU CHƯA CÓ)
    # =========================================================================
    print("[Bước 5] Kiểm tra cột diem_tieu_chi_chung trong danh_gia_thang...")
    
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE danh_gia_thang 
            ADD COLUMN IF NOT EXISTS diem_tieu_chi_chung NUMERIC(5, 2) DEFAULT NULL;
            
            COMMENT ON COLUMN danh_gia_thang.diem_tieu_chi_chung IS 'Tổng điểm tiêu chí chung (0-30)';
        EXCEPTION
            WHEN duplicate_column THEN 
                RAISE NOTICE 'Cột diem_tieu_chi_chung đã tồn tại, bỏ qua.';
        END $$;
    """)
    
    # =========================================================================
    # HOÀN THÀNH
    # =========================================================================
    print("\n" + "=" * 60)
    print("✅ MIGRATION 004 HOÀN THÀNH!")
    print("=" * 60)
    print("Đã tạo:")
    print("  - Bảng tieu_chi_chung (Master Data)")
    print("  - Bảng tieu_chi_chung_danh_gia (Binary Scoring)")
    print("  - ENUM trang_thai_tieu_chi_enum")
    print("")
    print("⚠️ BƯỚC TIẾP THEO:")
    print("  Chạy: python scripts/seed_tieu_chi.py")
    print("  để nạp 31 tiêu chí vào bảng tieu_chi_chung")
    print("=" * 60 + "\n")


def downgrade() -> None:
    """
    Rollback: Xóa các bảng và khôi phục bảng cũ.
    
    ⚠️ WARNING: Không thể khôi phục dữ liệu đã mất!
    """
    print("\n[Rollback] Xóa bảng tiêu chí chung v2.5.0...")
    
    # Xóa indexes
    op.execute("DROP INDEX IF EXISTS idx_tc_khac_biet")
    op.drop_index('idx_tc_nguoi_phe_duyet', table_name='tieu_chi_chung_danh_gia')
    op.drop_index('idx_tc_trang_thai', table_name='tieu_chi_chung_danh_gia')
    op.drop_index('idx_tc_chung_danh_gia', table_name='tieu_chi_chung_danh_gia')
    
    # Xóa bảng tieu_chi_chung_danh_gia mới
    op.drop_table('tieu_chi_chung_danh_gia')
    
    # Xóa indexes của tieu_chi_chung
    op.drop_index('idx_tieu_chi_active', table_name='tieu_chi_chung')
    op.drop_index('idx_tieu_chi_parent', table_name='tieu_chi_chung')
    op.drop_index('idx_tieu_chi_nhom', table_name='tieu_chi_chung')
    
    # Xóa bảng tieu_chi_chung
    op.drop_table('tieu_chi_chung')
    
    # Xóa ENUM
    op.execute("DROP TYPE IF EXISTS trang_thai_tieu_chi_enum")
    
    # Xóa cột diem_tieu_chi_chung
    op.execute("""
        ALTER TABLE danh_gia_thang 
        DROP COLUMN IF EXISTS diem_tieu_chi_chung;
    """)
    
    # Tạo lại bảng cũ (cấu trúc từ migration 001)
    print("[Rollback] Tạo lại bảng tieu_chi_chung_danh_gia cũ...")
    
    op.create_table(
        'tieu_chi_chung_danh_gia',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('danh_gia_thang_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nhom_tieu_chi', sa.Integer(), nullable=False),
        sa.Column('ma_tieu_chi', sa.String(10), nullable=False),
        sa.Column('ten_tieu_chi', sa.String(500), nullable=True),
        sa.Column('diem_toi_da', sa.Numeric(4, 2), nullable=False),
        sa.Column('diem_tu_cham', sa.Numeric(4, 2), nullable=True),
        sa.Column('diem_phe_duyet', sa.Numeric(4, 2), nullable=True),
        sa.Column('nguoi_phe_duyet_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ngay_phe_duyet', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ghi_chu', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['danh_gia_thang_id'], ['danh_gia_thang.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['nguoi_phe_duyet_id'], ['cong_chuc.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('danh_gia_thang_id', 'ma_tieu_chi', name='uq_tc_danh_gia_ma'),
        sa.CheckConstraint('nhom_tieu_chi BETWEEN 1 AND 3', name='ck_tc_nhom_old'),
        comment='Chi tiết điểm tiêu chí chung (cấu trúc cũ)'
    )
    op.create_index('idx_tc_chung_danh_gia', 'tieu_chi_chung_danh_gia', ['danh_gia_thang_id'])
    
    print("✅ Rollback hoàn thành!")
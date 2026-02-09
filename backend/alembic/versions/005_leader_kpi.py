"""
Migration 005: Tạo bảng Kê khai công việc Lãnh đạo và Đánh giá d,đ,e

Revision ID: 005_leader_kpi
Revises: 004_tieu_chi_chung
Create Date: 2026-01-27

CHUỖI MIGRATION:
    001_init_tables
    002_add_super_admin
    003_add_self_evaluation
    a660585d9c09_add_leave_management_table
    83b03c6bb879_reset_initial
    004_tieu_chi_chung          <- HEAD trước đó
    005_leader_kpi              <- MIGRATION NÀY

MÔ TẢ:
    Module Kê khai KPI cho Lãnh đạo (Phó ĐV, Trưởng ĐV, Phó CCT, CCT)
    
    Khác với CC thường:
    - KHÔNG có danh mục SP, cấp độ, hệ số quy đổi
    - Mỗi công việc = 1 SP
    - Có thêm đánh giá d, đ, e (năng lực lãnh đạo)
    
    Công thức điểm KPI Lãnh đạo:
    Điểm = (a + b + c + d + đ + e) / 6 × 70
    
    Trong đó:
    - a = Số CV hoàn thành / Target
    - b = Số CV đạt chất lượng / Target
    - c = Số CV đúng tiến độ / Target
    - d = Kết quả đơn vị (100% hoặc 50%)
    - đ = Tổ chức triển khai (100% hoặc 50%)
    - e = Đoàn kết nội bộ (100% hoặc 50%)

BẢNG TẠO MỚI:
    1. ke_khai_lanh_dao - Kê khai công việc của Lãnh đạo
    2. danh_gia_dde - Đánh giá d, đ, e
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_leader_kpi'
down_revision: Union[str, None] = '004_tieu_chi_chung'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Tạo bảng kê khai công việc Lãnh đạo và đánh giá d,đ,e.
    """
    
    print("\n" + "=" * 60)
    print("MIGRATION 005: TẠO MODULE KÊ KHAI LÃNH ĐẠO")
    print("=" * 60)
    
    # =========================================================================
    # BƯỚC 1: TẠO ENUM trang_thai_hoan_thanh_enum
    # =========================================================================
    print("\n[Bước 1] Tạo ENUM trang_thai_hoan_thanh_enum...")
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE trang_thai_hoan_thanh_enum AS ENUM ('DA_HOAN_THANH', 'CHUA_HOAN_THANH');
        EXCEPTION
            WHEN duplicate_object THEN 
                RAISE NOTICE 'ENUM trang_thai_hoan_thanh_enum đã tồn tại, bỏ qua.';
        END $$;
    """)
    
    # =========================================================================
    # BƯỚC 2: TẠO BẢNG ke_khai_lanh_dao
    # =========================================================================
    print("[Bước 2] Tạo bảng ke_khai_lanh_dao...")
    
    op.create_table(
        'ke_khai_lanh_dao',
        
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'),
                  nullable=False,
                  comment='Primary Key (UUID)'),
        
        # Foreign Key - Công chức (Lãnh đạo)
        sa.Column('cong_chuc_id', postgresql.UUID(as_uuid=True), nullable=False,
                  comment='FK → cong_chuc.id (người kê khai - phải là Lãnh đạo)'),
        
        # Thời gian
        sa.Column('thang', sa.Integer(), nullable=False,
                  comment='Tháng kê khai (1-12)'),
        sa.Column('nam', sa.Integer(), nullable=False,
                  comment='Năm kê khai'),
        
        # =====================================================================
        # THÔNG TIN CÔNG VIỆC (ĐƠN GIẢN HƠN CC THƯỜNG)
        # =====================================================================
        sa.Column('ten_cong_viec', sa.String(500), nullable=False,
                  comment='Tên công việc'),
        sa.Column('mo_ta', sa.Text(), nullable=True,
                  comment='Mô tả chi tiết công việc'),
        sa.Column('ngay_thuc_hien', sa.Date(), nullable=False,
                  comment='Ngày thực hiện công việc'),
        
        # Trạng thái hoàn thành
        sa.Column('trang_thai_hoan_thanh',
                  postgresql.ENUM('DA_HOAN_THANH', 'CHUA_HOAN_THANH',
                                  name='trang_thai_hoan_thanh_enum', create_type=False),
                  nullable=False, server_default='CHUA_HOAN_THANH',
                  comment='Trạng thái hoàn thành công việc'),
        
        # Số lượng (mỗi công việc = 1 SP, không quy đổi)
        sa.Column('so_luong', sa.Integer(), nullable=False, server_default='1',
                  comment='Số lượng công việc (mặc định = 1)'),
        
        # =====================================================================
        # PHÊ DUYỆT
        # =====================================================================
        sa.Column('nguoi_phe_duyet_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='FK → cong_chuc.id (người phê duyệt)'),
        
        # Trạng thái phê duyệt (dùng chung enum với ke_khai_cong_viec)
        sa.Column('trang_thai', sa.String(20), nullable=False, server_default='NHAP',
                  comment='Trạng thái: NHAP, CHO_PHE_DUYET, DA_PHE_DUYET, TU_CHOI'),
        
        # =====================================================================
        # ĐÁNH GIÁ (sau phê duyệt)
        # =====================================================================
        sa.Column('so_loi_chat_luong', sa.Integer(), nullable=False, server_default='0',
                  comment='Số lỗi chất lượng (LĐ cấp trên chốt)'),
        sa.Column('so_loi_tien_do', sa.Integer(), nullable=False, server_default='0',
                  comment='Số lỗi tiến độ (LĐ cấp trên chốt)'),
        sa.Column('y_kien_lanh_dao', sa.Text(), nullable=True,
                  comment='Ý kiến của người phê duyệt'),
        
        # =====================================================================
        # AUDIT
        # =====================================================================
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false',
                  comment='Soft delete flag'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cong_chuc_id'], ['cong_chuc.id'],
                                name='fk_kkld_cong_chuc', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['nguoi_phe_duyet_id'], ['cong_chuc.id'],
                                name='fk_kkld_nguoi_phe_duyet', ondelete='SET NULL'),
        sa.CheckConstraint('thang BETWEEN 1 AND 12', name='ck_kkld_thang'),
        sa.CheckConstraint('nam >= 2025', name='ck_kkld_nam'),
        sa.CheckConstraint('so_luong >= 1', name='ck_kkld_so_luong'),
        sa.CheckConstraint('so_loi_chat_luong >= 0', name='ck_kkld_loi_cl'),
        sa.CheckConstraint('so_loi_tien_do >= 0', name='ck_kkld_loi_td'),
        sa.CheckConstraint(
            "trang_thai IN ('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET', 'TU_CHOI')",
            name='ck_kkld_trang_thai'
        ),
        
        comment='Kê khai công việc của Lãnh đạo (Phó ĐV, Trưởng ĐV, Phó CCT, CCT)'
    )
    
    # Indexes cho ke_khai_lanh_dao
    op.create_index('idx_kkld_cong_chuc', 'ke_khai_lanh_dao', ['cong_chuc_id'])
    op.create_index('idx_kkld_thang_nam', 'ke_khai_lanh_dao', ['thang', 'nam'])
    op.create_index('idx_kkld_trang_thai', 'ke_khai_lanh_dao', ['trang_thai'])
    op.create_index('idx_kkld_nguoi_phe_duyet', 'ke_khai_lanh_dao', ['nguoi_phe_duyet_id'])
    op.create_index('idx_kkld_deleted', 'ke_khai_lanh_dao', ['is_deleted'])
    
    # Index composite cho query thường dùng
    op.create_index('idx_kkld_cc_thang_nam', 'ke_khai_lanh_dao', 
                    ['cong_chuc_id', 'thang', 'nam', 'is_deleted'])
    
    print("   ✅ Đã tạo bảng ke_khai_lanh_dao")
    
    # =========================================================================
    # BƯỚC 3: TẠO BẢNG danh_gia_dde
    # =========================================================================
    print("[Bước 3] Tạo bảng danh_gia_dde...")
    
    op.create_table(
        'danh_gia_dde',
        
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'),
                  nullable=False,
                  comment='Primary Key (UUID)'),
        
        # Foreign Key - Công chức (Lãnh đạo)
        sa.Column('cong_chuc_id', postgresql.UUID(as_uuid=True), nullable=False,
                  comment='FK → cong_chuc.id (người đánh giá - phải là Lãnh đạo)'),
        
        # Thời gian
        sa.Column('thang', sa.Integer(), nullable=False,
                  comment='Tháng đánh giá (1-12)'),
        sa.Column('nam', sa.Integer(), nullable=False,
                  comment='Năm đánh giá'),
        
        # =====================================================================
        # CHỈ SỐ d: KẾT QUẢ ĐƠN VỊ
        # 100% = Đơn vị hoàn thành nhiệm vụ
        # 50% = Đơn vị chưa hoàn thành
        # =====================================================================
        sa.Column('d_ket_qua_don_vi', sa.Integer(), nullable=False, server_default='100',
                  comment='d: Kết quả đơn vị (100 hoặc 50)'),
        sa.Column('d_ghi_chu', sa.Text(), nullable=True,
                  comment='Ghi chú cho chỉ số d'),
        
        # =====================================================================
        # CHỈ SỐ đ: TỔ CHỨC TRIỂN KHAI
        # 100% = Tổ chức triển khai tốt
        # 50% = Còn hạn chế
        # =====================================================================
        sa.Column('dd_to_chuc_trien_khai', sa.Integer(), nullable=False, server_default='100',
                  comment='đ: Tổ chức triển khai (100 hoặc 50)'),
        sa.Column('dd_ghi_chu', sa.Text(), nullable=True,
                  comment='Ghi chú cho chỉ số đ'),
        
        # =====================================================================
        # CHỈ SỐ e: ĐOÀN KẾT NỘI BỘ
        # 100% = Đoàn kết, không có mâu thuẫn
        # 50% = Có vấn đề nội bộ
        # =====================================================================
        sa.Column('e_doan_ket_noi_bo', sa.Integer(), nullable=False, server_default='100',
                  comment='e: Đoàn kết nội bộ (100 hoặc 50)'),
        sa.Column('e_ghi_chu', sa.Text(), nullable=True,
                  comment='Ghi chú cho chỉ số e'),
        
        # =====================================================================
        # PHÊ DUYỆT
        # =====================================================================
        sa.Column('trang_thai', sa.String(20), nullable=False, server_default='NHAP',
                  comment='Trạng thái: NHAP, CHO_PHE_DUYET, DA_PHE_DUYET'),
        sa.Column('nguoi_phe_duyet_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='FK → cong_chuc.id (người phê duyệt)'),
        sa.Column('y_kien_phe_duyet', sa.Text(), nullable=True,
                  comment='Ý kiến của người phê duyệt'),
        sa.Column('ngay_phe_duyet', sa.DateTime(timezone=True), nullable=True,
                  comment='Ngày phê duyệt'),
        
        # =====================================================================
        # GIÁ TRỊ SAU PHÊ DUYỆT (LĐ cấp trên có thể điều chỉnh)
        # =====================================================================
        sa.Column('d_phe_duyet', sa.Integer(), nullable=True,
                  comment='Giá trị d sau phê duyệt (nếu điều chỉnh)'),
        sa.Column('dd_phe_duyet', sa.Integer(), nullable=True,
                  comment='Giá trị đ sau phê duyệt (nếu điều chỉnh)'),
        sa.Column('e_phe_duyet', sa.Integer(), nullable=True,
                  comment='Giá trị e sau phê duyệt (nếu điều chỉnh)'),
        
        # =====================================================================
        # AUDIT
        # =====================================================================
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cong_chuc_id'], ['cong_chuc.id'],
                                name='fk_dde_cong_chuc', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['nguoi_phe_duyet_id'], ['cong_chuc.id'],
                                name='fk_dde_nguoi_phe_duyet', ondelete='SET NULL'),
        sa.UniqueConstraint('cong_chuc_id', 'thang', 'nam', name='uq_dde_user_month'),
        sa.CheckConstraint('thang BETWEEN 1 AND 12', name='ck_dde_thang'),
        sa.CheckConstraint('nam >= 2025', name='ck_dde_nam'),
        sa.CheckConstraint('d_ket_qua_don_vi IN (50, 100)', name='ck_dde_d'),
        sa.CheckConstraint('dd_to_chuc_trien_khai IN (50, 100)', name='ck_dde_dd'),
        sa.CheckConstraint('e_doan_ket_noi_bo IN (50, 100)', name='ck_dde_e'),
        sa.CheckConstraint(
            "trang_thai IN ('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET')",
            name='ck_dde_trang_thai'
        ),
        
        comment='Đánh giá d, đ, e của Lãnh đạo (năng lực lãnh đạo)'
    )
    
    # Indexes cho danh_gia_dde
    op.create_index('idx_dde_cong_chuc', 'danh_gia_dde', ['cong_chuc_id'])
    op.create_index('idx_dde_thang_nam', 'danh_gia_dde', ['thang', 'nam'])
    op.create_index('idx_dde_trang_thai', 'danh_gia_dde', ['trang_thai'])
    op.create_index('idx_dde_nguoi_phe_duyet', 'danh_gia_dde', ['nguoi_phe_duyet_id'])
    
    print("   ✅ Đã tạo bảng danh_gia_dde")
    
    # =========================================================================
    # HOÀN THÀNH
    # =========================================================================
    print("\n" + "=" * 60)
    print("✅ MIGRATION 005 HOÀN THÀNH!")
    print("=" * 60)
    print("Đã tạo:")
    print("  - Bảng ke_khai_lanh_dao (Kê khai công việc Lãnh đạo)")
    print("  - Bảng danh_gia_dde (Đánh giá d, đ, e)")
    print("  - ENUM trang_thai_hoan_thanh_enum")
    print("=" * 60 + "\n")


def downgrade() -> None:
    """
    Rollback: Xóa các bảng kê khai Lãnh đạo.
    """
    print("\n[Rollback] Xóa bảng kê khai Lãnh đạo...")
    
    # Xóa indexes của danh_gia_dde
    op.drop_index('idx_dde_nguoi_phe_duyet', table_name='danh_gia_dde')
    op.drop_index('idx_dde_trang_thai', table_name='danh_gia_dde')
    op.drop_index('idx_dde_thang_nam', table_name='danh_gia_dde')
    op.drop_index('idx_dde_cong_chuc', table_name='danh_gia_dde')
    
    # Xóa bảng danh_gia_dde
    op.drop_table('danh_gia_dde')
    
    # Xóa indexes của ke_khai_lanh_dao
    op.drop_index('idx_kkld_cc_thang_nam', table_name='ke_khai_lanh_dao')
    op.drop_index('idx_kkld_deleted', table_name='ke_khai_lanh_dao')
    op.drop_index('idx_kkld_nguoi_phe_duyet', table_name='ke_khai_lanh_dao')
    op.drop_index('idx_kkld_trang_thai', table_name='ke_khai_lanh_dao')
    op.drop_index('idx_kkld_thang_nam', table_name='ke_khai_lanh_dao')
    op.drop_index('idx_kkld_cong_chuc', table_name='ke_khai_lanh_dao')
    
    # Xóa bảng ke_khai_lanh_dao
    op.drop_table('ke_khai_lanh_dao')
    
    # Xóa ENUM
    op.execute("DROP TYPE IF EXISTS trang_thai_hoan_thanh_enum")
    
    print("✅ Rollback hoàn thành!")
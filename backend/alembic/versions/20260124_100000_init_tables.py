"""init_tables

Revision ID: 001_init_tables
Revises: 
Create Date: 2026-01-24

Migration đầu tiên - Tạo tất cả bảng cho hệ thống KPI Hải quan KV8.
Bao gồm:
- ENUM types
- Bảng tổ chức & nhân sự (don_vi, vai_tro, cong_chuc)
- Bảng danh mục công việc (sp_cong_viec_chuan, cap_do_phuc_tap, danh_muc_sp_cong_viec)
- Bảng kê khai & phê duyệt (ke_khai_cong_viec, phe_duyet_sp)
- Bảng đánh giá (danh_gia_thang, tieu_chi_chung_danh_gia, lanh_dao_chi_so)
- Bảng audit (audit_log)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_init_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Tạo tất cả ENUM types và bảng.
    """
    
    # =========================================================================
    # BƯỚC 1: TẠO ENUM TYPES
    # =========================================================================
    
    # Enum cho đơn vị
    loai_don_vi_enum = postgresql.ENUM(
        'LANH_DAO_CHI_CUC', 'PHONG', 'DOI', 'HAI_QUAN_CUA_KHAU',
        name='loai_don_vi_enum',
        create_type=True
    )
    loai_don_vi_enum.create(op.get_bind(), checkfirst=True)
    
    # Enum cho vai trò
    cap_bac_vai_tro_enum = postgresql.ENUM(
        'CHI_CUC_TRUONG', 'PHO_CHI_CUC_TRUONG', 'TRUONG_DON_VI', 
        'PHO_DON_VI', 'CONG_CHUC', 'TCCB',
        name='cap_bac_vai_tro_enum',
        create_type=True
    )
    cap_bac_vai_tro_enum.create(op.get_bind(), checkfirst=True)
    
    # Enum cho giới tính
    gioi_tinh_enum = postgresql.ENUM(
        'NAM', 'NU',
        name='gioi_tinh_enum',
        create_type=True
    )
    gioi_tinh_enum.create(op.get_bind(), checkfirst=True)
    
    # Enum cho trạng thái kê khai
    trang_thai_ke_khai_enum = postgresql.ENUM(
        'NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET', 'TU_CHOI', 'HUY',
        name='trang_thai_ke_khai_enum',
        create_type=True
    )
    trang_thai_ke_khai_enum.create(op.get_bind(), checkfirst=True)
    
    # Enum cho trạng thái phê duyệt
    trang_thai_phe_duyet_enum = postgresql.ENUM(
        'CHO_XU_LY', 'PHE_DUYET', 'TU_CHOI', 'YEU_CAU_SUA',
        name='trang_thai_phe_duyet_enum',
        create_type=True
    )
    trang_thai_phe_duyet_enum.create(op.get_bind(), checkfirst=True)
    
    # Enum cho mức xếp loại
    muc_xep_loai_enum = postgresql.ENUM(
        'A', 'B', 'C', 'D',
        name='muc_xep_loai_enum',
        create_type=True
    )
    muc_xep_loai_enum.create(op.get_bind(), checkfirst=True)
    
    # Enum cho trạng thái đánh giá
    trang_thai_danh_gia_enum = postgresql.ENUM(
        'DANG_DANH_GIA', 'CHO_TONG_HOP', 'DA_TONG_HOP', 
        'CHO_PHE_DUYET', 'HOAN_THANH', 'CO_KIEN_NGHI',
        name='trang_thai_danh_gia_enum',
        create_type=True
    )
    trang_thai_danh_gia_enum.create(op.get_bind(), checkfirst=True)
    
    # Enum cho audit action
    audit_action_enum = postgresql.ENUM(
        'INSERT', 'UPDATE', 'DELETE',
        name='audit_action_enum',
        create_type=True
    )
    audit_action_enum.create(op.get_bind(), checkfirst=True)
    
    # =========================================================================
    # BƯỚC 2: TẠO BẢNG TỔ CHỨC & NHÂN SỰ
    # =========================================================================
    
    # --- Bảng don_vi ---
    op.create_table(
        'don_vi',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ma_don_vi', sa.String(20), nullable=False),
        sa.Column('ten_don_vi', sa.String(200), nullable=False),
        sa.Column('ten_viet_tat', sa.String(50), nullable=True),
        sa.Column('loai_don_vi', postgresql.ENUM('LANH_DAO_CHI_CUC', 'PHONG', 'DOI', 'HAI_QUAN_CUA_KHAU', name='loai_don_vi_enum', create_type=False), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('thu_tu_hien_thi', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['don_vi.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ma_don_vi'),
        comment='Đơn vị (Phòng/Đội/HQCK) trong Chi cục'
    )
    op.create_index('idx_don_vi_ma', 'don_vi', ['ma_don_vi'], unique=False)
    op.create_index('idx_don_vi_active', 'don_vi', ['is_active'], unique=False, postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_don_vi_loai', 'don_vi', ['loai_don_vi'], unique=False)
    
    # --- Bảng vai_tro ---
    op.create_table(
        'vai_tro',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ma_vai_tro', sa.String(50), nullable=False),
        sa.Column('ten_vai_tro', sa.String(100), nullable=False),
        sa.Column('cap_bac', postgresql.ENUM('CHI_CUC_TRUONG', 'PHO_CHI_CUC_TRUONG', 'TRUONG_DON_VI', 'PHO_DON_VI', 'CONG_CHUC', 'TCCB', name='cap_bac_vai_tro_enum', create_type=False), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('is_lanh_dao', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('quyen_han', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ma_vai_tro'),
        comment='Vai trò trong hệ thống phân quyền'
    )
    op.create_index('idx_vai_tro_ma', 'vai_tro', ['ma_vai_tro'], unique=False)
    
    # --- Bảng cong_chuc ---
    op.create_table(
        'cong_chuc',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ma_cc', sa.String(20), nullable=False),
        sa.Column('ho_ten', sa.String(100), nullable=False),
        sa.Column('ngay_sinh', sa.Date(), nullable=True),
        sa.Column('gioi_tinh', postgresql.ENUM('NAM', 'NU', name='gioi_tinh_enum', create_type=False), nullable=True),
        sa.Column('so_dien_thoai', sa.String(20), nullable=True),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('don_vi_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vai_tro_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chuc_vu', sa.String(100), nullable=True),
        sa.Column('ngay_vao_nganh', sa.Date(), nullable=True),
        sa.Column('ngay_vao_chi_cuc', sa.Date(), nullable=True),
        sa.Column('is_lanh_dao', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('username', sa.String(50), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['don_vi_id'], ['don_vi.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['vai_tro_id'], ['vai_tro.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ma_cc'),
        sa.UniqueConstraint('username'),
        comment='Công chức Chi cục Hải quan KV8'
    )
    op.create_index('idx_cong_chuc_ma', 'cong_chuc', ['ma_cc'], unique=False)
    op.create_index('idx_cong_chuc_don_vi', 'cong_chuc', ['don_vi_id'], unique=False)
    op.create_index('idx_cong_chuc_vai_tro', 'cong_chuc', ['vai_tro_id'], unique=False)
    op.create_index('idx_cong_chuc_active', 'cong_chuc', ['is_active'], unique=False, postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_cong_chuc_lanh_dao', 'cong_chuc', ['is_lanh_dao'], unique=False, postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_cong_chuc_username', 'cong_chuc', ['username'], unique=False)
    
    # =========================================================================
    # BƯỚC 3: TẠO BẢNG DANH MỤC CÔNG VIỆC
    # =========================================================================
    
    # --- Bảng sp_cong_viec_chuan ---
    op.create_table(
        'sp_cong_viec_chuan',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ma_sp', sa.String(10), nullable=False),
        sa.Column('ten_sp', sa.String(200), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('thoi_gian_phut', sa.Integer(), nullable=False),
        sa.Column('he_so_quy_doi_sp1', sa.Numeric(10, 2), server_default='1', nullable=False),
        sa.Column('is_sp_goc', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ma_sp'),
        sa.CheckConstraint('thoi_gian_phut > 0', name='ck_sp_thoi_gian_positive'),
        sa.CheckConstraint('he_so_quy_doi_sp1 > 0', name='ck_sp_he_so_positive'),
        comment='Sản phẩm công việc chuẩn (SP1-SP4)'
    )
    op.create_index('idx_sp_chuan_ma', 'sp_cong_viec_chuan', ['ma_sp'], unique=False)
    
    # --- Bảng cap_do_phuc_tap ---
    op.create_table(
        'cap_do_phuc_tap',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ma_cap_do', sa.String(10), nullable=False),
        sa.Column('ten_cap_do', sa.String(100), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('he_so_sp1', sa.Numeric(10, 2), nullable=False),
        sa.Column('he_so_sp2', sa.Numeric(10, 2), nullable=False),
        sa.Column('is_theo_thuc_te', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('thu_tu', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ma_cap_do'),
        sa.CheckConstraint('thu_tu BETWEEN 1 AND 5', name='ck_cap_do_thu_tu'),
        sa.CheckConstraint('he_so_sp1 >= 0', name='ck_cap_do_he_so_sp1'),
        sa.CheckConstraint('he_so_sp2 >= 0', name='ck_cap_do_he_so_sp2'),
        comment='Cấp độ phức tạp công việc (C1-C5)'
    )
    op.create_index('idx_cap_do_ma', 'cap_do_phuc_tap', ['ma_cap_do'], unique=False)
    op.create_index('idx_cap_do_thu_tu', 'cap_do_phuc_tap', ['thu_tu'], unique=False)
    
    # --- Bảng danh_muc_sp_cong_viec ---
    op.create_table(
        'danh_muc_sp_cong_viec',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ma_danh_muc', sa.String(20), nullable=False),
        sa.Column('ten_cong_viec', sa.String(500), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('sp_chuan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('don_vi_ap_dung_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nhom_cong_viec', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sp_chuan_id'], ['sp_cong_viec_chuan.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['don_vi_ap_dung_id'], ['don_vi.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ma_danh_muc'),
        comment='Danh mục sản phẩm/công việc cụ thể của Chi cục'
    )
    op.create_index('idx_danh_muc_sp_ma', 'danh_muc_sp_cong_viec', ['ma_danh_muc'], unique=False)
    op.create_index('idx_danh_muc_sp_chuan', 'danh_muc_sp_cong_viec', ['sp_chuan_id'], unique=False)
    op.create_index('idx_danh_muc_don_vi', 'danh_muc_sp_cong_viec', ['don_vi_ap_dung_id'], unique=False)
    op.create_index('idx_danh_muc_nhom', 'danh_muc_sp_cong_viec', ['nhom_cong_viec'], unique=False)
    
    # =========================================================================
    # BƯỚC 4: TẠO BẢNG KÊ KHAI & PHÊ DUYỆT
    # =========================================================================
    
    # --- Bảng ke_khai_cong_viec ---
    op.create_table(
        'ke_khai_cong_viec',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('cong_chuc_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('thang', sa.Integer(), nullable=False),
        sa.Column('nam', sa.Integer(), nullable=False),
        sa.Column('ngay_thuc_hien', sa.Date(), nullable=True),
        sa.Column('danh_muc_sp_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cap_do_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('so_luong', sa.Integer(), server_default='1', nullable=False),
        sa.Column('he_so_thuc_te', sa.Numeric(10, 2), nullable=True),
        sa.Column('nguoi_phe_duyet_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mo_ta_cong_viec', sa.Text(), nullable=True),
        sa.Column('is_doi_moi_sang_tao', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ngay_deadline', sa.Date(), nullable=True),
        sa.Column('ngay_hoan_thanh', sa.Date(), nullable=True),
        sa.Column('trang_thai', postgresql.ENUM('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET', 'TU_CHOI', 'HUY', name='trang_thai_ke_khai_enum', create_type=False), server_default='NHAP', nullable=False),
        sa.Column('so_sp_goc_quy_doi', sa.Numeric(10, 2), nullable=True),
        sa.Column('so_sp_chat_luong', sa.Numeric(10, 2), nullable=True),
        sa.Column('so_sp_tien_do', sa.Numeric(10, 2), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cong_chuc_id'], ['cong_chuc.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['danh_muc_sp_id'], ['danh_muc_sp_cong_viec.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['cap_do_id'], ['cap_do_phuc_tap.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nguoi_phe_duyet_id'], ['cong_chuc.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cong_chuc_id', 'danh_muc_sp_id', 'cap_do_id', 'thang', 'nam', 'ngay_thuc_hien', name='uq_ke_khai_unique'),
        sa.CheckConstraint('thang BETWEEN 1 AND 12', name='ck_ke_khai_thang'),
        sa.CheckConstraint('nam >= 2025', name='ck_ke_khai_nam'),
        sa.CheckConstraint('so_luong > 0', name='ck_ke_khai_so_luong'),
        comment='Bản kê khai công việc của công chức'
    )
    op.create_index('idx_ke_khai_cc', 'ke_khai_cong_viec', ['cong_chuc_id'], unique=False)
    op.create_index('idx_ke_khai_thang_nam', 'ke_khai_cong_viec', ['thang', 'nam'], unique=False)
    op.create_index('idx_ke_khai_trang_thai', 'ke_khai_cong_viec', ['trang_thai'], unique=False)
    op.create_index('idx_ke_khai_phe_duyet', 'ke_khai_cong_viec', ['nguoi_phe_duyet_id'], unique=False)
    op.create_index('idx_ke_khai_cc_thang_nam', 'ke_khai_cong_viec', ['cong_chuc_id', 'thang', 'nam'], unique=False)
    
    # --- Bảng phe_duyet_sp ---
    op.create_table(
        'phe_duyet_sp',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ke_khai_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nguoi_phe_duyet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trang_thai', postgresql.ENUM('CHO_XU_LY', 'PHE_DUYET', 'TU_CHOI', 'YEU_CAU_SUA', name='trang_thai_phe_duyet_enum', create_type=False), nullable=False),
        sa.Column('lan_loi_chat_luong', sa.Integer(), server_default='0', nullable=False),
        sa.Column('lan_loi_tien_do', sa.Integer(), server_default='0', nullable=False),
        sa.Column('ghi_chu', sa.Text(), nullable=True),
        sa.Column('ly_do_tu_choi', sa.Text(), nullable=True),
        sa.Column('ngay_phe_duyet', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ke_khai_id'], ['ke_khai_cong_viec.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['nguoi_phe_duyet_id'], ['cong_chuc.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('lan_loi_chat_luong >= 0', name='ck_phe_duyet_loi_cl'),
        sa.CheckConstraint('lan_loi_tien_do >= 0', name='ck_phe_duyet_loi_td'),
        comment='Lịch sử phê duyệt sản phẩm'
    )
    op.create_index('idx_phe_duyet_ke_khai', 'phe_duyet_sp', ['ke_khai_id'], unique=False)
    op.create_index('idx_phe_duyet_nguoi', 'phe_duyet_sp', ['nguoi_phe_duyet_id'], unique=False)
    
    # =========================================================================
    # BƯỚC 5: TẠO BẢNG ĐÁNH GIÁ
    # =========================================================================
    
    # --- Bảng danh_gia_thang ---
    op.create_table(
        'danh_gia_thang',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('cong_chuc_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('thang', sa.Integer(), nullable=False),
        sa.Column('nam', sa.Integer(), nullable=False),
        sa.Column('so_sp_goc_duoc_giao', sa.Numeric(10, 2), nullable=True),
        sa.Column('so_ngay_lam_viec', sa.Integer(), nullable=True),
        sa.Column('so_ngay_nghi_phep', sa.Integer(), server_default='0', nullable=False),
        sa.Column('diem_tieu_chi_chung', sa.Numeric(5, 2), nullable=True),
        sa.Column('diem_kpi', sa.Numeric(5, 4), nullable=True),
        sa.Column('diem_so_luong', sa.Numeric(5, 4), nullable=True),
        sa.Column('diem_chat_luong', sa.Numeric(5, 4), nullable=True),
        sa.Column('diem_tien_do', sa.Numeric(5, 4), nullable=True),
        sa.Column('diem_tong', sa.Numeric(5, 2), nullable=True),
        sa.Column('muc_xep_loai_tu_dong', postgresql.ENUM('A', 'B', 'C', 'D', name='muc_xep_loai_enum', create_type=False), nullable=True),
        sa.Column('muc_xep_loai_de_xuat', postgresql.ENUM('A', 'B', 'C', 'D', name='muc_xep_loai_enum', create_type=False), nullable=True),
        sa.Column('muc_xep_loai_chinh_thuc', postgresql.ENUM('A', 'B', 'C', 'D', name='muc_xep_loai_enum', create_type=False), nullable=True),
        sa.Column('ly_do_dieu_chinh', sa.Text(), nullable=True),
        sa.Column('nguoi_de_xuat_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nguoi_phe_duyet_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('trang_thai', postgresql.ENUM('DANG_DANH_GIA', 'CHO_TONG_HOP', 'DA_TONG_HOP', 'CHO_PHE_DUYET', 'HOAN_THANH', 'CO_KIEN_NGHI', name='trang_thai_danh_gia_enum', create_type=False), server_default='DANG_DANH_GIA', nullable=False),
        sa.Column('ngay_tong_hop', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ngay_de_xuat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ngay_phe_duyet', sa.DateTime(timezone=True), nullable=True),
        sa.Column('uu_diem', sa.Text(), nullable=True),
        sa.Column('han_che', sa.Text(), nullable=True),
        sa.Column('ghi_chu', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cong_chuc_id'], ['cong_chuc.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nguoi_de_xuat_id'], ['cong_chuc.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['nguoi_phe_duyet_id'], ['cong_chuc.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cong_chuc_id', 'thang', 'nam', name='uq_danh_gia_cc_thang_nam'),
        sa.CheckConstraint('thang BETWEEN 1 AND 12', name='ck_danh_gia_thang'),
        sa.CheckConstraint('nam >= 2025', name='ck_danh_gia_nam'),
        sa.CheckConstraint('diem_tieu_chi_chung IS NULL OR diem_tieu_chi_chung BETWEEN 0 AND 30', name='ck_danh_gia_diem_tc'),
        sa.CheckConstraint('diem_kpi IS NULL OR diem_kpi BETWEEN 0 AND 1', name='ck_danh_gia_diem_kpi'),
        sa.CheckConstraint('diem_tong IS NULL OR diem_tong BETWEEN 0 AND 100', name='ck_danh_gia_diem_tong'),
        comment='Đánh giá tổng hợp tháng của công chức'
    )
    op.create_index('idx_danh_gia_cc', 'danh_gia_thang', ['cong_chuc_id'], unique=False)
    op.create_index('idx_danh_gia_thang_nam', 'danh_gia_thang', ['thang', 'nam'], unique=False)
    op.create_index('idx_danh_gia_trang_thai', 'danh_gia_thang', ['trang_thai'], unique=False)
    op.create_index('idx_danh_gia_xep_loai', 'danh_gia_thang', ['muc_xep_loai_chinh_thuc'], unique=False)
    
    # --- Bảng tieu_chi_chung_danh_gia ---
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
        sa.CheckConstraint('nhom_tieu_chi BETWEEN 1 AND 3', name='ck_tc_nhom'),
        comment='Chi tiết điểm tiêu chí chung (Nhóm I, II, III)'
    )
    op.create_index('idx_tc_chung_danh_gia', 'tieu_chi_chung_danh_gia', ['danh_gia_thang_id'], unique=False)
    
    # --- Bảng lanh_dao_chi_so ---
    op.create_table(
        'lanh_dao_chi_so',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('danh_gia_thang_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chi_so_d', sa.Numeric(5, 4), server_default='1.0', nullable=False),
        sa.Column('ghi_chu_d', sa.Text(), nullable=True),
        sa.Column('co_cc_khong_hoan_thanh', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('chi_so_dd', sa.Numeric(5, 4), server_default='1.0', nullable=False),
        sa.Column('ghi_chu_dd', sa.Text(), nullable=True),
        sa.Column('co_ton_tai_cham_tre', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('chi_so_e', sa.Numeric(5, 4), server_default='1.0', nullable=False),
        sa.Column('ghi_chu_e', sa.Text(), nullable=True),
        sa.Column('co_mau_thuan_noi_bo', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['danh_gia_thang_id'], ['danh_gia_thang.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('danh_gia_thang_id'),
        sa.CheckConstraint('chi_so_d IN (0.5, 1.0)', name='ck_ld_chi_so_d'),
        sa.CheckConstraint('chi_so_dd IN (0.5, 1.0)', name='ck_ld_chi_so_dd'),
        sa.CheckConstraint('chi_so_e IN (0.5, 1.0)', name='ck_ld_chi_so_e'),
        comment='Chỉ số d, đ, e cho lãnh đạo'
    )
    
    # =========================================================================
    # BƯỚC 6: TẠO BẢNG AUDIT LOG
    # =========================================================================
    
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', postgresql.ENUM('INSERT', 'UPDATE', 'DELETE', name='audit_action_enum', create_type=False), nullable=False),
        sa.Column('old_value', postgresql.JSONB(), nullable=True),
        sa.Column('new_value', postgresql.JSONB(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Audit log - ghi lại mọi thay đổi dữ liệu'
    )
    op.create_index('idx_audit_table_time', 'audit_log', ['table_name', 'created_at'], unique=False)
    op.create_index('idx_audit_user_time', 'audit_log', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_audit_record', 'audit_log', ['table_name', 'record_id'], unique=False)
    op.create_index('idx_audit_action', 'audit_log', ['action'], unique=False)
    
    # =========================================================================
    # BƯỚC 7: INSERT DỮ LIỆU SEED (VAI TRÒ & SP CHUẨN & CẤP ĐỘ)
    # =========================================================================
    
    # Insert vai trò mặc định
    op.execute("""
        INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro, cap_bac, is_lanh_dao, mo_ta) VALUES
        ('CCT', 'Chi cục trưởng', 'CHI_CUC_TRUONG', true, 'Lãnh đạo cao nhất Chi cục'),
        ('PCCT', 'Phó Chi cục trưởng', 'PHO_CHI_CUC_TRUONG', true, 'Phó lãnh đạo Chi cục'),
        ('TDV', 'Trưởng đơn vị', 'TRUONG_DON_VI', true, 'Trưởng phòng/Đội trưởng'),
        ('PDV', 'Phó đơn vị', 'PHO_DON_VI', true, 'Phó phòng/Phó Đội trưởng'),
        ('CC', 'Công chức', 'CONG_CHUC', false, 'Công chức thường'),
        ('TCCB', 'Cán bộ Tổ chức', 'TCCB', false, 'Cán bộ Phòng Tổ chức cán bộ')
    """)
    
    # Insert sản phẩm chuẩn
    op.execute("""
        INSERT INTO sp_cong_viec_chuan (ma_sp, ten_sp, thoi_gian_phut, he_so_quy_doi_sp1, is_sp_goc) VALUES
        ('SP1', 'Tờ khai HQ được kiểm tra chi tiết hồ sơ', 5, 1, true),
        ('SP2', 'Văn bản hành chính', 60, 12, false),
        ('SP3', 'Giờ trực làm việc', 60, 12, false),
        ('SP4', 'Giờ tuần tra kiểm soát', 60, 12, false)
    """)
    
    # Insert cấp độ phức tạp
    op.execute("""
        INSERT INTO cap_do_phuc_tap (ma_cap_do, ten_cap_do, he_so_sp1, he_so_sp2, thu_tu, is_theo_thuc_te) VALUES
        ('C1', 'Dễ - Đơn giản', 1, 1, 1, false),
        ('C2', 'Trung bình - Thông thường', 4, 2, 2, false),
        ('C3', 'Khó - Nâng cao', 12, 4, 3, false),
        ('C4', 'Rất khó - Phức tạp', 24, 8, 4, false),
        ('C5', 'Theo thực tế', 0, 0, 5, true)
    """)


def downgrade() -> None:
    """
    Xóa tất cả bảng và ENUM types.
    
    ⚠️ WARNING: Sẽ mất toàn bộ dữ liệu!
    Chỉ chạy khi chắc chắn muốn reset database.
    """
    
    # Xóa bảng theo thứ tự ngược (do foreign key constraints)
    op.drop_table('audit_log')
    op.drop_table('lanh_dao_chi_so')
    op.drop_table('tieu_chi_chung_danh_gia')
    op.drop_table('danh_gia_thang')
    op.drop_table('phe_duyet_sp')
    op.drop_table('ke_khai_cong_viec')
    op.drop_table('danh_muc_sp_cong_viec')
    op.drop_table('cap_do_phuc_tap')
    op.drop_table('sp_cong_viec_chuan')
    op.drop_table('cong_chuc')
    op.drop_table('vai_tro')
    op.drop_table('don_vi')
    
    # Xóa ENUM types
    op.execute('DROP TYPE IF EXISTS audit_action_enum')
    op.execute('DROP TYPE IF EXISTS trang_thai_danh_gia_enum')
    op.execute('DROP TYPE IF EXISTS muc_xep_loai_enum')
    op.execute('DROP TYPE IF EXISTS trang_thai_phe_duyet_enum')
    op.execute('DROP TYPE IF EXISTS trang_thai_ke_khai_enum')
    op.execute('DROP TYPE IF EXISTS gioi_tinh_enum')
    op.execute('DROP TYPE IF EXISTS cap_bac_vai_tro_enum')
    op.execute('DROP TYPE IF EXISTS loai_don_vi_enum')

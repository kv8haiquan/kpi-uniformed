"""xep_loai_moi - Hệ thống xếp loại mới

Revision ID: 006_xep_loai_moi
Revises: 20260128_001_bao_cao_xep_loai
Create Date: 2026-01-29

Migration cho hệ thống Xếp loại mới:
1. Thêm NGHI_TET vào enum LoaiNghi
2. Tạo bảng lich_su_dieu_chinh (lưu lịch sử chỉnh sửa của lãnh đạo)
3. Thêm cột is_khoa vào ke_khai_cong_viec, danh_gia_thang, dang_ky_nghi
4. Thêm phê duyệt 2 cấp cho nghỉ phép (Phó ĐT → ĐT)
5. Thêm phê duyệt 2 cấp cho tiêu chí chung (Phó ĐT → ĐT)

Luồng mới:
- Công việc: CC → Người giao việc (Phó/ĐT) duyệt
- Tiêu chí: CC tự chấm → Phó ĐT duyệt → ĐT duyệt lại
- Nghỉ phép: CC → Phó ĐT duyệt → ĐT duyệt
- Xếp loại: ĐT đề xuất → CCT duyệt → KHÓA DỮ LIỆU
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '006_xep_loai_moi'
down_revision: Union[str, None] = '20260128_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Thêm các cấu trúc mới cho hệ thống xếp loại.
    """
    
    # =========================================================================
    # BƯỚC 1: THÊM NGHI_TET VÀO ENUM LOAI_NGHI
    # =========================================================================
    print("[Migration] Bước 1: Thêm NGHI_TET vào enum loai_nghi_enum...")
    
    # Thêm giá trị mới vào enum (PostgreSQL)
    op.execute("ALTER TYPE loai_nghi_enum ADD VALUE IF NOT EXISTS 'NGHI_TET' AFTER 'NGHI_LE'")
    
    print("[Migration] ✓ Đã thêm NGHI_TET")
    
    # =========================================================================
    # BƯỚC 2: TẠO ENUM CHO BẢNG LỊCH SỬ ĐIỀU CHỈNH
    # =========================================================================
    print("[Migration] Bước 2: Tạo enum loai_doi_tuong_dieu_chinh...")
    
     # Tạo enum bằng raw SQL để tránh lỗi duplicate
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE loai_doi_tuong_dieu_chinh_enum AS ENUM (
                'KE_KHAI_CONG_VIEC',
                'TIEU_CHI_CHUNG', 
                'DANG_KY_NGHI',
                'DANH_GIA_THANG'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    print("[Migration] ✓ Đã tạo enum loai_doi_tuong_dieu_chinh_enum")
    
    # =========================================================================
    # BƯỚC 3: TẠO BẢNG LỊCH SỬ ĐIỀU CHỈNH
    # =========================================================================
    print("[Migration] Bước 3: Tạo bảng lich_su_dieu_chinh...")
    
    op.create_table(
        'lich_su_dieu_chinh',
        
        # Primary key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Đối tượng được điều chỉnh
        sa.Column(
            'loai_doi_tuong',
            sa.VARCHAR(50),
            nullable=False,
            comment='Loại đối tượng: KE_KHAI_CONG_VIEC, TIEU_CHI_CHUNG, DANG_KY_NGHI, DANH_GIA_THANG'
        ),
        sa.Column(
            'doi_tuong_id',
            UUID(as_uuid=True),
            nullable=False,
            comment='ID của đối tượng bị điều chỉnh'
        ),
        
        # Người điều chỉnh
        sa.Column(
            'nguoi_dieu_chinh_id',
            UUID(as_uuid=True),
            sa.ForeignKey('cong_chuc.id', ondelete='RESTRICT'),
            nullable=False,
            comment='ID người thực hiện điều chỉnh (Phó ĐT/ĐT)'
        ),
        
        # Chi tiết điều chỉnh
        sa.Column(
            'truong_du_lieu',
            sa.String(100),
            nullable=False,
            comment='Tên trường bị chỉnh: cap_do_id, so_loi_chat_luong, is_achieved, ...'
        ),
        sa.Column(
            'gia_tri_cu',
            sa.Text,
            nullable=True,
            comment='Giá trị cũ trước khi chỉnh'
        ),
        sa.Column(
            'gia_tri_moi',
            sa.Text,
            nullable=True,
            comment='Giá trị mới sau khi chỉnh'
        ),
        sa.Column(
            'ly_do',
            sa.Text,
            nullable=True,
            comment='Lý do điều chỉnh (bắt buộc nhập trên UI)'
        ),
        
        # Thời gian
        sa.Column(
            'ngay_dieu_chinh',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Thời điểm điều chỉnh'
        ),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Indexes
    op.create_index('idx_lich_su_doi_tuong', 'lich_su_dieu_chinh', ['loai_doi_tuong', 'doi_tuong_id'])
    op.create_index('idx_lich_su_nguoi', 'lich_su_dieu_chinh', ['nguoi_dieu_chinh_id'])
    op.create_index('idx_lich_su_ngay', 'lich_su_dieu_chinh', ['ngay_dieu_chinh'])
    
    print("[Migration] ✓ Đã tạo bảng lich_su_dieu_chinh với 3 indexes")
    
    # =========================================================================
    # BƯỚC 4: THÊM CỘT is_khoa VÀO CÁC BẢNG
    # =========================================================================
    print("[Migration] Bước 4: Thêm cột is_khoa vào các bảng...")
    
    # 4.1 ke_khai_cong_viec
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'is_khoa',
            sa.Boolean(),
            server_default='false',
            nullable=False,
            comment='Khóa dữ liệu sau khi CCT phê duyệt báo cáo xếp loại tháng'
        )
    )
    print("[Migration]   ✓ ke_khai_cong_viec.is_khoa")
    
    # 4.2 danh_gia_thang
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'is_khoa',
            sa.Boolean(),
            server_default='false',
            nullable=False,
            comment='Khóa dữ liệu sau khi CCT phê duyệt báo cáo xếp loại tháng'
        )
    )
    print("[Migration]   ✓ danh_gia_thang.is_khoa")
    
    # 4.3 dang_ky_nghi
    op.add_column(
        'dang_ky_nghi',
        sa.Column(
            'is_khoa',
            sa.Boolean(),
            server_default='false',
            nullable=False,
            comment='Khóa dữ liệu sau khi CCT phê duyệt báo cáo xếp loại tháng'
        )
    )
    print("[Migration]   ✓ dang_ky_nghi.is_khoa")
    
    # =========================================================================
    # BƯỚC 5: THÊM PHÊ DUYỆT 2 CẤP CHO NGHỈ PHÉP (dang_ky_nghi)
    # =========================================================================
    print("[Migration] Bước 5: Thêm phê duyệt 2 cấp cho nghỉ phép...")
    
    # Luồng mới: CC → Phó ĐT (cấp 1) → ĐT (cấp 2)
    # Cột cũ nguoi_phe_duyet_id = Phó ĐT (cấp 1)
    # Cột mới nguoi_phe_duyet_cap2_id = ĐT (cấp 2)
    
    # 5.1 Người phê duyệt cấp 2 (ĐT)
    op.add_column(
        'dang_ky_nghi',
        sa.Column(
            'nguoi_phe_duyet_cap2_id',
            UUID(as_uuid=True),
            sa.ForeignKey('cong_chuc.id', ondelete='SET NULL'),
            nullable=True,
            comment='ID Đội trưởng phê duyệt cấp 2'
        )
    )
    
    # 5.2 Trạng thái cấp 1 (Phó ĐT đã duyệt chưa)
    op.add_column(
        'dang_ky_nghi',
        sa.Column(
            'trang_thai_cap1',
            sa.Enum('CHO_PHE_DUYET', 'DA_PHE_DUYET', 'TU_CHOI', 'HUY',
                    name='trang_thai_nghi_enum', create_type=False),
            nullable=True,
            comment='Trạng thái phê duyệt cấp 1 (Phó ĐT)'
        )
    )
    
    # 5.3 Ngày phê duyệt cấp 1
    op.add_column(
        'dang_ky_nghi',
        sa.Column(
            'ngay_phe_duyet_cap1',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Thời điểm Phó ĐT phê duyệt cấp 1'
        )
    )
    
    # 5.4 Lý do từ chối cấp 1
    op.add_column(
        'dang_ky_nghi',
        sa.Column(
            'ly_do_tu_choi_cap1',
            sa.Text(),
            nullable=True,
            comment='Lý do Phó ĐT từ chối (nếu có)'
        )
    )
    
    # Index cho phê duyệt cấp 2
    op.create_index('idx_dang_ky_nghi_cap2', 'dang_ky_nghi', ['nguoi_phe_duyet_cap2_id'])
    
    print("[Migration] ✓ Đã thêm 4 cột phê duyệt 2 cấp cho dang_ky_nghi")
    
    # =========================================================================
    # BƯỚC 6: THÊM PHÊ DUYỆT 2 CẤP CHO TIÊU CHÍ CHUNG (danh_gia_thang)
    # =========================================================================
    print("[Migration] Bước 6: Thêm phê duyệt 2 cấp cho tiêu chí chung...")
    
    # Luồng: CC tự chấm → Phó ĐT duyệt (cấp 1) → ĐT duyệt lại (cấp 2)
    
    # 6.1 Người phê duyệt tiêu chí cấp 1 (Phó ĐT)
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'nguoi_phe_duyet_tc_cap1_id',
            UUID(as_uuid=True),
            sa.ForeignKey('cong_chuc.id', ondelete='SET NULL'),
            nullable=True,
            comment='ID Phó ĐT phê duyệt tiêu chí chung cấp 1'
        )
    )
    
    # 6.2 Người phê duyệt tiêu chí cấp 2 (ĐT)
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'nguoi_phe_duyet_tc_cap2_id',
            UUID(as_uuid=True),
            sa.ForeignKey('cong_chuc.id', ondelete='SET NULL'),
            nullable=True,
            comment='ID Đội trưởng phê duyệt tiêu chí chung cấp 2 (duyệt lại)'
        )
    )
    
    # 6.3 Trạng thái tiêu chí (riêng biệt với trạng thái đánh giá tổng)
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'trang_thai_tc',
            sa.Enum('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET',
                    name='trang_thai_tieu_chi_enum', create_type=False),
            server_default='NHAP',
            nullable=True,
            comment='Trạng thái phê duyệt tiêu chí chung: NHAP, CHO_PHE_DUYET, DA_PHE_DUYET'
        )
    )
    
    # 6.4 Ngày phê duyệt tiêu chí cấp 1
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'ngay_phe_duyet_tc_cap1',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Thời điểm Phó ĐT phê duyệt tiêu chí'
        )
    )
    
    # 6.5 Ngày phê duyệt tiêu chí cấp 2
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'ngay_phe_duyet_tc_cap2',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Thời điểm ĐT duyệt lại tiêu chí'
        )
    )
    
    # 6.6 Điểm tiêu chí do Phó ĐT chấm (có thể khác CC tự chấm)
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'diem_tc_cap1',
            sa.Numeric(5, 2),
            nullable=True,
            comment='Điểm tiêu chí chung sau khi Phó ĐT duyệt (0-30)'
        )
    )
    
    # 6.7 Điểm tiêu chí do ĐT chấm cuối cùng
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'diem_tc_cap2',
            sa.Numeric(5, 2),
            nullable=True,
            comment='Điểm tiêu chí chung sau khi ĐT duyệt lại (0-30) - Điểm cuối cùng'
        )
    )
    
    # Indexes
    op.create_index('idx_danh_gia_tc_cap1', 'danh_gia_thang', ['nguoi_phe_duyet_tc_cap1_id'])
    op.create_index('idx_danh_gia_tc_cap2', 'danh_gia_thang', ['nguoi_phe_duyet_tc_cap2_id'])
    op.create_index('idx_danh_gia_trang_thai_tc', 'danh_gia_thang', ['trang_thai_tc'])
    
    print("[Migration] ✓ Đã thêm 7 cột phê duyệt 2 cấp cho tiêu chí chung")
    
    # =========================================================================
    # HOÀN THÀNH
    # =========================================================================
    print("")
    print("=" * 60)
    print("[Migration] ✅ HOÀN THÀNH MIGRATION 006_xep_loai_moi")
    print("=" * 60)
    print("")
    print("Tóm tắt thay đổi:")
    print("  1. Enum NGHI_TET đã được thêm vào loai_nghi_enum")
    print("  2. Bảng lich_su_dieu_chinh đã được tạo")
    print("  3. Cột is_khoa đã thêm vào 3 bảng")
    print("  4. Phê duyệt 2 cấp cho nghỉ phép (4 cột mới)")
    print("  5. Phê duyệt 2 cấp cho tiêu chí chung (7 cột mới)")
    print("")


def downgrade() -> None:
    """
    Rollback - Xóa các cấu trúc mới.
    """
    print("[Migration] Bắt đầu rollback 006_xep_loai_moi...")
    
    # =========================================================================
    # BƯỚC 6: XÓA CỘT PHÊ DUYỆT TIÊU CHÍ CHUNG
    # =========================================================================
    op.drop_index('idx_danh_gia_trang_thai_tc', table_name='danh_gia_thang')
    op.drop_index('idx_danh_gia_tc_cap2', table_name='danh_gia_thang')
    op.drop_index('idx_danh_gia_tc_cap1', table_name='danh_gia_thang')
    
    op.drop_column('danh_gia_thang', 'diem_tc_cap2')
    op.drop_column('danh_gia_thang', 'diem_tc_cap1')
    op.drop_column('danh_gia_thang', 'ngay_phe_duyet_tc_cap2')
    op.drop_column('danh_gia_thang', 'ngay_phe_duyet_tc_cap1')
    op.drop_column('danh_gia_thang', 'trang_thai_tc')
    op.drop_column('danh_gia_thang', 'nguoi_phe_duyet_tc_cap2_id')
    op.drop_column('danh_gia_thang', 'nguoi_phe_duyet_tc_cap1_id')
    
    print("[Migration] ✓ Đã xóa cột phê duyệt tiêu chí chung")
    
    # =========================================================================
    # BƯỚC 5: XÓA CỘT PHÊ DUYỆT 2 CẤP NGHỈ PHÉP
    # =========================================================================
    op.drop_index('idx_dang_ky_nghi_cap2', table_name='dang_ky_nghi')
    
    op.drop_column('dang_ky_nghi', 'ly_do_tu_choi_cap1')
    op.drop_column('dang_ky_nghi', 'ngay_phe_duyet_cap1')
    op.drop_column('dang_ky_nghi', 'trang_thai_cap1')
    op.drop_column('dang_ky_nghi', 'nguoi_phe_duyet_cap2_id')
    
    print("[Migration] ✓ Đã xóa cột phê duyệt 2 cấp nghỉ phép")
    
    # =========================================================================
    # BƯỚC 4: XÓA CỘT is_khoa
    # =========================================================================
    op.drop_column('dang_ky_nghi', 'is_khoa')
    op.drop_column('danh_gia_thang', 'is_khoa')
    op.drop_column('ke_khai_cong_viec', 'is_khoa')
    
    print("[Migration] ✓ Đã xóa cột is_khoa")
    
    # =========================================================================
    # BƯỚC 3: XÓA BẢNG LỊCH SỬ ĐIỀU CHỈNH
    # =========================================================================
    op.drop_index('idx_lich_su_ngay', table_name='lich_su_dieu_chinh')
    op.drop_index('idx_lich_su_nguoi', table_name='lich_su_dieu_chinh')
    op.drop_index('idx_lich_su_doi_tuong', table_name='lich_su_dieu_chinh')
    op.drop_table('lich_su_dieu_chinh')
    
    print("[Migration] ✓ Đã xóa bảng lich_su_dieu_chinh")
    
    # =========================================================================
    # BƯỚC 2: XÓA ENUM
    # =========================================================================
    op.execute("DROP TYPE IF EXISTS loai_doi_tuong_dieu_chinh_enum")
    
    print("[Migration] ✓ Đã xóa enum loai_doi_tuong_dieu_chinh_enum")
    
    # =========================================================================
    # BƯỚC 1: KHÔNG THỂ XÓA GIÁ TRỊ ENUM TRONG POSTGRESQL
    # =========================================================================
    # PostgreSQL không hỗ trợ xóa giá trị enum đã thêm
    # NGHI_TET sẽ vẫn tồn tại nhưng không ảnh hưởng gì
    print("[Migration] ⚠ Không thể xóa NGHI_TET khỏi enum (PostgreSQL limitation)")
    
    print("")
    print("[Migration] ✅ Rollback hoàn thành")
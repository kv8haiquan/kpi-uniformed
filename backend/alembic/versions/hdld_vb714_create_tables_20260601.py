"""HĐLĐ 111 — Bộ tiêu chí đánh giá theo QĐ 714/QĐ-CHQ (08/5/2026)

Revision ID: hdld_vb714_20260601
Revises: portal_vd_anh_vi_tri_20260530
Create Date: 2026-06-01

Tạo 3 bảng phục vụ kê khai/đánh giá HĐLĐ 111 theo Bộ tiêu chí VB714:
  - hdld_tieu_chi            : danh mục 18 tiêu chí (6 nhóm nghề × 3 tiêu chí), seed sẵn
  - hdld_danh_gia           : header đánh giá theo tháng (1 bản/người/tháng)
  - hdld_danh_gia_chi_tiet  : 3 dòng chi tiết/header (2 cột: tự đánh giá + cấp quản lý)

Mô hình: mỗi tiêu chí thang 0-100. Điểm = TB 3 tiêu chí (cột cấp quản lý) → quy
về KPI-70 (× 70/100), cộng tiêu chí chung 30 như công chức → xếp loại A/B/C/D.
Áp dụng từ tháng 5/2026. Tháng ≤ 4/2026 giữ nguyên đọc ke_khai_lanh_dao cũ.

Luồng 1 cấp: NHAP → CHO_DUYET → DA_DUYET / TRA_LAI.
HĐLĐ tự chọn người duyệt (TDV/PDV cùng đơn vị).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'hdld_vb714_20260601'
down_revision = 'portal_vd_anh_vi_tri_20260530'
branch_labels = None
depends_on = None


# Tên 6 nhóm nghề theo VB714
TEN_NHOM = {
    'I': 'Nhân viên lái xe',
    'II': 'Nhân viên bảo vệ',
    'III': 'Nhân viên lễ tân, phục vụ',
    'IV': 'Nhân viên tạp vụ',
    'V': 'Nhân viên bảo trì, bảo dưỡng, vận hành trụ sở, trang thiết bị, máy móc (nhân viên kỹ thuật)',
    'VI': 'Nhân viên hợp đồng lao động làm các công việc khác',
}

# 18 tiêu chí — trích nguyên văn từ QĐ 714/QĐ-CHQ. (nhom, so_tt, ten_tieu_chi, mo_ta_chi_tiet)
TIEU_CHI = [
    # I — Lái xe
    ('I', 1, 'Chất lượng công việc',
     'Đảm bảo yêu cầu công việc, nhiệm vụ công tác: '
     '- Lái xe đưa đón lãnh đạo, công chức đảm bảo đúng giờ, đúng địa điểm; '
     '- Vận chuyển tài liệu, hàng hóa, trang thiết bị của cơ quan đảm bảo bí mật '
     '(đối với tài liệu) đúng địa điểm, đúng thời gian từ nơi đi đến nơi đến.'),
    ('I', 2, 'Tuân thủ quy định, quy trình',
     '- Tác phong làm việc chuyên nghiệp, lịch sự; '
     '- Chấp hành tuyệt đối sự điều động của Thủ trưởng cơ quan; không sử dụng xe công vào mục đích riêng; '
     '- Tuân thủ quy định quản lý, sử dụng tài sản công, có trách nhiệm bảo quản, bảo dưỡng xe định kỳ; '
     '- Tuân thủ pháp luật về an toàn giao thông, không sử dụng các chất kích thích khi làm nhiệm vụ; '
     'đảm bảo an toàn về người, tài sản, phương tiện khi tham gia giao thông; xử lý tốt các sự cố '
     'phát sinh trong quá trình sử dụng, khai thác phương tiện.'),
    ('I', 3, 'Hiệu quả công việc',
     '- Điều khiển phương tiện an toàn; đảm bảo an toàn cho người, tài sản và phương tiện khi tham gia giao thông; '
     '- Đảm bảo phương tiện luôn sạch sẽ; thường xuyên kiểm tra vệ sinh, bảo dưỡng định kỳ đúng quy trình. '
     'Sử dụng vật tư, thiết bị và nhiên liệu hiệu quả, tiết kiệm.'),
    # II — Bảo vệ
    ('II', 1, 'Chất lượng công việc',
     '- Đảm bảo an ninh trật tự khu vực trụ sở 24/7; kiểm soát chặt chẽ người, phương tiện, tài sản ra vào cơ quan; '
     '- Hướng dẫn khách đến liên hệ công tác đúng quy định, lịch sự, chuẩn mực.'),
    ('II', 2, 'Tuân thủ quy định, quy trình',
     '- Thực hiện nghiêm nội quy cơ quan, quy trình ca trực; bàn giao ca trực rõ ràng, đầy đủ; '
     '- Tuân thủ tuyệt đối các quy định về phòng cháy chữa cháy (PCCC); '
     '- Tuân thủ quy định về trang phục, phù hiệu, biển hiệu (nếu có); không tự ý rời vị trí khi đang làm '
     'nhiệm vụ mà chưa được phép của cấp trên; '
     '- Kiểm soát người, phương tiện ra vào cơ quan theo quy định; '
     '- Tuyệt đối không tiếp khách tại nơi làm việc.'),
    ('II', 3, 'Hiệu quả công việc',
     '- Đảm bảo an toàn về tài sản, không để xảy ra mất mát, hư hỏng tài sản do nguyên nhân chủ quan; '
     '- Phát hiện, báo cáo và phối hợp xử lý kịp thời các tình huống khẩn cấp, bất thường theo nhiệm vụ được phân công.'),
    # III — Lễ tân, phục vụ
    ('III', 1, 'Chất lượng công việc',
     '- Tiếp đón, hướng dẫn khách đến liên hệ công tác chuyên nghiệp, lịch sự; '
     '- Tiếp nhận, chuyển nối thông tin chính xác các cuộc điện thoại đến đúng đơn vị khách hàng cần liên hệ; '
     '- Quản lý khu vực lễ tân sạch sẽ, ngăn nắp.'),
    ('III', 2, 'Tuân thủ quy định, quy trình',
     '- Tuân thủ quy chế văn hóa công sở; '
     '- Tuân thủ quy trình an ninh và quy định của cơ quan; '
     '- Nắm vững nghiệp vụ đón khách, hướng dẫn khách với thái độ thân thiện, tôn trọng; '
     '- Sử dụng trang phục theo quy định.'),
    ('III', 3, 'Hiệu quả công việc',
     '- Đảm bảo khu vực sảnh lễ tân, bàn lễ tân luôn gọn gàng, sạch đẹp, ngăn nắp, thể hiện bộ mặt chuyên nghiệp của cơ quan; '
     '- Cập nhật và luân chuyển thông tin nhanh chóng, không để sót việc.'),
    # IV — Tạp vụ
    ('IV', 1, 'Chất lượng công việc',
     'Hoàn thành nhiệm vụ vệ sinh, đảm bảo sạch sẽ, ngăn nắp trong khuôn viên cơ quan, đơn vị; '
     'không để xảy ra tình trạng ô nhiễm, mất vệ sinh trong khu vực được phân công.'),
    ('IV', 2, 'Tuân thủ quy định, quy trình',
     '- Tuân thủ quy trình an toàn lao động, vệ sinh môi trường, công sở; nội quy, quy chế cơ quan (nếu có); '
     'tuân thủ kỷ luật lao động; '
     '- Chấp hành nghiêm sự phân công, điều động của người có thẩm quyền; '
     '- Tuyệt đối không sử dụng hóa chất tẩy rửa gây độc hại.'),
    ('IV', 3, 'Hiệu quả công việc',
     '- Thực hiện đúng công việc được giao, bảo đảm thời gian và chất lượng; '
     '- Đảm bảo hậu cần cho các cuộc họp, hội nghị và tiếp khách (sắp xếp bàn ghế, chuẩn bị trà nước, ..); '
     'đảm bảo vệ sinh phòng họp, khu vực làm việc (sảnh, hành lang,…); cảnh quan (sân vườn nếu có), nhà vệ sinh; '
     'thu gom, xử lý rác thải đúng quy định; '
     '- Bảo quản, sử dụng vật tư tiêu hao (giấy, hoá chất tẩy rửa...), điện, nước đúng mục đích, tiết kiệm; '
     '- Kịp thời phát hiện và báo cáo các hỏng hóc về cơ sở vật chất, kịp thời báo cáo người có thẩm quyền giải quyết.'),
    # V — Kỹ thuật
    ('V', 1, 'Chất lượng công việc',
     'Theo dõi, vận hành, kiểm tra theo định kỳ hệ thống điện, nước, máy phát điện, điều hòa, thang máy. '
     'Trực tiếp sửa chữa hoặc giám sát nhà thầu khắc phục các sự cố kỹ thuật, đảm bảo hệ thống vận hành '
     'toà nhà, các trang thiết bị hoạt động tốt.'),
    ('V', 2, 'Tuân thủ quy định, quy trình',
     'Tuân thủ nghiêm ngặt quy trình kỹ thuật, khuyến cáo của nhà sản xuất và quy định về an toàn lao động, PCCC. '
     'Ghi chép nhật ký vận hành, bảo trì định kỳ đầy đủ.'),
    ('V', 3, 'Hiệu quả công việc',
     'Đảm bảo hạ tầng kỹ thuật hoạt động ổn định, liên tục. Đề xuất kịp thời kế hoạch bảo trì, thay thế '
     'vật tư hợp lý, hiệu quả và tối ưu hóa chi phí cho cơ quan.'),
    # VI — Công việc khác
    ('VI', 1, 'Chất lượng công việc',
     '- Công việc được phân công; '
     '- Chất lượng, tiến độ của công việc được giao.'),
    ('VI', 2, 'Tuân thủ quy định, quy trình',
     '- Việc chấp hành quy định, văn bản phân công công việc của cơ quan đối với người lao động; '
     '- Việc tuân thủ quy định, quy trình nhiệm vụ của nhiệm vụ được giao đảm nhiệm.'),
    ('VI', 3, 'Hiệu quả công việc',
     '- Hiệu quả công việc đảm bảo chất lượng theo yêu cầu nhiệm vụ được giao.'),
]


def upgrade():
    # ------------------------------------------------------------------ #
    # 1) hdld_tieu_chi — danh mục tiêu chí cố định theo VB714
    # ------------------------------------------------------------------ #
    op.create_table(
        'hdld_tieu_chi',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('nhom', sa.String(5), nullable=False, comment='Nhóm nghề I..VI'),
        sa.Column('ten_nhom', sa.String(200), nullable=False, comment='Tên nhóm nghề'),
        sa.Column('so_tt', sa.Integer(), nullable=False, comment='Số thứ tự tiêu chí 1..3'),
        sa.Column('ten_tieu_chi', sa.String(200), nullable=False),
        sa.Column('mo_ta_chi_tiet', sa.Text(), nullable=False),
        sa.Column('diem_toi_da', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.UniqueConstraint('nhom', 'so_tt', name='uq_hdld_tieu_chi_nhom_sott'),
        sa.CheckConstraint("nhom IN ('I','II','III','IV','V','VI')", name='ck_hdld_tieu_chi_nhom'),
        sa.CheckConstraint('so_tt >= 1 AND so_tt <= 3', name='ck_hdld_tieu_chi_sott'),
    )

    # ------------------------------------------------------------------ #
    # 2) hdld_danh_gia — header đánh giá theo tháng
    # ------------------------------------------------------------------ #
    op.create_table(
        'hdld_danh_gia',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('cong_chuc_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('thang', sa.Integer(), nullable=False),
        sa.Column('nam', sa.Integer(), nullable=False),
        sa.Column('nhom_nghe', sa.String(5), nullable=True, comment='Nhóm nghề I..VI do HĐLĐ tự chọn'),
        sa.Column('trang_thai', sa.String(50), nullable=False, server_default='NHAP',
                  comment='NHAP | CHO_DUYET | DA_DUYET | TRA_LAI'),
        sa.Column('nguoi_duyet_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('public.cong_chuc.id'), nullable=True,
                  comment='Người duyệt HĐLĐ tự chọn (TDV/PDV cùng đơn vị)'),
        sa.Column('diem_tc_tb_tu', sa.Numeric(6, 2), nullable=True,
                  comment='TB 3 tiêu chí cột Tự đánh giá (0-100), để đối chiếu'),
        sa.Column('diem_tc_tb_ql', sa.Numeric(6, 2), nullable=True,
                  comment='TB 3 tiêu chí cột Cấp quản lý (0-100), điểm chính thức'),
        sa.Column('diem_kpi_70', sa.Numeric(6, 2), nullable=True,
                  comment='= diem_tc_tb_ql / 100 * 70'),
        sa.Column('ghi_chu', sa.Text(), nullable=True),
        sa.Column('ly_do_tra_lai', sa.Text(), nullable=True),
        sa.Column('ngay_nop', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('ngay_duyet', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.UniqueConstraint('cong_chuc_id', 'thang', 'nam', name='uq_hdld_danh_gia_cc_thang_nam'),
        sa.CheckConstraint('thang >= 1 AND thang <= 12', name='ck_hdld_danh_gia_thang'),
        sa.CheckConstraint('nam >= 2020 AND nam <= 2100', name='ck_hdld_danh_gia_nam'),
        sa.CheckConstraint("nhom_nghe IS NULL OR nhom_nghe IN ('I','II','III','IV','V','VI')",
                           name='ck_hdld_danh_gia_nhom'),
    )
    op.create_index('idx_hdld_danh_gia_thang_nam', 'hdld_danh_gia', ['thang', 'nam'])
    op.create_index('idx_hdld_danh_gia_trang_thai', 'hdld_danh_gia', ['trang_thai'])
    op.create_index('idx_hdld_danh_gia_nguoi_duyet', 'hdld_danh_gia', ['nguoi_duyet_id'])

    # ------------------------------------------------------------------ #
    # 3) hdld_danh_gia_chi_tiet — 3 dòng/header (2 cột điểm)
    # ------------------------------------------------------------------ #
    op.create_table(
        'hdld_danh_gia_chi_tiet',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('danh_gia_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('hdld_danh_gia.id', ondelete='CASCADE'), nullable=False),
        sa.Column('so_tt', sa.Integer(), nullable=False, comment='1..3 khớp hdld_tieu_chi.so_tt'),
        sa.Column('diem_tu', sa.Numeric(5, 2), nullable=True, comment='Tự đánh giá 0-100'),
        sa.Column('ghi_chu_tu', sa.Text(), nullable=True, comment='Bắt buộc nếu diem_tu < 100'),
        sa.Column('diem_ql', sa.Numeric(5, 2), nullable=True, comment='Cấp quản lý đánh giá 0-100'),
        sa.Column('ghi_chu_ql', sa.Text(), nullable=True),
        sa.Column('ly_do_sua', sa.Text(), nullable=True,
                  comment='Bắt buộc nếu cấp quản lý sửa khác điểm tự chấm'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.UniqueConstraint('danh_gia_id', 'so_tt', name='uq_hdld_ct_danhgia_sott'),
        sa.CheckConstraint('so_tt >= 1 AND so_tt <= 3', name='ck_hdld_ct_sott'),
        sa.CheckConstraint('diem_tu IS NULL OR (diem_tu >= 0 AND diem_tu <= 100)', name='ck_hdld_ct_diem_tu'),
        sa.CheckConstraint('diem_ql IS NULL OR (diem_ql >= 0 AND diem_ql <= 100)', name='ck_hdld_ct_diem_ql'),
    )

    # ------------------------------------------------------------------ #
    # 4) Seed 18 tiêu chí VB714
    # ------------------------------------------------------------------ #
    tieu_chi_tbl = sa.table(
        'hdld_tieu_chi',
        sa.column('nhom', sa.String),
        sa.column('ten_nhom', sa.String),
        sa.column('so_tt', sa.Integer),
        sa.column('ten_tieu_chi', sa.String),
        sa.column('mo_ta_chi_tiet', sa.Text),
    )
    op.bulk_insert(tieu_chi_tbl, [
        {
            'nhom': nhom,
            'ten_nhom': TEN_NHOM[nhom],
            'so_tt': so_tt,
            'ten_tieu_chi': ten,
            'mo_ta_chi_tiet': mo_ta,
        }
        for (nhom, so_tt, ten, mo_ta) in TIEU_CHI
    ])


def downgrade():
    op.drop_table('hdld_danh_gia_chi_tiet')
    op.drop_index('idx_hdld_danh_gia_nguoi_duyet', table_name='hdld_danh_gia')
    op.drop_index('idx_hdld_danh_gia_trang_thai', table_name='hdld_danh_gia')
    op.drop_index('idx_hdld_danh_gia_thang_nam', table_name='hdld_danh_gia')
    op.drop_table('hdld_danh_gia')
    op.drop_table('hdld_tieu_chi')

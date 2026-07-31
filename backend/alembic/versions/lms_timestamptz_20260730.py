"""LMS: chuyen toan bo cot datetime schema lms sang TIMESTAMPTZ (gio VN chuan)

Boi canh: du lieu cu tron 2 convention trong cung schema:
- Cot do backend ghi bang datetime.utcnow()  -> gia tri la gio UTC naive
- Cot do FE gui (input datetime-local) hoac default CURRENT_TIMESTAMP
  (Postgres timezone = Asia/Ho_Chi_Minh)      -> gia tri la gio VN naive

Migration nay convert TUNG COT theo dung convention goc cua no de instant
khong doi, sau do moi cot deu la TIMESTAMPTZ.

Luu y updated_at: default CURRENT_TIMESTAMP ghi gio VN nhung service code cu
ghi de bang utcnow() (UTC) -> du lieu tron trong cung cot. Chon convert theo
VN; cac row tung duoc update se lech toi da 7h — chap nhan vi chi la cot audit.

Revision ID: lms_timestamptz_20260730
Revises: lsdc_loai_20260717
Create Date: 2026-07-30
"""
from alembic import op

revision = "lms_timestamptz_20260730"
down_revision = "lsdc_loai_20260717"
branch_labels = None
depends_on = None

VN = "Asia/Ho_Chi_Minh"
UTC = "UTC"

# (bang, cot, mui gio goc cua du lieu hien tai)
COLUMNS = [
    # --- ky_thi ---
    ("ky_thi", "ngay_bat_dau", VN),   # FE datetime-local (gio VN naive)
    ("ky_thi", "ngay_ket_thuc", VN),  # FE datetime-local
    ("ky_thi", "ngay_duyet", UTC),    # utcnow()
    ("ky_thi", "created_at", VN),     # CURRENT_TIMESTAMP (server tz VN)
    ("ky_thi", "updated_at", VN),
    # --- thi_sinh ---
    ("thi_sinh", "thoi_gian_bat_dau", UTC),  # utcnow()
    ("thi_sinh", "thoi_gian_nop", UTC),      # utcnow()
    ("thi_sinh", "created_at", VN),
    ("thi_sinh", "updated_at", VN),
    # --- phien_thi ---
    ("phien_thi", "last_seen", UTC),  # utcnow() (heartbeat)
    ("phien_thi", "created_at", VN),
    # --- dang_ky_khoa_hoc ---
    ("dang_ky_khoa_hoc", "ngay_phe_duyet", UTC),    # utcnow()
    ("dang_ky_khoa_hoc", "ngay_bat_dau_hoc", UTC),  # utcnow() (bai_hoc_service)
    ("dang_ky_khoa_hoc", "ngay_hoan_thanh", UTC),   # utcnow()
    ("dang_ky_khoa_hoc", "created_at", VN),
    ("dang_ky_khoa_hoc", "updated_at", VN),
    # --- ket_qua_bai_kiem_tra ---
    ("ket_qua_bai_kiem_tra", "ngay_lam", UTC),
    ("ket_qua_bai_kiem_tra", "ngay_nop", UTC),
    ("ket_qua_bai_kiem_tra", "ngay_cham", UTC),
    # --- khoa_hoc ---
    ("khoa_hoc", "ngay_duyet", UTC),
    ("khoa_hoc", "created_at", VN),
    ("khoa_hoc", "updated_at", VN),
    # --- tien_do_bai_hoc ---
    ("tien_do_bai_hoc", "lan_xem_cuoi", UTC),
    ("tien_do_bai_hoc", "ngay_hoan_thanh", UTC),
    # --- chung_chi ---
    ("chung_chi", "ngay_cap", UTC),  # utcnow()
    # --- cac bang chi co created_at/updated_at (CURRENT_TIMESTAMP) ---
    ("bai_hoc", "created_at", VN),
    ("bai_kiem_tra", "created_at", VN),
    ("cau_hoi", "created_at", VN),
    ("cau_hoi_dgnl", "created_at", VN),
    ("cau_hoi_dgnl", "updated_at", VN),
    ("cau_truc_de", "created_at", VN),
    ("chuyen_de", "created_at", VN),
    ("khao_sat", "created_at", VN),
    ("linh_vuc", "created_at", VN),
    ("linh_vuc", "updated_at", VN),
    ("vi_tri_viec_lam", "created_at", VN),
    ("vi_tri_viec_lam", "updated_at", VN),
]


def upgrade() -> None:
    for table, col, tz in COLUMNS:
        op.execute(
            f'ALTER TABLE lms.{table} '
            f'ALTER COLUMN {col} TYPE TIMESTAMPTZ '
            f"USING {col} AT TIME ZONE '{tz}'"
        )
    # server_default CURRENT_TIMESTAMP giu nguyen: voi TIMESTAMPTZ luon la instant dung.


def downgrade() -> None:
    # Quay ve TIMESTAMP naive theo dung convention cu (mat thong tin offset).
    for table, col, tz in COLUMNS:
        op.execute(
            f'ALTER TABLE lms.{table} '
            f'ALTER COLUMN {col} TYPE TIMESTAMP '
            f"USING {col} AT TIME ZONE '{tz}'"
        )

"""Kết nối cơ sở dữ liệu và tiện ích dùng chung cho script di trú.

An toàn: mặc định chạy trên `kpi_haiquan_test`. Muốn chạy trên prod phải đặt
CẢ HAI biến môi trường `DB_NAME=kpi_haiquan` và `CHO_PHEP_PROD=toi_dong_y`.
Theo CLAUDE.md, ghi vào prod phải có người duyệt từng lần (giai đoạn G6.1).
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from pathlib import Path

import psycopg2
import psycopg2.extras

BACKEND = Path(__file__).resolve().parents[2]
DB_TEST = "kpi_haiquan_test"
DB_PROD = "kpi_haiquan"


def _doc_env() -> dict[str, str]:
    env: dict[str, str] = {}
    f = BACKEND / ".env"
    if f.exists():
        for dong in f.read_text(encoding="utf8").splitlines():
            dong = dong.strip()
            if dong and not dong.startswith("#") and "=" in dong:
                k, v = dong.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def ket_noi(tu_dong_commit: bool = False):
    env = _doc_env()
    ten_db = os.getenv("DB_NAME", DB_TEST)

    if ten_db == DB_PROD and os.getenv("CHO_PHEP_PROD") != "toi_dong_y":
        sys.exit(
            "⛔ Từ chối ghi vào production.\n"
            "   Script này mặc định chạy trên kpi_haiquan_test.\n"
            "   Muốn chạy trên prod (giai đoạn G6.1, phải có người duyệt):\n"
            "     DB_NAME=kpi_haiquan CHO_PHEP_PROD=toi_dong_y python <script>.py"
        )

    conn = psycopg2.connect(
        host=env.get("DB_HOST", "localhost"),
        port=env.get("DB_PORT", "5432"),
        user=env.get("DB_USER", "kpi_user"),
        password=env.get("DB_PASSWORD", ""),
        dbname=ten_db,
    )
    conn.autocommit = tu_dong_commit
    print(f"→ Kết nối {ten_db}", flush=True)
    return conn


# ── chuẩn hoá tên để khớp công chức ────────────────────────────────────────

# Tiền tố xưng hô. Dữ liệu thật có cả 'Đ/c', 'Đc', 'đ/c' — chấp nhận mọi biến thể.
_CHUC_DANH = re.compile(r"^\s*(đ\s*/?\s*c|ông|bà)\b[\s.]*", re.IGNORECASE)

# Ngăn cách giữa họ tên và chức danh. Dữ liệu thật dùng cả ba kiểu:
#   'Nguyễn Cảnh Thắng - Phó CCT'      dấu gạch có khoảng trắng
#   'Phạm Quốc Hưng- Chi cục trưởng'   dấu gạch dính tên
#   'Ngô Tùng Dương, Phó Chi cục trưởng' dấu phẩy
_NGAN_CACH = re.compile(r"\s*[-–,]\s*")


def bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def chuan_ten(s: str) -> str:
    """Chuẩn hoá để so khớp: bỏ dấu, thường hoá, gộp khoảng trắng."""
    return re.sub(r"\s+", " ", bo_dau(s or "")).strip().lower()


def tach_ho_ten(token: str) -> str:
    """Bỏ tiền tố xưng hô và phần chức danh, còn lại họ tên.

    'Đ/c Nguyễn Cảnh Thắng - Phó CCT'      → 'Nguyễn Cảnh Thắng'
    'Đ/c Phạm Quốc Hưng- Chi cục trưởng'   → 'Phạm Quốc Hưng'
    'Đc Ngô Tùng Dương, Phó CCT'           → 'Ngô Tùng Dương'
    """
    t = _CHUC_DANH.sub("", (token or "").strip())
    t = _NGAN_CACH.split(t)[0]
    return re.sub(r"\s+", " ", t).strip()


class BangTraCongChuc:
    """Tra công chức theo họ tên đã chuẩn hoá.

    Tên trùng nhau thì KHÔNG khớp — thà để trống còn hơn gán nhầm người.
    """

    def __init__(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, ma_cc, ho_ten FROM public.cong_chuc WHERE is_active")
            rows = cur.fetchall()
        theo_ten: dict[str, list] = {}
        self.theo_ma: dict[str, str] = {}
        for _id, ma_cc, ho_ten in rows:
            theo_ten.setdefault(chuan_ten(ho_ten), []).append(_id)
            self.theo_ma[(ma_cc or "").strip().upper()] = _id
        self.theo_ten = {k: v[0] for k, v in theo_ten.items() if len(v) == 1}
        self.trung_ten = {k for k, v in theo_ten.items() if len(v) > 1}
        self.tong = len(rows)

        # username lichkv8 → công chức, nạp qua nap_username()
        self.theo_username: dict[str, str] = {}

    def tim(self, ten: str):
        return self.theo_ten.get(chuan_ten(tach_ho_ten(ten)))

    def tim_theo_ma(self, ma_cc: str):
        return self.theo_ma.get((ma_cc or "").strip().upper())

    def tim_theo_username(self, username: str):
        return self.theo_username.get((username or "").strip().lower())

    def nap_username(self, xlsx) -> tuple[int, int]:
        """Nạp ánh xạ USERNAME → công chức từ sheet USER của lichkv8.

        Các cột NGUOI_TAO / NGUOI_SUA / UPLOADED_BY của lichkv8 lưu USERNAME
        ('vanntt1990', 'hattt'), không phải mã công chức. Sheet USER có cả hai:
        USER_ID chính là ma_cc (547/548 dòng), USERNAME là tên đăng nhập.
        """
        from doc_sheet import doc_bang

        idx, rows = doc_bang(xlsx, "USER", "USER_ID")
        khop = 0
        for r in rows:
            username = (r.get(idx["USERNAME"], "") or "").strip().lower()
            ma_cc = (r.get(idx["USER_ID"], "") or "").strip()
            if not username or not ma_cc:
                continue
            cc_id = self.tim_theo_ma(ma_cc)
            if cc_id:
                self.theo_username[username] = cc_id
                khop += 1
        return khop, len(rows)


def lay_id_don_vi(conn) -> dict[str, str]:
    with conn.cursor() as cur:
        cur.execute("SELECT ma_don_vi, id FROM public.don_vi")
        return {ma: _id for ma, _id in cur.fetchall()}


def lay_tai_khoan_he_thong(conn) -> str:
    """Tài khoản gán cho created_by khi bản ghi gốc ghi 'import'.

    272/489 dòng MEETING có NGUOI_TAO='import' — không phải người thật.
    Dùng tài khoản quản trị sẵn có thay vì tạo mới (public là chỉ đọc).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM public.cong_chuc WHERE ma_cc = 'ADMIN-001' LIMIT 1")
        row = cur.fetchone()
    if not row:
        sys.exit("⛔ Không tìm thấy tài khoản hệ thống ADMIN-001")
    return row[0]


# ── truy vết di trú ────────────────────────────────────────────────────────

def ghi_nguon(cur, bang_nguon: str, khoa_nguon: str, bang_dich: str,
              id_dich, drive_file_id: str | None = None,
              ghi_chu: str | None = None) -> None:
    """Ghi ánh xạ bản ghi cũ → mới. Chạy lại script không nhân đôi."""
    cur.execute("""
        INSERT INTO meeting.di_tru_nguon
            (bang_nguon, khoa_nguon, bang_dich, id_dich, drive_file_id, ghi_chu)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (bang_nguon, khoa_nguon) DO UPDATE
            SET id_dich = EXCLUDED.id_dich,
                drive_file_id = EXCLUDED.drive_file_id,
                ghi_chu = EXCLUDED.ghi_chu
    """, (bang_nguon, khoa_nguon, bang_dich, id_dich, drive_file_id, ghi_chu))


def da_di_tru(cur, bang_nguon: str) -> dict[str, str]:
    cur.execute(
        "SELECT khoa_nguon, id_dich FROM meeting.di_tru_nguon "
        "WHERE bang_nguon = %s", (bang_nguon,))
    return {k: v for k, v in cur.fetchall()}

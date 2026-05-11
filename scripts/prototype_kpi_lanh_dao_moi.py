#!/usr/bin/env python3
"""
Prototype tính KPI lãnh đạo theo CÔNG THỨC MỚI (file Phuong phap tinh KPI cho lanh dao.docx).

CHỈ ĐỌC — không sửa DB.

Công thức MỚI:
- PDV  = SP tự kê + SP CC do PDV trực tiếp duyệt
- TDV  = toàn bộ SP của CC trong đơn vị + SP các PDV trong đơn vị tự kê + SP TDV tự kê
- PCCT = gộp toàn bộ SP của các TDV phụ trách (raw, không lấy KPI)
- CCT  = gộp SP của các PCCT phụ trách + SP các TDV trực tiếp phụ trách

Tổng điểm KPI = (a + b + c + d + đ + e) / 6
- a = số CV hoàn thành / tổng CV
- b = (Σ max(0, 1 - so_loi_tien_do × 0.25)) / tổng CV
- c = (Σ max(0, 1 - so_loi_chat_luong × 0.25)) / tổng CV
- d, đ, e: từ danh_gia_dde (final / 100), thiếu → mặc định 1.0

Công thức CŨ (để so sánh) = chỉ tính scope = CV LĐ tự kê (ke_khai_lanh_dao).

⚠️ PHÂN CÔNG PHỤ TRÁCH HIỆN CHƯA CÓ TRONG DB → tạm hardcode bên dưới.
   Cần Chi cục trưởng xác nhận lại trước khi áp dụng thật.
"""

import os
import sys
from collections import defaultdict
from decimal import Decimal

import psycopg2
import psycopg2.extras

DB_CONFIG = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    dbname=os.getenv("DB_NAME", "kpi_haiquan"),
    user=os.getenv("DB_USER", "kpi_user"),
    password=os.getenv("DB_PASSWORD", "KpiHaiQuan2026!"),
)

THANG = int(os.getenv("THANG", "4"))
NAM = int(os.getenv("NAM", "2026"))

# =============================================================================
# PHÂN CÔNG PHỤ TRÁCH (TẠM — CẦN USER XÁC NHẬN)
# =============================================================================
# Mỗi đơn vị (TDV) tại 1 thời điểm chỉ thuộc đúng 1 người (PCCT hoặc CCT).
PHAN_CONG = {
    # PCCT 1 - Bùi Ngọc Lợi
    "20ZZ-0565": ["VP", "TCCB", "NVHQ", "QLRR"],
    # PCCT 2 - Ngô Tùng Dương
    "20ZZ-0119": ["CNTT", "PTSTQ", "KSHQ"],
    # PCCT 3 - Nguyễn Cảnh Thắng
    "20ZZ-0479": ["HQCK-MC", "HQCK-HM", "HQCK-BPS"],
    # CCT - Phạm Quốc Hưng (trực tiếp phụ trách)
    "20ZZ-0224": ["HQCK-HG", "HQCK-CP", "HQCK-VG"],
}


def diem_loi(so_loi: int) -> float:
    """Điểm 1 CV theo số lỗi (CL hoặc TĐ): max(0, 1 - lỗi × 0.25)."""
    if so_loi is None or so_loi < 0:
        return 1.0
    return max(0.0, 1.0 - so_loi * 0.25)


def chia_an_toan(tu: float, mau: float, default: float = 0.0) -> float:
    return tu / mau if mau and mau > 0 else default


def calc_abc(rows):
    """Trả về (tong_cv, hoan_thanh, a, b, c) với rows là list dict có
       'hoan_thanh', 'so_loi_chat_luong', 'so_loi_tien_do'."""
    n = len(rows)
    if n == 0:
        return 0, 0, 0.0, 0.0, 0.0
    ht = sum(1 for r in rows if r["hoan_thanh"])
    sum_td = sum(diem_loi(r["so_loi_tien_do"]) for r in rows)
    sum_cl = sum(diem_loi(r["so_loi_chat_luong"]) for r in rows)
    return n, ht, ht / n, sum_td / n, sum_cl / n


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_session(readonly=True)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # -------------------------------------------------------------------------
    # 1) TẢI DỮ LIỆU CƠ BẢN
    # -------------------------------------------------------------------------

    # Đơn vị
    cur.execute("""
        SELECT id, ma_don_vi, ten_don_vi
        FROM don_vi WHERE is_active=true AND is_deleted=false
    """)
    don_vi_by_id = {r["id"]: r for r in cur.fetchall()}
    don_vi_by_ma = {r["ma_don_vi"]: r for r in don_vi_by_id.values()}

    # Lãnh đạo
    cur.execute("""
        SELECT c.id, c.ma_cc, c.ho_ten, c.chuc_vu, c.don_vi_id, v.ma_vai_tro, v.cap_bac::text AS cap_bac
        FROM cong_chuc c JOIN vai_tro v ON v.id = c.vai_tro_id
        WHERE v.cap_bac IN ('CHI_CUC_TRUONG','PHO_CHI_CUC_TRUONG','TRUONG_DON_VI','PHO_DON_VI')
          AND c.is_active=true AND c.is_deleted=false
    """)
    leaders = list(cur.fetchall())
    leader_by_ma = {l["ma_cc"]: l for l in leaders}
    leader_by_id = {l["id"]: l for l in leaders}

    # CV của CC (ke_khai_cong_viec) DA_PHE_DUYET tháng-năm
    cur.execute("""
        SELECT k.id, k.cong_chuc_id, k.nguoi_phe_duyet_id, k.so_luong,
               k.so_loi_chat_luong, k.so_loi_tien_do,
               TRUE AS hoan_thanh,
               cc.don_vi_id, cc.ma_cc, cc.ho_ten,
               v.cap_bac::text AS cap_bac_nguoi_kk
        FROM ke_khai_cong_viec k
        JOIN cong_chuc cc ON cc.id = k.cong_chuc_id
        JOIN vai_tro v ON v.id = cc.vai_tro_id
        WHERE k.thang=%s AND k.nam=%s AND k.is_deleted=false AND k.trang_thai='DA_PHE_DUYET'
    """, (THANG, NAM))
    cv_cc = list(cur.fetchall())

    # Index CV CC theo đơn vị + theo người duyệt
    cv_by_donvi = defaultdict(list)
    cv_by_nguoiduyet = defaultdict(list)
    for r in cv_cc:
        cv_by_donvi[r["don_vi_id"]].append(r)
        if r["nguoi_phe_duyet_id"]:
            cv_by_nguoiduyet[r["nguoi_phe_duyet_id"]].append(r)

    # CV của LĐ tự kê (ke_khai_lanh_dao) DA_PHE_DUYET
    cur.execute("""
        SELECT k.id, k.cong_chuc_id, k.so_loi_chat_luong, k.so_loi_tien_do,
               (k.trang_thai_hoan_thanh = 'DA_HOAN_THANH') AS hoan_thanh,
               cc.don_vi_id
        FROM ke_khai_lanh_dao k
        JOIN cong_chuc cc ON cc.id = k.cong_chuc_id
        WHERE k.thang=%s AND k.nam=%s AND k.is_deleted=false AND k.trang_thai='DA_PHE_DUYET'
    """, (THANG, NAM))
    cv_ld_self = list(cur.fetchall())
    cv_ld_by_user = defaultdict(list)
    cv_ld_by_donvi = defaultdict(list)
    for r in cv_ld_self:
        cv_ld_by_user[r["cong_chuc_id"]].append(r)
        cv_ld_by_donvi[r["don_vi_id"]].append(r)

    # d, đ, e đã duyệt
    cur.execute("""
        SELECT cong_chuc_id,
               COALESCE(d_phe_duyet, d_ket_qua_don_vi) AS d_val,
               COALESCE(dd_phe_duyet, dd_to_chuc_trien_khai) AS dd_val,
               COALESCE(e_phe_duyet, e_doan_ket_noi_bo) AS e_val
        FROM danh_gia_dde
        WHERE thang=%s AND nam=%s AND trang_thai='DA_PHE_DUYET'
    """, (THANG, NAM))
    dde_by_user = {r["cong_chuc_id"]: r for r in cur.fetchall()}

    # -------------------------------------------------------------------------
    # 2) HÀM TÍNH KPI
    # -------------------------------------------------------------------------

    def get_dde(user_id):
        d = dde_by_user.get(user_id)
        if not d:
            return 1.0, 1.0, 1.0
        return d["d_val"] / 100.0, d["dd_val"] / 100.0, d["e_val"] / 100.0

    def kpi_tu_scope(rows, user_id):
        n, ht, a, b, c = calc_abc(rows)
        d, dd, e = get_dde(user_id)
        kpi = (a + b + c + d + dd + e) / 6 if n > 0 else (d + dd + e) / 6
        return {
            "tong_cv": n,
            "hoan_thanh": ht,
            "a": a, "b": b, "c": c,
            "d": d, "dd": dd, "e": e,
            "kpi": kpi,
        }

    def scope_cu(user_id):
        """Cách CŨ: chỉ CV LĐ tự kê."""
        return cv_ld_by_user.get(user_id, [])

    def scope_pdv(user_id):
        return cv_ld_by_user.get(user_id, []) + cv_by_nguoiduyet.get(user_id, [])

    def scope_donvi(don_vi_id):
        """Toàn bộ CV của đơn vị: CV của CC + CV LĐ thuộc đơn vị tự kê."""
        return cv_by_donvi.get(don_vi_id, []) + cv_ld_by_donvi.get(don_vi_id, [])

    def scope_tdv(user_id):
        leader = leader_by_id[user_id]
        return scope_donvi(leader["don_vi_id"])

    def scope_pcct_or_cct(ma_cc):
        """Gộp CV của tất cả đơn vị mà LĐ này phụ trách."""
        ma_dv_list = PHAN_CONG.get(ma_cc, [])
        rows = []
        for ma_dv in ma_dv_list:
            dv = don_vi_by_ma.get(ma_dv)
            if not dv:
                continue
            rows.extend(scope_donvi(dv["id"]))
        return rows

    # -------------------------------------------------------------------------
    # 3) TÍNH CHO TỪNG LĐ
    # -------------------------------------------------------------------------

    print(f"Tháng {THANG}/{NAM} — So sánh KPI lãnh đạo: cũ vs mới\n")
    print(f"⚠️  Phân công PCCT/CCT đang HARDCODE (cần xác nhận):")
    for ma, dvs in PHAN_CONG.items():
        l = leader_by_ma.get(ma)
        if l:
            print(f"   - {ma} {l['ho_ten']:30s} → {', '.join(dvs)}")
    print()

    # CSV header
    rows_out = []
    rows_out.append([
        "cap_bac", "ma_cc", "ho_ten", "don_vi_or_phu_trach",
        "cv_cu", "kpi_cu",
        "cv_moi", "ht_moi", "a", "b", "c", "d", "dd", "e", "kpi_moi",
        "delta_kpi"
    ])

    cap_bac_order = {
        "CHI_CUC_TRUONG": 1,
        "PHO_CHI_CUC_TRUONG": 2,
        "TRUONG_DON_VI": 3,
        "PHO_DON_VI": 4,
    }
    leaders.sort(key=lambda x: (cap_bac_order.get(x["cap_bac"], 99), x["ho_ten"]))

    for l in leaders:
        cap = l["cap_bac"]
        ma = l["ma_cc"]
        uid = l["id"]
        ho_ten = l["ho_ten"]
        dv = don_vi_by_id.get(l["don_vi_id"])
        ten_dv = dv["ma_don_vi"] if dv else "?"

        # Cũ
        cu = kpi_tu_scope(scope_cu(uid), uid)

        # Mới
        if cap == "PHO_DON_VI":
            scope = scope_pdv(uid)
            mota_dv = ten_dv
        elif cap == "TRUONG_DON_VI":
            scope = scope_tdv(uid)
            mota_dv = ten_dv
        elif cap == "PHO_CHI_CUC_TRUONG":
            scope = scope_pcct_or_cct(ma)
            mota_dv = "+".join(PHAN_CONG.get(ma, []))
        elif cap == "CHI_CUC_TRUONG":
            # Tổng SP CCT = SP các PCCT phụ trách + SP TDV mình trực tiếp phụ trách
            # = TOÀN BỘ 13 đơn vị có TDV (vì 3 PCCT + CCT đã phủ hết)
            # Ngoài ra theo spec, CCT cũng cộng "SP của các PCCT" — nhưng SP của PCCT đã
            # = SP các đơn vị PCCT phụ trách → đã nằm trong tổng các đơn vị → KHÔNG CỘNG LẠI
            scope = []
            for ma_pcct, ds in PHAN_CONG.items():
                for ma_dv in ds:
                    d2 = don_vi_by_ma.get(ma_dv)
                    if d2:
                        scope.extend(scope_donvi(d2["id"]))
            mota_dv = "TOÀN CHI CỤC"
        else:
            scope = scope_cu(uid)
            mota_dv = ten_dv

        moi = kpi_tu_scope(scope, uid)
        delta = moi["kpi"] - cu["kpi"]

        rows_out.append([
            cap,
            ma,
            ho_ten,
            mota_dv,
            cu["tong_cv"],
            f"{cu['kpi']:.4f}",
            moi["tong_cv"],
            moi["hoan_thanh"],
            f"{moi['a']:.4f}",
            f"{moi['b']:.4f}",
            f"{moi['c']:.4f}",
            f"{moi['d']:.4f}",
            f"{moi['dd']:.4f}",
            f"{moi['e']:.4f}",
            f"{moi['kpi']:.4f}",
            f"{delta:+.4f}",
        ])

    # -------------------------------------------------------------------------
    # 4) IN BẢNG
    # -------------------------------------------------------------------------

    widths = [max(len(str(r[i])) for r in rows_out) for i in range(len(rows_out[0]))]
    for ri, r in enumerate(rows_out):
        line = "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r))
        print(line)
        if ri == 0:
            print("-" * len(line))

    # CSV cho file
    out_csv = f"/tmp/kpi_ld_so_sanh_{NAM}_{THANG:02d}.csv"
    import csv
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(rows_out)
    print(f"\n→ CSV: {out_csv}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()

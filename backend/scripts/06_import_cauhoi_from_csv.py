"""
Script doc 5 file CSV va gan cau hoi vao dung bai kiem tra.
- Match cau hoi trong DB theo noi_dung (LIKE)
- Neu chua co trong DB → tao moi
- Cap nhat bai_kiem_tra_id + tao junction record

Chay: cd /root/kpi-haiquan/backend && python scripts/06_import_cauhoi_from_csv.py
"""

import csv
import os
import sys
import uuid

import psycopg2

# ===========================================================================
# CONFIG
# ===========================================================================

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "kpi_haiquan")
DB_USER = os.getenv("DB_USER", "kpi_user")
DB_PASS = os.getenv("DB_PASSWORD", "")

# Doc password tu .env neu co
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("DB_PASSWORD=") or line.startswith("DATABASE_PASSWORD="):
                DB_PASS = line.split("=", 1)[1].strip().strip('"').strip("'")

# Khoa hoc THONG TU 121
KHOA_HOC_ID = "0b224977-5c20-4501-9896-15a1cc1fa47e"

# Mapping: ten file CSV → bai_kiem_tra_id
CSV_BKT_MAP = {
    "Giám Sát Hải Quan.csv": "4b413315-5854-4b7f-b775-bec9c5f78b4e",
    "Hàng Gia Công.csv": "a68e86e7-aaf1-437a-aacb-3f53dd9c049d",
    "Kiểm Tra Sau Thông Quan.csv": "4291ae46-0e80-4691-9afa-bdc582135cf1",
    "Quản Lý Thuế.csv": "8a34df8f-0e02-49aa-b6e8-c72c28637f08",
    "Thủ Tục Hải Quan.csv": "1b11b83d-8c37-4d55-bdd7-191ce3c2818e",
}

# Folder chua file CSV (root project)
CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "..")

# Nguoi tao mac dinh (admin/system)
# Lay tu user dau tien co vai_tro SUPER_ADMIN
NGUOI_TAO_ID = None


def build_dap_an(loai, a, b, c, d, dung):
    """Xay dung JSONB dap_an tu cac cot CSV."""
    import json
    options = [a, b, c, d]
    options = [o for o in options if o.strip()]

    if loai == "TRAC_NGHIEM_1":
        # dung = "A", "B", "C", "D" hoac "A hoặc B..."
        dung = dung.strip().upper()
        if len(dung) == 1 and dung in "ABCD":
            correct_idx = ord(dung) - ord("A")
        else:
            correct_idx = 0
        return json.dumps({"options": options, "correct": correct_idx})

    elif loai == "TRAC_NGHIEM_NHIEU":
        dung = dung.strip().upper()
        correct_indices = [ord(c) - ord("A") for c in dung if c in "ABCD"]
        return json.dumps({"options": options, "correct": correct_indices})

    elif loai == "DUNG_SAI":
        dung = dung.strip().upper()
        return json.dumps({"correct": dung in ("A", "DUNG", "TRUE")})

    elif loai == "TU_LUAN":
        return json.dumps({"goi_y": dung.strip()})

    return json.dumps({})


def main():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS,
    )
    conn.autocommit = False
    cur = conn.cursor()

    # Lay nguoi_tao_id
    cur.execute("SELECT id FROM public.cong_chuc WHERE ma_cc = '20ZZ-0001' LIMIT 1")
    row = cur.fetchone()
    if row:
        nguoi_tao_id = str(row[0])
    else:
        cur.execute("SELECT id FROM public.cong_chuc LIMIT 1")
        row = cur.fetchone()
        nguoi_tao_id = str(row[0]) if row else None

    print(f"Nguoi tao ID: {nguoi_tao_id}")
    print(f"Khoa hoc ID: {KHOA_HOC_ID}")
    print("=" * 60)

    total_matched = 0
    total_created = 0
    total_linked = 0

    for csv_name, bkt_id in CSV_BKT_MAP.items():
        csv_path = os.path.join(CSV_DIR, csv_name)
        if not os.path.exists(csv_path):
            print(f"SKIP: Khong tim thay {csv_path}")
            continue

        # Lay ten bai kiem tra
        cur.execute("SELECT tieu_de FROM lms.bai_kiem_tra WHERE id = %s", (bkt_id,))
        bkt_row = cur.fetchone()
        bkt_ten = bkt_row[0] if bkt_row else "?"
        print(f"\n--- {bkt_ten} (bkt_id={bkt_id}) ---")
        print(f"    File: {csv_name}")

        # Doc CSV
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"    So cau trong CSV: {len(rows)}")

        thu_tu_offset_r = cur.execute(
            "SELECT COALESCE(MAX(thu_tu), 0) FROM lms.bai_kiem_tra_cau_hoi WHERE bai_kiem_tra_id = %s",
            (bkt_id,)
        )
        cur.execute(
            "SELECT COALESCE(MAX(thu_tu), 0) FROM lms.bai_kiem_tra_cau_hoi WHERE bai_kiem_tra_id = %s",
            (bkt_id,)
        )
        max_thu_tu = cur.fetchone()[0] or 0

        for idx, row in enumerate(rows):
            noi_dung = row.get("noi_dung", "").strip()
            if not noi_dung:
                continue

            loai = row.get("loai", "TRAC_NGHIEM_1").strip()
            do_kho = row.get("do_kho", "TRUNG_BINH").strip()
            diem = float(row.get("diem", "1.0") or "1.0")
            giai_thich = row.get("giai_thich", "").strip() or None
            dap_an_a = row.get("dap_an_a", "").strip()
            dap_an_b = row.get("dap_an_b", "").strip()
            dap_an_c = row.get("dap_an_c", "").strip()
            dap_an_d = row.get("dap_an_d", "").strip()
            dap_an_dung = row.get("dap_an_dung", "").strip()

            dap_an_json = build_dap_an(loai, dap_an_a, dap_an_b, dap_an_c, dap_an_d, dap_an_dung)

            # Tim cau hoi trong DB theo noi_dung (first 80 chars match)
            search_text = noi_dung[:80]
            cur.execute(
                """SELECT id, bai_kiem_tra_id FROM lms.cau_hoi
                   WHERE LEFT(noi_dung, 80) = LEFT(%s, 80)
                     AND khoa_hoc_id = %s
                     AND is_active = true
                   LIMIT 1""",
                (search_text, KHOA_HOC_ID)
            )
            existing = cur.fetchone()

            if existing:
                cau_hoi_id = str(existing[0])
                old_bkt_id = existing[1]

                # Cap nhat bai_kiem_tra_id
                cur.execute(
                    "UPDATE lms.cau_hoi SET bai_kiem_tra_id = %s, dap_an = %s::jsonb, giai_thich = %s WHERE id = %s",
                    (bkt_id, dap_an_json, giai_thich, cau_hoi_id)
                )
                total_matched += 1
                action = "MATCHED"
            else:
                # Tao cau hoi moi
                cau_hoi_id = str(uuid.uuid4())
                cur.execute(
                    """INSERT INTO lms.cau_hoi
                       (id, khoa_hoc_id, bai_kiem_tra_id, noi_dung, loai, do_kho, diem, dap_an, giai_thich, nguoi_tao_id, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, true)""",
                    (cau_hoi_id, KHOA_HOC_ID, bkt_id, noi_dung, loai, do_kho, diem, dap_an_json, giai_thich, nguoi_tao_id)
                )
                total_created += 1
                action = "CREATED"

            # Tao junction record (neu chua co)
            cur.execute(
                """SELECT 1 FROM lms.bai_kiem_tra_cau_hoi
                   WHERE bai_kiem_tra_id = %s AND cau_hoi_id = %s""",
                (bkt_id, cau_hoi_id)
            )
            if not cur.fetchone():
                max_thu_tu += 1
                cur.execute(
                    "INSERT INTO lms.bai_kiem_tra_cau_hoi (bai_kiem_tra_id, cau_hoi_id, thu_tu) VALUES (%s, %s, %s)",
                    (bkt_id, cau_hoi_id, max_thu_tu)
                )
                total_linked += 1

            print(f"    [{action}] {noi_dung[:60]}...")

        # Cap nhat so_cau_hoi
        cur.execute(
            """UPDATE lms.bai_kiem_tra SET so_cau_hoi = (
                 SELECT COUNT(*) FROM lms.bai_kiem_tra_cau_hoi WHERE bai_kiem_tra_id = %s
               ) WHERE id = %s""",
            (bkt_id, bkt_id)
        )

    # Xu ly 2 khoa hoc con lai (1 bai KT moi khoa, gan het cau hoi chua gan)
    print("\n" + "=" * 60)
    print("Xu ly 2 khoa hoc con lai (1 bai KT / khoa)...")

    other_courses = [
        ("8d88e2d0-4e31-4a5a-acf8-f43ec42d2399", "69114bb2-e10e-4ab9-8ae9-1ea045d2648a", "NGHI DINH 167"),
        ("cdee01b7-83db-4ef5-afce-3d6b17ff0688", "ad0049d2-4753-4f6d-9302-f039e0e9fe08", "Tieng Trung"),
    ]

    for kh_id, bkt_id, label in other_courses:
        # Cap nhat bai_kiem_tra_id
        cur.execute(
            """UPDATE lms.cau_hoi SET bai_kiem_tra_id = %s
               WHERE khoa_hoc_id = %s AND bai_kiem_tra_id IS NULL AND is_active = true""",
            (bkt_id, kh_id)
        )
        updated = cur.rowcount
        print(f"  [{label}] Cap nhat bai_kiem_tra_id: {updated} cau")

        # Tao junction records
        cur.execute(
            """INSERT INTO lms.bai_kiem_tra_cau_hoi (bai_kiem_tra_id, cau_hoi_id, thu_tu)
               SELECT %s, ch.id, ROW_NUMBER() OVER (ORDER BY ch.created_at ASC)
               FROM lms.cau_hoi ch
               WHERE ch.khoa_hoc_id = %s AND ch.bai_kiem_tra_id = %s AND ch.is_active = true
                 AND NOT EXISTS (
                   SELECT 1 FROM lms.bai_kiem_tra_cau_hoi l
                   WHERE l.bai_kiem_tra_id = %s AND l.cau_hoi_id = ch.id
                 )""",
            (bkt_id, kh_id, bkt_id, bkt_id)
        )
        linked = cur.rowcount
        total_linked += linked
        print(f"  [{label}] Junction records: {linked}")

        # Cap nhat so_cau_hoi
        cur.execute(
            """UPDATE lms.bai_kiem_tra SET so_cau_hoi = (
                 SELECT COUNT(*) FROM lms.bai_kiem_tra_cau_hoi WHERE bai_kiem_tra_id = %s
               ) WHERE id = %s""",
            (bkt_id, bkt_id)
        )

    # Kiem tra con cau nao chua gan khong
    cur.execute(
        "SELECT COUNT(*) FROM lms.cau_hoi WHERE is_active = true AND bai_kiem_tra_id IS NULL"
    )
    con_chua_gan = cur.fetchone()[0]

    # Ket qua cuoi
    print("\n" + "=" * 60)
    print("KET QUA:")
    print(f"  Matched (da co trong DB): {total_matched}")
    print(f"  Created (tao moi):        {total_created}")
    print(f"  Junction links tao moi:   {total_linked}")
    print(f"  Cau hoi con chua gan:     {con_chua_gan}")

    # In bang tong hop
    print("\nBANG TONG HOP:")
    cur.execute("""
        SELECT kh.ten_khoa_hoc, bkt.tieu_de, bkt.so_cau_hoi,
               (SELECT COUNT(*) FROM lms.bai_kiem_tra_cau_hoi WHERE bai_kiem_tra_id = bkt.id) AS links
        FROM lms.khoa_hoc kh
        JOIN lms.bai_kiem_tra bkt ON bkt.khoa_hoc_id = kh.id AND bkt.is_active = true
        WHERE kh.is_active = true
        ORDER BY kh.ten_khoa_hoc, bkt.tieu_de
    """)
    print(f"  {'Khoa hoc':<35} {'Bai KT':<30} {'So cau':>6} {'Links':>6}")
    print(f"  {'-'*35} {'-'*30} {'-'*6} {'-'*6}")
    for r in cur.fetchall():
        print(f"  {str(r[0])[:35]:<35} {str(r[1])[:30]:<30} {r[2]:>6} {r[3]:>6}")

    conn.commit()
    print("\nCOMMIT thanh cong!")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()

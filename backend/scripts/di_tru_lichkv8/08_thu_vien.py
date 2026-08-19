"""G5.1 — Di trú Thư viện văn bản pháp quy sang portal.

Nguồn: kho Drive `03.THU_VIEN_VAN_BAN` — **189 thư mục nhưng chỉ 23 file**.
Đây gần như là bộ khung phân loại 3 cấp được dựng sẵn mà chưa dùng: 3 nhóm gốc
(`06.BO_NGANH_KHAC`, `07.TINH_QN`, `99.KHAC`) rỗng hoàn toàn.

Vì vậy phần việc chính là **dựng lại cây thư mục**, không phải chuyển file.

Đích là `portal_service` chứ không phải `meeting_service`:
  - Mục "Tài liệu" trên giao diện đã trỏ sang portal;
  - `portal.thu_muc` sẵn có cây cha–con và cột phân quyền;
  - Thư viện văn bản là quản lý tài liệu, không phải nghiệp vụ họp.

    PORTAL_UPLOAD_ROOT=/var/data/kpi/uploads \\
    CHO_PHEP_PROD=toi_dong_y DB_NAME=kpi_haiquan python 08_thu_vien.py [--thu]
"""

from __future__ import annotations

import argparse
import collections
import json
import mimetypes
import os
import shutil
import sys
import uuid as uuid_mod
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ket_noi import da_di_tru, ghi_nguon, ket_noi, lay_tai_khoan_he_thong

HERE = Path(__file__).resolve().parent
DUMPS = HERE / "dumps"
KHO_FILE = DUMPS / "drive_files"
QUET = DUMPS / "drive_thu-vien.json"

# Kho của portal: `<gốc>/portal/thu-vien/...`.
#
# `portal_service/services/file_service.py` đặt `UPLOAD_DIR = Path("uploads/portal")`
# — đường dẫn TƯƠNG ĐỐI so với thư mục chạy tiến trình. Nên gốc phải là
# `uploads/` của đúng cây mà portal-backend đang chạy:
#
#   prod : /opt/kpi-prod/backend/uploads      (là liên kết tới /var/data/kpi/uploads)
#   dev  : /root/kpi-haiquan/backend/uploads
#
# KHÔNG dùng biến `HKG_UPLOAD_DIR` — đó là biến của meeting_service, portal
# không đọc, đặt vào là file rơi ra chỗ portal không phục vụ được.
GOC_UPLOAD = Path(os.environ.get("PORTAL_UPLOAD_ROOT")
                  or (HERE.parents[1] / "uploads"))
UPLOAD_PORTAL = GOC_UPLOAD / "portal" / "thu-vien"

# File thử nghiệm của người dựng kho — không phải văn bản.
BO_QUA_TEN = {"TEST_UPLOAD_THU_VIEN.txt"}

# Tên thư mục trên Drive viết dạng mã (`QUOC_HOI`, `NGHI_DINH`) vì Apps Script
# đặt tên không dấu. Đổi sang tiếng Việt để người dùng đọc được.
#
# CHỈ đổi những mã chắc chắn. Mã không rõ nghĩa (`PTKTSTQ`) giữ nguyên — đoán
# sai một tên là gán nhầm nhãn cho cả một nhánh văn bản pháp quy, tệ hơn hẳn
# so với để nguyên mã cho người dùng tự sửa.
DOI_TEN = {
    # Cơ quan ban hành
    "QUOC_HOI": "Quốc hội",
    "CHINH_PHU": "Chính phủ",
    "CP": "Chính phủ",
    "BO_TAI_CHINH": "Bộ Tài chính",
    "CUC_HAI_QUAN": "Cục Hải quan",
    "CHI_CUC_HQKV8": "Chi cục Hải quan khu vực VIII",
    "BO_NGANH_KHAC": "Bộ, ngành khác",
    "TINH_QN": "Tỉnh Quảng Ninh",
    "DANG": "Đảng",
    "KHAC": "Khác",
    # Bộ, ngành
    "BO_CONG_AN": "Bộ Công an",
    "BO_CONG_THUONG": "Bộ Công Thương",
    "BO_KHOA_HOC_CONG_NGHE": "Bộ Khoa học và Công nghệ",
    "BO_NGOAI_GIAO": "Bộ Ngoại giao",
    "BO_NOI_VU": "Bộ Nội vụ",
    "BO_NONG_NGHIEP_VA_MOI_TRUONG": "Bộ Nông nghiệp và Môi trường",
    "BO_QUOC_PHONG": "Bộ Quốc phòng",
    "BO_TU_PHAP": "Bộ Tư pháp",
    "BO_VHTTDL": "Bộ Văn hoá, Thể thao và Du lịch",
    "BO_XAY_DUNG": "Bộ Xây dựng",
    "BO_Y_TE": "Bộ Y tế",
    "NGAN_HANG_NN": "Ngân hàng Nhà nước",
    "THANH_TRA_CP": "Thanh tra Chính phủ",
    "VAN_PHONG_CP": "Văn phòng Chính phủ",
    # Loại văn bản
    "HIEN_PHAP": "Hiến pháp",
    "LUAT": "Luật",
    "PHAP_LENH": "Pháp lệnh",
    "NGHI_QUYET": "Nghị quyết",
    "NGHI_DINH": "Nghị định",
    "THONG_TU": "Thông tư",
    "QUYET_DINH": "Quyết định",
    "QUYET_DINH_THU_TUONG": "Quyết định của Thủ tướng",
    "CHI_THI": "Chỉ thị",
    "CHI_THI_THU_TUONG": "Chỉ thị của Thủ tướng",
    "CONG_VAN": "Công văn",
    "CONG_VAN_DI": "Công văn đi",
    "BAO_CAO": "Báo cáo",
    "KE_HOACH": "Kế hoạch",
    "CHUONG_TRINH": "Chương trình",
    "HUONG_DAN": "Hướng dẫn",
    "KET_LUAN": "Kết luận",
    "QUY_CHE": "Quy chế",
    "QUY_DINH": "Quy định",
    # Tổ chức Đảng
    "TRUNG_UONG": "Trung ương",
    "TINH_UY_QN": "Tỉnh uỷ Quảng Ninh",
    "CAC_CHI_BO": "Các chi bộ",
    "UBKT": "Uỷ ban Kiểm tra",
    "BAN_TC": "Ban Tổ chức",
    # Xác nhận nghĩa bằng thư mục cha: BAN_TGDV nằm trong "Tỉnh uỷ Quảng Ninh",
    # DU_* nằm trong "Đảng", NVHQ nằm trong "Các chi bộ".
    "BAN_TGDV": "Ban Tuyên giáo - Dân vận",
    "DU_HQKV8": "Đảng uỷ Hải quan khu vực VIII",
    "DU_UBND_TINH": "Đảng uỷ UBND tỉnh",
    "NVHQ": "Chi bộ Nghiệp vụ Hải quan",
    # PTKTSTQ: nằm trong "Các chi bộ" nhưng không suy được đầy đủ tên —
    # giữ nguyên mã, để người dùng đổi trên giao diện.
    # Đơn vị thuộc Chi cục — đối chiếu với danh mục trụ sở đã seed ở G2.3
    "VP": "Văn phòng",
    "TCCB": "Tổ chức cán bộ",
    "CNTT": "Công nghệ thông tin",
    "QLRR": "Quản lý rủi ro",
    "KSHQ": "Kiểm soát Hải quan",
    "HG": "Hòn Gai",
    "MC": "Móng Cái",
    "VG": "Vạn Gia",
    "HM": "Hoành Mô",
    "BPS": "Bắc Phong Sinh",
    # Thư mục gốc của kho
    "THU_VIEN_VAN_BAN": "Thư viện văn bản pháp quy",
}


def ten_hien_thi(duong_dan: str) -> str:
    """`01.QUOC_HOI` → `Quốc hội`. Mã lạ thì giữ nguyên."""
    ten = duong_dan.rsplit("/", 1)[-1]
    if "." in ten[:3]:
        phan = ten.split(".", 1)
        if phan[0].isdigit():
            ten = phan[1]
    return DOI_TEN.get(ten, ten)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--thu", action="store_true", help="chỉ thống kê, không ghi")
    args = ap.parse_args()

    quet = json.loads(QUET.read_text(encoding="utf8"))
    thu_muc = quet["thu_muc"]
    # Sắp theo độ sâu để cha luôn được tạo trước con.
    thu_muc.sort(key=lambda x: (x["do_sau"], x["duong_dan"]))

    tk: collections.Counter = collections.Counter()
    conn = ket_noi()
    he_thong = lay_tai_khoan_he_thong(conn)

    # duong_dan → id trong portal.thu_muc
    ban_do: dict[str, str] = {}

    with conn.cursor() as cur:
        # Chạy lại không được nhân đôi cây thư mục: 189 thư mục nhân hai lần
        # là người dùng mở ra thấy mọi nhánh xuất hiện hai bận.
        da_co_tm = da_di_tru(cur, "DRIVE_THU_MUC_THU_VIEN")
        da_co_file = da_di_tru(cur, "DRIVE_FILE_THU_VIEN")
        if da_co_tm:
            print(f"Đã di trú trước đó: {len(da_co_tm)} thư mục, "
                  f"{len(da_co_file)} tài liệu — chỉ bổ sung phần thiếu.\n")

        for tm in thu_muc:
            duong_dan = tm["duong_dan"]
            cha = duong_dan.rsplit("/", 1)[0] if "/" in duong_dan else None
            parent_id = ban_do.get(cha) if cha else None

            if cha and parent_id is None:
                # Không thể xảy ra khi đã sắp theo độ sâu, nhưng nếu xảy ra thì
                # tạo thư mục ở gốc còn hơn bỏ mất cả nhánh con.
                tk["thư mục mất cha"] += 1

            tk[f"thư mục cấp {tm['do_sau']}"] += 1

            cu = da_co_tm.get(tm["drive_folder_id"])
            if cu:
                ban_do[duong_dan] = cu
                tk["thư mục đã có"] += 1
                continue

            if args.thu:
                ban_do[duong_dan] = f"gia-{len(ban_do)}"
                continue

            cur.execute("""
                INSERT INTO portal.thu_muc (ten, parent_id, thu_tu,
                                            quyen_truy_cap, created_by)
                VALUES (%s, %s, %s, 'TAT_CA', %s)
                RETURNING id
            """, (ten_hien_thi(duong_dan)[:200], parent_id,
                  tm["do_sau"] * 100, he_thong))
            tm_id = cur.fetchone()[0]
            ban_do[duong_dan] = tm_id
            ghi_nguon(cur, "DRIVE_THU_MUC_THU_VIEN", tm["drive_folder_id"],
                      "portal.thu_muc", tm_id,
                      drive_file_id=None, ghi_chu=duong_dan)
            tk["đã tạo thư mục"] += 1

        # ── File ──────────────────────────────────────────────────────
        for tm in thu_muc:
            for f in tm.get("files", []):
                ten = f["ten"]
                if ten in BO_QUA_TEN:
                    tk["bỏ qua file thử nghiệm"] += 1
                    continue

                nguon = KHO_FILE / f["id"]
                if not nguon.exists():
                    tk["file chưa tải được"] += 1
                    continue

                tk["file hợp lệ"] += 1
                if f["id"] in da_co_file:
                    tk["tài liệu đã có"] += 1
                    continue
                if args.thu:
                    continue

                ten_dich = f"{uuid_mod.uuid4().hex}_{ten}"
                dich = UPLOAD_PORTAL / ten_dich
                dich.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(nguon, dich)

                cur.execute("""
                    INSERT INTO portal.tai_lieu
                        (ten_tai_lieu, thu_muc_id, file_url, file_name,
                         file_size_bytes, file_type, quyen_truy_cap,
                         nguoi_tai_len_id)
                    VALUES (%s, %s, %s, %s, %s, %s, 'TAT_CA', %s)
                    RETURNING id
                """, (ten[:300], ban_do.get(tm["duong_dan"]),
                      f"/uploads/portal/thu-vien/{ten_dich}", ten,
                      dich.stat().st_size,
                      mimetypes.guess_type(ten)[0], he_thong))
                tl_id = cur.fetchone()[0]
                ghi_nguon(cur, "DRIVE_FILE_THU_VIEN", f["id"],
                          "portal.tai_lieu", tl_id, drive_file_id=f["id"],
                          ghi_chu=tm["duong_dan"])
                tk["đã ghi tài liệu"] += 1

    if args.thu:
        conn.rollback()
        print("\n(chế độ thử — đã rollback)")
    else:
        conn.commit()

    print("\n── Kết quả ──")
    for k, v in sorted(tk.items()):
        print(f"  {v:5}  {k}")


if __name__ == "__main__":
    main()

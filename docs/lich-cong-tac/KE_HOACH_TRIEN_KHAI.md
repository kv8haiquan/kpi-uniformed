# Kế hoạch triển khai — Lịch công tác HQKV8 vào Nền tảng số thống nhất

> **Trạng thái:** ✅ G1, G2, **G3 trọn vẹn** *(18/08)* · nhánh `feature/lich-cong-tac`
> **Ngày lập:** 17/08/2026
> **Nguồn dữ liệu khảo sát:** `docs/Lich Hop Cong Tac/` (mã nguồn `Mã.gs` 5.227 dòng, `index.html` 6.898 dòng, bản xuất `LICH CONG TAC HQKV8.xlsx`), quét metadata Drive, truy vấn chỉ đọc `kpi_haiquan`
> **Báo cáo phân tích:** https://claude.ai/code/artifact/b80fd077-2acb-4882-9de2-e393b8039f4c

---

## 0. Quyết định đã chốt — căn cứ triển khai

| # | Nội dung | Quyết định |
|---|----------|------------|
| 1 | **Kiến trúc** | Một bảng `meeting.cuoc_hop` duy nhất + cột `nguon` (`HKG`/`LICH_CONG_TAC`) + `CHECK` ràng buộc theo loại dòng. Bảng mở rộng `cuoc_hop_hkg` **để dành**, chưa làm. |
| 2 | **Tiêu chí 8.3** | Cuộc họp tạo mới → hiện trên lịch của mọi người dự. 487 cuộc họp lịch sử → chỉ hiện trên lịch của **lãnh đạo liên quan** (dữ liệu người dự chưa từng tồn tại). |
| 3 | **Trực ban** | Bảng riêng, **không** ép thành loại sự kiện lịch. Giữ nguyên phạm vi **thứ 7 + chủ nhật**. |
| 4 | **Thư viện tài liệu** | Gộp vào mục **Tài liệu** đã có, làm một mục con riêng. Không tạo kho thứ ba. |
| 5 | **Màn hình đối soát** | Chánh Văn phòng **Tống Thị Thái Hà** (`20ZZ-0097`, lichkv8 = `hattt`) + Quản trị viên. |
| 6 | **Thả file trực tiếp** | **Chặn.** Sau chuyển đổi mọi tài liệu phải upload qua phần mềm. |
| 7 | **Thu hồi chia sẻ Drive** | Làm **sau khi** xác nhận tài liệu đã sang cloud thành công (giai đoạn 6). |
| 8 | **Định dạng file** | **Giữ nguyên 13 định dạng** của HKG, không mở rộng cho `.zip`/`.rar`. File nén phải tách ra trước khi tải lên. 4 file nén lịch sử vẫn được di trú và mở được. |

### Số liệu gốc dùng để đối soát

Ghim lại để kiểm tra sau mỗi bước di trú. Đây là ảnh chụp bản bàn giao — **phải lấy lại qua API ở G1.2** vì hệ cũ vẫn đang chạy.

| Bảng / kho | Số lượng |
|---|---|
| `MEETING` | 487 (PUBLISHED 461, CANCELLED 16, DRAFT 10; `IS_DELETED`=0 toàn bộ) |
| `LOAI_LICH` | HOP 232 · TRUC_BAN 85 · HOI_NGHI 69 · LAM_VIEC 46 · CONG_TAC 37 · LICH_KHAC 18 |
| `MEETING_FILE` | 587 bản ghi (Active 421, Deleted 166) |
| Kho Drive tài liệu họp | **230 thư mục cấp 1 · 1.226 file** (đo lại G1.3) |
| `MEETING_PARTICIPANT` | 294 (100% `ROLE_IN_MEETING=LANH_DAO_LIEN_QUAN` — **không phải** danh sách người dự) |
| `MEETING_LOG` | 4.279 |
| `MEETING_RATING` | 105 (SCORE 5.0 ×102, 4.0 ×3) |
| `MEETING_NOTE` / `NOTE_SHARE` | 7 / 0 |
| `DUTY_ENTRY` | 709 (SUBMITTED 333, Deleted 376) — 100% `DUTY_TYPE="Thứ 7/CN"`, `DUTY_SHIFT="Cả ngày"` |
| `DUTY_UNIT_STATUS` | 200 (100% SUBMITTED, `LOCKED`=0) |
| Trụ sở trực ban | 9 (`CHICUC`, `HONGAI`, `CAMPHA`, `VANGIA`, `HOANHMO`, `BPS`, `MONGCAI`, `KSHQ_HL`, `KSHQ_MC`) |
| Thư viện văn bản | 189 thư mục · 23 file |
| `USER` | 548 (547 có `USER_ID` đúng dạng `ma_cc`) |
| `DEPT` | 13 đơn vị (chỉ 1 có `ROOT_FOLDER_ID`) |

Khoảng ngày: `MEETING` **09/03/2026 → 18/08/2026**. Kho Drive có tài liệu từ **24/01/2026** (tài liệu tiền hệ thống).

---

## Giai đoạn 1 — Chốt phạm vi và lấy dữ liệu gốc

**Ước lượng:** 1 ngày · **Chặn:** không còn gì

- [x] **G1.1** — Tạo nhánh `feature/lich-cong-tac` ✅ *17/08*
  > ⚠️ **Sửa so với bản plan đầu:** nhánh tạo từ **`feature/hkg-zalo-oa`** (commit `1912c2e`), **không** từ `main`.
  > Lý do: `main` (`6101d3f`) đi sau HEAD **174 commit** và **không có `backend/meeting_service/` lẫn migration `meeting_*` nào** —
  > branch từ `main` thì không có module HKG để mở rộng, toàn bộ giai đoạn 2 bất khả thi.
  > Lưu ý: cây làm việc còn **22 file sửa + 29 file mới chưa commit** thuộc module KPI của các việc khác — không stage vào commit của dự án này.
- [x] **G1.2** — Xuất bản sống của cơ sở dữ liệu ✅ *17/08* → `xuat_sheet.py`, `doc_sheet.py`
  > 🔴 **Tìm được ID bảng tính:** `1Kyp9ce15Og0b6z9iqNIWk0rziuiukJ-05hG5nbKfo-w`
  > Nó **nằm ngay tại gốc kho tài liệu họp** `01.TAI_LIEU_HOP`, không phải ngoài kho như tài liệu bàn giao ngụ ý.
  > Đây là **Google Sheets gốc** (`application/vnd.google-apps.spreadsheet`), không phải bản xuất `.xlsx` — nên
  > xuất lại được bất cứ lúc nào, không cần xin quyền. Mã nguồn để `CFG.SPREADSHEET_ID = ''` và dùng
  > `getActiveSpreadsheet()` nên ID không xuất hiện ở đâu trong 5.227 dòng mã — chỉ tìm được bằng cách quét kho Drive.

  Chênh lệch so với bản bàn giao — **hệ cũ vẫn đang phát sinh dữ liệu**:

  | Sheet | mốc | sống | chênh |
  |---|---:|---:|---:|
  | `MEETING` | 487 | **489** | +2 |
  | `MEETING_FILE` | 587 | **590** | +3 |
  | `MEETING_LOG` | 4.279 | **4.295** | +16 |
  | 11 sheet còn lại | | | không đổi |

  Hai cuộc họp mới là `LH0488`, `LH0489` → **mã lịch lớn nhất hiện tại là `LH0489`**, không phải `LH0487`.
  Sinh mã mới ở G4.3 phải bắt đầu từ `LH0490`, và phải đọc lại lúc cắt chuyển chứ không hardcode.

- [x] **G1.3** — Quét cây Drive cả 2 kho ✅ *17/08* → `quet_drive.py`, `dumps/drive_*.json`

  | Kho | Drive folder ID | Thư mục | File |
  |---|---|---:|---:|
  | `01.TAI_LIEU_HOP` | `1AkMxFT-OQlmW5K9lLw_Aoj8X1tZWRSTx` | 295 | **1.226** |
  | `03.THU_VIEN_VAN_BAN` | `1nDn4qEgJ99rRpdn5x-2VEEPA_SkX6rvv` | 189 | 23 |

  Quét hai lần cách nhau 2 giờ cho thấy kho tăng **1 thư mục + 2 file** (`LH0489` mới, `LH0488` thêm 1 file)
  → xác nhận cần G6.2 (di trú lần cuối) và G6.5 (khoá ghi) chứ không thể di trú một lần rồi thôi.
- [x] **G1.4** — Ánh xạ đơn vị và trụ sở ✅ *17/08* → `backend/scripts/di_tru_lichkv8/anh_xa.py`
  - `DEPT` có **13 đơn vị**, chỉ **1/13** (`HQKV8`) có `ROOT_FOLDER_ID` và nó trỏ vào chính kho tài liệu chung
    → **không có thư mục Drive riêng theo đơn vị nào đang dùng**, không phát sinh cây thư mục thứ ba
  - 🔴 Phát hiện: tồn tại **ba hệ mã đơn vị** không hệ nào trùng hệ nào — `public.don_vi` (15),
    `DEPT.MA_DON_VI` (13), `DUTY_ENTRY.UNIT_CODE` (9). Hệ thứ ba là **trụ sở vật lý**, không phải đơn vị
    → làm đổi thiết kế bảng trực ban, xem G2.3

**Nghiệm thu G1:** ✅ Đủ. Sản phẩm tại `backend/scripts/di_tru_lichkv8/`:

| File | Vai trò |
|---|---|
| `xuat_sheet.py` | Xuất bản sống Google Sheets + đối chiếu số dòng với mốc |
| `doc_sheet.py` | Đọc `.xlsx` không cần thư viện ngoài (xử lý đúng ô rỗng tự đóng) |
| `quet_drive.py` | Quét metadata cây Drive cả 2 kho, chỉ đọc |
| `anh_xa.py` | Bảng ánh xạ đơn vị, trụ sở, trạng thái, loại lịch, vai trò |
| `dumps/lichkv8_live.xlsx` | Bản sống 18 sheet |
| `dumps/drive_tai-lieu.json` · `dumps/drive_thu-vien.json` | Mốc đối soát cây Drive |

Cả 4 script chạy lại được ở G6.2 để di trú phần phát sinh.

---

## Giai đoạn 2 — Mở rộng schema `meeting`

**Ước lượng:** 3 ngày · **Chặn bởi:** G1 · ✅ **Hoàn thành 17/08**

> 🔴 **Hai bẫy đã gặp, ghi lại để lần sau không mắc:**
>
> 1. **Chuỗi alembic TUYẾN TÍNH qua mọi module** (kpi, lms, zalo, meeting…), không tách nhánh theo module.
>    Plan ban đầu ghi dùng `mt_015_nhom_tp_chi_tiet_20260503` làm `down_revision` — sai, sẽ tạo **head thứ hai**
>    và `alembic upgrade head` báo *"Multiple head revisions are present"*. Head thật là `zalo_oa_20260731`.
>    Kiểm tra trước khi viết: `ScriptDirectory.from_config(Config("alembic.ini")).get_heads()`.
> 2. **`alembic_version.version_num` là `varchar(32)`.** Revision id dài hơn 32 ký tự làm migration vỡ
>    *giữa chừng* (DDL đã chạy, ghi version thất bại) → phải tạo lại DB test.
>    `mt_017_lanh_dao_lien_quan_20260817` = 34 ký tự → đổi thành `mt_017_ld_lien_quan_20260817`.

### G2.1 — `meeting_016`: mở rộng `cuoc_hop`

- [x] Thêm cột phân loại và các cột của Lịch công tác:

| Cột mới | Kiểu | Ghi chú |
|---|---|---|
| `nguon` | `VARCHAR(20) NOT NULL DEFAULT 'HKG'` | `HKG` / `LICH_CONG_TAC` |
| `ma_lich` | `VARCHAR(20) UNIQUE` | `LHxxxx` — **bắt buộc giữ nguyên mã lịch sử** |
| `ngay_ket_thuc` | `DATE` | lịch kéo dài nhiều ngày |
| `ngay_hien_thi` | `DATE` | ngày dùng để xếp lên lịch, có thể khác ngày bắt đầu |
| `loai_lich` | `VARCHAR(30)` | 6 giá trị đã có sẵn, **không** trùng `khoi` |
| `chu_tri_text` | `VARCHAR(300)` | 9% chủ trì là chức danh chung / người ngoài ngành |
| `thanh_phan_text` | `TEXT` | văn bản tự do, dài nhất 246 ký tự |
| `don_vi_chuan_bi` | `VARCHAR(200)` | trục của báo cáo Thống kê tài liệu |
| `so_van_ban` | `VARCHAR(100)` | dùng cho việc gắn thư mục theo số giấy mời |
| `ly_do_huy` | `TEXT` | 16 cuộc họp đã huỷ có lý do |
| `updated_by` | `UUID FK public.cong_chuc(id)` | hiện chỉ có `updated_at` |

- [x] Nới `chu_toa_id` và `don_vi_to_chuc_id` thành nullable
- [x] Thêm ràng buộc có điều kiện:

```sql
ALTER TABLE meeting.cuoc_hop
  ADD CONSTRAINT ck_hkg_bat_buoc CHECK (
    nguon <> 'HKG' OR (chu_toa_id IS NOT NULL AND don_vi_to_chuc_id IS NOT NULL)
  );
```

- [x] Index: `ma_lich`, `(nguon, ngay_hien_thi)`, `(ngay_hien_thi)`, `don_vi_chuan_bi`
- [x] **Kiểm tra hồi quy:** `nhom_thanh_phan_chi_tiet` có logic auto-fill `chu_toa_id` khi thêm nhóm vào cuộc họp (xem docstring `meeting_015`) — đảm bảo không vỡ khi cột thành nullable

### G2.2 — `meeting_017`: lãnh đạo liên quan

- [x] Bảng `meeting.lanh_dao_lien_quan` — quan hệ nhiều–nhiều
  - `cuoc_hop_id` FK CASCADE, `cong_chuc_id` FK `public.cong_chuc(id)`, `thu_tu`
  - UNIQUE `(cuoc_hop_id, cong_chuc_id)`
  - **Khớp 100%** với `cong_chuc` (480/480 token) → chuẩn hoá sạch, đây là trục của Lịch lãnh đạo + Dashboard + Tóm tắt lịch

### G2.3 — `meeting_018`: trực ban

> 🔴 **Sửa thiết kế sau khảo sát G1.4:** bản plan đầu định khoá trực ban theo `don_vi_id` — **sai**.
> Dữ liệu cho thấy trực ban tổ chức theo **trụ sở vật lý**, không theo đơn vị: `UNIT_NAME` ghi rõ
> *"Trụ sở HQCK cảng Vạn Gia"*, *"Trụ sở Chi cục HQKV VIII"*. Quan hệ trụ sở ↔ đơn vị **không 1:1**:
>
> - 6 trụ sở cửa khẩu → khớp 1:1 với đơn vị HQCK tương ứng
> - `KSHQ_HL` + `KSHQ_MC` → **cùng một** đơn vị `KSHQ` (một đơn vị, hai trụ sở)
> - `CHICUC` → trụ sở dùng chung của VP, LDCC, CNTT, NVHQ, TCCB, QLRR, PTSTQ — không ứng đơn vị nào
>
> Bảng ánh xạ đầy đủ: `backend/scripts/di_tru_lichkv8/anh_xa.py`

- [x] `meeting.tru_so` — danh mục 9 trụ sở trực ban (bảng mới, không có trong lichkv8)
  - `ma_tru_so VARCHAR(20) UNIQUE` (`CHICUC`, `HONGAI`, `CAMPHA`, `VANGIA`, `HOANHMO`, `BPS`, `MONGCAI`, `KSHQ_HL`, `KSHQ_MC`)
  - `ten_tru_so`, `don_vi_id` FK `public.don_vi(id)` **nullable** (rỗng với `CHICUC`), `thu_tu`, `is_active`
  - Seed sẵn 9 dòng từ `anh_xa.TRU_SO`
- [x] `meeting.truc_ban` — thay `DUTY_ENTRY` (333 bản ghi còn hiệu lực)
  - `ngay_truc DATE`, `tru_so_id` FK `meeting.tru_so(id)`, `unit_code_cu VARCHAR(20)` (giữ mã cũ để đối soát)
  - `cong_chuc_id` FK nullable, `ho_ten`, `chuc_vu`, `so_dien_thoai` (333/333 có giá trị — trường cốt lõi)
  - `loai_truc VARCHAR(20) DEFAULT 'CUOI_TUAN'` — **giữ cột để sau mở rộng, giao diện chỉ hiện cuối tuần**
  - `ca_truc VARCHAR(20) DEFAULT 'CA_NGAY'`, `ghi_chu`, `trang_thai`
- [x] `meeting.truc_ban_tru_so` — thay `DUTY_UNIT_STATUS` (200 bản ghi)
  - `(ngay_truc, tru_so_id)` UNIQUE, `trang_thai` (`NHAP`/`DA_NOP`), `nguoi_nop_id`, `thoi_diem_nop`, `is_locked`
- [x] **Quyền theo trụ sở:** `truc_ban.sua_don_vi_minh` cho phép sửa các trụ sở có `don_vi_id` = đơn vị của user.
      Trụ sở `CHICUC` (`don_vi_id` rỗng) do **Văn phòng** điều phối — mã cũ cấp quyền này bằng regex `"van phong"`,
      nay khai báo tường minh qua `anh_xa.DON_VI_DIEU_PHOI_CHICUC`

### G2.4 — `meeting_019`: đánh giá + ghi chú

- [x] `meeting.danh_gia_cuoc_hop` — thay `MEETING_RATING` (105 bản ghi)
- [x] `meeting.ghi_chu` + `meeting.ghi_chu_chia_se` — thay `MEETING_NOTE` / `NOTE_SHARE` (7 / 0 bản ghi)

### G2.5b — `meeting_021`: trigger đồng bộ `ngay_hien_thi` ✅ *17/08*

> 🔴 **Phát sinh sau khi rà lại 016** — hai lỗi đều phá vỡ tiêu chí 8.3, tìm ra bằng cách chạy thật
> câu INSERT mà `cuoc_hop_service.tao_moi()` sinh ra:
>
> 1. Cuộc họp HKG **tạo mới** có `ngay_hien_thi = NULL` → **vô hình trên Lịch công tác**.
>    Model `CuocHop` không biết cột này (đúng thiết kế), nên INSERT bỏ trống.
>    016 chỉ backfill 9 dòng sẵn có, không lo được cho dòng tương lai.
> 2. Cuộc họp HKG **dời ngày** thì `ngay_hien_thi` giữ ngày cũ → lịch hiện sai ngày.
>    `cap_nhat()` dùng `setattr` theo model, model không có cột này.
>
> Sửa bằng **trigger ở mức cơ sở dữ liệu**, không sửa model/service — giữ đúng nguyên tắc
> HKG không phải biết gì về Lịch công tác, và đúng với mọi đường ghi (kể cả script di trú, sửa tay).

- [x] `fn_dong_bo_ngay_hien_thi()` + trigger `BEFORE INSERT OR UPDATE`
  - `nguon='HKG'` → `ngay_hien_thi` **luôn** soi gương `ngay_hop`; `loai_lich` trống thì gán `'HOP'`
  - `nguon='LICH_CONG_TAC'` → giữ nguyên giá trị người dùng đặt, chỉ điền khi bỏ trống
    (lichkv8 có `NGAY_HIEN_THI` khác ngày bắt đầu thật)

### G2.5 — `meeting_020`: bảng lưu vết di trú

- [x] `meeting.di_tru_doi_soat` — phục vụ màn hình đối soát và biên bản nghiệm thu
  - `duong_dan_thu_muc`, `drive_folder_id`, `so_file`, `ngay_suy_ra`
  - `nhom VARCHAR(2)` (`A`–`E`), `quyet_dinh VARCHAR(30)`, `cuoc_hop_id` nullable
  - `nguoi_quyet_dinh_id`, `thoi_diem`, `ghi_chu`
- [x] `meeting.di_tru_nguon` — map bản ghi cũ ↔ mới (`meeting_id_cu`, `drive_file_id`, `bang_nguon`) để truy vết và chạy lại được

**Nghiệm thu G2:** ✅ Đủ.

| Kiểm tra | Kết quả |
|---|---|
| `alembic upgrade head` trên `kpi_haiquan_test` (clone tươi từ prod) | ✅ 5 migration chạy sạch |
| Số bảng schema `meeting` | 13 → **22** (thêm 9) |
| HKG tạo cuộc họp mới không đụng field nào của Lịch công tác | ✅ chạy nguyên câu INSERT cũ |
| Cuộc họp HKG mới hiện trên Lịch công tác | ✅ qua trigger `meeting_021` |
| Dời ngày họp HKG thì lịch cập nhật theo | ✅ tiêu chí 8.3 |
| `alembic downgrade zalo_oa_20260731` rồi upgrade lại | ✅ về đúng 13 bảng, nâng lại được |
| Test ràng buộc mới `test_lich_cong_tac_schema.py` | ✅ **35/35 PASS** |
| Hồi quy test HKG (trừ 2 file phụ thuộc giờ) | ✅ **169/169 PASS** |
| 9 cuộc họp HKG sẵn có | ✅ `nguon='HKG'`, `ngay_hien_thi` backfill đủ |
| Seed 9 trụ sở + ánh xạ đơn vị | ✅ đúng, `CHICUC` để `don_vi_id` NULL |

Bằng chứng ràng buộc `CHECK` hoạt động thật (không chỉ trên giấy):

```
INSERT nguon='HKG' thiếu chu_toa_id
  → ERROR: violates check constraint "ck_cuoc_hop_hkg_bat_buoc"
INSERT nguon='LICH_CONG_TAC' thiếu chu_toa_id, có ma_lich
  → THÀNH CÔNG
```

Tức mục tiêu chính của phương án một-bảng đạt được: **dòng HKG vẫn không thể tạo mà thiếu chủ trì**,
ép ở mức cơ sở dữ liệu, trong khi 117 cuộc họp lịch sử không có chủ trì vẫn nạp được — và **không phải
sửa `chu_toa_id` ở 103 chỗ** trong 14.221 dòng code HKG.

> ⚠️ **14 test đỏ có sẵn từ trước, không do migration này.** `test_presentation_rest.py` và
> `test_presentation_ws.py` phụ thuộc giờ chạy: WS token hết hạn = `gio_bat_dau + 4h`
> (`ws_token_service.py:60-66`), test tạo họp giờ sáng nên chạy buổi tối là 410 `MEETING_EXPIRED`.
> Đã chứng minh bằng cách hạ migration rồi chạy lại — **đúng 14 test đó vẫn đỏ**. Nên sửa riêng,
> ngoài phạm vi dự án này.

> ⚠️ Migration **chỉ chạy trên `kpi_haiquan_test`** ở giai đoạn này. Chạy prod ở G6.1 sau khi user duyệt.

---

## Giai đoạn 3 — Di trú dữ liệu và 1.223 file

**Ước lượng:** 5–6 ngày · **Chặn bởi:** G2

### G3.1 — ETL bảng dữ liệu ✅ *17/08*

> 🔴 **Lỗi ngày tháng trong dữ liệu gốc — phát hiện khi rà, suýt làm hỏng 43% dữ liệu.**
>
> Cột serial `NGAY_BAT_DAU`/`NGAY_KET_THUC` **lệch sớm 1 ngày ở 212/489 dòng**. Chênh lệch
> chỉ có đúng hai giá trị (+0 và +1) nên không phải dữ liệu tự nhiên mà là lỗi hệ thống của lichkv8.
> Dùng cột `THU` (thứ trong tuần, người nhập) làm trọng tài độc lập:
>
> | | khớp `THU` |
> |---|---:|
> | `NGAY_HIEN_THI` (chuỗi dd/mm/yyyy) | **476/476 (100%)** |
> | `NGAY_BAT_DAU` (serial) | **0/476** |
>
> → ETL lấy `NGAY_HIEN_THI` làm chuẩn. Cặp serial vẫn nhất quán về độ dài (13/13 dòng nhiều ngày
> khớp) nên `ngay_ket_thuc` = ngày đúng + độ dài từ serial. Sau di trú: **489/489 khớp `THU`, 0 lệch**.
>
> 🔴 **`GIO_BAT_DAU` lẫn hai định dạng**: 278 dòng `'HH:MM'` và **211 dòng phân số Excel**
> (`'0.3333'` = 08:00). Chỉ parse `'HH:MM'` thì mất giờ của 43% cuộc họp.
>
> 🔴 **`NGUOI_TAO` là USERNAME**, không phải mã công chức → phải qua sheet `USER` để ánh xạ
> username → `ma_cc` → `cong_chuc.id`. Kết quả: 217 người thật, 272 dòng `'import'` → tài khoản
> hệ thống `ADMIN-001` (dùng tài khoản sẵn có, không tạo mới vì `public` là chỉ đọc).

- [x] Script `backend/scripts/di_tru_lichkv8/01_cuoc_hop.py`
  - 487 dòng `MEETING` → `cuoc_hop` với `nguon='LICH_CONG_TAC'`, giữ `ma_lich`
  - Ánh xạ trạng thái: `PUBLISHED`→`DA_THONG_BAO`, `CANCELLED`→`HUY`, `DRAFT`→`LEN_KE_HOACH`
  - `CHU_TRI`: khớp `cong_chuc` (91%) → `chu_toa_id`; phần còn lại → `chu_tri_text`
  - `NGUOI_TAO`: 272 dòng ghi `import` → **cần tài khoản hệ thống** cho `created_by` (FK NOT NULL)
  - `THANH_PHAN` → `thanh_phan_text` nguyên văn (rỗng ở 214/487)
- [x] `02_lanh_dao_lien_quan.py` — 480 token, khớp 100%
- [x] `03_truc_ban.py` — `DUTY_ENTRY` 333 còn hiệu lực + `DUTY_UNIT_STATUS` 200; map `UNIT_CODE` cũ (`CHICUC`, `VANGIA`, `MONGCAI`, `HONGAI`, `BPS`, `KSHQ_MC`, `HOANHMO`, `CAMPHA`) → `don_vi_id`
- [x] `04_danh_gia_ghi_chu.py` — 105 đánh giá + 7 ghi chú
- [x] `05_nguoi_dung.py` — ánh xạ `USER.USER_ID` = `ma_cc` (547/548), ngoại lệ `superadmin`
  - ⛔ **KHÔNG nạp cột `PASSWORD_HASH`** dưới bất kỳ hình thức nào (505 dòng là mật khẩu dạng rõ)
  - Map vai trò lichkv8 → RBAC nền tảng: `SuperAdmin`/`Admin` → admin; `Lanhdaochicuc` → CCT/PCCT; `Lanhdaophong`/`Lanhdaodoi` → TDV/PDV; `Thuky` → quyền tác nghiệp lịch; `Congchuc` → CC

### G3.2 — Di trú file **theo thư mục**

> **Sản phẩm:** `05_tai_file_drive.py` (tải bản lạnh), `phan_nhom.py` (phân nhóm A–E dùng chung
> với màn hình đối soát G4.9), `06_gan_tai_lieu.py` (đẩy vào kho + gắn cuộc họp).
>
> Đường đi của file: `dumps/drive_files/<drive_id>` → `uploads/meeting/tai-lieu/<cuoc_hop_id>/<uuid>_<tên>`
> — trùng quy ước `storage_service.py` để API xem/tải sẵn có dùng được ngay, không phải sửa gì.
>
> ⚠️ **Whitelist 13 phần mở rộng của HKG không áp dụng khi di trú.** Kho có 5 file ngoài danh sách
> (2 `.zip`, 2 `.rar`, 1 `.db`); từ chối là mất dữ liệu đã tồn tại. Whitelist chỉ áp cho upload mới —
> cần quyết định có mở rộng không.
>
> ⚠️ `dumps/drive_files/` bị `.gitignore` nên **không nằm trong backup mã nguồn**. Đây là chủ ý
> (hơn 1 GB không nên vào git) nhưng nghĩa là phải off-site nó **trước G6.7** — sau khi thu hồi
> chia sẻ Drive thì không tải lại được nữa.
>
> 🔴 **File Google gốc không tải nhị phân được.** 2 file trả HTTP 500 ở endpoint
> `uc?export=download` vì là Google Docs/Sheets gốc chứ không phải file tải lên (nhận biết: ID dài
> 44 ký tự thay vì 33). Phải dùng endpoint xuất riêng. Bẫy phụ: trang Drive khai báo nhiều mime
> cùng lúc (`vnd.google-apps.document` **và** `vnd.google-apps.kix`) nên phải duyệt hết rồi chọn,
> không được lấy cái gặp đầu tiên.

**Kết quả G3.2** *(18/08)*:

| | |
|---|---:|
| File tải về từ kho tài liệu họp | **1.225** · 1,35 GB |
| Gắn tự động (nhóm A + B + C) | **813** |
| Vào hàng đợi đối soát (D + E) | **412** file / **34 cụm** |
| Cuộc họp có tài liệu | 197 |
| Tài liệu HKG sẵn có (không đụng) | 40 |
| Trùng khoá lưu trữ | 0 |

23 file kho thư viện **không** vào hàng đợi cuộc họp — thuộc portal, xử lý ở G5.1.

> **Nguyên tắc:** thư mục Drive là nguồn sự thật của file, **không phải** bảng `MEETING_FILE`.
> Bảng chỉ dùng bổ sung metadata (ai tải lên, lúc nào) ở chỗ nào có.

- [x] Script `06_tai_file_drive.py` — tải toàn bộ cây về đĩa, giữ nguyên cấu trúc, ghi log từng file
- [x] Script `07_gan_tai_lieu.py` — đẩy qua `StorageService` sẵn có (`meeting_service/services/storage_service.py`, hiện `uploads/meeting/`), gắn vào cuộc họp:

| Nhóm | Căn cứ | Thư mục | File | Xử lý |
|---|---|---:|---:|---|
| A | Tên thư mục là `LHxxxx` | 169 | 672 | Tự động |
| B | Khớp cả ngày lẫn số GM | 14 | 76 | Tự động |
| C | Khớp số giấy mời ↔ `SO_VAN_BAN` | 12 | 63 | Tự động |
| D | Chỉ khớp ngày (2–8 ứng viên) | 15 | 210 | → màn hình đối soát |
| E | Không khớp gì | 19 | 202 | → màn hình đối soát |

  - **811 file (66%) gắn tự động**, 412 file chờ đối soát
  - ⚠️ **`DA_KET_THUC` là ngoại lệ**: không phải 1 cuộc họp mà là kho lưu trữ chứa **13 cuộc họp con** (75 file). Script phải đi thêm 1 cấp ở thư mục này
  - ⚠️ Loại **4 bản ghi có file đã biến mất khỏi Drive**: `LH0327`, `LH0354`, `LH0373`, `LH0399`
  - ⚠️ Loại 166 bản ghi `STATUS=Deleted`

### G3.3 — Đối soát sau di trú

- [x] So khớp: số cuộc họp, số bản ghi trực ban, số file, tổng dung lượng trước/sau
- [x] Mở thử ngẫu nhiên 20 file mỗi định dạng (pdf, docx, doc, xlsx, pptx) — không hỏng
- [x] Kiểm tra tiếng Việt, ngày giờ, số điện thoại, tên file không bị lỗi mã hoá
- [x] Xuất biên bản đối chiếu ra Excel

**Nghiệm thu G3:** biên bản đối chiếu khớp số lượng; mọi `ma_lich` lịch sử giữ nguyên; không mất dữ liệu tiếng Việt.

---

## Giai đoạn 4 — API và giao diện Lịch công tác

**Ước lượng:** 10–14 ngày · **Chặn bởi:** G2 (không cần chờ G3)

> Backend: `backend/meeting_service/` (port 8006, PM2 `meeting-backend`), prefix nginx `/api/v1/hop-khong-giay/`
> Frontend: `frontend/src/app/(main)/lich-cong-tac/`, service `frontend/src/services/hkg.ts` (mở rộng) hoặc tách `lich-cong-tac.ts`

### G4.1 — Điều hướng ✅ *18/08*

- [x] Thêm mục **Lịch công tác** vào `frontend/src/components/common/Sidebar.tsx`, đặt **ngay trên** mục Họp Không Giấy (dòng ~172)
- [x] Thêm widget vào lưới trang Tổng quan (`app/(main)/tong-quan/`), theo mẫu `WidgetHKG.tsx`

### G4.2 — Lịch công tác (màn hình trung tâm) ✅ *18/08*

- [x] `GET /lich-cong-tac` — lọc theo khoảng ngày, loại lịch, lãnh đạo, trạng thái; **phân trang server-side** (hệ cũ tải hết vào bộ nhớ, có ngưỡng cảnh báo 3000ms)
- [x] Xem theo tháng / tuần / danh sách
- [x] Tìm kiếm toàn văn trên: nội dung, ghi chú, địa điểm, chủ trì, thành phần, lãnh đạo liên quan
- [x] Chi tiết lịch: đầy đủ trường + tài liệu + lãnh đạo liên quan
- [x] **Bấm sự kiện loại họp → mở thẳng chi tiết cuộc họp trong HKG** (tiêu chí 8.3 gạch 2)

### G4.3 — Quản lý lịch ✅ *19/08*

- [x] CRUD + huỷ (giữ trạng thái, không xoá vật lý) + xoá mềm theo quyền
- [x] Sinh `ma_lich` tiếp nối: `LH0488` trở đi, có khoá chống trùng
- [x] Xuất Excel: STT, mã lịch, ngày, giờ, loại, nội dung, thành phần, địa điểm, chủ trì, lãnh đạo, đơn vị chuẩn bị, số văn bản, ghi chú, trạng thái, số file
- [x] Ghi nhật ký thay đổi theo từng trường (thay `MEETING_LOG`)

### G4.4 — Tóm tắt lịch ✅ *18/08*

- [x] Tổng hợp theo khoảng ngày (mặc định 3 ngày), nhóm theo ngày → lãnh đạo
- [x] Chế độ gọn, chọn thông tin đi kèm: địa điểm, chức danh, lịch trực, chỉ lịch đã đăng
- [x] Nút copy để dán sang Zalo/email
- [x] **Sinh trực tiếp từ dữ liệu lịch**, không lưu bản riêng

### G4.5 — Lịch lãnh đạo ✅ *18/08*

- [x] Thẻ chương trình công tác từng lãnh đạo, dựa trên `lanh_dao_lien_quan` (khớp 100%)
- [x] Hiển thị: ngày, giờ, nội dung, địa điểm, vai trò

### G4.6 — Thống kê tài liệu họp ✅ *19/08*

- [x] Lọc: từ ngày, đến ngày, từ khoá, lãnh đạo, trạng thái lịch, tình trạng tài liệu, tính/không tính lịch huỷ
- [x] 5 trạng thái: Tất cả · Có giao chuẩn bị · Đã gắn tài liệu · Thiếu tài liệu · Chưa giao chuẩn bị
- [x] Xuất Excel
- [x] 🔴 **BÊ NGUYÊN quy tắc "giấy mời không tính là tài liệu chuẩn bị"** — port nguyên văn 3 hàm từ `Mã.gs` dòng 1513–1570:
  - `hasMeetingDocsMaterialSignal_()` — regex tín hiệu tài liệu chuyên môn
  - `hasInvitationSignal_()` — regex tín hiệu giấy mời
  - `isInvitationDocFile_()` — **thứ tự ưu tiên: có tín hiệu tài liệu thì TÍNH, kể cả khi nằm trong nhóm `GIAY_MOI`**
  - Lý do: bình luận V145 trong mã ghi rõ làm sai sẽ *"báo oan đơn vị chưa nộp tài liệu"*. 279/587 file mang nhóm `GIAY_MOI` → quy tắc này chi phối gần một nửa báo cáo
  - Viết test theo đúng các ca đã tinh chỉnh

### G4.7 — Trực ban ✅ *19/08*

- [x] Bảng ma trận: hàng = ngày, cột = 8 trụ sở, ô = người trực (họ tên, chức vụ, SĐT)
- [x] Sắp xếp theo thứ tự chức vụ: CCT → PCCT → Trưởng/Chánh → Phó → Công chức
- [x] Lọc tuần trước / tuần này / tuần sau + khoảng ngày tuỳ chọn + theo đơn vị
- [x] Tab dữ liệu chi tiết
- [x] Nhập thủ công · sửa trực tiếp · nộp chính thức (`NHAP → DA_NOP`) · copy báo cáo · in · xuất Excel
- [x] 🔴 **Phân quyền phải THAY, không port**: hệ cũ dùng `isDutyAdmin_()` dò chuỗi trên họ tên + chức vụ + đơn vị gộp lại (`Mã.gs` dòng 4591) — ai có đơn vị chứa "Văn phòng" hoặc chức vụ chứa "lãnh đạo" đều thành quản trị toàn Chi cục. Thay bằng quyền chức năng thật:
  - `truc_ban.xem` · `truc_ban.sua_don_vi_minh` · `truc_ban.sua_tat_ca` · `truc_ban.import` · `truc_ban.xoa`
  - Dựa trên `vai_tro` + `don_vi_id` khoá ngoại, không so khớp chuỗi

### G4.8 — Import trực ban từ Excel ✅ *19/08*

- [x] Quy trình 2 bước: parse → **preview** → commit (không ghi thẳng)
- [x] Nhận diện linh hoạt biến thể tên cột (`GHI_CHU` / `Ghi chú` / `Ghi chu` / `NOTE` là cùng một cột)
- [x] Báo dòng hợp lệ / không hợp lệ trước khi ghi
- [x] 📎 **Mang file mẫu sang**: `docs/Lich Hop Cong Tac/Github/Mau_import_lich_truc_ban_HQKV8_v127.xlsx` → đặt làm file mẫu tải về trên nền tảng

### G4.9 — Màn hình đối soát tài liệu (dùng một lần) ✅ *19/08*

- [x] Route riêng, **chỉ** Chánh VP `20ZZ-0097` + Quản trị viên thấy
- [x] Liệt kê 34 thư mục (15 nhóm D + 19 nhóm E), 412 file
- [x] Mỗi dòng: tên thư mục, số file, ngày suy ra, **danh sách tên file mở rộng được** (nhiều khi phải nhìn tên file mới đoán ra cuộc họp)
- [x] Gợi ý ứng viên **xếp hạng theo từ khoá trùng** giữa tên thư mục và nội dung cuộc họp
  - ⚠️ **Không thư mục nào có ứng viên duy nhất** — ngày nào cũng có 2–8 cuộc họp vì "Chỉ đạo trực ban" lặp gần như hằng ngày. Phải là danh sách để chọn, không phải nút xác nhận một chạm
  - Xếp hạng giúp rõ 9/29 trường hợp; số còn lại tên viết tắt quá (`TL HN chỉ số`, `260519-CCT lv KTSTQ`)
- [x] 4 hành động: gắn vào cuộc họp đã chọn · **tạo cuộc họp lịch sử từ chính thư mục này** · đưa vào kho lưu trữ không gắn · không di trú
- [x] Ghi `meeting.di_tru_doi_soat` kèm người + thời điểm → xuất Excel = **biên bản đối chiếu nộp khi nghiệm thu**
- [x] Dùng xong ẩn khỏi menu

### G4.10 — Dashboard ✅ *19/08*

- [x] Chỉ số: hôm nay, ngày mai, trong tuần, trong tháng, trong năm
- [x] Thống kê theo lãnh đạo (từ `lanh_dao_lien_quan`)
- [x] Bấm thẻ → nhảy tới nhóm lịch tương ứng
- [x] **Tính từ dữ liệu thật**, không lưu số thủ công

**Nghiệm thu G4:** đủ 7 màn hình nghiệp vụ; mục Lịch công tác nằm trên Họp Không Giấy; xuất/nhập Excel hoạt động; test quy tắc giấy mời PASS.

---

## Giai đoạn 5 — Thư viện, ghi chú, đánh giá, phân quyền tài liệu

**Ước lượng:** 4–5 ngày · **Chặn bởi:** G4

### G5.1 — Thư viện văn bản → gộp vào mục Tài liệu ✅ *19/08*

> ✅ **Đã quét thư mục thư viện `1nDn4qE...` (17/08):** **189 thư mục nhưng chỉ 23 file.**
> Đây gần như là bộ khung phân loại được dựng sẵn 3 cấp mà chưa dùng — trong đó có 1 file
> `TEST_UPLOAD_THU_VIEN.txt`. 3 nhóm gốc (`06.BO_NGANH_KHAC`, `07.TINH_QN`, `99.KHAC`) rỗng hoàn toàn.
>
> Việc di trú thư viện vì thế **rất nhẹ**: phần việc là dựng lại cây 189 thư mục, không phải chuyển file.

| Nhóm gốc | File |
|---|---:|
| `08.DANG` | 6 |
| `01.QUOC_HOI` | 5 |
| `04.CUC_HAI_QUAN` | 5 |
| `05.CHI_CUC_HQKV8` | 4 |
| `02.CHINH_PHU` · `03.BO_TAI_CHINH` · gốc | 1 mỗi nhóm |
| `06.BO_NGANH_KHAC` · `07.TINH_QN` · `99.KHAC` | 0 |

> ⚠️ **Vẫn cần chốt trước khi code:** mục Tài liệu hiện dùng `frontend/src/services/portal.ts` →
> **portal_service (port 8004)**, bảng `portal.thu_muc` (5 dòng) và `portal.tai_lieu` (**0 dòng** — mới là khung).
> Tài liệu họp nằm ở `meeting_service`, thư viện sẽ nằm ở `portal_service` → hai service, hai cơ chế lưu file.
> Điểm nhẹ nhõm: cả hai bên đều gần như rỗng nên không có xung đột dữ liệu, chỉ là quyết định kiến trúc.

- [x] **Chốt: dùng `portal_service`** — mục Tài liệu trên giao diện đã trỏ sang đó, `portal.thu_muc` sẵn có cây cha–con và cột phân quyền, và thư viện văn bản là quản lý tài liệu chứ không phải nghiệp vụ họp
- [x] Dựng lại cây 189 thư mục theo 9 nhóm gốc (`01.QUOC_HOI` … `99.KHAC`)
- [x] Di trú 23 file, bỏ file `TEST_UPLOAD_THU_VIEN.txt`
- [x] Duyệt thư mục · breadcrumb · tìm kiếm theo tên/số hiệu · upload · xem trước · tải
- [x] ⛔ **Không** nhúng iframe Google Drive — kho phải nằm trên nền tảng

### G5.2 — Ghi chú và chia sẻ ✅ *20/08*

- [x] CRUD ghi chú (độc lập hoặc gắn cuộc họp), đính kèm file, chia sẻ cho người khác, đếm chưa đọc
- [x] Dữ liệu thật rất ít (6 ghi chú, 0 chia sẻ) → làm gọn, không cần tối ưu
- [x] 14 endpoint `/ghi-chu/*` · trang `/lich-cong-tac/ghi-chu` · 20 test PASS
- [x] Đính kèm dùng chung `meeting.tai_lieu` (CHECK `ck_tai_lieu_chu_the`), file ở `uploads/meeting/ghi-chu/{id}/` — **không cần migration**
- [x] ⚠️ Riêng tư tuyệt đối: **quản trị KHÔNG đọc được** ghi chú người khác. Người ngoài nhận 404 (không lộ ghi chú có tồn tại), người được chia sẻ nhận 403 khi thử sửa

### G5.3 — Đánh giá cuộc họp ✅ *20/08*

- [x] Chấm sao, giới hạn vai trò (lãnh đạo Chi cục + quản trị) theo `canRateMeetingPrep_`
- [x] Giữ liên kết user–meeting–rating khi di trú (102 bản ghi, 2 người chấm — cả hai là Phó Chi cục trưởng)
- [x] 5 endpoint `/danh-gia-chuan-bi/*` · sao trên trang chi tiết + huy hiệu trên thẻ lịch · bảng theo đơn vị ở Tổng quan · 13 test PASS
- [x] Quyền THAY chứ không port: `canRateMeetingPrep_` dò chuỗi trên họ tên + chức vụ + tên đăng nhập; ở đây dùng `vai_tro` (CCT/PCCT + ADMIN/SUPER_ADMIN). Chánh Văn phòng **không** nằm trong nhóm chấm — điểm này chấm chính công tác chuẩn bị của Văn phòng
- [x] Xem thì ai cũng xem được (giữ `publicPrepRating`); chấm lại là ghi đè nhờ `uq_danh_gia_cuoc_hop_nguoi`; không ai xoá được điểm người khác

> ⚠️ 82/102 lượt chấm mang sang thuộc cuộc họp **không ghi đơn vị chuẩn bị** → bảng theo đơn vị hiện phần lớn ở dòng "(Không ghi đơn vị chuẩn bị)". Sẽ tự hết khi lịch mới nhập đủ trường này.

### G5.4 — Phân quyền tài liệu 2 mức ✅ *20/08*

> ⚠️ Đây là **xây mới theo thiết kế**, không phải giữ hành vi cũ: `FILE_VISIBILITY` không có giá trị `LEADER_*` nào trong 587 file (chỉ `PUBLIC`=374, rỗng=213). Cơ chế này chưa từng vận hành thật.

- [x] 2 mức hạn chế: `LANH_DAO_CHI_CUC` (= `LEADER_CHICUC`) và `LANH_DAO_DON_VI` (= `LEADER_PHONGDOI_UP`), trên nền `CONG_KHAI`
- [x] Ánh xạ sang RBAC nền tảng qua `vai_tro` (CCT/PCCT/ADMIN) + `is_lanh_dao`, không dò chuỗi trên chức vụ
- [x] Toàn bộ tài liệu lịch sử giữ mức công khai nội bộ; thêm `PATCH /tai-lieu/{id}` để Văn phòng nâng mức từng file (trước G5.4 **không có** đường nào sửa `phan_quyen` sau khi tải lên)
- [x] Migration `meeting_023` — mở rộng CHECK `ck_tai_lieu_phan_quyen`, loại bỏ `HAN_CHE` (0 dòng, nhãn chưa từng được kiểm ở đâu), thêm chỉ mục một phần `idx_tai_lieu_han_che`
- [x] 11 test PASS — mỗi **đường ra** của tài liệu một test: danh sách (nhúng sẵn token xem), `/xem`, `/tai`, trình chiếu, xoá, sửa siêu dữ liệu

Ba quyết định thiết kế ghi lại để khỏi tranh luận lại:

1. **Người tải lên luôn xem lại được file của mình** — thư ký nâng mức rồi không mở lại được để kiểm tra là vô lý, và họ vốn đã có file trong tay.
2. **Không ai đặt được mức cao hơn bậc của chính mình** (`DOC_LEVEL_TOO_HIGH`) — đặt xong tự mình không mở lại được là cách chắc chắn nhất để mất tài liệu.
3. **Tài liệu hạn chế không trình chiếu được** — trình chiếu là đẩy nội dung ra cả phòng họp, trong đó có người không đủ mức. Chặn tại thao tác của chủ toạ (`DOCUMENT_RESTRICTED`), không để cả phòng nhận 403 khi tải nội dung.

> Không xem được thì cũng không xoá/sửa được: thao tác trên tài liệu chưa từng thấy nội dung là mù, và là đường vòng để phá tài liệu hạn chế. Mọi lần đổi mức đều ghi nhật ký kèm **giá trị cũ** (`phan_quyen_cu`).

### G4.11 — Quản trị danh mục ✅ *21/08*

> 🔴 **Phát hiện khi rà soát hồ sơ nguồn (21/08): kế hoạch đã BỎ SÓT mục này.**
> Yêu cầu chuyển đổi mục II.15 đòi *“quản lý các danh mục dùng chung của phần mềm
> như đơn vị, loại lịch, trạng thái và các danh mục cấu hình khác”*, bảng nghiệm thu
> XI.9 kiểm lại điểm này. Hệ cũ có màn hình `settings` (“QUẢN TRỊ DANH MỤC”) chạy
> trên sheet `SETUP` với **12 nhóm**. Bên ta viết chết trong mã nguồn — thêm một
> loại lịch phải gọi người sửa mã, đúng thứ yêu cầu đòi bỏ.

- [x] Bảng `meeting.danh_muc` + migration `meeting_024` — 4 nhóm, 24 mục
- [x] 6 endpoint `/danh-muc/*` · trang `/lich-cong-tac/danh-muc` · 22 test PASS
- [x] Nối vào nghiệp vụ: ô Loại lịch, ô Loại tài liệu (cả modal Thêm lịch lẫn
      trang chi tiết), gợi ý ô Địa điểm

**Chỉ mang 4 trong 12 nhóm.** Tám nhóm còn lại nền tảng đã có nơi quản lý thật,
đưa vào đây là đẻ ra bản sao thứ hai rồi hai bên lệch nhau:

| Nhóm hệ cũ | Nền tảng quản ở đâu |
|---|---|
| `ROLE_LIST`, `SCOPE_LIST` | `public.vai_tro` + RBAC |
| `DEPT_LIST` (13) | `public.don_vi` (15 đơn vị thật) |
| `LEADER_LIST` | `cong_chuc.is_lanh_dao` |
| `USER_STATUS` | `cong_chuc.is_active` |
| `PARTICIPANT_ROLE`, `PARTICIPANT_PERMISSION` | `thanh_phan.loai_tham_du` + phân quyền tài liệu G5.4 |
| `YES_NO` | là kiểu dữ liệu, không phải danh mục |

Ba quyết định thiết kế ghi lại để khỏi tranh luận lại:

1. **Cờ `he_thong` tách “đổi tên” khỏi “đổi mã”.** Đếm thực tế: `trang_thai` có
   **62 điểm rẽ nhánh** trong `meeting_service/`, `loai_lich` có **0**. Nên trạng
   thái sửa được nhãn (“Đã đăng” → “Đã công bố”) nhưng không đổi mã / xoá / tắt;
   loại lịch thì tự do, trừ `HOP` là giá trị mặc định nên khoá lại.
2. **Mã bất biến kể cả với mục thường** (`DM_KHONG_DOI_MA`). Dữ liệu đã ghi tham
   chiếu bằng mã — đổi là làm mồ côi hàng loạt bản ghi mà không báo ai.
3. **Đang có bản ghi dùng thì chỉ được TẮT, không xoá** (`DM_DANG_SU_DUNG`, kèm
   số bản ghi). Thêm lại mã đã tắt thì **bật lại đúng mục cũ**, không báo lỗi cụt
   và không đẻ mục thứ hai — dữ liệu cũ mang mã đó hiện đúng nhãn trở lại ngay.

> ⚠️ **Bỏ CHECK `ck_cuoc_hop_loai_lich`.** Giữ lại thì đơn vị thêm loại lịch mới
> sẽ bị cơ sở dữ liệu chối, tức là màn hình quản trị vô nghĩa. Lưới chặn chuyển
> xuống tầng dịch vụ (`_kiem_loai_lich`). Đổi lại, đường ghi thẳng bằng SQL
> (script di trú) mất lưới an toàn — chấp nhận, vì đó là đường chỉ người viết mã
> đi. CHECK của `trang_thai` **giữ nguyên**: mã trạng thái không bao giờ đổi.

**Bổ sung `TIEP_DOAN`** — loại lịch thứ 7 của hệ cũ mà đợt chuyển đổi làm sót.
Dữ liệu lịch sử không mất gì (490 sự kiện di trú không dùng loại này lần nào),
nhưng Văn phòng trước đó **không tạo được** lịch tiếp đoàn. Thiếu ở cả ba tầng:
CHECK cơ sở dữ liệu, từ điển nhãn backend, ô chọn giao diện.

**Bổ sung `PHONG_HOP`** — `ROOM_LIST` của hệ cũ, 5 địa điểm. `dia_diem` vẫn là
chuỗi tự do (đã có 6 tháng dữ liệu gõ tay, đổi sang lưu mã là phải di trú lại cả
cột), nên danh mục này đóng vai **gợi ý** qua `datalist` để lần sau mọi người gõ
giống nhau — không phải ràng buộc.

### G4.12 — Mỗi tài liệu một loại riêng ✅ *21/08*

- [x] Hàng đợi tải lên chuyển từ `File[]` sang `FileCho[]` (`{ file, loai }`)
- [x] Ô chọn loại phía trên thành **loại mặc định** cho file thả vào tiếp theo;
      mỗi dòng trong hàng đợi có ô chọn riêng, hiện ngay cạnh tên file
- [x] Loại đã gán mà đơn vị vừa tắt vẫn hiện trong ô chọn của dòng đó — không
      thì ô nhảy sang loại khác mà người dùng không hề bấm

> Trước đó cả hàng đợi dùng chung một loại: nộp giấy mời và báo cáo trong cùng
> một lượt thì phải tải hai lần.

### G5.5 — Chặn thả file trực tiếp

- [ ] Mọi tài liệu chỉ vào kho qua API upload có xác thực
- [ ] 📣 **Thông báo trước cho Văn phòng và các đơn vị** — hiện 49% tài liệu (605/1.223 file) vào kho bằng đường thả trực tiếp. Bật lặng lẽ sẽ có người kéo file vào Drive rồi tưởng đã nộp

**Nghiệm thu G5:** thư viện duyệt/tìm/upload/tải hoạt động không phụ thuộc Drive; phân quyền 2 mức đúng theo vai trò.

---

## Giai đoạn 6 — Chạy song song và cắt chuyển

**Ước lượng:** 2 tuần chạy song song · **Chặn bởi:** G3, G4, G5

- [ ] **G6.1** — Chạy migration trên prod `kpi_haiquan` (⚠️ **cần user duyệt từng lần**, xem `CLAUDE.md`)
- [ ] **G6.2** — Di trú lần cuối phần dữ liệu phát sinh từ G1.2 đến nay
- [ ] **G6.3** — Bà Hà rà 34 thư mục trên màn hình đối soát (ước 1 buổi)
- [ ] **G6.4** — Mở cho người dùng đối chiếu, chạy song song với lichkv8
- [ ] **G6.5** — Khoá ghi trên Google Sheets sau khi lãnh đạo xác nhận dữ liệu đủ
- [ ] **G6.6** — Dừng deploy Apps Script Web App + gỡ GitHub Pages
  - ⛔ **Không tự ý tắt** — chỉ làm sau xác nhận của lãnh đạo, đây là hệ nhiều người đang dùng thật
- [ ] **G6.7** — Xử lý phụ thuộc Google, **sau khi** xác nhận tài liệu đã sang cloud thành công:
  - [ ] Thu hồi chia sẻ công khai thư mục Drive `1AkMxFT-...` và `1nDn4qE...`
  - [ ] Chuyển file Sheets `LICH CONG TAC HQKV8` sang chỉ đọc, giữ làm bản lưu, **thu hồi chia sẻ** (file này chứa 505 mật khẩu dạng rõ)
  - [ ] Rà các link Drive đã gửi kèm giấy mời / email trước đây — sẽ chết sau khi thu hồi, cần thông báo
- [ ] **G6.8** — Bàn giao: mã nguồn, tài khoản quản trị, hướng dẫn sử dụng, hướng dẫn sao lưu/khôi phục, biên bản đối chiếu

---

## Rủi ro và điểm dễ mất

| # | Rủi ro | Cách xử lý |
|---|--------|-----------|
| 1 | **Quy tắc giấy mời** viết lại từ đặc tả sẽ sai — đặc tả chỉ mô tả 1 câu, mã thật là 3 hàm với thứ tự ưu tiên | Port nguyên văn regex + test theo ca đã tinh chỉnh (G4.6) |
| 2 | **Phân quyền trực ban** hệ cũ dò chuỗi → ai có "Văn phòng"/"lãnh đạo" trong hồ sơ đều thành admin toàn Chi cục | Thay bằng quyền chức năng thật, không port (G4.7) |
| 3 | `created_by` NOT NULL nhưng 272 dòng `NGUOI_TAO='import'` | Tạo tài khoản hệ thống trước khi ETL (G3.1) |
| 4 | `DA_KET_THUC` không phải 1 cuộc họp mà là kho chứa 13 cuộc họp con | Script đi thêm 1 cấp (G3.2) |
| 5 | Tài liệu **tiền hệ thống** (24/01 → trước 09/03) không có bản ghi cuộc họp để gắn | Lựa chọn "tạo cuộc họp lịch sử từ thư mục" trên màn hình đối soát (G4.9) |
| 6 | Thư viện thuộc `portal_service` còn tài liệu họp thuộc `meeting_service` → 2 cơ chế lưu file | Chốt phương án trước khi code (G5.1). Cả hai bên gần như rỗng nên không xung đột dữ liệu |
| 7 | Hệ cũ vẫn phát sinh dữ liệu trong lúc làm | Di trú lần cuối ở G6.2, khoá ghi ở G6.5 |
| 8 | Chặn thả file là thay đổi thói quen của 49% lượng tài liệu | Thông báo trước, không bật lặng lẽ (G5.5) |
| 9 | Múi giờ — hệ cũ dùng `CFG.TZ`, nền tảng dùng TIMESTAMPTZ giờ VN | Chuẩn hoá khi ETL, kiểm tra giờ bắt đầu/kết thúc không lệch |

---

## Tổng hợp ước lượng

| Giai đoạn | Nội dung | Ngày công |
|---|---|---:|
| G1 | Chốt phạm vi, lấy dữ liệu gốc | 1 |
| G2 | Mở rộng schema `meeting` | 3 |
| G3 | Di trú dữ liệu + 1.223 file | 5–6 |
| G4 | API và giao diện Lịch công tác | 10–14 |
| G5 | Thư viện, ghi chú, đánh giá, phân quyền | 4–5 |
| | **Tổng xây dựng** | **23–29** |
| G6 | Chạy song song + cắt chuyển | 2 tuần |

---

## Tiêu chí nghiệm thu cuối

- [ ] Mục **Lịch công tác** xuất hiện **phía trên** Họp Không Giấy trong điều hướng
- [ ] Tạo/sửa/huỷ cuộc họp phản ánh đúng và kịp thời giữa Họp Không Giấy và Lịch công tác
- [ ] Bấm sự kiện họp trên lịch mở đúng chi tiết cuộc họp tương ứng
- [ ] Toàn bộ cuộc họp, bản ghi trực ban, file đính kèm được di trú đầy đủ, đối soát khớp số lượng
- [ ] Mọi `ma_lich` `LHxxxx` lịch sử **giữ nguyên**, liên kết đúng tài liệu
- [ ] Người dùng lichkv8 cũ đăng nhập bằng đúng tài khoản SSO, không tạo mới
- [ ] Phân quyền xem tài liệu 2 mức hoạt động đúng sau ánh xạ RBAC
- [ ] Trực ban đúng quy trình nộp/khoá theo đơn vị, phạm vi thứ 7 + chủ nhật
- [ ] Các chức năng chính **không còn phụ thuộc** Google Apps Script / Sheets / Drive
- [ ] Có biên bản đối chiếu dữ liệu và file, nêu rõ trường hợp ngoại lệ

---

## Việc nằm ngoài phạm vi dự án này

Phát hiện trong lúc khảo sát, cần xử lý riêng:

- [ ] **Báo cáo Thống kê tài liệu của lichkv8 đang sai** — đọc từ `MEETING_FILE` nên báo đơn vị chưa nộp trong khi tài liệu đã có trên Drive (cá biệt `LH0347` bảng ghi 1 file, Drive có 14). Đáng sửa ngay trên hệ cũ.
- [ ] **505 mật khẩu dạng rõ trong Google Sheets** — sẽ tự tiêu khi chuyển sang SSO, nhưng trong lúc chờ thì file vẫn đang chia sẻ. Nhật ký có 225 lượt `LOGIN_FAIL` đáng rà.
- [ ] **Kho tài liệu đang công khai với bất kỳ ai có link** — tải được toàn bộ cấu trúc không cần đăng nhập Google. Xử lý ở G6.7.

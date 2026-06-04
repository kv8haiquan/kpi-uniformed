# CHI_TIEU_BUSINESS_RULES.md
## Module Quản lý Chỉ tiêu Đơn vị — Nền tảng Số HQKV8

> **Phiên bản:** 1.0 | **Ngày:** 04/06/2026
> **Schema:** `chi_tieu` | **Service:** chi_tieu_service (port 8007)
> **Nguồn nghiệp vụ:** File rà soát chỉ tiêu các đơn vị T4/2026, các Kế hoạch công tác của Chi cục
> **Quan hệ với KPI cá nhân:** ĐỘC LẬP HOÀN TOÀN (không tính vào điểm KPI công chức)

---

## 1. TỔNG QUAN & PHẠM VI

Module này quản lý **chỉ tiêu công tác cấp ĐƠN VỊ** (Phòng/Đội/HQ cửa khẩu), tách bạch hoàn toàn với module KPI đánh giá cá nhân công chức.

| Tiêu chí | Module KPI cá nhân (hiện có) | Module Chỉ tiêu đơn vị (MỚI) |
|----------|------------------------------|------------------------------|
| Đối tượng | Từng công chức | Từng đơn vị |
| Dữ liệu gốc | Kê khai sản phẩm/công việc | Đăng ký + kết quả chỉ tiêu theo kế hoạch |
| Schema | `public` | `chi_tieu` |
| Service | port 8000 | port 8007 |
| Liên kết | — | Không ghi vào KPI cá nhân |

### 1.1. Các lĩnh vực công tác (7 nhóm chỉ tiêu)

Mỗi lĩnh vực gắn với một (hoặc nhiều) văn bản kế hoạch của Chi cục:

| Mã | Lĩnh vực | Văn bản căn cứ (ví dụ) |
|----|----------|------------------------|
| GSQL | Giám sát quản lý | KH 24/KH-HQKV8 |
| THUE | Thuế XNK | KH 306, KH 1342 |
| KTSTQ | Kiểm tra sau thông quan | KH 251, CV 851 |
| DAOTAO | Đào tạo, tập huấn | KH 91 |
| QLRR | Quản lý rủi ro | QĐ 51, QĐ 56 |
| CBL | Kiểm soát chống buôn lậu | KH 15 |
| TRUYENTHONG | Truyền thông | — |

> Danh mục lĩnh vực và chỉ tiêu là **dữ liệu động**: quản trị viên (`QT_CHI_TIEU`) thêm/sửa được mà không cần lập trình lại.

---

## 2. KHÁI NIỆM CỐT LÕI

### 2.1. Chỉ tiêu (danh mục)

Mỗi chỉ tiêu có **đơn vị tính riêng** (triệu USD, tỷ đồng, số vụ, số doanh nghiệp, số hội nghị, %...). Vì khuôn dữ liệu của mọi chỉ tiêu giống nhau (xem 2.3), hệ thống dùng **một danh mục chỉ tiêu chung** thay vì code cứng từng chỉ tiêu.

### 2.2. Hai mức chỉ tiêu năm

Một số chỉ tiêu có 2 mức giao năm:

| Mức | Ý nghĩa | Ví dụ |
|-----|---------|-------|
| **PHAP_LENH** | Chỉ tiêu pháp lệnh (bắt buộc) | Thuế: 18.300 tỷ; KTSTQ số thu: 5.000 triệu |
| **PHAN_DAU** | Chỉ tiêu phấn đấu | Thuế: 25.000 tỷ; KTSTQ số thu: 35.000 triệu |

Chỉ tiêu chỉ có 1 mức thì chỉ tạo dòng `PHAP_LENH`.

### 2.3. Khuôn dữ liệu lặp lại của mọi chỉ tiêu (theo tháng)

| Trường | Nguồn | Ghi chú |
|--------|-------|---------|
| Đăng ký tháng | Người theo dõi nhập đầu tháng | Có thể "Không đăng ký" |
| Kết quả thực hiện | Người theo dõi nhập cuối tháng | |
| Đánh giá | Tự tính + cho phép ghi đè bằng chữ | Vd "Đạt 142%", "Vượt chỉ tiêu", "Chưa đạt" |
| Chỉ tiêu giao năm | Từ bảng giao năm | Theo từng mức |
| Lũy kế thực hiện năm | **Tự tính** | = lũy kế đầu kỳ + Σ kết quả đã duyệt |
| Đạt% | **Tự tính** | Lũy kế / chỉ tiêu giao năm |

### 2.4. Phân biệt 2 trạng thái "không có số"

| Trạng thái | Ý nghĩa | Cách thể hiện |
|------------|---------|---------------|
| **Không giao chỉ tiêu** | Đơn vị KHÔNG có dòng giao năm cho chỉ tiêu này | Không tồn tại bản ghi giao năm |
| **Không đăng ký** | Đơn vị CÓ chỉ tiêu giao năm nhưng tháng này không đăng ký | `khong_dang_ky = TRUE` |

---

## 3. VAI TRÒ & PHÂN QUYỀN

Hai vai trò bổ sung (`platform_role`), gán thêm cho công chức, **không** thay đổi `vai_tro`/`cap_bac` hiện có:

| Mã role | Tên | Phạm vi |
|---------|-----|---------|
| `THEO_DOI_CHI_TIEU` | Người theo dõi chỉ tiêu | Gán theo đơn vị (`pham_vi.don_vi_ids`); linh hoạt — 1 người có thể theo dõi nhiều đơn vị, và 1 đơn vị có thể có nhiều người theo dõi (không ràng buộc cứng) |
| `QT_CHI_TIEU` | Quản trị chỉ tiêu | Toàn Chi cục: quản lý danh mục + giao chỉ tiêu năm + xem báo cáo |

Việc **duyệt** do **Trưởng đơn vị (Trưởng ĐV)** đảm nhiệm — dùng `cap_bac = TRUONG_DON_VI` sẵn có, không cần role mới.

### 3.1. Ma trận phân quyền

| Chức năng | Người theo dõi CT | Trưởng ĐV | QT chỉ tiêu | LĐ Chi cục |
|-----------|:----------------:|:---------:|:-----------:|:----------:|
| Quản lý danh mục lĩnh vực/chỉ tiêu | | | ✓ | ✓ |
| Giao chỉ tiêu năm cho đơn vị | | | ✓ | ✓ |
| Đăng ký chỉ tiêu tháng | ✓ | | | |
| Sửa đăng ký (gửi duyệt lại) | ✓ | | | |
| Nhập kết quả cuối tháng | ✓ | | | |
| **Duyệt** đăng ký / sửa / kết quả | | ✓ | | |
| Mở khóa bản ghi đã chốt | | | ✓ | ✓ |
| Xem báo cáo đơn vị mình | ✓ | ✓ | | |
| Xem báo cáo toàn Chi cục | | | ✓ | ✓ |

> Người theo dõi chỉ thao tác trong **phạm vi đơn vị được gán**. Trưởng ĐV chỉ duyệt bản ghi **của đơn vị mình**.

---

## 4. QUY TRÌNH NGHIỆP VỤ & MÁY TRẠNG THÁI

Mỗi bản ghi = một bộ ba `(đơn vị, chỉ tiêu, tháng/năm)` đi qua các trạng thái sau:

```
                  ┌─────────────┐
   tạo/sửa  ──────►   NHAP       │ (Người theo dõi soạn đăng ký)
                  └──────┬───────┘
            gửi duyệt    │
                  ┌──────▼─────────────┐
                  │ CHO_DUYET_DANG_KY  │ ──từ chối──► NHAP
                  └──────┬─────────────┘
            TĐV duyệt    │
                  ┌──────▼─────────────┐
       ┌─────────►│  DA_DUYET_DANG_KY  │
       │          └──────┬─────────────┘
       │   muốn sửa      │            nhập kết quả cuối tháng
       │  ┌──────────────▼──────┐   ┌──────────────────────┐
       │  │   CHO_DUYET_SUA     │   │  CHO_DUYET_KET_QUA   │◄─┐
       │  └──────────┬──────────┘   └──────────┬───────────┘  │
       └──TĐV duyệt──┘            TĐV duyệt     │      từ chối─┘
                                        ┌───────▼────────────┐
                                        │  DA_DUYET_KET_QUA  │ (CHỐT → tính lũy kế)
                                        └────────────────────┘
```

### 4.1. Đầu tháng — Đăng ký chỉ tiêu

1. Người theo dõi chọn tháng/năm → hệ thống tạo sẵn danh sách chỉ tiêu mà đơn vị **có giao năm**.
2. Nhập giá trị đăng ký từng chỉ tiêu (hoặc đánh dấu "Không đăng ký").
3. Gửi Trưởng ĐV duyệt → `CHO_DUYET_DANG_KY`.
4. Trưởng ĐV **duyệt** (`DA_DUYET_DANG_KY`) hoặc **từ chối** (kèm lý do → quay về `NHAP`).

### 4.2. Sửa đăng ký đã duyệt

- Từ `DA_DUYET_DANG_KY`, người theo dõi tạo yêu cầu sửa → `CHO_DUYET_SUA` → Trưởng ĐV duyệt → quay lại `DA_DUYET_DANG_KY` với giá trị mới. Mọi lần sửa đều ghi `lich_su_duyet`.

### 4.3. Cuối tháng — Nhập & duyệt kết quả

1. Người theo dõi nhập "Kết quả thực hiện" cho từng chỉ tiêu.
2. Gửi duyệt → `CHO_DUYET_KET_QUA`.
3. Trưởng ĐV duyệt → `DA_DUYET_KET_QUA` (chốt) hoặc **từ chối**.
4. Khi chốt, hệ thống cập nhật lũy kế năm & Đạt%.

> **Từ chối kết quả** (`TU_CHOI_KET_QUA`): bản ghi quay về `DA_DUYET_DANG_KY` (KHÔNG có trạng thái "đang nhập kết quả" riêng — việc nhập kết quả diễn ra ngay trên trạng thái `DA_DUYET_DANG_KY`). **Giá trị kết quả cũ (`gia_tri_ket_qua`) được GIỮ NGUYÊN** để người theo dõi nhìn con số bị từ chối + lý do mà sửa, không nhập lại từ đầu. Hệ thống chỉ reset `ngay_gui_ket_qua`/`ngay_duyet_ket_qua` về NULL và ghi `ly_do_tu_choi` + `lich_su_duyet` (snapshot trước/sau). Sửa lại `gia_tri_ket_qua` → tính lại `danh_gia_tu_dong` → gửi duyệt lần nữa.

### 4.4. Khóa & mở khóa

- Sau `DA_DUYET_KET_QUA`, bản ghi **bị khóa**. Muốn sửa phải được `QT_CHI_TIEU`/LĐ Chi cục mở khóa (ghi audit).

### 4.5. Mốc thời gian (cấu hình trong `platform_config`)

| Mốc | Mặc định | Khóa cấu hình |
|-----|----------|---------------|
| Hạn đăng ký chỉ tiêu tháng | Ngày 5 của tháng | `chi_tieu.han_dang_ky_ngay` |
| Hạn nhập kết quả tháng | Ngày 3 tháng sau | `chi_tieu.han_ket_qua_ngay` |

> Quá hạn: hệ thống cảnh báo (không tự khóa), Trưởng ĐV/QT vẫn duyệt được.

---

## 5. CÔNG THỨC TÍNH

### 5.1. Đạt% theo tháng (so với đăng ký)

```
Đạt%_tháng = (Kết quả thực hiện / Giá trị đăng ký tháng) × 100
```
> Nếu "Không đăng ký" hoặc đăng ký = 0 → không tính %, để trống.

### 5.2. Lũy kế năm

```
Lũy kế năm (đến tháng N) = Lũy kế đầu kỳ + Σ (Kết quả đã DUYỆT của tháng 1..N)
```
> `Lũy kế đầu kỳ` (`luy_ke_dau_ky`) phục vụ khi nhập liệu giữa năm (số liệu đã phát sinh trước khi dùng phần mềm). Mặc định 0.
>
> ⚠️ **Lũy kế luôn cắt theo THÁNG ĐANG XEM (N), không cộng toàn bộ năm.** Khi xem báo cáo tháng 4, lũy kế chỉ gồm kết quả đã duyệt của tháng 1→4, kể cả khi tháng 5, 6 đã chốt. Báo cáo phải truyền tham số tháng vào điều kiện `thang <= N` (xem View hỗ trợ trong DATABASE_DESIGN).

### 5.3. Đạt% theo năm (so với chỉ tiêu giao)

```
Đạt%_năm = (Lũy kế năm / Chỉ tiêu giao năm) × 100      [theo từng mức PHAP_LENH / PHAN_DAU]
```

### 5.4. Nhãn đánh giá tự động

| Điều kiện | Nhãn gợi ý |
|-----------|-----------|
| Đạt%_tháng ≥ 100 | `Đạt {x}%` (hoặc `Vượt chỉ tiêu`) |
| 0 < Đạt%_tháng < 100 | `Đạt {x}%` |
| Kết quả = 0, có đăng ký | `Chưa đạt` |
| Không đăng ký | `Không đăng ký` |

> Nhãn tự động chỉ là **gợi ý**; người theo dõi/Trưởng ĐV được ghi đè bằng chữ tùy chỉnh (vd "Đã thực hiện T3").
>
> ⚠️ **`danh_gia_tu_dong` phải được tính lại NGAY mỗi khi `gia_tri_ket_qua` hoặc `gia_tri_dang_ky` thay đổi** (nhập/sửa kết quả, duyệt sửa đăng ký, mở khóa nhập lại). Không để nhãn cũ tồn tại sau khi số liệu đã đổi. `danh_gia_ghi_chu` (chữ ghi đè thủ công) thì giữ nguyên cho tới khi người dùng tự sửa.

---

## 6. AUDIT & CẢNH BÁO

### 6.1. Sự kiện ghi `chi_tieu.lich_su_duyet`

Gửi duyệt đăng ký, duyệt/từ chối đăng ký, gửi sửa, duyệt sửa, gửi kết quả, duyệt/từ chối kết quả, mở khóa.

### 6.2. Cảnh báo tự động

| Cảnh báo | Đối tượng nhận |
|----------|----------------|
| Quá hạn chưa đăng ký chỉ tiêu tháng | Người theo dõi, Trưởng ĐV |
| Quá hạn chưa nhập kết quả | Người theo dõi, Trưởng ĐV |
| Có bản ghi đang `CHO_DUYET_*` chờ xử lý | Trưởng ĐV |
| Đạt%_năm < ngưỡng cảnh báo (cấu hình) | QT chỉ tiêu, LĐ Chi cục |

> Thông báo gửi qua module dùng chung (`common.thong_bao`) theo Internal API hiện có — không tự dựng cơ chế thông báo riêng.

---

## 7. BÁO CÁO

| Báo cáo | Mô tả |
|---------|-------|
| Rà soát theo tháng | Tái lập đúng biểu Excel: theo lĩnh vực → chỉ tiêu → đơn vị, đủ 6 cột |
| Lũy kế năm theo đơn vị | Đạt% năm từng chỉ tiêu (2 mức nếu có) |
| Tổng hợp toàn Chi cục | Gộp tất cả đơn vị, xuất Excel |

---

## 8. DANH MỤC THUẬT NGỮ

| Thuật ngữ | Định nghĩa |
|-----------|------------|
| Chỉ tiêu | Mục tiêu công tác giao cho đơn vị theo kế hoạch |
| Lĩnh vực | Nhóm chỉ tiêu theo mảng công tác (GSQL, THUE...) |
| Giao năm | Mức chỉ tiêu cả năm giao cho 1 đơn vị |
| Đăng ký tháng | Mức đơn vị tự đăng ký thực hiện trong tháng |
| Lũy kế | Tổng kết quả đã duyệt cộng dồn trong năm |
| Người theo dõi CT | Công chức được gán role `THEO_DOI_CHI_TIEU` của đơn vị |

---

## 9. LỊCH SỬ THAY ĐỔI

| Phiên bản | Ngày | Nội dung |
|-----------|------|----------|
| 1.0 | 04/06/2026 | Bản đầu tiên — định nghĩa nghiệp vụ module Chỉ tiêu đơn vị |
| 1.1 | 04/06/2026 | Port 8004→8007 (tránh trùng portal); nới "1 người/đơn vị"; làm rõ từ chối kết quả → DA_DUYET_DANG_KY; lũy kế cắt theo tháng đang xem; tính lại nhãn khi đổi số liệu |

# CHI_TIEU_API_SPECS.md
## Đặc tả REST API — Module Quản lý Chỉ tiêu Đơn vị

> **Phiên bản:** 1.0 | **Ngày:** 04/06/2026
> **Service:** chi_tieu_service (port 8004) | **Base URL:** `https://kpi.kv08.vn/api/v1/chi-tieu`
> **Tham chiếu:** CHI_TIEU_BUSINESS_RULES.md, CHI_TIEU_DATABASE_DESIGN.md, API_CONTRACT_BETWEEN_MODULES.md

---

## 1. QUY ƯỚC CHUNG

- Xác thực: JWT Bearer (cùng `SECRET_KEY` với KPI backend). Backend đọc `platform_roles` và `pham_vi.don_vi_ids`.
- Response/error format, status code, phân trang: **giống chuẩn dự án** (`{success, data, message}` / `{success:false, error:{code,message,details}}`).
- Mã lỗi module dùng tiền tố `CT_ERR_xxx`.

### 1.1. Mã lỗi riêng

| Code | Ý nghĩa |
|------|---------|
| `CT_ERR_001` | Không có quyền theo dõi đơn vị này |
| `CT_ERR_002` | Bản ghi đã khóa, không sửa được |
| `CT_ERR_003` | Sai trạng thái cho thao tác (vd duyệt khi chưa gửi) |
| `CT_ERR_004` | Chỉ Trưởng ĐV của đơn vị mới được duyệt |
| `CT_ERR_005` | Đơn vị chưa được giao chỉ tiêu năm |
| `CT_ERR_006` | Trùng đăng ký (đơn vị, chỉ tiêu, tháng, năm) |

---

## 2. DANH SÁCH API ROUTER

| Prefix | Tag | Quyền chính |
|--------|-----|-------------|
| `/linh-vuc` | Danh mục lĩnh vực | QT_CHI_TIEU (ghi), mọi vai trò (đọc) |
| `/danh-muc` | Danh mục chỉ tiêu | QT_CHI_TIEU (ghi) |
| `/giao-nam` | Giao chỉ tiêu năm | QT_CHI_TIEU (ghi) |
| `/dang-ky` | Đăng ký + kết quả tháng | THEO_DOI_CHI_TIEU |
| `/duyet` | Duyệt của Trưởng ĐV | TRUONG_DON_VI |
| `/bao-cao` | Báo cáo & xuất Excel | tùy phạm vi |

---

## 3. DANH MỤC (QT_CHI_TIEU)

### 3.1. Lĩnh vực
```
GET  /linh-vuc                      # danh sách (mọi vai trò đọc)
POST /linh-vuc                      # tạo (QT_CHI_TIEU)
PUT  /linh-vuc/{id}
```
`POST /linh-vuc` body:
```json
{ "ma_linh_vuc": "GSQL", "ten_linh_vuc": "Giám sát quản lý",
  "van_ban_ke_hoach": "KH 24/KH-HQKV8 ngày 06/01/2026", "thu_tu": 1 }
```

### 3.2. Chỉ tiêu
```
GET  /danh-muc?linh_vuc_id=&is_active=true
POST /danh-muc
PUT  /danh-muc/{id}
DELETE /danh-muc/{id}               # soft delete
```
`POST /danh-muc` body:
```json
{ "linh_vuc_id": "uuid", "ma_chi_tieu": "GSQL_01",
  "ten_chi_tieu": "Kim ngạch XNK (không gồm KNQ, TNTX)",
  "don_vi_tinh": "triệu USD", "kieu_du_lieu": "THAP_PHAN",
  "co_phan_dau": false, "thu_tu": 1 }
```

### 3.3. Giao chỉ tiêu năm
```
GET  /giao-nam?nam=2026&don_vi_id=
POST /giao-nam
PUT  /giao-nam/{id}
```
`POST /giao-nam` body (mỗi mức 1 bản ghi):
```json
{ "don_vi_id": "uuid", "chi_tieu_id": "uuid", "nam": 2026,
  "loai_muc": "PHAP_LENH", "gia_tri_giao": 6885, "luy_ke_dau_ky": 2444 }
```

---

## 4. ĐĂNG KÝ & KẾT QUẢ (THEO_DOI_CHI_TIEU)

> Backend kiểm tra đơn vị thao tác ∈ `pham_vi.don_vi_ids`, nếu không → `403 CT_ERR_001`.

### 4.1. Lấy danh sách chỉ tiêu cần đăng ký trong tháng
```
GET /dang-ky?don_vi_id=&thang=4&nam=2026
```
Trả về mỗi chỉ tiêu mà đơn vị **có giao năm**, kèm trạng thái bản ghi (nếu đã tạo).

### 4.2. Tạo / sửa đăng ký (khi NHAP)
```
POST /dang-ky                       # tạo mới
PUT  /dang-ky/{id}                  # sửa khi trạng thái NHAP
```
Body:
```json
{ "don_vi_id": "uuid", "chi_tieu_id": "uuid", "thang": 4, "nam": 2026,
  "khong_dang_ky": false, "gia_tri_dang_ky": 482 }
```

### 4.3. Gửi Trưởng ĐV duyệt đăng ký
```
POST /dang-ky/{id}/gui-duyet        # NHAP → CHO_DUYET_DANG_KY
```

### 4.4. Yêu cầu sửa đăng ký đã duyệt
```
POST /dang-ky/{id}/yeu-cau-sua      # DA_DUYET_DANG_KY → CHO_DUYET_SUA
```
Body: `{ "gia_tri_dang_ky_moi": 500, "ly_do": "Điều chỉnh theo chỉ đạo" }`

### 4.5. Nhập & gửi kết quả cuối tháng
```
POST /dang-ky/{id}/nhap-ket-qua     # lưu nháp kết quả (DA_DUYET_DANG_KY)
POST /dang-ky/{id}/gui-ket-qua      # → CHO_DUYET_KET_QUA
```
Body nhập kết quả:
```json
{ "gia_tri_ket_qua": 684, "danh_gia_ghi_chu": "Vượt chỉ tiêu" }
```
> `danh_gia_tu_dong` ("Đạt 142%") do hệ thống tự tính khi lưu.

---

## 5. DUYỆT (TRUONG_DON_VI)

> Backend kiểm tra người duyệt là Trưởng ĐV **đúng đơn vị** của bản ghi, nếu không → `403 CT_ERR_004`.

### 5.1. Hàng chờ duyệt
```
GET /duyet/cho-xu-ly?loai=DANG_KY        # loai = DANG_KY | SUA | KET_QUA
```

### 5.2. Duyệt / từ chối
```
POST /duyet/{id}/duyet                   # chuyển trạng thái theo loại đang chờ
POST /duyet/{id}/tu-choi                 # kèm lý do → quay lại bước trước
```
`tu-choi` body: `{ "ly_do_tu_choi": "Số liệu chưa khớp báo cáo tuần" }`

Logic chuyển trạng thái khi **duyệt**:

| Trạng thái hiện tại | Sau khi duyệt |
|---------------------|---------------|
| CHO_DUYET_DANG_KY | DA_DUYET_DANG_KY |
| CHO_DUYET_SUA | DA_DUYET_DANG_KY (áp giá trị mới) |
| CHO_DUYET_KET_QUA | DA_DUYET_KET_QUA + `is_khoa=true` + cập nhật lũy kế |

### 5.3. Mở khóa (QT_CHI_TIEU / LĐ Chi cục)
```
POST /dang-ky/{id}/mo-khoa               # DA_DUYET_KET_QUA → DA_DUYET_DANG_KY
```

---

## 6. BÁO CÁO

### 6.1. Rà soát theo tháng (tái lập biểu Excel)
```
GET /bao-cao/ra-soat?thang=4&nam=2026[&linh_vuc_id=][&don_vi_id=]
```
Trả về cấu trúc lồng: `linh_vuc[] → chi_tieu[] → dong_don_vi[]`, mỗi dòng gồm: đăng ký tháng, kết quả, đánh giá, chỉ tiêu giao năm (theo mức), lũy kế năm, đạt%.

### 6.2. Lũy kế năm
```
GET /bao-cao/luy-ke?nam=2026&don_vi_id=
```

### 6.3. Xuất Excel
```
GET /bao-cao/ra-soat/export?thang=4&nam=2026     # trả file .xlsx
```

---

## 7. INTERNAL API

Module này **độc lập**, không đẩy dữ liệu sang KPI cá nhân. Chỉ dùng Internal API hiện có để **gửi thông báo**:

```
POST /internal/v1/common/thong-bao        # nhắc đăng ký/nhập kết quả, báo có việc chờ duyệt
```
> Không tạo bản ghi `common.kpi-log` (giữ độc lập với KPI cá nhân theo yêu cầu nghiệp vụ).

---

## 8. LỊCH SỬ THAY ĐỔI

| Phiên bản | Ngày | Nội dung |
|-----------|------|----------|
| 1.0 | 04/06/2026 | Đặc tả API module Chỉ tiêu đơn vị (danh mục, giao năm, đăng ký/kết quả, duyệt, báo cáo) |

# BỘ PROMPT 02 — IMPLEMENT THAY ĐỔI KPI V2_PL3

> **Mục đích:** Hướng dẫn Claude Code CLI implement 2 thay đổi nghiệp vụ:
> 1. Đổi mẫu số KPI từ "ngày × 96" sang "tổng SP công chức kê khai"
> 2. Thay danh mục 46 mục + cấp độ C1-C5 bằng PL3 (2.812 mục, 5 nhóm, 15 lĩnh vực)

---

## Cách dùng

Chạy **TUẦN TỰ** từ A → E. **Sau mỗi phase, dừng lại review** trước khi chạy phase tiếp theo. Nếu phase nào fail acceptance, fix xong mới sang phase sau.

| File | Phase | Nội dung | Phụ thuộc |
|---|---|---|---|
| `PROMPT_02A_DATABASE.md` | A — Database | Migration Alembic, model SQLAlchemy, seed Excel PL3 | Không |
| `PROMPT_02B_BACKEND_KPI.md` | B — Backend KPI logic | Kê khai V2, phê duyệt V2, xếp loại V2, công thức trừ điểm | A |
| `PROMPT_02C_BACKEND_ADMIN.md` | C — Backend Admin + Tests | CRUD danh mục PL3, import Excel, unit/integration tests | A, B |
| `PROMPT_02D_FRONTEND_KPI.md` | D — Frontend KPI flow | Service V2, modal kê khai V2, route /ke-khai-v2, render xếp loại | B |
| `PROMPT_02E_FRONTEND_ADMIN.md` | E — Frontend Admin + Docs | Trang admin redesign, import Excel UI, cập nhật BUSINESS_RULES | C, D |

---

## 19 quyết định nghiệp vụ đã CHỐT (LOCKED)

Mọi prompt dưới đây đều giả định 19 quyết định này là CỐ ĐỊNH. **CLI KHÔNG được chất vấn lại** — nếu phát hiện mâu thuẫn, dừng lại và báo cáo, không tự suy diễn.

### Về công thức tính KPI

1. **Mẫu số V2** = `SUM(so_sp_goc_quy_doi)` của các bản kê khai **đã phê duyệt** trong tháng (không bao gồm nhập, chờ duyệt, từ chối).
2. **Hệ số quy đổi V2** = đọc thẳng từ `danh_muc_sp_cong_viec.he_so_quy_doi` (đã có sẵn trong file Excel PL3, đã được tính = `diem_cham / 25`).
3. **Công thức trừ điểm CL/TĐ tuyến tính GIỮ NGUYÊN:** `(SL - 0.25 × min(lỗi, SL × 4))` — đã chứng minh hoạt động đúng với hệ số thập phân.
4. **KPI lãnh đạo (a, b, c, d, đ, e) GIỮ NGUYÊN logic V1** — không bị ảnh hưởng bởi PL3.
5. **CC kê 0 SP → mẫu số = 0 → KPI = 0 → tự xếp mức D**, ghi log cảnh báo TCCB.

### Về cấu trúc dữ liệu

6. **Bỏ dependency vào `cap_do_phuc_tap` (C1-C5) cho V2.** Bảng `cap_do_phuc_tap` GIỮ + soft deactivate (`is_active=FALSE` sau cutover), không xoá vì FK lịch sử.
7. **MỞ RỘNG bảng `danh_muc_sp_cong_viec`** (không tạo bảng mới), thêm 12 cột PL3 + cờ `nguon_du_lieu IN ('V1', 'PL3')`.
8. **Cột `cap_do_id` trên `ke_khai_cong_viec`:** nullable, chỉ V1 dùng.
9. **Tiêu chí chung KHÔNG đổi** — KHÔNG nằm trong scope. CLI nếu phát hiện cấu trúc khác trong PL khác, KHÔNG được động vào.

### Về cờ phiên bản

10. **`version_kekhai`** trên `ke_khai_cong_viec`: `IN ('V1', 'V2_PL3')`, default `'V1'`, NOT NULL.
11. **`version_tinh_diem`** trên `danh_gia_thang`: `IN ('V1', 'V2_PL3')`, default `'V1'`, NOT NULL.
12. **1 tháng = 1 version** — không cho mix V1+V2 trong cùng `(cong_chuc, thang, nam)`. Bản kê khai đầu tiên trong tháng quyết định version cho cả tháng.

### Về snapshot & immutability

13. **`he_so_quy_doi_snapshot`** lưu vào `ke_khai_cong_viec` lúc tạo. Admin sửa danh mục về sau KHÔNG ảnh hưởng kê khai cũ (snapshot final).
14. **KHÔNG cho phép lãnh đạo override `he_so_quy_doi`** trong V2. C5 "theo thực tế" KHÔNG tồn tại trong V2 — mọi mục PL3 đã có hệ số cố định.

### Về UX & Filter

15. **Filter lĩnh vực: MỀM** — đơn vị có "lĩnh vực mặc định" được gợi ý lên trên dropdown, nhưng CC vẫn thấy được TẤT CẢ 15 lĩnh vực và 2.812 mục. Lĩnh vực là dòng tiêu đề trong Excel (Row 9, 374, 426...), không phải cột riêng — phải parse theo section.
16. **`khung_diem_toi_da` chỉ tham khảo**, KHÔNG ràng buộc trần.
17. **`so_luong` giữ `> 0` (số nguyên)** — không cho 0.5.

### Về triển khai

18. **Test environment trước** — KHÔNG cần backfill dữ liệu production cũ. CLI không phải viết script chuyển đổi V1 → V2 cho dữ liệu cũ.
19. **Giữ song song UI cũ + mới** — route `/ke-khai` (V1) và `/ke-khai-v2` (V2). Cờ chuyển đổi: `cong_chuc.kpi_version_pinned VARCHAR(10) NULL`.

### Về số ngày làm việc

20. Số ngày làm việc / nghỉ phép **vẫn track** (cho Mức E - Không xếp loại), nhưng **KHÔNG quyết định mẫu số V2**.

---

## Quy ước file output

- Migration Alembic: prefix `pl3_v2_`, ngày tháng theo lúc CLI tạo.
- Code mới có hậu tố `_v2` (Python) hoặc `V2` (TypeScript/React).
- Code V1 cũ KHÔNG sửa nội dung (giữ regression-free), chỉ thêm nhánh `if version == 'V2_PL3'`.
- `Decimal` xuyên suốt mọi tính toán Python; `Numeric(10,2)` hoặc `Numeric(8,4)` xuyên suốt schema.
- Làm tròn chỉ ở display layer.

---

## Khi nào DỪNG báo cáo cho user

CLI phải dừng lại và hỏi user nếu:
- Phát hiện file/code/quyết định mâu thuẫn với 19 LOCKED DECISIONS phía trên.
- Phát hiện schema thực tế khác `IMPACT_ANALYSIS_KPI_V2_PL3.md`.
- Cần quyết định nghiệp vụ chưa được liệt kê trong 19 quyết định.
- Hoàn thành 1 phase → báo cáo acceptance để user review.

KHÔNG tự ý quyết định những vấn đề ngoài scope.

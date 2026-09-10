# Nhật ký reset lượt thi ĐGNL (thủ công bằng SQL)

Ghi tay vì bảng `lms.lich_su_reset_thi` và endpoint reset (commit `6c7270d`,
nhánh `feature/lms-reset-luot-thi`) **chưa được deploy lên production**.
Khi công cụ đó lên prod, các ca sau phải bấm nút thay vì sửa SQL.

---

## Ca 1 — 20ZZ-0005, kỳ ĐGNL-THANG 8 - TA

| Mục | Nội dung |
|---|---|
| Thời điểm thực hiện | 10/09/2026 14:17 (giờ VN) |
| Người yêu cầu | admin@kv08.vn |
| Người thực hiện | Claude Code (SQL trực tiếp trên `kpi_haiquan`, localhost:5432) |
| Lý do | Xoá kết quả 2 lượt đã làm, trả bản ghi về `CHUA_THI` để thí sinh thi lại từ lượt 1 |
| Mức reset | `XOA_SACH` (mirror đúng nhánh XOA_SACH của `reset_luot_thi()` tại commit `6c7270d`) |
| Thí sinh | Võ Hồng Chung — `cong_chuc_id = bc5283e7-dbd2-4119-ab64-f629eb872c9a` |
| Kỳ thi | ĐGNL-THANG 8 - TA — `ky_thi_id = a6aa0796-8eab-452a-9bb7-309c0663cf0d` (mở tới 15/09/2026, tối đa 2 lượt) |
| Bản ghi | `thi_sinh_id = 6509b063-404c-4001-892d-9b686c256b85` |
| Snapshot nguyên trạng | `snapshot_20ZZ-0005_20260910.json` — có đủ `chi_tiet_tra_loi` 50 câu của **cả 2 lượt**, 3 dòng vi phạm, 1 dòng phiên thi |
| Bảng đối chứng trước | `truoc_khi_reset.txt` |

> Hai file dữ liệu trên **chỉ nằm trên máy chủ**, không đưa vào git: chúng chứa
> bài làm của một người cụ thể (từng câu, từng đáp án đã chọn). Đường dẫn:
> `/root/kpi-haiquan/docs/fix-reset-luot-thi/`. Chỉ file nhật ký này được commit.

### Dữ liệu đã xoá

| Lượt | Bắt đầu | Nộp | Điểm | Xếp loại | Đúng/Sai |
|---|---|---|---|---|---|
| 1 | 26/08 15:14 | 10/09 10:44 | 6.00 | KHÔNG_ĐẠT | 3/47 |
| 2 | 10/09 10:45 | 10/09 11:09 | 74.00 | ĐẠT | 37/13 |

Kết quả chính trước reset mang lượt tốt nhất = **74.00 / DAT**.

### Số dòng đã thay đổi

| Bảng | Thao tác | Số dòng |
|---|---|---|
| `lms.thi_sinh` | UPDATE về hình dạng `CHUA_THI` | 1 |
| `lms.vi_pham_thi` | DELETE (3 SWITCH_TAB của lượt 1, ngày 26/08) | 3 |
| `lms.phien_thi` | DELETE (`7034ede3-9312-4a20-8203-20af0d437fcb`) | 1 |

Chạy trong một `BEGIN … COMMIT`, có khối `DO` kiểm chứng ngay trong transaction
(hình dạng bản ghi, 0 vi phạm, 0 phiên, 5 bản ghi thi_sinh khác nguyên vẹn,
tổng thí sinh của kỳ vẫn 402). Toàn bộ điều kiện PASS mới COMMIT.

### Đối soát sau COMMIT

- Kỳ tháng 8: tổng 402 (không đổi), `DA_NOP` 401 → **400**, `CHUA_THI` 1 → **2**.
- 5 bản ghi thi_sinh còn lại của 20ZZ-0005: `updated_at` không đổi (DGNL lần 1 94đ, tháng 6 86đ, tháng 7 94đ đã xác nhận, 2 kỳ thử nghiệm CHUA_THI).
- `vi_pham_thi` của kỳ tháng 8: 39 → 36 (đúng 3 dòng của thí sinh này).
- Điều kiện thi lại: `lan_thi_hien_tai = 0 < so_lan_thi_toi_da = 2`, kỳ `DANG_MO` đến 15/09/2026 17:17 → thí sinh vào thi được ngay, tính là **lượt 1**.

### Đã ghi ngược vào nhật ký trong hệ thống (10/09/2026, sau khi công cụ lên prod)

Công cụ reset lên prod cùng ngày (commit `13647f8`), nên ca này đã được chèn 1 dòng
vào `lms.lich_su_reset_thi` để nhật ký trên giao diện không bỏ trống ca gần nhất:

- `nguoi_reset_id` = `a0000000-0000-0000-0000-000000000002` (**ADMIN-001 — Quản trị viên**)
- `loai_reset` = `XOA_SACH`, `trang_thai_truoc` = `DA_NOP`, `lan_thi_truoc` = 2, `diem_truoc` = 74.00
- `thoi_gian` = 10/09/2026 14:17:55 (đúng lúc chạy SQL, không phải lúc chèn)
- `du_lieu_truoc` dựng từ file snapshot, đúng hình dạng công cụ tự sinh (24 cột `thi_sinh`
  + `_vi_pham`), kèm khoá `_ghi_chu_backfill` nói rõ đây là dòng ghi ngược
- `ly_do` ghi thẳng rằng thao tác gốc làm bằng SQL trước khi có công cụ

Đối chiếu sau khi chèn: nhật ký kỳ ĐGNL-THANG 8 - TA có đúng 1 dòng, join ra
"20ZZ-0005 · Võ Hồng Chung — ADMIN-001 · Quản trị viên", `du_lieu_truoc` giữ đủ
2 lượt thi và 3 vi phạm.

### Đường lùi

Khôi phục từ `snapshot_20ZZ-0005_20260910.json`: `UPDATE lms.thi_sinh … FROM jsonb_populate_record`
với khối `thi_sinh`, rồi `INSERT` lại 3 dòng `vi_pham_thi` và 1 dòng `phien_thi` (giữ nguyên `id` cũ).
Snapshot giữ đủ bài làm nên dựng lại được nguyên vẹn cả điểm lẫn đáp án đã chọn.

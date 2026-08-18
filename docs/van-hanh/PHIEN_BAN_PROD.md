# Mốc phiên bản production

Ghi lại commit đang phục vụ người dùng, để luôn có điểm quay lui xác định.
Cập nhật mỗi lần triển khai.

## Hiện tại

| | |
|---|---|
| **Commit** | `19bea09a2eeab82442fde5852c88b6ea5469b9ca` |
| **Ngắn** | `19bea09` |
| **Nhánh nguồn** | `prod` (tách từ `feature/lich-cong-tac`) |
| **Ngày ghi mốc** | 18/08/2026 19:47 |
| **Alembic** | `zalo_oa_20260731` |

Nội dung: 4 tính năng KPI (phiếu Quý 02A/02B, vô hiệu hóa có ngày hiệu lực,
fix tính điểm theo loại công chức, chọn xếp loại A–E) + `meeting_service` ở
bản TRƯỚC Lịch công tác.

⚠️ **Chưa gồm Lịch công tác** — phần đó cần migration `meeting_016` → `021`
chạy trước, sẽ triển khai ở đợt riêng.

## Lịch sử triển khai

| Ngày | Commit | Ghi chú |
|---|---|---|
| 18/08/2026 | `19bea09` | Mốc đầu tiên khi tách môi trường |

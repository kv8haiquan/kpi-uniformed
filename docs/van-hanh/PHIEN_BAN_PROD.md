# Mốc phiên bản production

Ghi lại commit đang phục vụ người dùng, để luôn có điểm quay lui xác định.
Cập nhật mỗi lần triển khai.

## Hiện tại

| | |
|---|---|
| **Commit** | `be0670b655a966bf9d1e977cb5d682138bea3181` |
| **Ngắn** | `be0670b` |
| **Nhánh nguồn** | `prod` (fast-forward từ `feature/lich-cong-tac`) |
| **Ngày ghi mốc** | 19/08/2026 20:0x |
| **Alembic** | `mt_022_ds_file_doi_soat_20260819` |

Nội dung: toàn bộ **Lịch công tác** (Giai đoạn 4 — 7 màn hình) cùng dữ liệu di
trú từ lichkv8, chồng lên bản KPI ngày 18/08.

Số liệu sau di trú: 498 sự kiện lịch · 9 cuộc họp HKG · 844 tài liệu ·
333 lượt trực ban · 34 cụm chờ đối soát (412 file).

## Lịch sử triển khai

| Ngày | Commit | Ghi chú |
|---|---|---|
| 18/08/2026 | `19bea09` | Mốc đầu tiên khi tách môi trường |
| 19/08/2026 | `be0670b` | Lịch công tác G4 + migration `meeting_016`→`022` + di trú dữ liệu |

# Phase 4.1 — UAT Checklist (Page-Sync HKG)

**Mục tiêu**: Verify end-to-end page-sync 1 chủ tọa + 5 đại biểu trên staging trước khi deploy production.

**Môi trường UAT đề xuất**: staging (`staging.kpihaiquan.vn` hoặc port riêng) với database snapshot hôm nay (KHÔNG chạm production data).

---

## 1. Tiền điều kiện

- [ ] Backend `meeting_service` (port 8006) đã deploy với commits Phase 4.1 BE_P0..BE_P6
- [ ] Frontend đã build với commits Phase 4.1 FE_P0..FE_P5
- [ ] Migration `meeting_013_trang_thai_trinh_chieu_20260502.py` đã chạy → check bảng `meeting.trang_thai_trinh_chieu` tồn tại
- [ ] Cron `backup_daily.sh` đang chạy (đã setup từ P0 hardening)
- [ ] pm2-logrotate config: `max_size=50M, retain=7, compress=true, rotate='0 0 * * *'`
- [ ] 1 cuộc họp test có ≥2 file PDF, trạng thái `DA_THONG_BAO`
- [ ] 6 user test (1 chu_toa + 5 đại biểu là thanh_phan)

---

## 2. Kịch bản test

### 2.1. Smoke (1 host, không đại biểu)

| # | Bước | Pass/Fail |
|---|------|-----------|
| 1 | Host login → vào tab Tài liệu cuộc họp test | ☐ |
| 2 | Quan sát: SyncStatusBadge "Đang đồng bộ"/"Chờ chủ tọa" | ☐ |
| 3 | Bấm "Bắt đầu họp" → trạng thái chuyển `DANG_DIEN_RA` | ☐ |
| 4 | Bấm "Trình chiếu" trên file PDF → viewer hiện trang 1 | ☐ |
| 5 | Bấm Trang sau → hiển thị trang 2, badge vẫn "Đang đồng bộ" | ☐ |
| 6 | Bấm "Đổi" sang file PDF khác → viewer reload tài liệu mới | ☐ |
| 7 | Bấm "Kết thúc trình chiếu" → viewer ẩn, list documents trở lại | ☐ |
| 8 | Bấm "Kết thúc họp" → confirm → trạng thái `HOAN_THANH` | ☐ |

### 2.2. Multi-client (1 host + 5 đại biểu)

| # | Bước | Pass/Fail |
|---|------|-----------|
| 1 | Host bắt đầu họp + bắt đầu trình chiếu trang 1 | ☐ |
| 2 | 5 đại biểu mở cùng cuộc họp → tất cả thấy trang 1 trong vòng 2s | ☐ |
| 3 | Host lật sang trang 5 → 5 đại biểu lật theo trong ≤500ms (đo cảm tính) | ☐ |
| 4 | Đại biểu bấm "Xem độc lập" → tách khỏi sync, banner tím hiện | ☐ |
| 5 | Đại biểu lật trang trong độc lập → 4 đại biểu khác KHÔNG đổi | ☐ |
| 6 | Đại biểu bấm "Quay về đồng bộ" → confirm dialog → jump về trang host | ☐ |
| 7 | Host close tab → 30s sau, đại biểu thấy badge "Chờ chủ tọa" | ☐ |
| 8 | Host mở lại tab → đại biểu thấy badge "Đang đồng bộ" | ☐ |

### 2.3. Edge cases

| # | Bước | Pass/Fail |
|---|------|-----------|
| E1 | Đại biểu join giữa session: thấy spinner buffer rồi viewer render đúng trang host | ☐ |
| E2 | Host xóa file PDF đang chiếu → đại biểu thấy banner "Tài liệu đã bị xóa" | ☐ |
| E3 | Host hủy cuộc họp → đại biểu thấy banner đỏ "Cuộc họp đã hủy" + nút Tải lại | ☐ |
| E4 | Host mở 2 tab → tab phụ thấy banner "Tab phụ" + disable nút điều khiển | ☐ |
| E5 | Đại biểu mở mobile (iPhone/Android Chrome) → viewer scale 0.9, layout gọn | ☐ |
| E6 | Đại biểu chuyển tab khác >5s rồi quay lại → viewer auto resync state | ☐ |
| E7 | Mất mạng tạm thời (DevTools Network → Offline 3s rồi Online) → badge "Đang kết nối lại..." → "Đang đồng bộ" | ☐ |
| E8 | Backend restart đột ngột → frontend reconnect tự động trong ≤16s (5 lần exp backoff) | ☐ |

### 2.4. Performance

| # | Metric | Target | Đo được |
|---|--------|--------|---------|
| P1 | Latency host page_change → đại biểu page_changed | <500ms p95 | ___ms |
| P2 | Buffer late-join: thời gian từ click vào tab → viewer render trang đầu | <3s p95 | ___s |
| P3 | Build size frontend (gzip, app/(main)/hop-khong-giay/chi-tiet/[id]/tai-lieu) | <500KB | ___KB |
| P4 | CPU mobile (Chrome DevTools low-end) khi chuyển trang | <30% spike | ___% |

---

## 3. Sign-off

- Người test: ____________________
- Ngày: ___/___/2026
- Số case PASS / Total: ___/24
- Issues found: ____________________
- Sẵn sàng deploy production? ☐ Yes ☐ No

---

## Phụ lục — Lệnh tiện ích khi UAT

```bash
# Tail log meeting_service realtime
pm2 logs meeting_service --lines 100

# Check WS connection count đang active (in-process backend)
# Quan sát bằng curl /health hoặc grep audit_log
psql kpi_haiquan -c "SELECT * FROM meeting.audit_log WHERE created_at > NOW() - INTERVAL '5 minutes' ORDER BY created_at DESC LIMIT 20;"

# Reset state khi test bị stuck (CHỈ trên staging)
psql kpi_haiquan -c "UPDATE meeting.trang_thai_trinh_chieu SET is_active=FALSE WHERE cuoc_hop_id='<uuid-test>';"
```

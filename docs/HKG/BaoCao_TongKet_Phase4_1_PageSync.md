# Báo cáo Tổng kết — Phase 4.1: Page-Sync HKG (Họp Không Giấy)

> **Tên gọi nội bộ**: "Phase 2" của module HKG — page-sync cho phiên trình chiếu cuộc họp.
> **Branch**: `feature/kpi-lanh-dao-phan-cong`
> **Thời gian thực hiện**: 02/05/2026 – 09/05/2026
> **Trạng thái**: ✅ Code hoàn thành, chưa deploy production (chờ UAT mini)

---

## 1. Mục tiêu

Cho phép **chủ tọa cuộc họp** chia sẻ trang trình chiếu (PDF) đến **mọi đại biểu** đang xem cuộc họp trên cùng tab "Tài liệu" — gần real-time qua WebSocket.

| Tính năng | Ai dùng |
|---|---|
| Bắt đầu / Kết thúc phiên trình chiếu | Chủ tọa |
| Chuyển tài liệu / Đổi trang / Đổi zoom | Chủ tọa |
| Xem theo trang chủ tọa (sync mode mặc định) | Đại biểu |
| Tách khỏi sync để tự xem (independent mode) | Đại biểu |
| Quay lại sync (jump trang về chủ tọa) | Đại biểu |
| Bắt đầu / Kết thúc cuộc họp (lifecycle) | Chủ tọa (host) |

---

## 2. Phạm vi — gì đã làm, gì để lại

### ✅ Đã làm (16 commits)

**Database layer (DB_P1..P3, 3 commits)**

| Commit | Nội dung |
|---|---|
| `3641d6e` | Migration `meeting_013_trang_thai_trinh_chieu_20260502` — bảng state realtime 1 row/cuộc họp, 4 CHECK constraint, UPSERT pattern (UNIQUE cuoc_hop_id, KHÔNG có is_deleted) |
| `50c7c8c` | SQLAlchemy model `TrangThaiTrinhChieu` + 8 unit tests |
| `7a08fff` | Pydantic schemas: REST response + 5 inbound + 10 outbound WS events (discriminated union) + zoom validator [0.5, 4.0] |

**Backend layer (BE_P1..P6, 7 commits)**

| Commit | Nội dung |
|---|---|
| `f7ea8f3` | P0 hardening — backup_daily.sh (pg_dump + rsync, 30d/12m retention), cleanup_preview_cache, rate-limit slowapi 10/5min trên upload tài liệu |
| `aa750aa` | Backup script fix — chấp nhận `.pgpass` thay PGPASSWORD env (deploy thực tế) |
| `2a45ad0` | Endpoints `POST /cuoc-hop/{id}/bat-dau` + `/ket-thuc` (v3.1 blocker — lifecycle prerequisites) |
| `7a443a2` | REST `GET /cuoc-hop/{id}/presentation/state` — UPSERT lazy, scope check DA_THONG_BAO/DANG_DIEN_RA, WS token TTL theo formula v3.1 (`min(ngay_hop + gio_ket_thuc + 1h, NOW + 6h)`) |
| `777ba02` | `BroadcastBackend` Protocol + `InMemoryBackend` + `PresentationManager` — handle 5 inbound events, debounce 150ms, audit 3 events |
| `1a90fdd` | WebSocket endpoint `/ws/cuoc-hop/{id}/presentation` — token auth qua query, heartbeat 30s, idle timeout 120s, host reconnect grace 30s |
| `68932b1` | Edge cases (5 audit events, cleanup khi cuộc họp HUY/HOAN_THANH) + stress test 50 client × 100 broadcast |

**Frontend layer (FE_P0..P5, 6 commits)**

| Commit | Nội dung |
|---|---|
| `67d1e16` | Setup Vitest 4.1 + @testing-library/react + jsdom + mock-socket (`vitest.config.ts`, `vitest.setup.ts`) |
| `802c754` | `PresentationViewer` + `PresentationViewerLazy` (pdfjs-dist@4.10.38 + `dynamic({ssr:false})`) |
| `4e84055` | Hook `usePresentationSync` — fetch token, mở WS, reduce 10 outbound events, host actions, reconnect exp backoff (1/2/4/8/16s × 5), visibility resync |
| `e45c238` | 5 UI components (MeetingLifecycleButton, SyncStatusBadge, IndependentViewBanner, ConfirmReturnDialog, ToggleModeButton) + integrate vào tab Tài liệu |
| `d7a9934` | Mobile detect (`useMediaQuery`, scale 0.9), buffer late-join (spinner overlay + `onReady`), multi-tab leader (`useTabLeader` BroadcastChannel) |
| `a190f87` | Edge handling (meeting_ended banner, doc 404), OnboardingHint, docs UAT + Deploy checklists |

### 🚫 Chưa làm (sẽ ở các phase sau)

- Annotation real-time (vẽ trên PDF) — Phase 4.2
- Recording phiên trình chiếu — Phase 4.3
- Q&A panel — chưa có roadmap
- Multi-presenter (co-host) — out of scope v1
- Redis pub/sub backend thay InMemory (cần khi scale > 1 process) — đã abstract qua Protocol, đổi sau dễ

---

## 3. Quyết định kỹ thuật quan trọng

### 3.1. Auth WebSocket bằng query token

Vì FastAPI WebSocket không hỗ trợ Authorization header reliable cross-browser, dùng JWT short-lived **scope = `meeting:{cuoc_hop_id}`** truyền qua `?token=`. Token issue lại mỗi lần frontend cần (TTL ≤ 6h hoặc đến giờ kết thúc + 1h, lấy giá trị nhỏ hơn).

→ Chống cross-meeting injection: token cuộc họp A KHÔNG mở được WS cuộc họp B.

### 3.2. State 1-1 bằng UPSERT, không soft delete

Bảng `meeting.trang_thai_trinh_chieu` UNIQUE trên `cuoc_hop_id`. Khi cuộc họp delete → CASCADE xóa luôn state. Không có `is_deleted` vì:
- 1 cuộc họp chỉ có 1 phiên trình chiếu cùng lúc
- Audit log riêng đã track lịch sử
- UPSERT đơn giản hơn versioning

### 3.3. Discriminated union cho WS payloads

Pydantic `Annotated[Union[...], Field(discriminator="type")]` auto-validate đúng subclass theo trường `type`. Chống lỗ hổng "client gửi field thừa" và "type confusion" tại schema layer, defense-in-depth trước CHECK constraint DB.

### 3.4. InMemoryBackend qua Protocol — sẵn sàng Redis

`BroadcastBackend` là Protocol với `add_client / remove_client / broadcast / host_count / close_channel`. Hôm nay dùng `InMemoryBackend` (asyncio dict). Khi scale multi-worker chỉ cần implement `RedisPubSubBackend` — KHÔNG sửa code nghiệp vụ.

### 3.5. Host reconnect grace 30s

Khi host close tab/refresh nhanh, không nên broadcast `host_disconnected` ngay (đại biểu sẽ thấy "Chờ chủ tọa" nhấp nháy). Schedule task delay 30s. Reconnect trong 30s → cancel task + broadcast `host_reconnected`.

### 3.6. Debounce 150ms per (channel, user, event_type)

Host kéo zoom hoặc lật trang nhanh có thể spam event 30/s. Debounce 150ms giữ event cuối cùng → giảm 95% traffic, đại biểu vẫn cảm nhận mượt.

### 3.7. Frontend: PDF.js bắt buộc `dynamic({ ssr: false })`

`pdfjs-dist` gọi `window`/`DOMMatrix` ở module-load time → crash khi SSR. Wrapper `PresentationViewerLazy` ép client-only + loại 1.4MB worker khỏi server bundle (giảm cold start Next.js).

### 3.8. Multi-tab leader election qua BroadcastChannel

Tránh host mở 2 tab cùng cuộc họp → double event. Optimistic leader: tab đầu tự nhận leader, gửi "claim" với random tabId; tab cũ "ack" lại nếu đã làm leader. Tab phụ disable nút điều khiển + banner "Tab phụ". Fallback graceful (Safari < 15.4 không có BroadcastChannel → mọi tab leader, hành vi cũ).

### 3.9. Đại biểu independent mode = local FE state

Khi đại biểu tách khỏi sync, **không gửi gì lên WS** — chỉ giữ `localPage` trong React state. Quay về sync: jump `localPage = sync.state.page`. Backend không cần biết.

### 3.10. Audit log — chỉ 5 events có business value

Bỏ qua spam events (page_change, zoom_change x 100/min). Chỉ audit:
- `PRESENTATION_START`
- `PRESENTATION_END`
- `DOCUMENT_OPEN` (đổi tài liệu)
- `CUOC_HOP_BAT_DAU`
- `CUOC_HOP_KET_THUC`

---

## 4. Files mới + thay đổi

### Backend (`backend/`)

```
alembic/versions/meeting_013_trang_thai_trinh_chieu_20260502.py    [NEW]
meeting_service/
  models/trang_thai_trinh_chieu.py                                 [NEW]
  schemas/presentation.py                                          [NEW]
  api/endpoints/presentation_rest.py                               [NEW]
  api/endpoints/presentation_ws.py                                 [NEW]
  api/endpoints/cuoc_hop.py                                        [MOD] +bat_dau, ket_thuc
  services/
    broadcast_backend.py                                           [NEW]
    presentation_manager.py                                        [NEW]
    presentation_singletons.py                                     [NEW]
    ws_token_service.py                                            [NEW]
    rate_limit.py                                                  [NEW]
    cuoc_hop_service.py                                            [MOD]
  tests/                                                           [NEW] ~12 file mới
```

### Frontend (`frontend/`)

```
src/
  components/hkg/presentation/                                     [NEW dir]
    PresentationViewer.tsx
    PresentationViewerLazy.tsx
    MeetingLifecycleButton.tsx
    SyncStatusBadge.tsx
    IndependentViewBanner.tsx
    ConfirmReturnDialog.tsx
    ToggleModeButton.tsx
    OnboardingHint.tsx
  hooks/
    usePresentationSync.ts                                         [NEW]
    useMediaQuery.ts                                               [NEW]
    useTabLeader.ts                                                [NEW]
  types/hkg-presentation.ts                                        [NEW]
  services/hkg.ts                                                  [MOD] +presentationApi, batDau, ketThuc
  app/(main)/hop-khong-giay/chi-tiet/[id]/tai-lieu/page.tsx        [MOD] integrate tất cả
public/pdf.worker.min.mjs                                          [NEW] 1.4MB
vitest.config.ts, vitest.setup.ts                                  [NEW]
```

### Scripts + Docs

```
scripts/
  backup_daily.sh                                                  [NEW]
  cleanup_preview_cache.sh                                         [NEW]
  INSTALL_CRON.md                                                  [NEW]
docs/HKG/
  KeHoach_Phase4_1_PageSync_v3_FINAL.md                            [MOD] v3.0 → v3.1 (6 fixes)
  Phase_4_1_UAT_Checklist.md                                       [NEW] 24 test cases
  Phase_4_1_Deploy_Checklist.md                                    [NEW] deploy + rollback
  BaoCao_TongKet_Phase4_1_PageSync.md                              [NEW] file này
```

---

## 5. Tests + Quality

### Backend

| Phase | Tests trước | Tests sau | Note |
|---|---|---|---|
| DB_P2 | 72 | 80 | +8 model tests |
| DB_P3 | 80 | 85 | +5 schema tests |
| BE_P1 | 85 | 88 | +3 rate_limit smoke |
| BE_P2..P6 | 88 | **153** | Cộng dồn 65 test endpoints + WS + edge |
| Stress | — | 50 client × 100 broadcast | p95=0.33ms, 100% delivery |

### Frontend

| Phase | Test files | Tests | Note |
|---|---|---|---|
| FE_P0 | 1 | 1 | smoke |
| FE_P1 | 2 | 2 | +PresentationViewer lazy fallback |
| FE_P2 | 3 | 10 | +8 usePresentationSync (mock-socket) |
| FE_P4 | 5 | **15** | +useMediaQuery + useTabLeader |
| Build prod | — | ✅ pass | mọi commit verify trước khi push |

---

## 6. Edge cases được handle

| Case | Xử lý |
|---|---|
| Token WS hết hạn giữa session | Server close 1008 → FE re-fetch token (max 3 lần) |
| Cuộc họp HUY/HOAN_THANH giữa session | Server broadcast `meeting_ended` → FE banner đỏ + nút Tải lại |
| Tài liệu đang chiếu bị xóa | FE phát hiện 404 trên `xemUrl` → "Tài liệu đã bị xóa" |
| Host close tab vô tình | Grace 30s rồi broadcast `host_disconnected` |
| Host reconnect | Cancel pending task + broadcast `host_reconnected` |
| Đại biểu join giữa session | State sync + spinner overlay đến khi viewer ready |
| Đại biểu chuyển tab >5s | Visibility change → re-fetch token + reconnect |
| Mất mạng tạm thời | Exp backoff 1/2/4/8/16s, max 5 lần |
| Host mở 2 tab | Leader election → tab phụ banner amber + disable nút |
| Mobile thiết bị yếu | Scale 0.9, maxHeight 60vh, toolbar gọn |
| Backend restart | FE tự reconnect trong ≤16s |
| WS abnormal close 1006 | Reconnect bình thường (không cần token mới) |

---

## 7. Hướng dẫn deploy

Đọc 2 file:

1. `docs/HKG/Phase_4_1_UAT_Checklist.md` — 24 test case cần PASS trên staging trước
2. `docs/HKG/Phase_4_1_Deploy_Checklist.md` — quy trình BE/FE deploy + rollback (downgrade migration + restore snapshot)

### Lệnh quick reference

```bash
# Backend (port 8006)
cd /root/kpi-haiquan/backend
source venv/bin/activate
alembic upgrade head            # → revision mt_013_ttc_20260502
pm2 restart meeting_service
curl -s http://localhost:8006/health  # phải trả {"status":"ok"}

# Frontend (port 3000)
cd /root/kpi-haiquan/frontend
npm ci && npm run build
pm2 restart frontend
# Smoke: mở browser → tab Tài liệu cuộc họp DA_THONG_BAO/DANG_DIEN_RA
```

### Rollback nhanh nếu cần

```bash
# FE only (không động DB):
git checkout <commit-before-FE_P0>
cd frontend && npm ci && npm run build && pm2 restart frontend

# BE + DB:
cd backend && alembic downgrade -1   # revert mt_013
git checkout <commit-before-BE_P0>
pm2 restart meeting_service
```

---

## 8. Việc còn cần user thực hiện

| # | Task | Khi nào | Người làm |
|---|------|---------|-----------|
| 1 | Mở PR `feature/kpi-lanh-dao-phan-cong` → `main` | Sau khi review nội bộ | User |
| 2 | Triển khai INSTALL_CRON.md mục 3 (verify rate-limit) và mục 4 (rollback procedures) | Trước deploy production | User + DBA |
| 3 | UAT mini trên staging — 24 case checklist | Trước deploy | User + 5 đại biểu test |
| 4 | Deploy production theo Deploy_Checklist | Sau khi UAT ≥22/24 PASS | User trong maintenance window |
| 5 | Monitor 1h sau deploy: pm2 logs, audit_log, user feedback | Ngay sau deploy | User |

> **Tôi (Claude) không thực hiện được** các bước 1-5 vì cần production access + cửa sổ bảo trì + người dùng thực để UAT. Tôi đã chuẩn bị đầy đủ scripts + checklists.

---

## 9. Metrics tổng kết

| Metric | Value |
|---|---|
| **Total commits Phase 4.1** | 16 (3 DB + 7 BE + 6 FE) |
| **Total files mới** | ~30 (BE ~15, FE ~15) |
| **Total LOC mới (insertions)** | ~10,500 (BE ~5,000, FE ~3,500, tests + docs ~2,000) |
| **Backend tests** | 153 PASS (tăng từ baseline 72) |
| **Frontend tests** | 15 PASS |
| **Stress test** | 50 client × 100 broadcast → p95 **0.33ms**, 100% delivery |
| **Build prod** | ✅ Mọi commit verify pass |
| **Critical issues fixed** | 6 trong plan (DA_HUY→HUY, Session→AsyncSession, migration path, etc.) |
| **Backward compatibility** | ✅ Không sửa endpoint cũ, chỉ thêm |

---

## 10. Lessons learned

1. **Plan v3.0 → v3.1**: phát hiện 6 critical issues trong các prompt MASTER/DB/BE/FE → fix toàn bộ trước khi implement, tiết kiệm rework
2. **mock-socket** giúp test WS hook không cần real server — 8 case usePresentationSync chạy 700ms
3. **BroadcastChannel + Protocol** = pattern tốt cho multi-tab, dễ test (fake constructor)
4. **Dynamic import ssr:false** là không thương lượng cho pdfjs trên Next.js 16 — phát hiện ở FE_P1 nhờ build pre-flight
5. **Audit minimalist**: chỉ 5 business events thay vì spam mọi page_change → DB không growing wild

---

**Người soạn**: Claude Opus 4.7 (collaboration với KPI System)
**Ngày**: 09/05/2026
**Commit ref**: `a190f87` (HEAD of Phase 4.1 trên `feature/kpi-lanh-dao-phan-cong`)

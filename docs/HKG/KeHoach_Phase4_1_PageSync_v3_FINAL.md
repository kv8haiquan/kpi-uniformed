# KẾ HOẠCH PHASE 4.1 — PAGE-SYNC + P0 HARDENING (v3.1 FINAL)

**Phiên bản:** 3.1 FINAL · **Ngày:** 2026-05-02 · **Trạng thái:** Sẵn sàng code

> Phase 4.1 = hạng mục #1 trong `KeHoach_Phase4_HKG.docx`. Plan này là kết quả 3 vòng review + 13 quyết định kiến trúc đã chốt. **Sau khi approve, không thay đổi scope giữa chừng.**
>
> **v3.1 changelog (so với v3.0):** áp 6 fix sau khi đối chiếu codebase thực tế (02/05/2026):
> 1. Đổi tên migration cho khớp convention `meeting_NNN_*`
> 2. Fix WS token TTL — `gio_ket_thuc` là `Time` nullable, không phải `TIMESTAMPTZ`
> 3. Bỏ `is_deleted` khỏi bảng `trang_thai_trinh_chieu` để UPSERT 1-1 hoạt động
> 4. Thêm dependency: bổ sung endpoint `POST /cuoc-hop/{id}/bat-dau` + `/ket-thuc` (codebase chưa có cách chuyển sang `DANG_DIEN_RA`)
> 5. Giới hạn scope cấp WS token: chỉ `DA_THONG_BAO`/`DANG_DIEN_RA`
> 6. Bắt buộc dynamic import `ssr:false` cho `<PresentationViewer />` (pdfjs-dist@4 không SSR-safe)
>
> Số test mục tiêu hạ từ "180+" xuống **~107** (72 hiện tại + 35 mới — số liệu đếm thực tế trong `meeting_service/tests/`).

---

## 1. DECISION LOG (13 quyết định)

| # | Vấn đề | Quyết định | Ghi chú |
|---|---|---|---|
| 1 | Quyền broadcast | Chỉ `chu_toa_id` | Spec gốc |
| 2 | Đồng bộ zoom | Có (page + zoom) | Bỏ scroll position |
| 3 | Đại biểu Xem độc lập + chủ tọa đổi tài liệu | Không bị kéo, banner thông báo | |
| 4 | Nút "Quay lại theo chủ trì" khác tài liệu | Confirm dialog | |
| 5 | Multi-tab + cross-device cùng user | Sync tất cả | |
| 6 | Mobile default mode | Xem độc lập | |
| 7 | Chủ tọa offline | Acceptable, banner thông báo | Không có fallback đề cử thư ký |
| 8 | Lifecycle | Nút "Bắt đầu/Kết thúc trình chiếu" | Cho phép start/end nhiều lần, không lưu history |
| 9 | PDF viewer | Replace bằng PDF.js | **Chỉ trong viewer cuộc họp**, page standalone giữ iframe |
| 10 | Late-join file lớn | Buffer pendingState, apply state mới nhất sau load | |
| 11 | Audit log | Chỉ audit `start`, `end`, `document_open` | Bỏ `page_change`/`zoom_change` để tránh flood |
| 12 | WS token TTL | `cuoc_hop.gio_ket_thuc + 1h buffer` (max 6h) | Đơn giản, không cần auto-refresh |
| 13 | Throttle policy | **Debounce 150ms** thay vì throttle 100ms | UX mượt hơn, không reject events |

---

## 2. SCOPE LOCK — WHAT WE'RE NOT DOING IN PHASE 4.1

Để tránh slip schedule, các tính năng sau **DỨT KHOÁT** không làm trong phase này:

| Tính năng | Đẩy sang |
|---|---|
| Annotation realtime (highlight/draw/underline) | Phase 4.2 (~2 tuần) |
| PWA offline + IndexedDB cache | Phase 4.3 (~2 tuần) |
| Replace PDF viewer ở page standalone | Phase 5 |
| Lưu history các phiên trình chiếu (start/end nhiều lần) | Phase 5 |
| Multi-host (>1 chủ tọa cùng cuộc họp) | Phase 5 |
| Đại biểu broadcast (2-way sync) | Không có kế hoạch |
| Replay/playback cuộc họp đã trình chiếu | Phase 6+ |
| Fallback đề cử thư ký tạm điều khiển khi chu_toa offline | Phase 5 (nếu thực tế cần) |
| Page-sync cho file ảnh PNG/JPG | Phase 5 (đa số tài liệu là PDF/Office) |
| Audit log đầy đủ mọi page change | Không làm — dump structured log file nếu cần debug |

---

## 3. KIẾN TRÚC

### 3.1. Schema database — bảng mới

**Migration:** `meeting_013_trang_thai_trinh_chieu_20260502.py`
*(v3.1: đổi tên cho khớp convention `meeting_NNN_<desc>_<YYYYMMDD>.py` — số 012 đã bị `meeting_012_extend_diem_danh_hinh_thuc_20260501.py` chiếm.)*

```sql
CREATE TABLE meeting.trang_thai_trinh_chieu (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cuoc_hop_id             UUID UNIQUE NOT NULL
                             REFERENCES meeting.cuoc_hop(id) ON DELETE CASCADE,
    -- State hiện tại
    tai_lieu_hien_tai_id    UUID NULL
                             REFERENCES meeting.tai_lieu(id) ON DELETE SET NULL,
    trang_hien_tai          INTEGER DEFAULT 1 CHECK (trang_hien_tai > 0),
    zoom_level              NUMERIC(4,2) DEFAULT 1.0
                             CHECK (zoom_level >= 0.5 AND zoom_level <= 4.0),
    -- Lifecycle (cho phép start/end nhiều lần, ghi đè timestamp lần cuối)
    is_active               BOOLEAN DEFAULT FALSE,
    bat_dau_luc             TIMESTAMPTZ NULL,  -- thời điểm start CUỐI CÙNG
    ket_thuc_luc            TIMESTAMPTZ NULL,  -- thời điểm end CUỐI CÙNG
    -- Audit
    cap_nhat_luc            TIMESTAMPTZ DEFAULT NOW(),
    cap_nhat_boi_id         UUID NULL REFERENCES public.cong_chuc(id)
);

CREATE INDEX idx_ttc_cuoc_hop ON meeting.trang_thai_trinh_chieu(cuoc_hop_id);
```

> **v3.1 fix:** Bỏ cột `is_deleted` — bảng state 1-1 với `cuoc_hop` (đã có UNIQUE constraint), soft-delete vô nghĩa và sẽ chặn UPSERT khi cuộc họp tái dùng record. Nếu cần dọn data, xoá thẳng theo `ON DELETE CASCADE` từ `cuoc_hop`.

### 3.2. WS Protocol

**Endpoint:** `WS /ws/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/presentation?token={ws_token}`

**Token strategy (D12):**
- REST `GET /presentation/state` cấp WS token
- **Điều kiện cấp:** `cuoc_hop.trang_thai IN ('DA_THONG_BAO','DANG_DIEN_RA')` — `LEN_KE_HOACH`/`HOAN_THANH`/`HUY` → 403 *(v3.1 fix: chặn token cấp quá sớm cho cuộc họp chưa thông báo)*
- **TTL** *(v3.1 fix: `gio_ket_thuc` là `Time` nullable, không phải `TIMESTAMPTZ`)*:
  ```python
  end_dt = (
      datetime.combine(ch.ngay_hop, ch.gio_ket_thuc, tzinfo=ASIA_HCM)
      if ch.gio_ket_thuc
      else datetime.combine(ch.ngay_hop, ch.gio_bat_dau, tzinfo=ASIA_HCM) + timedelta(hours=4)
  )
  ttl = min(end_dt + timedelta(hours=1) - now(), timedelta(hours=6))
  if ttl <= 0: raise HTTPException(410, "Cuộc họp đã kết thúc")
  ```
- Scope: `meeting:{cuoc_hop_id}`
- KHÔNG auto-refresh (đơn giản); user nào cần refresh thì gọi lại REST

**Inbound events** (chỉ chu_toa được gửi, server reject silently nếu khác):

| Event | Payload | Validate |
|---|---|---|
| `presentation_start` | `{tai_lieu_id, page=1}` | chu_toa + cuoc_hop=`DANG_DIEN_RA` |
| `presentation_end` | `{}` | chu_toa + presentation đang active |
| `document_open` | `{tai_lieu_id, page=1}` | chu_toa + tai_lieu thuộc cuoc_hop, NOT deleted |
| `page_change` | `{page}` | chu_toa + active + page hợp lệ |
| `zoom_change` | `{zoom}` | chu_toa + active + 0.5≤zoom≤4.0 |

**Outbound events:** `state_sync`, `presentation_started`, `presentation_ended`, `document_changed`, `page_changed`, `zoom_changed`, `error`, `host_disconnected`, `host_reconnected`, `meeting_ended` (cuộc họp kết thúc/hủy → đóng tất cả WS).

**Debounce policy (D13):** Server gom `page_change`/`zoom_change` của cùng chu_toa trong window 150ms, broadcast event cuối cùng. Implement với `asyncio.sleep` + cancel token pattern.

**Audit policy (D11):** Chỉ ghi `common.audit_log` cho 3 events: `presentation_start`, `presentation_end`, `document_open`. `page_change`/`zoom_change` KHÔNG vào DB — nếu cần debug, dump structured log file `/var/log/hkg-presentation.log`.

### 3.3. Edge cases handling (fix IMPORTANT-7)

Mỗi inbound event handler phải check trước khi broadcast:

```python
async def handle_event(event, ws):
    # 1. Cuộc họp còn active?
    cuoc_hop = await get_cuoc_hop(event.cuoc_hop_id)
    if cuoc_hop.trang_thai != 'DANG_DIEN_RA':
        await ws.send({"type": "error", "code": "MEETING_NOT_ACTIVE"})
        await pool.broadcast(cuoc_hop.id, {"type": "meeting_ended"})
        await pool.close_all(cuoc_hop.id)
        return
    
    # 2. Tài liệu còn tồn tại?
    if event.type in ("document_open", "page_change"):
        tai_lieu = await get_tai_lieu(event.tai_lieu_id)
        if not tai_lieu or tai_lieu.is_deleted:
            await ws.send({"type": "error", "code": "DOCUMENT_DELETED"})
            return
    
    # 3. User vẫn là chu_toa?
    if cuoc_hop.chu_toa_id != ws.user_id:
        await ws.send({"type": "error", "code": "NOT_HOST"})
        return  # silent reject
    
    # 4. Process event...
```

### 3.4. iPad/Mobile background tab handling (fix IMPORTANT-6)

Frontend hook `usePresentationSync` thêm:

```typescript
useEffect(() => {
  const handler = () => {
    if (document.visibilityState === 'hidden') {
      // Tab background, có thể bị Safari kill connection
      setStatus('paused');
    } else if (document.visibilityState === 'visible') {
      // Tab visible lại, force reconnect + fetch state mới
      reconnectWS();
      fetchLatestState();
    }
  };
  document.addEventListener('visibilitychange', handler);
  return () => document.removeEventListener('visibilitychange', handler);
}, []);
```

### 3.5. PresentationManager + abstract backend

```python
# services/presentation_manager.py

class BroadcastBackend(Protocol):
    async def add_client(self, channel: str, ws: WebSocket): ...
    async def remove_client(self, channel: str, ws: WebSocket): ...
    async def broadcast(self, channel: str, event: dict): ...

class InMemoryBackend:
    """MVP backend — single PM2 process. Swap RedisPubSub khi cần multi-worker."""
    def __init__(self):
        self._pools: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._debounce_tasks: Dict[str, asyncio.Task] = {}  # cho debounce 150ms

class PresentationManager:
    def __init__(self, backend: BroadcastBackend):
        self.backend = backend
```

---

## 4. P0 HARDENING (TUẦN 1, TRACK SONG SONG)

| Việc | File | Effort |
|---|---|---|
| Backup daily script + cron | `scripts/backup_daily.sh` | 0.5 ngày |
| Cleanup preview cache cron | `scripts/cleanup_preview_cache.sh` | 0.25 ngày |
| Rate limit upload (slowapi) | middleware trong `meeting_service` | 0.5 ngày |
| pm2-logrotate config | command-line | 0.25 ngày |

**Total:** 1.5 ngày, hoàn tất trong Th.2 + nửa ngày Th.3 tuần 1.

---

## 5. LỘ TRÌNH 3 TUẦN

### Tuần 1 — Backend WebSocket + P0 (track song song)

**Track A — P0 (Th.2 + sáng Th.3):**
- Th.2 sáng: backup_daily.sh + cron + test pg_dump/restore
- Th.2 chiều: cleanup_preview_cache.sh + cron
- Th.3 sáng: slowapi rate limit upload + pm2-logrotate

**Track B — Backend WS:**
| Ngày | Việc |
|---|---|
| Th.3 chiều | Migration `meeting_013_trang_thai_trinh_chieu` (apply + rollback test) |
| Th.3 chiều | **(v3.1 mới)** Endpoint `POST /cuoc-hop/{id}/bat-dau` + `POST /cuoc-hop/{id}/ket-thuc` (codebase chưa có cách chuyển sang `DANG_DIEN_RA`/`HOAN_THANH`) — chỉ chu_toa hoặc thư ký được gọi; +5 test |
| Th.4 | Model + Pydantic schemas + REST `GET /presentation/state` (cấp WS token) |
| Th.4 | Token logic: TTL theo công thức 3.2, scope check, chặn `LEN_KE_HOACH` |
| Th.5 | `BroadcastBackend` interface + `InMemoryBackend` implementation |
| Th.5 | `PresentationManager` core (add/remove/broadcast với async lock) |
| Th.5 | Unit tests `test_presentation_manager.py` (~12 test) |
| Th.6 | WS endpoint + connection lifecycle (state_sync on connect) |
| Th.6 | Inbound handlers (5 events) với edge case checks (mục 3.3) |
| Th.7 | Debounce 150ms cho page_change/zoom_change |
| Th.7 | Audit log integration (chỉ 3 events business-value) |
| Th.7 | Integration tests `test_presentation_ws.py` (~20 test) |

**🎯 Exit criteria Tuần 1 — KHÔNG sang Tuần 2 nếu chưa đạt:**
- [ ] P0: 4 deliverables chạy production
- [ ] Migration `meeting_013` apply prod thành công, rollback test OK
- [ ] Endpoint `bat-dau`/`ket-thuc` hoạt động + 5 test pass *(v3.1)*
- [ ] Backend test: 37 tests pass (12 manager + 20 WS + 5 lifecycle endpoint)
- [ ] Multi-client wscat test: 1 chu_toa + 5 đại biểu giả lập, broadcast OK
- [ ] Debounce 150ms verified (gửi 10 events trong 100ms → chỉ 1 event broadcast)
- [ ] Audit log có 3 events `start/end/document_open`, KHÔNG có page_change

### Tuần 2 — Frontend PDF.js + Sync logic

| Ngày | Việc |
|---|---|
| Th.2 | Cài `pdfjs-dist@^4.0.0`, copy worker file vào `/public/`, scaffold `<PresentationViewer />` — **bắt buộc dynamic import `ssr:false`** *(v3.1 fix: pdfjs-dist@4 không SSR-safe, sẽ break Next.js 16 build)* |
| Th.2 | Render PDF cơ bản (page change, zoom) — chưa sync; verify build production pass trước khi sang Th.3 |
| Th.3 | Hook `usePresentationSync(meetingId)` với exponential backoff reconnect |
| Th.3 | `visibilitychange` handler (fix iPad background tab) |
| Th.4 | Buffer late-join: pendingState logic, apply state mới nhất sau load |
| Th.4 | Toolbar nút "Bắt đầu/Kết thúc trình chiếu" (chỉ chu_toa thấy) |
| Th.5 | Toggle "Theo chủ trì" / "Xem độc lập" + 4 banner states |
| Th.5 | Nút "Quay lại theo chủ trì" + confirm dialog khi đổi tài liệu |
| Th.6 | Mobile detect (`window.matchMedia('(max-width: 768px)')`) → default Xem độc lập |
| Th.6 | Multi-tab/cross-device sync test (cùng user mở 2 tab, đổi tab này → tab kia sync) |
| Th.7 | Polish UX: tooltips, loading states, error handling |
| Th.7 | Manual test 4 browser × 3 device size (Chrome/Firefox/Safari/Edge × desktop/tablet/mobile) |

**🎯 Exit criteria Tuần 2:**
- [ ] PDF.js render đẹp trên Chrome desktop + Safari iPad + Chrome Android
- [ ] 2 tab cùng user: lật ở A → B sync
- [ ] Buffer late-join: file 30MB delay 5s vẫn jump đúng trang chủ tọa
- [ ] Toggle "Xem độc lập" → "Theo chủ trì" → confirm dialog → load đúng tài liệu
- [ ] Mobile mặc định Xem độc lập, prominent nút "Đồng bộ"
- [ ] Browser background tab 60s → reconnect graceful

### Tuần 3 — Edge cases + UAT mini + Deploy staging

| Ngày | Việc |
|---|---|
| Th.2 | Edge case: cuộc họp bị hủy giữa chừng → broadcast `meeting_ended` + close all WS |
| Th.2 | Edge case: tài liệu bị xóa giữa chừng → đại biểu thấy banner "Tài liệu đã bị xóa" |
| Th.3 | Stress test: 50 concurrent client + 100 page_change → đo p50/p95/p99 latency |
| Th.3 | Fix bugs từ stress test (nếu có) |
| Th.4 | Onboarding: tooltip "Bắt đầu trình chiếu" lần đầu chu_toa vào trang |
| Th.4 | Onboarding: hint mobile "Bạn đang xem độc lập, bấm để đồng bộ" |
| Th.5 | Soạn tài liệu hướng dẫn chu_toa (1 trang A4) + screenshot |
| Th.5 | Deploy staging + smoke test |
| Th.6 | UAT mini: 5 CBCC volunteer, 1 cuộc họp thử 30 phút |
| Th.6 | Sửa bug critical từ UAT (nếu có) |
| Th.7 | Buffer fix bugs minor + cập nhật `CLAUDE.md`, `PM2_DEPLOY.md` |
| Th.7 | Deploy production sau khi staging stable 48h |

**🎯 Exit criteria Tuần 3 (= Phase 4.1 done):**
- [ ] Stress test 50 client: p95 < 500ms latency
- [ ] UAT mini: 4/5 volunteer feedback OK (subjective UX "instant")
- [ ] Tài liệu hướng dẫn chu_toa published
- [ ] Production deploy thành công, monitoring 24h không alert
- [ ] Total tests sau Phase 4.1: **≥107** (72 hiện tại + 35 mới — số 180 ở v3.0 là sai, đếm lại từ `meeting_service/tests/` chỉ có 72 test functions)

---

## 6. DELIVERABLES

**Backend (~11 file mới + 2 file sửa):**
- `alembic/versions/meeting_013_trang_thai_trinh_chieu_20260502.py`
- `models/trang_thai_trinh_chieu.py`
- `schemas/presentation.py`
- `services/presentation_manager.py` + `services/broadcast_backend.py`
- `api/endpoints/presentation_rest.py` + `api/endpoints/presentation_ws.py`
- **(v3.1)** Sửa `api/endpoints/cuoc_hop.py` + `services/cuoc_hop_service.py`: thêm 2 endpoint `bat-dau`/`ket-thuc`
- `tests/test_presentation_manager.py` + `tests/test_presentation_ws.py` + `tests/test_presentation_rest.py`
- `tests/test_cuoc_hop_lifecycle.py` *(v3.1, 5 test cho bat-dau/ket-thuc)*
- `tests/integration/test_multi_client_sync.py`

**Frontend (~7 file mới):**
- `_components/PresentationViewer.tsx` (PDF.js based)
- `_components/StartPresentationButton.tsx`
- `_components/SyncStatusBadge.tsx`
- `_components/IndependentViewBanner.tsx`
- `_components/ConfirmReturnDialog.tsx`
- `_hooks/usePresentationSync.ts`
- `_utils/wsClient.ts` (exponential backoff wrapper)

**Ops:**
- `scripts/backup_daily.sh`
- `scripts/cleanup_preview_cache.sh`
- Cập nhật `CLAUDE.md` (port mapping, mới có Phase 4.1)
- Cập nhật `PM2_DEPLOY.md` (cron + pm2-logrotate)
- 1 trang hướng dẫn chu_toa (PDF + Markdown)

---

## 7. TEST STRATEGY

### 7.1. Unit + Integration (~35 test mới)

| File | Số test | Coverage |
|---|---|---|
| `test_presentation_manager.py` | 12 | add/remove/broadcast, async lock concurrency, debounce, host disconnect detection |
| `test_presentation_rest.py` | 5 | GET state, cấp WS token với TTL đúng, phân quyền |
| `test_presentation_ws.py` | 20 | auth, lifecycle, 5 inbound events, edge cases, reconnect, audit log scope |

### 7.2. Multi-client integration

`tests/integration/test_multi_client_sync.py`:
- Spawn 1 chu_toa + 50 đại biểu (asyncio websockets)
- Chu_toa gửi 100 events random
- Assert: p95 < 500ms, success rate > 95%

### 7.3. Manual UAT checklist (Tuần 3)

15 test cases manual + 1 cuộc họp thử 30 phút với 5 volunteer.

---

## 8. SECURITY CHECKLIST

| Vấn đề | Mitigation |
|---|---|
| WS token leak | TTL bounded, scope check, 1 token per session |
| Spam events | Server debounce 150ms |
| Cross-meeting injection | Validate JWT scope khớp path param |
| Đại biểu gửi inbound events | Reject silently + audit log attempt |
| Idle WS | Heartbeat ping/pong 30s, kick sau 2min idle |
| Audit flooding | Chỉ 3 events business-value vào DB |
| Tài liệu bị xóa | Handler check `is_deleted` trước broadcast |

---

## 9. RỦI RO TỒN TẠI (CHẤP NHẬN)

| Rủi ro | Mức | Lý do chấp nhận |
|---|---|---|
| Service restart giữa cuộc họp → mất pool 5-10s | Trung | Acceptable, DB lưu state, client tự reconnect |
| Mobile Safari WebSocket unstable | Trung | Mitigation bằng visibilitychange + reconnect; nếu fail nhiều ở UAT, thêm fallback Phase 5 |
| Latency >500ms tại HQ Cửa khẩu xa qua VPN | Thấp | Đo lúc UAT; nếu vấn đề → optimize event payload size |
| PM2 restart graceful close WS không hoạt động | Thấp | Test bằng `pm2 reload`; thêm SIGTERM handler nếu cần |

---

## 10. APPROVAL & NEXT STEP

**Tài liệu này thay thế plan v1, v2, v3.0.** Sau khi approve:

1. Tôi sẽ deliver code theo thứ tự **timeline tuần 1 chính xác** từ Th.2
2. Mỗi exit criteria cuối tuần phải pass mới sang tuần tiếp
3. Nếu phát sinh blocker giữa chừng → flag ngay, không tự ý mở rộng scope
4. UAT volunteer + tài liệu hướng dẫn anh giúp coordinate trong tuần 2-3

### 10.1. Tiền điều kiện ngoài kỹ thuật *(v3.1 thêm mới)*

- **Xác nhận scope-cut với Văn phòng:** plan gốc Phase 4 (`KeHoach_Phase4_HKG.docx`) có 10 hạng mục/4 tuần để nâng đáp ứng VP từ 72% → 92%. Plan 4.1 này chỉ làm 1/10 hạng mục (page-sync) trong 3 tuần, đẩy 9 hạng mục còn lại sang Phase 4.2/4.3/5. **Cần văn bản/email VP đồng ý** với lộ trình tách phase này TRƯỚC khi bắt đầu code, để tránh trượt cam kết "92% cuối tháng 5/2026".

---

*Hết plan v3.1. Sẵn sàng bắt đầu code khi anh confirm + VP duyệt scope-cut.*

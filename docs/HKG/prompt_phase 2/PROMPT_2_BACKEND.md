# PROMPT 2 — BACKEND LAYER (v3.1)

> **Prerequisites:** MASTER_PROMPT v3.1 + plan v3.1 + PROMPT 1 đã hoàn thành.
>
> **🔧 Convention codebase đã verify (BẮT BUỘC tuân thủ):**
> - **Async DB:** mọi endpoint dùng `async def` + `db: AsyncSession = Depends(get_db)` + `await db.execute(...)`. Codebase **KHÔNG dùng** `Session` (sync). Code mẫu trong prompt này phản ánh đúng pattern này.
> - **JWT:** `current_user` là `TokenPayload` (object có `.sub`, `.platform_roles`), KHÔNG phải `dict`. Verify từ `meeting_service/dependencies.py` + `app/schemas/auth.py`.
> - **Status enum:** `LEN_KE_HOACH | DA_THONG_BAO | DANG_DIEN_RA | HOAN_THANH | HUY` — **`HUY`** chứ KHÔNG phải `DA_HUY`.
> - **`cuoc_hop` audit cols:** chỉ có `created_at, updated_at, created_by` — KHÔNG có `updated_by`. Trace user-thực-hiện qua `common.audit_log.cong_chuc_id`.

---

## Mục tiêu

Hoàn thành toàn bộ backend cho page-sync + P0 hardening + endpoints meeting lifecycle (blocker mới phát hiện ở v3.1). Effort dự kiến **6-7 ngày**, chia làm **6 phases**.

| Phase | Nội dung | Effort | Commit |
|---|---|---|---|
| **P1** | P0 Hardening (backup + cleanup + rate limit + logrotate) | 1.5 ngày | 1 commit |
| **P2** ⭐ | **Endpoints lifecycle** `/cuoc-hop/{id}/bat-dau` + `/ket-thuc` (blocker v3.1) | 0.5 ngày | 1 commit |
| **P3** | REST endpoint `GET /presentation/state` + WS token | 1 ngày | 1 commit |
| **P4** | `BroadcastBackend` + `InMemoryBackend` + `PresentationManager` | 1 ngày | 1 commit |
| **P5** | WebSocket endpoint + 5 inbound handlers + lifecycle | 1.5 ngày | 1 commit |
| **P6** | Edge cases + audit + integration tests + stress test | 1 ngày | 1 commit |

⭐ **Phase 2 mới ở v3.1** — codebase chưa có cách set `cuoc_hop.trang_thai='DANG_DIEN_RA'`. Không có 2 endpoints này thì page-sync không bao giờ trigger được.

---

## Pre-flight (đọc trước Phase 1)

```
1. ecosystem.config.js — pm2 process name + env file path
2. backend/meeting_service/main.py — middleware order, app initialization
3. backend/meeting_service/dependencies.py — JWT decode pattern, get_current_user
4. backend/meeting_service/api/endpoints/cuoc_hop.py — pattern endpoint update + permission check
5. backend/meeting_service/api/endpoints/tai_lieu.py — pattern POST với JWT
6. backend/meeting_service/services/audit_log_service.py (nếu có) — pattern ghi audit
7. backend/meeting_service/models/cuoc_hop.py — verify cột thời gian:
   - ngay_hop (DATE)
   - gio_bat_dau (TIME) 
   - gio_ket_thuc (TIME, nullable?)
   - trang_thai (enum: `LEN_KE_HOACH, DA_THONG_BAO, DANG_DIEN_RA, HOAN_THANH, HUY` — verified `schemas/cuoc_hop.py:12`. **`HUY` chứ KHÔNG phải `DA_HUY`**)
8. backend/meeting_service/tests/conftest.py — fixtures có sẵn
9. /var/data/hkg/uploads (production path) hoặc HKG_UPLOAD_DIR
```

---

# PHASE 1 — P0 Hardening

## Task

### 1.1 — `scripts/backup_daily.sh`

Bash script backup hàng ngày:
- pg_dump DB `kpi_haiquan` → gzip → `/var/backup/kpi_haiquan/daily/db_YYYYMMDD_HHMM.sql.gz`
- rsync `$HKG_UPLOAD_DIR/` → `/var/backup/kpi_haiquan/uploads/` (loại trừ `_preview_cache/`)
- Monthly snapshot ngày 1 → `/monthly/`
- Retention: daily 30 ngày, monthly 12 tháng
- Pre-check disk space (>2x DB size); fail-fast nếu thiếu
- Verify dump không corrupt (size >1MB)
- Log timestamp prefix
- `set -euo pipefail`

### 1.2 — `scripts/cleanup_preview_cache.sh`

```bash
find $HKG_UPLOAD_DIR/_preview_cache -name "*.pdf" -mtime +30 -delete
```
+ logging số file deleted, fail-safe nếu thư mục không tồn tại.

### 1.3 — Rate limit upload

Cài `slowapi`, thêm vào `requirements.txt`.

Trong `meeting_service/main.py`:
- Init `limiter = Limiter(key_func=lambda req: req.state.user_id if hasattr(req.state, 'user_id') else get_remote_address(req))`
- `app.state.limiter = limiter`
- Add exception handler

Trong `api/endpoints/tai_lieu.py` POST upload:
- Decorator `@limiter.limit("10/5minutes")`

### 1.4 — pm2-logrotate

Document trong `INSTALL_CRON.md`:
```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 50M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true
```

### 1.5 — Cron config + INSTALL doc

`/etc/cron.d/hkg-backups`:
```
0 2 * * * root /opt/kpi/scripts/backup_daily.sh >> /var/log/backup_kpi.log 2>&1
0 3 * * 0 root /opt/kpi/scripts/cleanup_preview_cache.sh >> /var/log/cleanup_cache.log 2>&1
```

`scripts/INSTALL_CRON.md` hướng dẫn setup từ đầu (chmod 700, owner, install cron, test manual).

## Acceptance P1

- Manual run `backup_daily.sh` thành công, file `db_*.sql.gz` xuất hiện
- Restore test: `gunzip -c <dump>.sql.gz | psql -d test_kpi_haiquan` không lỗi
- Manual run `cleanup_preview_cache.sh` không lỗi
- 11 upload trong 5 phút → request 11 nhận `429`
- `pm2 list` thấy `pm2-logrotate` running
- 2 cron jobs visible
- Scripts `chmod 700`

## Commit P1

```
[Phase 4.1][BE_P1] Add P0 hardening: backup + cleanup cron + rate limit
```

> **STOP. Verify trước Phase 2.**

---

# PHASE 2 — Endpoints Meeting Lifecycle ⭐ (NEW v3.1)

## Context

Codebase MVP có enum `trang_thai = LEN_KE_HOACH | DA_THONG_BAO | DANG_DIEN_RA | HOAN_THANH | HUY` nhưng **không có endpoint nào set `DANG_DIEN_RA`**. Page-sync chỉ trigger khi cuộc họp ở trạng thái này → đây là **blocker thực sự** không thể skip.

Phase này thêm 2 endpoints để chu_toa/thu_ky chuyển trạng thái cuộc họp.

## Task

### 2.1 — `POST /api/v1/hop-khong-giay/cuoc-hop/{id}/bat-dau`

File: `backend/meeting_service/api/endpoints/cuoc_hop_lifecycle.py` (file mới hoặc append vào `cuoc_hop.py`)

```python
@router.post("/{cuoc_hop_id}/bat-dau", response_model=CuocHopResponse)
async def bat_dau_cuoc_hop(
    cuoc_hop_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Chu_toa hoặc thu_ky bấm bắt đầu cuộc họp.
    
    Valid transition: DA_THONG_BAO → DANG_DIEN_RA
    Permissions: chu_toa hoặc thu_ky của cuộc họp (hoặc TRUONG_CNTT)
    """
```

Logic:
1. Validate cuoc_hop tồn tại + chưa bị xóa (`is_deleted=FALSE`)
2. Permission: `chu_toa_id == user.sub OR thu_ky_id == user.sub OR 'TRUONG_CNTT' in (user.platform_roles or [])`
   *(`platform_roles` đã có sẵn trong JWT — verified `app/api/v1/endpoints/auth.py` thêm vào claims, `meeting_service/dependencies.py` đã consume.)*
3. State machine: chỉ accept transition `DA_THONG_BAO → DANG_DIEN_RA`. Status khác → 400 với thông báo rõ
4. Update `trang_thai = 'DANG_DIEN_RA'`, `updated_at = NOW()` *(KHÔNG có cột `updated_by` trên `cuoc_hop` — chỉ có `created_by`. Audit log đã capture `cong_chuc_id` ở bước 5, đủ trace.)*
5. Audit log: `module=MEETING`, `hanh_dong=CUOC_HOP_BAT_DAU`, `cong_chuc_id=user.sub`, `doi_tuong_loai='CUOC_HOP'`, `doi_tuong_id=cuoc_hop_id`
6. `await db.commit()` rồi return updated cuoc_hop

### 2.2 — `POST /api/v1/hop-khong-giay/cuoc-hop/{id}/ket-thuc`

```python
@router.post("/{cuoc_hop_id}/ket-thuc", response_model=CuocHopResponse)
async def ket_thuc_cuoc_hop(
    cuoc_hop_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Chu_toa hoặc thu_ky bấm kết thúc cuộc họp.
    
    Valid transition: DANG_DIEN_RA → HOAN_THANH
    """
```

Logic tương tự `bat-dau`:
1. Permission check
2. State machine: chỉ accept `DANG_DIEN_RA → HOAN_THANH`
3. Update status + audit log `CUOC_HOP_KET_THUC`
4. **Side effect:** nếu có row `trang_thai_trinh_chieu` với `is_active=TRUE` → set `is_active=FALSE`, `ket_thuc_luc=NOW()` (cleanup state)
5. Return updated cuoc_hop

### 2.3 — Tests `tests/test_cuoc_hop_lifecycle.py`

5 test cases:

| Test | Verify |
|---|---|
| `test_bat_dau_valid_transition` | DA_THONG_BAO → DANG_DIEN_RA OK, status updated |
| `test_bat_dau_invalid_transition` | LEN_KE_HOACH → bat-dau → 400 |
| `test_bat_dau_permission_required` | user không phải chu_toa/thu_ky → 403 |
| `test_ket_thuc_cleanup_presentation_state` | DANG_DIEN_RA + trang_thai_trinh_chieu(is_active=TRUE) → ket-thuc → state is_active=FALSE |
| `test_audit_log_recorded` | sau bat-dau → audit row có hanh_dong=CUOC_HOP_BAT_DAU |

## Acceptance P2

- 2 endpoints work, return 200 cho transition hợp lệ, 400/403 cho invalid
- 5/5 tests pass
- Audit log có 2 hanh_dong mới: `CUOC_HOP_BAT_DAU`, `CUOC_HOP_KET_THUC`
- Manual test: tạo cuộc họp test, chuyển từ LEN_KE_HOACH → DA_THONG_BAO → DANG_DIEN_RA → HOAN_THANH

## Commit P2

```
[Phase 4.1][BE_P2] Add endpoints POST /cuoc-hop/{id}/bat-dau + /ket-thuc (v3.1 blocker)
```

> **STOP. Verify trước Phase 3 — đây là blocker, không có Phase 2 thì Phase 3-6 không test được.**

---

# PHASE 3 — REST Endpoint + WS Token

## Task

### 3.1 — Token logic (TTL formula v3.1)

File: `backend/meeting_service/services/ws_token_service.py`

```python
import zoneinfo
from datetime import datetime, timedelta

HCM_TZ = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
TOKEN_MAX_TTL_HOURS = 6
DEFAULT_BUFFER_AFTER_END_HOURS = 1
FALLBACK_DURATION_HOURS = 4


def calculate_ws_token_expiry(cuoc_hop) -> datetime:
    """
    Tính WS token expiration theo formula plan v3.1 §3.2.
    
    Normal: combine(ngay_hop, gio_ket_thuc, tz=Asia/HCM) + 1h buffer
    Fallback (gio_ket_thuc NULL): combine(ngay_hop, gio_bat_dau, tz=Asia/HCM) + 4h
    Capped at NOW (HCM) + 6h to prevent abuse.
    
    Returns: timezone-aware datetime in Asia/HCM.
    """
    if cuoc_hop.gio_ket_thuc is not None:
        end_naive = datetime.combine(cuoc_hop.ngay_hop, cuoc_hop.gio_ket_thuc)
        end_aware = end_naive.replace(tzinfo=HCM_TZ)
        candidate = end_aware + timedelta(hours=DEFAULT_BUFFER_AFTER_END_HOURS)
    else:
        # Fallback: dùng gio_bat_dau + 4h
        start_naive = datetime.combine(cuoc_hop.ngay_hop, cuoc_hop.gio_bat_dau)
        start_aware = start_naive.replace(tzinfo=HCM_TZ)
        candidate = start_aware + timedelta(hours=FALLBACK_DURATION_HOURS)
    
    cap = datetime.now(HCM_TZ) + timedelta(hours=TOKEN_MAX_TTL_HOURS)
    return min(candidate, cap)


def create_ws_token(
    user_id: UUID,
    cuoc_hop_id: UUID,
    cuoc_hop,  # ORM object để extract ngay_hop, gio_*
) -> tuple[str, datetime]:
    """
    Tạo short-lived JWT cho WebSocket connection.

    JWT payload:
    {
      "sub": "<user_id>",
      "scope": "meeting:<cuoc_hop_id>",
      "type": "ws_presentation",
      "exp": <unix_timestamp>
    }

    Returns: (token, expires_at_dt)
    """
    expires_at = calculate_ws_token_expiry(cuoc_hop)
    # ... encode JWT với SECRET_KEY chung
    return token, expires_at


def verify_ws_token(token: str, cuoc_hop_id: UUID) -> UUID:
    """
    Verify token + return user_id.
    Raise nếu: expired, invalid signature, scope mismatch, type wrong.
    """
```

### 3.2 — REST endpoint với scope check (v3.1)

File: `backend/meeting_service/api/endpoints/presentation_rest.py`

```python
@router.get("/cuoc-hop/{cuoc_hop_id}/presentation/state",
            response_model=PresentationStateResponse)
async def get_presentation_state(
    cuoc_hop_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PresentationStateResponse:
    """
    GET state hiện tại của phiên trình chiếu + cấp WS token.

    v3.1 scope check:
    - Cuộc họp phải có trang_thai IN ('DA_THONG_BAO', 'DANG_DIEN_RA')
    - LEN_KE_HOACH / HOAN_THANH / HUY → 403
    - Cho phép DA_THONG_BAO để chu_toa pre-load tài liệu trước giờ họp
    
    Permissions: chu_toa, thu_ky, hoặc thanh_phan của cuoc_hop.
    Response gồm WS token với TTL theo formula v3.1.
    """
```

Logic:
1. Verify cuoc_hop tồn tại + chưa bị xóa
2. **Scope check (v3.1):** `cuoc_hop.trang_thai IN ('DA_THONG_BAO', 'DANG_DIEN_RA')` → nếu không, 403 với message rõ
3. Permission: chu_toa OR thu_ky OR thanh_phan
4. **UPSERT** row `trang_thai_trinh_chieu` (dùng `INSERT ... ON CONFLICT (cuoc_hop_id) DO UPDATE SET cap_nhat_luc=NOW()`)
5. Tạo WS token với `calculate_ws_token_expiry(cuoc_hop)`
6. Return state + token + flags `is_chu_toa`, `is_thu_ky`

Register router vào `main.py` với prefix `/api/v1/hop-khong-giay`.

### 3.3 — Tests `tests/test_presentation_rest.py`

Tối thiểu **8 test cases** (tăng so với v3.0 do thêm test scope mới):

| Test | Verify |
|---|---|
| `test_get_state_creates_row_lazy` | gọi lần đầu → row được tạo qua UPSERT |
| `test_get_state_returns_existing` | gọi lần 2 → return row cũ, KHÔNG tạo duplicate |
| `test_get_state_chu_toa_flags` | chu_toa user → `is_chu_toa=True` |
| `test_get_state_thu_ky_flags` | thu_ky user → `is_thu_ky=True` |
| `test_get_state_unauthorized_user` | user không liên quan → 403 |
| `test_get_state_status_len_ke_hoach_403` | cuoc_hop LEN_KE_HOACH → 403 (v3.1 scope) |
| `test_get_state_status_da_thong_bao_ok` | cuoc_hop DA_THONG_BAO → 200 (v3.1 cho phép pre-load) |
| `test_get_state_ws_token_ttl_formula` | verify TTL theo formula: ngay_hop + gio_ket_thuc + 1h, capped 6h |
| `test_get_state_ws_token_fallback_no_gio_ket_thuc` | gio_ket_thuc NULL → TTL = ngay_hop + gio_bat_dau + 4h |

## Acceptance P3

- Endpoint trả 200 + JSON đúng schema cho user hợp lệ với status hợp lệ
- Endpoint trả 403 cho các status ngoài DA_THONG_BAO/DANG_DIEN_RA
- WS token có thể decode bằng `verify_ws_token` thành công
- TTL formula đúng cả normal case lẫn fallback
- 8-9 tests pass

## Commit P3

```
[Phase 4.1][BE_P3] Add REST GET /presentation/state with v3.1 token TTL formula + scope check
```

> **STOP. Verify trước Phase 4.**

---

# PHASE 4 — PresentationManager + Broadcast Backend

## Task

### 4.1 — `BroadcastBackend` interface

File: `backend/meeting_service/services/broadcast_backend.py`

```python
from typing import Protocol
from fastapi import WebSocket

class BroadcastBackend(Protocol):
    """
    Abstract interface — MVP dùng InMemoryBackend.
    Phase sau swap sang RedisPubSubBackend khi cần multi-worker.
    """

    async def add_client(
        self, channel: str, ws: WebSocket, is_host: bool = False
    ) -> None: ...

    async def remove_client(
        self, channel: str, ws: WebSocket
    ) -> None: ...

    async def broadcast(
        self, channel: str, event: dict, exclude: WebSocket | None = None
    ) -> None: ...

    async def host_count(self, channel: str) -> int: ...
    async def client_count(self, channel: str) -> int: ...
    async def close_channel(self, channel: str, reason: dict) -> None: ...
```

### 4.2 — `InMemoryBackend` implementation

```python
class InMemoryBackend:
    """
    In-memory pool cho single PM2 process.

    Trade-offs:
    - Pros: 0 dependency, latency ~5-20ms
    - Cons: KHÔNG scale multi-worker (state local)
    - Restart service → mất pool, client tự reconnect (DB lưu state)
    """

    def __init__(self):
        self._pools: dict[str, set[WebSocket]] = defaultdict(set)
        self._host_conns: dict[str, set[WebSocket]] = defaultdict(set)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
```

Method implementation:
- `broadcast`: dùng `asyncio.gather(*[send safely], return_exceptions=True)` để 1 client lỗi không break broadcast
- `add_client`/`remove_client`: lock per channel để tránh race
- `host_count`: kiểm tra tracked WS host để gửi `host_disconnected`/`host_reconnected`
- `close_channel`: gửi event `meeting_ended` rồi close all WS với code 1000

### 4.3 — `PresentationManager`

File: `backend/meeting_service/services/presentation_manager.py`

```python
class PresentationManager:
    """
    High-level service: lifecycle + state DB UPSERT + debounce + broadcast routing.
    """

    def __init__(self, backend: BroadcastBackend, db_session_factory):
        self.backend = backend
        self._db_factory = db_session_factory
        self._debounce_tasks: dict[tuple, asyncio.Task] = {}

    async def handle_inbound_event(
        self,
        cuoc_hop_id: UUID,
        user_id: UUID,
        event: WSInboundEvent,
        ws: WebSocket,
    ) -> None:
        """
        Process inbound event từ chu_toa.
        Áp dụng debounce 150ms cho page_change/zoom_change.
        """
```

Logic:
1. Validate user là chu_toa của cuoc_hop (silent reject nếu không)
2. Validate cuoc_hop trang_thai = `DANG_DIEN_RA` (DA_THONG_BAO không cho phép start trình chiếu)
3. Switch theo event type:
   - `presentation_start`: UPSERT DB (is_active=TRUE, bat_dau_luc=NOW), broadcast `presentation_started`
   - `presentation_end`: UPDATE DB (is_active=FALSE, ket_thuc_luc=NOW), broadcast `presentation_ended`
   - `document_open`: validate tai_lieu thuộc cuoc_hop, UPDATE DB, broadcast `document_changed`
   - `page_change`: **debounce 150ms** rồi UPDATE + broadcast
   - `zoom_change`: **debounce 150ms** rồi UPDATE + broadcast
4. Audit log với 3 events business value: `PRESENTATION_START`, `PRESENTATION_END`, `DOCUMENT_OPEN` (v3.1 D11)

### 4.4 — Tests `tests/test_presentation_manager.py`

Tối thiểu **12 test cases**:

| Test | Verify |
|---|---|
| `test_add_remove_client` | pool tracking đúng |
| `test_broadcast_to_all_clients` | tất cả client nhận event |
| `test_broadcast_excludes_sender` | sender không nhận lại event |
| `test_broadcast_handles_client_error` | 1 client lỗi không break broadcast |
| `test_host_count_tracking` | đúng số host connections |
| `test_concurrent_add_remove` | async lock không gây race |
| `test_debounce_page_change` | 10 events trong 100ms → 1 broadcast |
| `test_debounce_per_user_isolation` | debounce user A không ảnh hưởng user B |
| `test_handle_event_non_host_silent_reject` | event từ non-chu_toa bị bỏ qua |
| `test_handle_presentation_start_upsert_db` | DB row UPSERT đúng (is_active=TRUE) |
| `test_handle_document_open_validates_tai_lieu` | tai_lieu sai cuoc_hop → reject |
| `test_close_channel_broadcasts_meeting_ended` | tất cả client nhận event + WS close |

## Acceptance P4

- 12/12 tests pass
- Debounce verified: bench 100 events trong 1 second → ~7 broadcasts (1 per 150ms window)
- No race condition khi spawn 50 concurrent client add/remove

## Commit P4

```
[Phase 4.1][BE_P4] Add BroadcastBackend interface + InMemoryBackend + PresentationManager
```

> **STOP. Verify trước Phase 5.**

---

# PHASE 5 — WebSocket Endpoint

## Task

### 5.1 — WS endpoint

File: `backend/meeting_service/api/endpoints/presentation_ws.py`

```python
@router.websocket("/cuoc-hop/{cuoc_hop_id}/presentation")
async def presentation_ws(
    websocket: WebSocket,
    cuoc_hop_id: UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint cho page-sync.

    Flow:
    1. Verify ws_token (scope=meeting:{cuoc_hop_id})
    2. Validate cuoc_hop trang_thai IN ('DA_THONG_BAO', 'DANG_DIEN_RA')
    3. Add to pool, send state_sync event
    4. Loop: receive events, dispatch to PresentationManager
    5. On disconnect: remove from pool, host detection
    """
```

Register vào main app với prefix `/ws/hop-khong-giay`.

### 5.2 — Connection lifecycle

(Logic giống v3.0 — không có thay đổi major. Xem plan v3.1 §3.2)

### 5.3 — Heartbeat

Heartbeat ping/pong 30s, kick connection nếu idle >2 phút.

### 5.4 — Tests `tests/test_presentation_ws.py`

Tối thiểu **15 test cases**. Dùng `httpx` hoặc `websockets` library + asyncio.

| Test | Verify |
|---|---|
| `test_connect_with_valid_token` | accept + receive state_sync |
| `test_connect_with_invalid_token` | close 1008 |
| `test_connect_with_expired_token` | close 1008 |
| `test_connect_wrong_scope` | token cho cuoc_hop khác → close 1008 |
| `test_connect_meeting_len_ke_hoach_close` | cuoc_hop LEN_KE_HOACH → close 1008 (v3.1 scope) |
| `test_connect_meeting_da_thong_bao_ok` | cuoc_hop DA_THONG_BAO → accept (v3.1 cho phép pre-connect) |
| `test_chu_toa_can_send_events` | chu_toa send page_change → others receive page_changed |
| `test_dai_bieu_send_event_silent_reject` | dai_bieu send → server không broadcast |
| `test_disconnect_removes_from_pool` | disconnect → pool size giảm |
| `test_host_disconnect_broadcast_30s_delay` | host disconnect 35s → others nhận host_disconnected |
| `test_host_reconnect_broadcast` | host reconnect trong 30s → others nhận host_reconnected |
| `test_state_sync_after_reconnect` | reconnect → nhận state mới nhất |
| `test_meeting_ended_closes_all` | cuoc_hop → HOAN_THANH → all WS close + nhận meeting_ended |
| `test_document_deleted_returns_error_event` | tai_lieu xóa giữa chừng → error event |
| `test_concurrent_50_clients_broadcast` | 50 client connect đồng thời, broadcast OK |
| `test_heartbeat_keeps_connection_alive` | idle 60s vẫn connected nhờ heartbeat |

## Acceptance P5

- 16/16 tests pass
- Manual test bằng `wscat` (sau khi gọi POST /bat-dau từ Phase 2 để cuoc_hop chuyển sang DANG_DIEN_RA):
  ```bash
  # Terminal 1 (host)
  wscat -c "ws://localhost:8006/ws/hop-khong-giay/cuoc-hop/<id>/presentation?token=<host_token>"
  > {"type":"presentation_start","tai_lieu_id":"<id>","page":1}

  # Terminal 2-6 (5 đại biểu)
  wscat -c "ws://..."
  ```

## Commit P5

```
[Phase 4.1][BE_P5] Add WebSocket endpoint /ws/.../presentation with full lifecycle
```

> **STOP. Verify trước Phase 6.**

---

# PHASE 6 — Edge Cases + Audit + Stress Test

## Task

### 6.1 — Edge case handlers (plan v3.1 §3.3)

Mỗi inbound event handler check trước broadcast:
1. Cuộc họp còn `DANG_DIEN_RA`? Nếu không → gửi `meeting_ended` + close all
2. Tài liệu còn tồn tại (NOT is_deleted)? Nếu không → error event
3. User vẫn là chu_toa? Nếu không → silent reject

Trigger khi cuoc_hop status thay đổi (từ Phase 2 endpoint `ket-thuc`):
- Hook trong `ket_thuc_cuoc_hop` handler → call `manager.backend.close_channel(channel, {"type": "meeting_ended", "reason": "completed"})`

### 6.2 — Audit log integration (v3.1: 5 events)

5 actions ghi `common.audit_log`:

| Action | Khi nào |
|---|---|
| `CUOC_HOP_BAT_DAU` | (đã làm ở Phase 2) |
| `CUOC_HOP_KET_THUC` | (đã làm ở Phase 2) |
| `PRESENTATION_START` | chu_toa bắt đầu trình chiếu |
| `PRESENTATION_END` | chu_toa kết thúc |
| `DOCUMENT_OPEN` | chu_toa mở tài liệu (cả lần đầu lẫn đổi tài liệu) |

KHÔNG audit `page_change`/`zoom_change` (D11). Nếu cần debug → structured log file `/var/log/hkg-presentation.log`.

### 6.3 — Stress test integration

File: `backend/meeting_service/tests/integration/test_multi_client_stress.py`

```python
@pytest.mark.slow
async def test_50_clients_page_sync_latency():
    """
    Spawn 1 chu_toa + 50 đại biểu (asyncio websockets).
    Chu_toa gửi 100 page_change ngẫu nhiên trong 30s.
    Đo: p50, p95, p99 latency từ send → receive ở client.

    Assert: p95 < 500ms, success rate > 95%.
    """
```

### 6.4 — Tests bổ sung edge cases `tests/test_presentation_edge_cases.py`

5 test cases:
- `test_meeting_cancelled_during_presentation` — admin hủy giữa chừng → broadcast meeting_ended + close all
- `test_meeting_completed_during_presentation` — gọi POST /ket-thuc → broadcast meeting_ended
- `test_document_deleted_during_active_presentation` — thư ký xóa tai_lieu đang chiếu → error event tới host
- `test_audit_log_only_business_events` — verify chỉ 5 actions (đã có) trong common.audit_log
- `test_audit_log_no_page_change` — gửi 50 page_change → 0 audit row PAGE_CHANGE

### 6.5 — Update CLAUDE.md / PM2_DEPLOY.md

Document Phase 4.1:
- Bảng mới `meeting.trang_thai_trinh_chieu` (no is_deleted)
- Endpoints mới: 4 endpoints
  - `POST /cuoc-hop/{id}/bat-dau` (v3.1)
  - `POST /cuoc-hop/{id}/ket-thuc` (v3.1)
  - `GET /cuoc-hop/{id}/presentation/state`
  - `WS /ws/.../presentation`
- 4 P0 deliverables (backup + cleanup + rate limit + logrotate)

## Acceptance P6

- 5/5 edge case tests pass
- Stress test (manual): p95 < 500ms với 50 client
- `common.audit_log` query verify: chỉ 5 hanh_dong values cho module=MEETING, không có PAGE_CHANGE
- Total tests: dùng `grep -rE "def test_" backend/meeting_service/tests/ | wc -l` để verify
- CLAUDE.md updated

## Commit P6

```
[Phase 4.1][BE_P6] Add edge case handlers + audit log (5 actions) + stress test
```

---

## Báo PM khi PROMPT 2 xong

- Tests trước/sau (grep count, không trust số tài liệu)
- Stress test result: p50, p95, p99 latency với 50 client
- Audit log: 5 actions found, total rows test cycle
- Conflict nào với MVP code không
- Ngày actually mất so với plan 6-7 ngày

Sẵn sàng nhận `PROMPT_3_FRONTEND.md`.

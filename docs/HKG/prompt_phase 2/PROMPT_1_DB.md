# PROMPT 1 — DATABASE LAYER (v3.1)

> **Prerequisites:** MASTER_PROMPT v3.1 + plan v3.1 đã trong context.

---

## Mục tiêu

Tạo foundation database cho page-sync: 1 migration, 1 SQLAlchemy model, Pydantic schemas đầy đủ cho REST + WS payloads.

**Bảng mới:** `meeting.trang_thai_trinh_chieu` — lưu state realtime của phiên trình chiếu (1 cuộc họp = 1 row, UNIQUE constraint, **KHÔNG có `is_deleted`** vì là state UPSERT 1-1).

**Effort dự kiến:** 0.5-1 ngày, chia làm **3 phases**.

---

## Pre-flight (bắt buộc đọc trước Phase 1)

```
1. backend/alembic/versions/ — list tất cả file để xác định:
   *(LƯU Ý: alembic là **shared** ở root `backend/alembic/`, KHÔNG có `backend/meeting_service/alembic/`. Tất cả service dùng chung 1 Alembic environment, chạy auto trên app startup.)*
   - Pattern filename thực tế (đang là meeting_NNN_<snake>_<YYYYMMDD>.py)
   - Số NNN tiếp theo cần dùng (verify, có thể là 013)
   - Pattern revision id (chuỗi tiếng Anh? hash 12 ký tự? format khác?)
2. 2-3 migration cũ tạo bảng (vd file tạo cuoc_hop, tai_lieu)
   → CREATE TABLE syntax style (raw SQL vs op.create_table), INDEX naming
3. backend/meeting_service/models/cuoc_hop.py
   → Base class import path, declarative pattern, relationships
   → Verify tên cột thời gian: ngay_hop (DATE), gio_bat_dau (TIME), gio_ket_thuc (TIME)
4. backend/meeting_service/models/tai_lieu.py
   → enum pattern, FK syntax tới public.cong_chuc
5. backend/meeting_service/models/__init__.py
   → export convention
6. backend/meeting_service/schemas/ (vd cuoc_hop.py, tai_lieu.py)
   → Pydantic v1 hay v2, ConfigDict pattern
```

Confirm:
- Pydantic v1 hay v2?
- SQLAlchemy 1.x style (`Column(...)`) hay 2.x (`Mapped[...]`)?
- Migration dùng `op.execute` raw SQL hay `op.create_table`?
- Migration filename pattern chính xác là gì?

---

# PHASE 1 — Migration `meeting_NNN_trang_thai_trinh_chieu_20260502`

## Task

File: `backend/alembic/versions/meeting_NNN_trang_thai_trinh_chieu_20260502.py`

**Trong đó NNN là số migration tiếp theo, verify từ thư mục.** Ví dụ nếu hiện tại có file mới nhất là `meeting_012_*`, thì file mới là `meeting_013_trang_thai_trinh_chieu_20260502.py`.

**Schema bảng** (theo plan v3.1 §3.1 — KHÔNG có `is_deleted`):

```sql
CREATE TABLE meeting.trang_thai_trinh_chieu (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cuoc_hop_id              UUID NOT NULL UNIQUE
                               REFERENCES meeting.cuoc_hop(id) ON DELETE CASCADE,
    tai_lieu_hien_tai_id     UUID NULL
                               REFERENCES meeting.tai_lieu(id) ON DELETE SET NULL,
    trang_hien_tai           INTEGER NOT NULL DEFAULT 1
                               CHECK (trang_hien_tai > 0),
    zoom_level               NUMERIC(4,2) NOT NULL DEFAULT 1.0
                               CHECK (zoom_level >= 0.5 AND zoom_level <= 4.0),
    is_active                BOOLEAN NOT NULL DEFAULT FALSE,
    bat_dau_luc              TIMESTAMPTZ NULL,
    ket_thuc_luc             TIMESTAMPTZ NULL,
    cap_nhat_luc             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cap_nhat_boi_id          UUID NULL
                               REFERENCES public.cong_chuc(id) ON DELETE SET NULL,
    -- KHÔNG có is_deleted (v3.1) — bảng state UPSERT 1-1, không cần soft delete

    CONSTRAINT chk_ttc_active_has_doc
        CHECK (NOT is_active OR tai_lieu_hien_tai_id IS NOT NULL),
    CONSTRAINT chk_ttc_thoi_gian_hop_le
        CHECK (bat_dau_luc IS NULL OR ket_thuc_luc IS NULL OR bat_dau_luc <= ket_thuc_luc)
);

-- Index thông thường, KHÔNG có WHERE NOT is_deleted
CREATE INDEX idx_ttc_cuoc_hop ON meeting.trang_thai_trinh_chieu(cuoc_hop_id);
CREATE INDEX idx_ttc_active ON meeting.trang_thai_trinh_chieu(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE meeting.trang_thai_trinh_chieu IS
    'Phase 4.1 — State phiên trình chiếu. 1 cuộc họp = 1 row, UPSERT, không soft delete.';
```

**Yêu cầu:**
- `revision` + `down_revision` theo pattern codebase thực tế (verify từ migration cũ — KHÔNG dùng pattern `mt_*`)
- Style migration giống file cũ (raw SQL hoặc op.create_table)
- `downgrade()`: `DROP TABLE IF EXISTS ... CASCADE`

## Acceptance Phase 1

- `alembic upgrade head` → success
- `alembic downgrade -1` → success
- `alembic upgrade head` lại → success (idempotent)
- `\d+ meeting.trang_thai_trinh_chieu` trong psql thấy đúng cột (KHÔNG có is_deleted) + constraint + index
- UNIQUE constraint trên `cuoc_hop_id` cho phép UPSERT (`INSERT ... ON CONFLICT (cuoc_hop_id) DO UPDATE`)

## Commit Phase 1

```
[Phase 4.1][DB_P1] Add migration meeting_NNN_trang_thai_trinh_chieu (no soft delete, UPSERT-friendly)
```

> **STOP HERE.** Verify acceptance trước khi sang Phase 2.

---

# PHASE 2 — SQLAlchemy Model

## Task

### File 1: `backend/meeting_service/models/trang_thai_trinh_chieu.py`

Class `TrangThaiTrinhChieu`:
- Inherit Base class (verify path)
- Match exactly với migration: cột, type, default, FK, constraints
- `__table_args__` reflect tất cả CheckConstraint, UniqueConstraint, schema
- **KHÔNG có cột `is_deleted`** (khác với các model nghiệp vụ khác)
- Relationship:
  - `cuoc_hop`: many-to-one, `back_populates="trang_thai_trinh_chieu"`, lazy="select"
  - `tai_lieu_hien_tai`: many-to-one tới TaiLieu, `foreign_keys=[tai_lieu_hien_tai_id]`, lazy="select"
- `__repr__` cho debug
- Docstring giải thích lý do KHÔNG có `is_deleted`

### File 2: Sửa `backend/meeting_service/models/cuoc_hop.py`

Thêm relationship 1-1:
```python
trang_thai_trinh_chieu: Mapped[Optional["TrangThaiTrinhChieu"]] = relationship(
    "TrangThaiTrinhChieu",
    back_populates="cuoc_hop",
    uselist=False,
    cascade="all, delete-orphan",
    lazy="select",
)
```

### File 3: Sửa `backend/meeting_service/models/__init__.py`

Export `TrangThaiTrinhChieu`.

### File 4: Tests `backend/meeting_service/tests/test_trang_thai_trinh_chieu_model.py`

Tối thiểu **8 test cases** (KHÔNG có test soft delete):

| Test | Verify |
|---|---|
| `test_create_with_default_values` | defaults đúng (page=1, zoom=1.0, is_active=False) |
| `test_unique_cuoc_hop_constraint` | tạo 2 row cùng cuoc_hop → IntegrityError |
| `test_upsert_via_on_conflict` | UPSERT bằng `INSERT ... ON CONFLICT (cuoc_hop_id) DO UPDATE` hoạt động |
| `test_check_active_has_doc` | is_active=True + tai_lieu_id=NULL → CheckViolation |
| `test_check_zoom_range` | zoom=5.0 hoặc zoom=0.3 → CheckViolation |
| `test_check_page_positive` | trang_hien_tai=0 → CheckViolation |
| `test_check_thoi_gian_hop_le` | bat_dau > ket_thuc → CheckViolation |
| `test_cascade_delete_cuoc_hop` | xóa cuoc_hop → trang_thai cũng xóa |

Dùng tx-rollback fixture có sẵn trong codebase.

**Bỏ test soft delete** (vì bảng không có cột is_deleted).

## Acceptance Phase 2

- `from meeting_service.models import TrangThaiTrinhChieu` không lỗi
- `cuoc_hop.trang_thai_trinh_chieu` access được (relationship 2 chiều OK)
- 8/8 tests pass
- Total tests: `grep -rE "def test_" backend/meeting_service/tests/ | wc -l` → tăng đúng 8

## Commit Phase 2

```
[Phase 4.1][DB_P2] Add SQLAlchemy model TrangThaiTrinhChieu + 8 tests (no soft delete)
```

> **STOP HERE.** Verify acceptance trước khi sang Phase 3.

---

# PHASE 3 — Pydantic Schemas

## Task

File: `backend/meeting_service/schemas/presentation.py`

### REST schemas

```python
class PresentationStateResponse(BaseModel):
    """Response của GET /presentation/state."""
    cuoc_hop_id: UUID
    is_active: bool
    tai_lieu_hien_tai_id: Optional[UUID] = None
    trang_hien_tai: int = 1
    zoom_level: Decimal = Decimal("1.0")
    bat_dau_luc: Optional[datetime] = None
    ket_thuc_luc: Optional[datetime] = None
    cap_nhat_luc: datetime
    cap_nhat_boi_id: Optional[UUID] = None
    # Token cho WebSocket connection
    ws_token: str
    ws_token_expires_at: datetime
    # User context cho FE quyết định UI
    is_chu_toa: bool
    is_thu_ky: bool
```

### WS Inbound schemas (discriminated union by `type`)

```python
class WSInboundEventType(str, Enum):
    PRESENTATION_START = "presentation_start"
    PRESENTATION_END = "presentation_end"
    DOCUMENT_OPEN = "document_open"
    PAGE_CHANGE = "page_change"
    ZOOM_CHANGE = "zoom_change"

class PresentationStartPayload(BaseModel):
    type: Literal[WSInboundEventType.PRESENTATION_START]
    tai_lieu_id: UUID
    page: int = Field(default=1, ge=1)

# ...4 schemas còn lại tương tự

WSInboundEvent = Union[
    PresentationStartPayload,
    PresentationEndPayload,
    DocumentOpenPayload,
    PageChangePayload,
    ZoomChangePayload,
]
```

### WS Outbound schemas

10 events tương ứng (xem plan v3.1 §3.2 bảng outbound):
- `StateSyncEvent`, `PresentationStartedEvent`, `PresentationEndedEvent`
- `DocumentChangedEvent`, `PageChangedEvent`, `ZoomChangedEvent`
- `HostDisconnectedEvent`, `HostReconnectedEvent`
- `MeetingEndedEvent` (có field `reason: Literal["completed", "cancelled"]`)
- `WSErrorEvent` (có `code: str`, `message: str`)

### Yêu cầu chung

- Pydantic v2 syntax (`ConfigDict(from_attributes=True)`, `Field(...)`, `field_validator`)
- Validate page > 0, zoom ∈ [0.5, 4.0]
- Discriminated union dùng `Literal[type]` để FastAPI auto-parse
- Type hints: `UUID`, `datetime`, `Decimal`
- Validator round zoom về 2 decimal: `Decimal(str(v)).quantize(Decimal("0.01"))`

### Tests `tests/test_presentation_schemas.py`

Tối thiểu **5 test cases**:
- `test_presentation_state_response_serialize` — model_dump OK
- `test_inbound_event_discriminated_union` — parse JSON đúng schema theo `type`
- `test_zoom_validation_range` — zoom 5.0 → ValidationError
- `test_page_validation_positive` — page 0 → ValidationError
- `test_zoom_rounded_to_2_decimal` — input 1.234567 → 1.23

## Acceptance Phase 3

- Import schemas không lỗi
- 5/5 tests pass
- Total tests: tăng đúng 5 so với phase 2

## Commit Phase 3

```
[Phase 4.1][DB_P3] Add Pydantic schemas for presentation REST + WS
```

---

## Báo PM khi PROMPT 1 xong

- Số tests trước/sau (dùng grep, không trust số tài liệu)
- Pydantic version verified: v1 hay v2
- SQLAlchemy version verified: 1.x hay 2.x
- Migration NNN thực tế dùng: `meeting_NNN_*`
- Có conflict naming nào với migration cũ không
- CheckConstraint có reflect được hết trong model không (note workaround nếu có)
- Test UPSERT `INSERT ... ON CONFLICT` có work không (verify migration đúng)

Sẵn sàng nhận `PROMPT_2_BACKEND.md`.

# PROMPT 3 — FRONTEND LAYER (v3.1)

> **Prerequisites:** MASTER_PROMPT v3.1 + plan v3.1 + PROMPT 1 + PROMPT 2 đã hoàn thành (backend WS verified bằng wscat sau khi gọi POST /cuoc-hop/{id}/bat-dau).

---

## Mục tiêu

Hoàn thành toàn bộ frontend cho page-sync + UAT + deploy production. Effort dự kiến **6.5-8.5 ngày**, chia làm **6 phases** (thêm Phase 0 vì frontend chưa có test framework).

| Phase | Nội dung | Effort | Commit |
|---|---|---|---|
| **P0** | **Setup test framework (Vitest)** — frontend hiện chỉ có ESLint, chưa có jest/vitest | 0.5 ngày | 1 commit |
| P1 | PDF.js setup (**dynamic import ssr:false** v3.1) + viewer cơ bản | 1 ngày | 1 commit |
| P2 | `usePresentationSync` hook + reconnect + visibility | 1.5 ngày | 1 commit |
| P3 | UI components (toggle, banner, dialog, button) + tích hợp tab Tài liệu | 2 ngày | 1 commit |
| P4 | Mobile + buffer late-join + multi-tab | 1.5 ngày | 1 commit |
| P5 | Edge cases FE + onboarding + UAT mini + deploy | 1.5-2 ngày | 1-2 commits |

---

## Pre-flight (đọc trước Phase 1)

```
1. frontend/package.json — Next.js version (verify là 16), deps hiện tại
2. frontend/next.config.js — webpack config, có conflict gì với pdfjs-dist không
3. frontend/src/app/(main)/hop-khong-giay/chi-tiet/[id]/page.tsx — pattern tab "Tài liệu"
4. frontend/src/app/(main)/hop-khong-giay/xem-tai-lieu/page.tsx — viewer iframe hiện tại
5. frontend/src/lib/api.ts (hoặc tương đương) — HTTP client + JWT attach pattern
6. frontend/src/components/hkg/MeetingContext.tsx — quyền/state cuộc họp *(verified path — KHÔNG nằm trong `src/contexts/`)*
7. frontend/src/lib/auth.ts — JWT decode pattern
8. components UI hiện có (Dialog, Tooltip, Banner) — shadcn/ui hay custom?
```

Confirm:
- Next.js 16 App Router pattern: `'use client'` cho component có hook
- Tailwind: có sẵn? shadcn/ui: có dùng?
- WebSocket: dùng native API hay library (vd `react-use-websocket`)?
- Có button "Bắt đầu cuộc họp" / "Kết thúc cuộc họp" trong trang chi tiết để gọi 2 endpoints lifecycle từ BE_P2 không? Nếu chưa → cần bổ sung trong Phase 3 dưới đây

---

# PHASE 0 — Setup Vitest + Testing Library (NEW v3.1)

## Context

Frontend hiện tại (`package.json`) **chưa có** test framework — chỉ có `eslint`. Phase 0 setup Vitest (chọn vì native ESM, fast, hợp Next.js 16 + React 19) trước khi P2/P3/P4 viết tests.

## Task

### 0.1 — Cài deps (dev only)

```bash
cd frontend
npm install -D vitest @vitejs/plugin-react jsdom \
  @testing-library/react @testing-library/jest-dom @testing-library/user-event \
  mock-socket
```

### 0.2 — `frontend/vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    css: false,
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
});
```

### 0.3 — `frontend/vitest.setup.ts`

```typescript
import '@testing-library/jest-dom/vitest';
```

### 0.4 — Update `package.json` scripts

```json
"scripts": {
  "test": "vitest",
  "test:run": "vitest run",
  "test:coverage": "vitest run --coverage"
}
```

### 0.5 — Smoke test

File: `frontend/src/__tests__/smoke.test.tsx`
```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('Vitest smoke test', () => {
  it('renders hello', () => {
    render(<div>hello vitest</div>);
    expect(screen.getByText('hello vitest')).toBeInTheDocument();
  });
});
```

## Acceptance P0

- `npm run test:run` chạy thành công, smoke test pass
- `npm run build` vẫn pass (vitest deps không leak vào production bundle)
- TypeScript không complain `expect(...).toBeInTheDocument()` (jest-dom types loaded)

## Commit P0

```
[Phase 4.1][FE_P0] Setup Vitest + Testing Library + jsdom for component/hook tests
```

> **STOP. Verify trước Phase 1.** Toàn bộ tests ở P2/P3/P4 phụ thuộc Phase 0 này.

---

# PHASE 1 — PDF.js Setup + Viewer (v3.1: dynamic import bắt buộc)

## ⚠️ Lưu ý quan trọng v3.1

`pdfjs-dist@4.x` access `window` và `document` ngay trong module top-level. Trên Next.js 16 App Router, dù component có `'use client'`, server-side bundle vẫn phải parse module → **build sẽ fail** với ReferenceError trong production build.

**Bắt buộc phải dùng `dynamic(() => import(...), { ssr: false })`** để loại module khỏi server bundle.

## Task

### 1.1 — Cài dependencies

```bash
cd frontend
npm install pdfjs-dist@^4.0.0
```

Copy worker file vào public:
```bash
cp node_modules/pdfjs-dist/build/pdf.worker.min.mjs public/pdf.worker.min.mjs
```

### 1.2 — Component `<PresentationViewer />` (client-only, isolated)

File: `frontend/src/app/(main)/hop-khong-giay/chi-tiet/[id]/_components/PresentationViewer.tsx`

```typescript
'use client';

// IMPORTANT: import pdfjs INSIDE component, NOT at top-level
// để tránh SSR access window/document

interface PresentationViewerProps {
  taiLieuId: string;
  taiLieuUrl: string;
  page: number;
  zoom: number;
  onPageChange?: (page: number) => void;
  onZoomChange?: (zoom: number) => void;
  onLoadComplete?: (totalPages: number) => void;
  controlled: boolean;
}

export function PresentationViewer({...}: PresentationViewerProps) {
  const [pdfjs, setPdfjs] = useState<any>(null);

  // Load pdfjs lib client-side only
  useEffect(() => {
    import('pdfjs-dist').then((mod) => {
      mod.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';
      setPdfjs(mod);
    });
  }, []);

  if (!pdfjs) return <Skeleton />;

  // ... render logic with pdfjs
}
```

### 1.3 — Export với dynamic import ssr:false

File: `frontend/src/app/(main)/hop-khong-giay/chi-tiet/[id]/_components/PresentationViewerLoader.tsx`

```typescript
'use client';
import dynamic from 'next/dynamic';

export const PresentationViewer = dynamic(
  () => import('./PresentationViewer').then(mod => mod.PresentationViewer),
  {
    ssr: false,  // ⭐ v3.1 BẮT BUỘC — pdfjs-dist không tương thích Next.js 16 SSR
    loading: () => <div className="h-full w-full animate-pulse bg-muted" />,
  }
);
```

Mọi nơi import dùng `PresentationViewerLoader`, KHÔNG import trực tiếp `PresentationViewer`.

### 1.4 — Replace viewer trong tab "Tài liệu" cuộc họp

Sửa `frontend/src/app/(main)/hop-khong-giay/chi-tiet/[id]/tai-lieu/page.tsx`:
- TRƯỚC: iframe với src=`/api/.../tai-lieu/{id}/file`
- SAU: `<PresentationViewer ... />` từ `PresentationViewerLoader`
- Page standalone `xem-tai-lieu/[id]` GIỮ NGUYÊN iframe (D9 — out of scope)

### 1.5 — Visual smoke test + build check

Manual:
- **Build production:** `cd frontend && npm run build` — phải success, không có ReferenceError window/document
- Mở 1 cuộc họp đang DANG_DIEN_RA, vào tab Tài liệu, chọn PDF
- Verify render trên: Chrome desktop, Firefox, Safari macOS, Chrome Android (BrowserStack nếu cần)
- Test PDF size: 1MB (nhỏ), 30MB (lớn) — đo thời gian load
- Test Office file (đã convert qua LibreOffice): Word, Excel, PPT — vẫn render OK qua PDF.js

## Acceptance P1

- **`npm run build` success** — KHÔNG có ReferenceError ở SSR (v3.1 critical check)
- PDF render đúng, không bị lệch màu/font
- Lật trang manual mượt
- Zoom +/- mượt
- Office file render OK (qua LibreOffice convert đã có sẵn từ MVP)
- File 30MB hiển thị progress bar
- Error case: file không tồn tại → fallback UI rõ ràng

## Commit P1

```
[Phase 4.1][FE_P1] Replace iframe with PDF.js viewer (dynamic import ssr:false for Next.js 16)
```

> **STOP. Verify trước Phase 2.** Đặc biệt verify `npm run build` success.

---

# PHASE 2 — Sync Hook

## Task

### 2.1 — `usePresentationSync` hook

File: `frontend/src/app/(main)/hop-khong-giay/chi-tiet/[id]/_hooks/usePresentationSync.ts`

```typescript
'use client';

interface PresentationSyncState {
  isActive: boolean;
  taiLieuId: string | null;
  page: number;
  zoom: number;
  hostOnline: boolean;
  isHost: boolean;
  mode: 'sync' | 'independent';
  connectionStatus: 'connecting' | 'connected' | 'reconnecting' | 'disconnected';
}

interface PresentationSyncActions {
  // Chỉ chu_toa
  startPresentation: (taiLieuId: string) => void;
  endPresentation: () => void;
  changeDocument: (taiLieuId: string) => void;
  changePage: (page: number) => void;
  changeZoom: (zoom: number) => void;

  // Tất cả user
  toggleMode: () => void;
  returnToHost: () => Promise<{ confirmRequired: boolean }>;
}

export function usePresentationSync(meetingId: string): {
  state: PresentationSyncState;
  actions: PresentationSyncActions;
}
```

Implementation tasks:
1. Fetch state + WS token từ REST `GET /presentation/state`
2. Connect WebSocket
3. Listen events: state_sync, presentation_started, document_changed, page_changed, ...
4. Update local state
5. Reconnect logic (exponential backoff)
6. Visibility change handler

### 2.2 — Reconnect logic

Exponential backoff:
```typescript
const backoffSchedule = [1000, 2000, 4000, 8000, 16000, 30000];
// 1s, 2s, 4s, 8s, 16s, 30s, sau đó stop và yêu cầu user reload
```

Khi reconnect thành công:
- Re-fetch state qua REST (token có thể đã thay đổi)
- Connect WS lại
- Server tự gửi `state_sync` → apply state mới

### 2.3 — Visibility change handler (D fix iPad)

```typescript
useEffect(() => {
  const handler = () => {
    if (document.visibilityState === 'hidden') {
      lastHiddenTimestampRef.current = Date.now();
    } else if (document.visibilityState === 'visible') {
      const hiddenDuration = Date.now() - (lastHiddenTimestampRef.current ?? 0);
      if (hiddenDuration > 30_000) {
        forceReconnect();
      }
    }
  };
  document.addEventListener('visibilitychange', handler);
  return () => document.removeEventListener('visibilitychange', handler);
}, []);
```

### 2.4 — Heartbeat (client side)

Listen `ping` event từ server, reply `pong`. Nếu không nhận `ping` trong 60s → force reconnect.

### 2.5 — Tests `__tests__/usePresentationSync.test.tsx`

Dùng **Vitest** (đã setup ở Phase 0) + React Testing Library + `mock-socket` cho WS mock. Import API: `import { describe, it, expect, vi } from 'vitest'`.

Tối thiểu **8 test cases**:
- `should fetch state and connect WS on mount`
- `should apply state_sync event`
- `should follow chu_toa page_changed event in sync mode`
- `should NOT follow page_changed in independent mode`
- `should reconnect with exponential backoff`
- `should force reconnect after long hidden tab`
- `should buffer events while loading PDF (late-join)`
- `should reject host actions when user is not chu_toa`

## Acceptance P2

- Hook fetch state + connect WS thành công
- 5 inbound events từ server → state cập nhật đúng
- Reconnect schedule đúng exponential backoff
- Hidden 30s → force reconnect khi visible
- 8/8 tests pass

## Commit P2

```
[Phase 4.1][FE_P2] Add usePresentationSync hook with reconnect + visibility handling
```

> **STOP. Verify trước Phase 3.**

---

# PHASE 3 — UI Components

## Task

### 3.1 — `<MeetingLifecycleButton />` (mới v3.1)

Vị trí: header trang chi tiết cuộc họp.
Visibility: chỉ chu_toa hoặc thu_ky thấy.

States theo `cuoc_hop.trang_thai`:
- `LEN_KE_HOACH`: nút disabled "Chưa thông báo"
- `DA_THONG_BAO`: nút xanh "🟢 Bắt đầu cuộc họp" → gọi `POST /cuoc-hop/{id}/bat-dau`
- `DANG_DIEN_RA`: nút đỏ "🔴 Kết thúc cuộc họp" → confirm dialog → gọi `POST /cuoc-hop/{id}/ket-thuc`
- `HOAN_THANH`/`HUY`: ẩn nút

### 3.2 — `<StartPresentationButton />`

Vị trí: toolbar trang Tài liệu (cùng row với Download, Print).
Visibility: chỉ chu_toa thấy. Active khi cuộc họp `DANG_DIEN_RA` (KHÔNG phải `DA_THONG_BAO`).

States:
- `is_active=FALSE`: nút xanh "🟢 Bắt đầu trình chiếu"
- `is_active=TRUE`: nút đỏ "🔴 Đang trình chiếu • {N} người xem • Kết thúc"

Mobile-friendly: floating button góc phải dưới khi viewport <768px.

### 3.3 — `<SyncStatusBadge />`

Banner phía trên viewer hiển thị status:

| State | Banner |
|---|---|
| Cuộc họp DA_THONG_BAO (chờ chu_toa bắt đầu) | 🟡 "Cuộc họp chưa bắt đầu" |
| Sync mode + presentation active | 🟢 "Đang đồng bộ với chủ tọa • {tai_lieu_name} • Trang {N}" |
| Independent mode | 👁️ "Bạn đang xem độc lập • Chủ tọa đang ở {tai_lieu_name}, trang {N} • [Quay lại theo chủ trì]" |
| Sync mode + presentation NOT active | 🟡 "Chờ chủ tọa bắt đầu trình chiếu..." |
| Host disconnected | ⚠️ "Chủ tọa đang vắng mặt" |
| Connecting | ⏳ "Đang kết nối..." |
| Reconnecting | 🔄 "Đang kết nối lại... ({attempt}/6)" |

### 3.4 — `<IndependentViewBanner />`

Hiển thị khi mode='independent', với info chu_toa đang ở đâu.

### 3.5 — `<ConfirmReturnDialog />`

Confirm dialog khi user bấm "Quay lại theo chủ trì" và chu_toa đang xem **tài liệu khác**:

```
"Chủ tọa đang xem tài liệu khác:
  📄 [Tên tài liệu Y] — Trang [N]

Bấm OK để chuyển sang xem theo chủ tọa.
[Hủy] [OK]"
```

Nếu cùng tài liệu (chỉ khác trang) → KHÔNG hiển thị dialog, jump trực tiếp.

### 3.6 — `<ToggleModeButton />`

Toggle 2 chế độ. Khi click:
- sync → independent: ngừng apply WS events
- independent → sync: nếu chu_toa đang ở tài liệu khác → confirm dialog (component 3.5); nếu cùng tài liệu → jump

### 3.7 — Tích hợp vào trang chi tiết cuộc họp

**Trang chi tiết** (`chi-tiet/[id]/page.tsx`): thêm `<MeetingLifecycleButton />` ở header.

**Tab Tài liệu** (`chi-tiet/[id]/tai-lieu/page.tsx`):
```tsx
'use client';
const { state, actions } = usePresentationSync(meetingId);

return (
  <>
    <SyncStatusBadge state={state} />
    <Toolbar>
      <StartPresentationButton state={state} actions={actions} />
      <ToggleModeButton state={state} actions={actions} />
      {/* ...nút download/print/etc */}
    </Toolbar>
    <PresentationViewer
      taiLieuId={state.taiLieuId}
      page={state.page}
      zoom={state.zoom}
      onPageChange={state.isHost ? actions.changePage : undefined}
      onZoomChange={state.isHost ? actions.changeZoom : undefined}
      controlled={state.isHost && state.isActive}
    />
    <ConfirmReturnDialog ... />
  </>
);
```

### 3.8 — Tests cho components

Tests cho từng component (~12 tests total):
- MeetingLifecycleButton: 4 states render đúng theo trang_thai
- StartPresentationButton: visible/hidden, label đúng theo state
- SyncStatusBadge: 7 states render đúng
- ConfirmReturnDialog: hiển thị đúng khi tài liệu khác, ẩn khi cùng tài liệu

## Acceptance P3

- Mở 2 tab/2 user (1 chu_toa + 1 đại biểu trong cùng cuộc họp DA_THONG_BAO)
- Chu_toa bấm "Bắt đầu cuộc họp" → status chuyển DANG_DIEN_RA, đại biểu cũng thấy update
- Chu_toa vào tab Tài liệu, bấm "Bắt đầu trình chiếu" → chọn PDF → đại biểu auto load + sync
- Chu_toa lật trang → đại biểu sync trong <500ms
- Đại biểu bấm "Xem độc lập" → lật trang riêng, banner update
- Chu_toa đổi tài liệu → đại biểu Xem độc lập thấy banner "đã chuyển sang [Y]"
- Đại biểu bấm "Quay lại theo chủ trì" → confirm dialog → OK → load tài liệu Y, đúng trang
- Chu_toa bấm "Kết thúc cuộc họp" → tất cả WS đóng, đại biểu thấy "Cuộc họp đã kết thúc"
- ~12 component tests pass

## Commit P3

```
[Phase 4.1][FE_P3] Add UI components: lifecycle button (v3.1) + presentation controls
```

> **STOP. Verify trước Phase 4.**

---

# PHASE 4 — Mobile + Buffer Late-Join + Multi-Tab

## Task

### 4.1 — Mobile detect + default mode

Trong `usePresentationSync`:

```typescript
const initialMode: 'sync' | 'independent' = useMemo(() => {
  // D6 — Mobile default Xem độc lập
  if (typeof window !== 'undefined' && window.matchMedia('(max-width: 768px)').matches) {
    return 'independent';
  }
  return 'sync';
}, []);
```

UI mobile: nút "Đồng bộ với chủ tọa" prominent ở banner.

### 4.2 — Buffer late-join (D10)

Trong `<PresentationViewer />`:
```typescript
const [pendingState, setPendingState] = useState<{page: number; zoom: number} | null>(null);
const [pdfLoading, setPdfLoading] = useState(true);

useEffect(() => {
  if (pdfLoading && syncState && mode === 'sync') {
    setPendingState(syncState);
  } else if (!pdfLoading && pendingState && mode === 'sync') {
    onPageChange?.(pendingState.page);
    onZoomChange?.(pendingState.zoom);
    setPendingState(null);
  }
}, [pdfLoading, syncState, pendingState, mode]);
```

UX: skeleton hiển thị "Đang tải tài liệu... ({loaded}/{total} MB)" trong lúc load.

### 4.3 — Multi-tab + cross-device sync (D5)

Verify hành vi mặc định:
- 1 user mở 2 tab cùng cuộc họp → mỗi tab tự connect WS riêng → cả 2 tab nhận events độc lập
- Tab A toggle sync → tab B vẫn theo state riêng (không broadcast giữa tab)
- KHÔNG cần thêm code đặc biệt

Test manual:
- Mở 2 tab → tab A đang sync, tab B đang independent
- Lật trang ở chu_toa → cả A và B đều nhận event nhưng A apply, B chỉ store

### 4.4 — Tests `__tests__/late_join_buffer.test.tsx`

5 tests:
- `should buffer state during PDF load`
- `should apply latest state when load complete`
- `should skip intermediate page changes during load`
- `should default to independent mode on mobile viewport`
- `should auto-detect viewport change`

## Acceptance P4

- Mobile (375px width) mở cuộc họp → mặc định Xem độc lập, banner có nút "Đồng bộ"
- Buffer test: mock load delay 5s, gửi 10 page_change → cuối cùng jump đúng trang cuối
- Multi-tab: 2 tab khác mode hoạt động độc lập
- 5/5 tests pass

## Commit P4

```
[Phase 4.1][FE_P4] Add mobile-first defaults + late-join buffer + multi-tab support
```

> **STOP. Verify trước Phase 5.**

---

# PHASE 5 — Edge Cases + Onboarding + UAT + Deploy

## Task

### 5.1 — Edge case handlers FE

| Server event | UX FE |
|---|---|
| `host_disconnected` | Banner ⚠️ "Chủ tọa đang vắng mặt" |
| `host_reconnected` | Banner mất, return to normal |
| `meeting_ended` (reason=completed) | Banner "Cuộc họp đã kết thúc", disable controls, đóng WS gracefully |
| `meeting_ended` (reason=cancelled) | Banner đỏ "Cuộc họp đã bị hủy", redirect về list cuộc họp sau 5s |
| `error` (DOCUMENT_DELETED) | Toast "Tài liệu đã bị xóa", fallback về tài liệu khác trong list |
| `error` (NOT_HOST) | Silent (đại biểu không bao giờ thấy) |
| WS disconnect 30s+ | Banner "Mất kết nối, đang thử lại..." + spinner |

### 5.2 — Onboarding lần đầu chu_toa

2 tooltip pop lần đầu chu_toa vào trang trong cuộc họp DA_THONG_BAO/DANG_DIEN_RA:

**Tooltip 1** trên `<MeetingLifecycleButton />` (DA_THONG_BAO):
```
💡 "Đây là nút bắt đầu cuộc họp. Bấm khi đến giờ
    để chuyển sang trạng thái 'Đang diễn ra'.
                              [Đã hiểu]
```

**Tooltip 2** trên `<StartPresentationButton />` (DANG_DIEN_RA):
```
💡 "Đây là nút bắt đầu trình chiếu. Bấm để chia sẻ
    màn hình tài liệu cho tất cả đại biểu.
    Có thể bắt đầu/kết thúc nhiều lần.
                              [Đã hiểu]
```

Lưu trạng thái "đã xem" trong `localStorage` để không spam.

Tương tự onboarding mobile: hint đầu tiên về Xem độc lập.

### 5.3 — Tài liệu hướng dẫn chu_toa

File: `docs/HKG/HUONG_DAN_CHU_TOA_PAGE_SYNC.md` (1-2 trang A4):
- Cách bắt đầu cuộc họp (DA_THONG_BAO → DANG_DIEN_RA)
- Cách bắt đầu/kết thúc trình chiếu
- Cách lật trang/zoom
- Đại biểu sẽ thấy gì
- Khi nào dùng "Xem độc lập"
- Cách kết thúc cuộc họp
- Troubleshooting (mất kết nối, đại biểu không sync)

Convert sang PDF + screenshot. Lưu vào `docs/HKG/`.

### 5.4 — UAT mini

Coordinate với 5 CBCC volunteer:
- 1 cuộc họp thật, 30 phút
- Test scenarios: chu_toa bấm bắt đầu/kết thúc cuộc họp, start/end trình chiếu, lật trang, đổi tài liệu, mobile join, mất mạng tạm
- Form feedback: UX score 1-5, bug report, suggestions
- Lưu kết quả vào `docs/HKG/UAT_PHASE_4_1_RESULT.md`

### 5.5 — Deploy staging → production

**Staging (deploy đầu Th.5):**
- Build FE: `cd frontend && npm run build` — verify success (đặc biệt PDF.js dynamic import OK)
- Restart pm2: `pm2 restart meeting-backend frontend`
- Smoke test 1 cuộc họp test với full flow lifecycle

**Production (deploy sau staging stable 48h):**
- Backup DB trước (verify có file backup_daily.sh chạy đúng từ Phase BE_P1)
- Deploy code (git pull + npm install + npm run build + pm2 restart)
- Apply migration mới (đã apply ở Phase DB_P1, verify)
- Monitor pm2 logs 24h sau deploy

### 5.6 — Update CLAUDE.md

Document Phase 4.1 hoàn thành:
- Tính năng mới: page-sync, P0 hardening, meeting lifecycle endpoints
- Bảng mới: `meeting.trang_thai_trinh_chieu` (no soft delete)
- Endpoints mới: 4 endpoints
- Tests: tổng số (grep count), file mới
- Deploy notes: cron jobs, pm2-logrotate
- v3.1 critical: PDF.js dynamic import ssr:false

## Acceptance P5

- 7/7 edge case scenarios manual test pass
- Onboarding tooltips hiển thị đúng lần đầu, không spam
- Tài liệu hướng dẫn published trong `docs/HKG/`
- UAT mini: ≥4/5 user feedback OK, không có bug critical
- Staging stable 48h
- Production deploy không có alert pm2 trong 24h sau deploy

## Commit P5 (có thể tách 2-3 commits)

```
[Phase 4.1][FE_P5] Add edge case handlers + onboarding tooltips
[Phase 4.1][FE_P5] Add user guide documentation + UAT results
[Phase 4.1][FE_P5] Deploy staging + production verified
```

---

## Báo PM khi PROMPT 3 xong (= Phase 4.1 done)

- Tests trước/sau (grep count, không trust số tài liệu)
- UAT result: số volunteer, scores, bugs found/fixed
- Deploy: staging date, production date, monitoring 24h status
- Browser compat: Chrome ✓ / Firefox ✓ / Safari macOS / Safari iOS / Chrome Android
- Mobile/tablet test result
- Performance: PDF load time avg, page-sync latency p95 thực tế
- Build production: `npm run build` time, bundle size impact (pdfjs-dist ~700KB)
- Recommendations cho Phase 4.2 (annotation realtime) — đã learn được gì từ 4.1

🎉 **Phase 4.1 closed.** Sẵn sàng plan cho Phase 4.2 (Annotation realtime).

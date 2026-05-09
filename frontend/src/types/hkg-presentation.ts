/**
 * Types cho Phase 4.1 — Page-Sync (HKG Presentation).
 * Khớp 1-1 với meeting_service/schemas/presentation.py.
 */

// ────────────────────────────────────────────────────────────
// REST: GET /cuoc-hop/{id}/presentation/state
// ────────────────────────────────────────────────────────────

export interface IPresentationStateResponse {
  cuoc_hop_id: string;
  is_active: boolean;
  tai_lieu_hien_tai_id: string | null;
  trang_hien_tai: number;
  zoom_level: string; // Decimal serialized as string, e.g. "1.00"
  bat_dau_luc: string | null;
  ket_thuc_luc: string | null;
  cap_nhat_luc: string;
  cap_nhat_boi_id: string | null;
  ws_token: string;
  ws_token_expires_at: string;
  is_chu_toa: boolean;
  is_thu_ky: boolean;
}

// ────────────────────────────────────────────────────────────
// WS Outbound (server → client)
// ────────────────────────────────────────────────────────────

export type WSOutboundEvent =
  | { type: 'state_sync'; is_active: boolean; tai_lieu_hien_tai_id: string | null; trang_hien_tai: number; zoom_level: string; host_online: boolean }
  | { type: 'presentation_started'; tai_lieu_id: string; page: number; bat_dau_luc: string }
  | { type: 'presentation_ended'; ket_thuc_luc: string }
  | { type: 'document_changed'; tai_lieu_id: string; page: number }
  | { type: 'page_changed'; page: number }
  | { type: 'zoom_changed'; zoom: string }
  | { type: 'host_disconnected' }
  | { type: 'host_reconnected' }
  | { type: 'meeting_ended'; reason: 'completed' | 'cancelled' }
  | { type: 'error'; code: string; message: string }
  | { type: 'ping' };

// ────────────────────────────────────────────────────────────
// WS Inbound (client → server) — chỉ host được gửi
// ────────────────────────────────────────────────────────────

export type WSInboundEvent =
  | { type: 'presentation_start'; tai_lieu_id: string; page?: number }
  | { type: 'presentation_end' }
  | { type: 'document_open'; tai_lieu_id: string; page?: number }
  | { type: 'page_change'; page: number }
  | { type: 'zoom_change'; zoom: string | number }
  | { type: 'pong' };

// ────────────────────────────────────────────────────────────
// Hook state machine
// ────────────────────────────────────────────────────────────

export type ConnectionStatus =
  | 'idle'           // chưa khởi tạo
  | 'connecting'     // đang fetch token / open WS
  | 'connected'      // WS open + state_sync nhận được
  | 'reconnecting'   // mất kết nối, đang retry
  | 'closed'         // closed sạch (meeting_ended/unmount)
  | 'error';         // lỗi không phục hồi (vd token revoked)

export interface IPresentationState {
  isActive: boolean;
  taiLieuId: string | null;
  page: number;
  zoom: string;       // giữ string để khớp Decimal
  hostOnline: boolean;
  hostDisconnected: boolean;
}

export const INITIAL_PRESENTATION_STATE: IPresentationState = {
  isActive: false,
  taiLieuId: null,
  page: 1,
  zoom: '1.00',
  hostOnline: false,
  hostDisconnected: false,
};

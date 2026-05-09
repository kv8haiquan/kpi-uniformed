'use client';

/**
 * usePresentationSync — Hook đồng bộ trang trình chiếu cho cuộc họp.
 *
 * Phase 4.1 FE_P2.
 *
 * Trách nhiệm:
 *  - Fetch ws_token qua REST → mở WebSocket → nhận state_sync
 *  - Reduce state theo các event server → expose cho UI
 *  - Cho phép host gửi action: presentation_start/end, change_doc/page/zoom
 *  - Reconnect: exponential backoff (1s, 2s, 4s, 8s, 16s — max 5 lần)
 *  - Pong reply khi nhận ping (giữ kết nối, idle timeout server = 120s)
 *  - Visibility change: tab ẩn quá 5s → snapshot lại state qua REST khi visible
 *  - Server đóng 1008 (auth/state) → re-fetch token 1 lần rồi bỏ cuộc nếu vẫn fail
 *  - Server đóng 1000 + meeting_ended → status='closed', không reconnect
 *
 * Kế thừa từ: meeting_service/api/endpoints/presentation_ws.py
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { presentationApi, buildPresentationWsUrl } from '@/services/hkg';
import {
  ConnectionStatus,
  INITIAL_PRESENTATION_STATE,
  IPresentationState,
  IPresentationStateResponse,
  WSInboundEvent,
  WSOutboundEvent,
} from '@/types/hkg-presentation';

// ────────────────────────────────────────────────────────────
// Constants
// ────────────────────────────────────────────────────────────

const MAX_RECONNECT_ATTEMPTS = 5;
const BACKOFF_MS = [1000, 2000, 4000, 8000, 16000];
const VISIBILITY_RESYNC_THRESHOLD_MS = 5_000;
const MAX_TOKEN_REFETCH = 3;

// WS close codes mà KHÔNG reconnect
const NO_RECONNECT_CODES = new Set<number>([
  1000, // normal — meeting_ended hoặc server tắt sạch
  1001, // going away
  1008, // policy violation — auth/state. Sẽ thử re-fetch token MỘT lần (xử lý riêng)
]);

// ────────────────────────────────────────────────────────────
// Hook props/return
// ────────────────────────────────────────────────────────────

export interface UsePresentationSyncOptions {
  cuocHopId: string;
  /** Bật hook. Set false khi unmount/page chưa ready. */
  enabled?: boolean;
}

export interface UsePresentationSyncReturn {
  status: ConnectionStatus;
  state: IPresentationState;
  isHost: boolean;
  isThuKy: boolean;
  /** Thông báo chuyển trạng thái cuối cùng (vd reason='cancelled'). */
  endReason: 'completed' | 'cancelled' | null;
  /** Mã lỗi server gửi qua event 'error'. */
  lastError: string | null;

  // Host actions — chạy no-op nếu !isHost hoặc chưa connected.
  startPresentation: (taiLieuId: string, page?: number) => void;
  endPresentation: () => void;
  changeDocument: (taiLieuId: string, page?: number) => void;
  changePage: (page: number) => void;
  changeZoom: (zoom: string | number) => void;
}

// ────────────────────────────────────────────────────────────
// Hook
// ────────────────────────────────────────────────────────────

export function usePresentationSync(
  options: UsePresentationSyncOptions,
): UsePresentationSyncReturn {
  const { cuocHopId, enabled = true } = options;

  const [status, setStatus] = useState<ConnectionStatus>('idle');
  const [state, setState] = useState<IPresentationState>(INITIAL_PRESENTATION_STATE);
  const [isHost, setIsHost] = useState(false);
  const [isThuKy, setIsThuKy] = useState(false);
  const [endReason, setEndReason] = useState<'completed' | 'cancelled' | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);

  // Refs giữ giá trị qua re-render (tránh stale closure)
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const tokenRefetchCountRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const tokenRef = useRef<string | null>(null);
  const isHostRef = useRef(false);
  const enabledRef = useRef(enabled);
  const lastVisibleAtRef = useRef<number>(Date.now());
  const cuocHopIdRef = useRef(cuocHopId);

  useEffect(() => { enabledRef.current = enabled; }, [enabled]);
  useEffect(() => { cuocHopIdRef.current = cuocHopId; }, [cuocHopId]);
  useEffect(() => { isHostRef.current = isHost; }, [isHost]);

  // ──────────────────────────────────────────────────────────
  // Send helper — chỉ gửi khi WS open
  // ──────────────────────────────────────────────────────────
  const sendInbound = useCallback((evt: WSInboundEvent) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    try {
      ws.send(JSON.stringify(evt));
    } catch {
      // ignore — disconnect handler sẽ kick in
    }
  }, []);

  // ──────────────────────────────────────────────────────────
  // Reduce outbound event → state
  // ──────────────────────────────────────────────────────────
  const handleEvent = useCallback((evt: WSOutboundEvent) => {
    switch (evt.type) {
      case 'state_sync':
        setState((s) => ({
          ...s,
          isActive: evt.is_active,
          taiLieuId: evt.tai_lieu_hien_tai_id,
          page: evt.trang_hien_tai,
          zoom: evt.zoom_level,
          hostOnline: evt.host_online,
          hostDisconnected: !evt.host_online,
        }));
        break;
      case 'presentation_started':
        setState((s) => ({
          ...s,
          isActive: true,
          taiLieuId: evt.tai_lieu_id,
          page: evt.page,
        }));
        break;
      case 'presentation_ended':
        setState((s) => ({ ...s, isActive: false }));
        break;
      case 'document_changed':
        setState((s) => ({
          ...s,
          taiLieuId: evt.tai_lieu_id,
          page: evt.page,
        }));
        break;
      case 'page_changed':
        setState((s) => ({ ...s, page: evt.page }));
        break;
      case 'zoom_changed':
        setState((s) => ({ ...s, zoom: evt.zoom }));
        break;
      case 'host_disconnected':
        setState((s) => ({ ...s, hostOnline: false, hostDisconnected: true }));
        break;
      case 'host_reconnected':
        setState((s) => ({ ...s, hostOnline: true, hostDisconnected: false }));
        break;
      case 'meeting_ended':
        setEndReason(evt.reason);
        setStatus('closed');
        break;
      case 'error':
        setLastError(`${evt.code}: ${evt.message}`);
        break;
      case 'ping':
        sendInbound({ type: 'pong' });
        break;
    }
  }, [sendInbound]);

  // ──────────────────────────────────────────────────────────
  // Mở 1 WS connection (đã có token)
  // ──────────────────────────────────────────────────────────
  const openSocket = useCallback((token: string, restState: IPresentationStateResponse) => {
    if (typeof window === 'undefined') return;

    // Snapshot từ REST trước khi WS mở (giảm UI flicker)
    setState((s) => ({
      ...s,
      isActive: restState.is_active,
      taiLieuId: restState.tai_lieu_hien_tai_id,
      page: restState.trang_hien_tai,
      zoom: restState.zoom_level,
    }));

    const url = buildPresentationWsUrl(cuocHopIdRef.current, token);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data) as WSOutboundEvent;
        handleEvent(data);
      } catch {
        // server không bao giờ gửi non-JSON; ignore corrupt
      }
    };

    ws.onerror = () => {
      // WebSocket spec: onerror always followed by onclose. Để onclose xử lý reconnect.
    };

    ws.onclose = (evt) => {
      wsRef.current = null;
      // Component đã unmount/disabled → không reconnect
      if (!enabledRef.current) {
        setStatus('closed');
        return;
      }
      // meeting_ended đã set status='closed' qua handleEvent; tôn trọng
      if (status === 'closed') return;

      const code = evt.code;

      // 1008 = policy violation (token expired/revoked hoặc state changed).
      // Thử re-fetch token 1 lần (max 3 lần tổng cộng phòng loop).
      if (code === 1008 && tokenRefetchCountRef.current < MAX_TOKEN_REFETCH) {
        tokenRefetchCountRef.current += 1;
        scheduleReconnect(true);
        return;
      }

      // Close codes "sạch" → không reconnect
      if (NO_RECONNECT_CODES.has(code)) {
        setStatus('closed');
        return;
      }

      // Còn lại: reconnect với token cũ (token còn hạn)
      scheduleReconnect(false);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [handleEvent, status]);

  // ──────────────────────────────────────────────────────────
  // Schedule reconnect (exp backoff)
  // ──────────────────────────────────────────────────────────
  const scheduleReconnect = useCallback((needNewToken: boolean) => {
    if (!enabledRef.current) return;
    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      setStatus('error');
      setLastError('Mất kết nối. Vui lòng tải lại trang.');
      return;
    }

    setStatus('reconnecting');
    const delay = BACKOFF_MS[Math.min(reconnectAttemptsRef.current, BACKOFF_MS.length - 1)];
    reconnectAttemptsRef.current += 1;

    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    reconnectTimerRef.current = setTimeout(() => {
      void connect(needNewToken);
    }, delay);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ──────────────────────────────────────────────────────────
  // Initial connect: GET state → openSocket
  // ──────────────────────────────────────────────────────────
  const connect = useCallback(async (forceNewToken = true) => {
    if (!enabledRef.current) return;
    setStatus('connecting');
    setLastError(null);

    try {
      let token = tokenRef.current;
      let restState: IPresentationStateResponse | null = null;

      if (!token || forceNewToken) {
        restState = await presentationApi.getState(cuocHopIdRef.current);
        token = restState.ws_token;
        tokenRef.current = token;
        setIsHost(restState.is_chu_toa);
        setIsThuKy(restState.is_thu_ky);
        // Khi re-fetch không phải lần đầu, restState vẫn dùng để snapshot
      } else {
        // reconnect không cần token mới — chỉ cần re-open WS
        restState = {
          cuoc_hop_id: cuocHopIdRef.current,
          is_active: state.isActive,
          tai_lieu_hien_tai_id: state.taiLieuId,
          trang_hien_tai: state.page,
          zoom_level: state.zoom,
          bat_dau_luc: null,
          ket_thuc_luc: null,
          cap_nhat_luc: new Date().toISOString(),
          cap_nhat_boi_id: null,
          ws_token: token,
          ws_token_expires_at: new Date(Date.now() + 3600_000).toISOString(),
          is_chu_toa: isHostRef.current,
          is_thu_ky: isThuKy,
        };
      }

      openSocket(token, restState);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Không lấy được token WS';
      setLastError(msg);
      // Không reset attempts — tiếp tục thử với backoff
      scheduleReconnect(true);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [openSocket, scheduleReconnect]);

  // ──────────────────────────────────────────────────────────
  // Visibility change: tab ẩn rồi visible lại → resync nếu lâu
  // ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const onVis = () => {
      if (document.visibilityState === 'hidden') {
        lastVisibleAtRef.current = Date.now();
      } else if (document.visibilityState === 'visible') {
        const gap = Date.now() - lastVisibleAtRef.current;
        if (
          enabledRef.current &&
          gap > VISIBILITY_RESYNC_THRESHOLD_MS &&
          (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN)
        ) {
          // Đóng WS (nếu còn) + reconnect với fresh token để miss-event recovery
          try { wsRef.current?.close(); } catch { /* noop */ }
          reconnectAttemptsRef.current = 0;
          void connect(true);
        }
      }
    };
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, [connect]);

  // ──────────────────────────────────────────────────────────
  // Lifecycle: mount/unmount + enabled toggle
  // ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!enabled) {
      // disable → đóng socket + clear timer
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      try { wsRef.current?.close(1000); } catch { /* noop */ }
      wsRef.current = null;
      setStatus('closed');
      return;
    }

    // (re)mount với enabled=true → connect lần đầu
    reconnectAttemptsRef.current = 0;
    tokenRefetchCountRef.current = 0;
    void connect(true);

    return () => {
      // unmount: đóng sạch
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      try { wsRef.current?.close(1000); } catch { /* noop */ }
      wsRef.current = null;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, cuocHopId]);

  // ──────────────────────────────────────────────────────────
  // Host actions
  // ──────────────────────────────────────────────────────────
  const startPresentation = useCallback((taiLieuId: string, page = 1) => {
    if (!isHostRef.current) return;
    sendInbound({ type: 'presentation_start', tai_lieu_id: taiLieuId, page });
  }, [sendInbound]);

  const endPresentation = useCallback(() => {
    if (!isHostRef.current) return;
    sendInbound({ type: 'presentation_end' });
  }, [sendInbound]);

  const changeDocument = useCallback((taiLieuId: string, page = 1) => {
    if (!isHostRef.current) return;
    sendInbound({ type: 'document_open', tai_lieu_id: taiLieuId, page });
  }, [sendInbound]);

  const changePage = useCallback((page: number) => {
    if (!isHostRef.current) return;
    sendInbound({ type: 'page_change', page });
  }, [sendInbound]);

  const changeZoom = useCallback((zoom: string | number) => {
    if (!isHostRef.current) return;
    sendInbound({ type: 'zoom_change', zoom });
  }, [sendInbound]);

  return {
    status,
    state,
    isHost,
    isThuKy,
    endReason,
    lastError,
    startPresentation,
    endPresentation,
    changeDocument,
    changePage,
    changeZoom,
  };
}

export default usePresentationSync;

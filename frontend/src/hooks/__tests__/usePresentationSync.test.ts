import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { Server, WebSocket as MockWS } from 'mock-socket';

import { usePresentationSync } from '@/hooks/usePresentationSync';

const TEST_WS_URL = 'ws://localhost:1234/ws/test';
const FAKE_TOKEN = 'fake-jwt';

// ────────────────────────────────────────────────────────────
// Mock services/hkg
// ────────────────────────────────────────────────────────────
const getStateMock = vi.fn();

vi.mock('@/services/hkg', () => ({
  presentationApi: {
    getState: (...args: unknown[]) => getStateMock(...args),
  },
  buildPresentationWsUrl: () => TEST_WS_URL,
}));

const restStateFixture = (overrides: Record<string, unknown> = {}) => ({
  cuoc_hop_id: 'ch-1',
  is_active: false,
  tai_lieu_hien_tai_id: null,
  trang_hien_tai: 1,
  zoom_level: '1.00',
  bat_dau_luc: null,
  ket_thuc_luc: null,
  cap_nhat_luc: new Date().toISOString(),
  cap_nhat_boi_id: null,
  ws_token: FAKE_TOKEN,
  ws_token_expires_at: new Date(Date.now() + 3600_000).toISOString(),
  is_chu_toa: false,
  is_thu_ky: false,
  ...overrides,
});

// ────────────────────────────────────────────────────────────
// Setup mock-socket — patch global WebSocket
// ────────────────────────────────────────────────────────────
const realWebSocket = globalThis.WebSocket;

let server: Server;

beforeEach(() => {
  // mock-socket cung cấp WebSocket fake; gán globally
  (globalThis as unknown as { WebSocket: typeof MockWS }).WebSocket = MockWS;
  server = new Server(TEST_WS_URL);
  getStateMock.mockReset();
});

afterEach(() => {
  server.stop();
  (globalThis as unknown as { WebSocket: typeof WebSocket }).WebSocket = realWebSocket;
  vi.useRealTimers();
});

// ────────────────────────────────────────────────────────────
// Tests
// ────────────────────────────────────────────────────────────

describe('usePresentationSync', () => {
  it('connect flow: getState → WS open → state_sync → connected', async () => {
    getStateMock.mockResolvedValue(restStateFixture({ is_chu_toa: true }));

    server.on('connection', (socket) => {
      socket.send(JSON.stringify({
        type: 'state_sync',
        is_active: true,
        tai_lieu_hien_tai_id: 'tl-1',
        trang_hien_tai: 5,
        zoom_level: '1.50',
        host_online: true,
      }));
    });

    const { result } = renderHook(() => usePresentationSync({ cuocHopId: 'ch-1' }));

    await waitFor(() => {
      expect(result.current.status).toBe('connected');
    });

    expect(getStateMock).toHaveBeenCalledWith('ch-1');
    expect(result.current.isHost).toBe(true);
    expect(result.current.state.isActive).toBe(true);
    expect(result.current.state.taiLieuId).toBe('tl-1');
    expect(result.current.state.page).toBe(5);
    expect(result.current.state.zoom).toBe('1.50');
    expect(result.current.state.hostOnline).toBe(true);
  });

  it('host changePage gửi frame page_change đúng format', async () => {
    getStateMock.mockResolvedValue(restStateFixture({ is_chu_toa: true }));

    const received: unknown[] = [];
    server.on('connection', (socket) => {
      socket.on('message', (raw) => {
        received.push(JSON.parse(raw as string));
      });
      socket.send(JSON.stringify({
        type: 'state_sync', is_active: false, tai_lieu_hien_tai_id: null,
        trang_hien_tai: 1, zoom_level: '1.00', host_online: true,
      }));
    });

    const { result } = renderHook(() => usePresentationSync({ cuocHopId: 'ch-1' }));
    await waitFor(() => expect(result.current.status).toBe('connected'));

    act(() => { result.current.changePage(7); });

    await waitFor(() => {
      expect(received).toContainEqual({ type: 'page_change', page: 7 });
    });
  });

  it('non-host: changePage không gửi frame', async () => {
    getStateMock.mockResolvedValue(restStateFixture({ is_chu_toa: false }));

    const received: unknown[] = [];
    server.on('connection', (socket) => {
      socket.on('message', (raw) => { received.push(JSON.parse(raw as string)); });
      socket.send(JSON.stringify({
        type: 'state_sync', is_active: false, tai_lieu_hien_tai_id: null,
        trang_hien_tai: 1, zoom_level: '1.00', host_online: true,
      }));
    });

    const { result } = renderHook(() => usePresentationSync({ cuocHopId: 'ch-1' }));
    await waitFor(() => expect(result.current.status).toBe('connected'));

    act(() => { result.current.changePage(99); });

    // Đợi 1 tick để chắc chắn không có gì gửi
    await new Promise((r) => setTimeout(r, 50));
    expect(received.find((e) => (e as { type: string }).type === 'page_change')).toBeUndefined();
  });

  it('server page_changed → state.page cập nhật', async () => {
    getStateMock.mockResolvedValue(restStateFixture({ is_chu_toa: false }));

    let socketRef: { send: (s: string) => void } | null = null;
    server.on('connection', (socket) => {
      socketRef = socket as unknown as { send: (s: string) => void };
      socket.send(JSON.stringify({
        type: 'state_sync', is_active: true, tai_lieu_hien_tai_id: 'tl-1',
        trang_hien_tai: 1, zoom_level: '1.00', host_online: true,
      }));
    });

    const { result } = renderHook(() => usePresentationSync({ cuocHopId: 'ch-1' }));
    await waitFor(() => expect(result.current.status).toBe('connected'));

    act(() => {
      socketRef?.send(JSON.stringify({ type: 'page_changed', page: 12 }));
    });

    await waitFor(() => expect(result.current.state.page).toBe(12));
  });

  it('host_disconnected → state.hostDisconnected=true; reconnected → false', async () => {
    getStateMock.mockResolvedValue(restStateFixture());

    let socketRef: { send: (s: string) => void } | null = null;
    server.on('connection', (socket) => {
      socketRef = socket as unknown as { send: (s: string) => void };
      socket.send(JSON.stringify({
        type: 'state_sync', is_active: false, tai_lieu_hien_tai_id: null,
        trang_hien_tai: 1, zoom_level: '1.00', host_online: true,
      }));
    });

    const { result } = renderHook(() => usePresentationSync({ cuocHopId: 'ch-1' }));
    await waitFor(() => expect(result.current.status).toBe('connected'));

    act(() => { socketRef?.send(JSON.stringify({ type: 'host_disconnected' })); });
    await waitFor(() => expect(result.current.state.hostDisconnected).toBe(true));

    act(() => { socketRef?.send(JSON.stringify({ type: 'host_reconnected' })); });
    await waitFor(() => expect(result.current.state.hostDisconnected).toBe(false));
  });

  it('meeting_ended → status=closed, endReason set', async () => {
    getStateMock.mockResolvedValue(restStateFixture());

    let socketRef: { send: (s: string) => void } | null = null;
    server.on('connection', (socket) => {
      socketRef = socket as unknown as { send: (s: string) => void };
      socket.send(JSON.stringify({
        type: 'state_sync', is_active: false, tai_lieu_hien_tai_id: null,
        trang_hien_tai: 1, zoom_level: '1.00', host_online: true,
      }));
    });

    const { result } = renderHook(() => usePresentationSync({ cuocHopId: 'ch-1' }));
    await waitFor(() => expect(result.current.status).toBe('connected'));

    act(() => { socketRef?.send(JSON.stringify({ type: 'meeting_ended', reason: 'cancelled' })); });

    await waitFor(() => {
      expect(result.current.status).toBe('closed');
      expect(result.current.endReason).toBe('cancelled');
    });
  });

  it('ping từ server → reply pong', async () => {
    getStateMock.mockResolvedValue(restStateFixture());

    const received: unknown[] = [];
    let socketRef: { send: (s: string) => void } | null = null;
    server.on('connection', (socket) => {
      socketRef = socket as unknown as { send: (s: string) => void };
      socket.on('message', (raw) => { received.push(JSON.parse(raw as string)); });
      socket.send(JSON.stringify({
        type: 'state_sync', is_active: false, tai_lieu_hien_tai_id: null,
        trang_hien_tai: 1, zoom_level: '1.00', host_online: true,
      }));
    });

    const { result } = renderHook(() => usePresentationSync({ cuocHopId: 'ch-1' }));
    await waitFor(() => expect(result.current.status).toBe('connected'));

    act(() => { socketRef?.send(JSON.stringify({ type: 'ping' })); });
    await waitFor(() => {
      expect(received).toContainEqual({ type: 'pong' });
    });
  });

  it('disabled=false không connect', async () => {
    getStateMock.mockResolvedValue(restStateFixture());

    const { result } = renderHook(() =>
      usePresentationSync({ cuocHopId: 'ch-1', enabled: false }),
    );

    await new Promise((r) => setTimeout(r, 50));
    expect(getStateMock).not.toHaveBeenCalled();
    expect(result.current.status).toBe('closed');
  });
});

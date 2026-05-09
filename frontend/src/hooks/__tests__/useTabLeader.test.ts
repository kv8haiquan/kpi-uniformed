import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';

import { useTabLeader } from '@/hooks/useTabLeader';

describe('useTabLeader', () => {
  let originalBC: typeof BroadcastChannel | undefined;

  beforeEach(() => {
    originalBC = (globalThis as { BroadcastChannel?: typeof BroadcastChannel }).BroadcastChannel;
  });

  afterEach(() => {
    if (originalBC) {
      (globalThis as { BroadcastChannel?: typeof BroadcastChannel }).BroadcastChannel = originalBC;
    }
  });

  it('fallback=true khi BroadcastChannel không có (mọi tab là leader)', async () => {
    delete (globalThis as { BroadcastChannel?: typeof BroadcastChannel }).BroadcastChannel;

    const { result } = renderHook(() => useTabLeader('ch-1', true));

    await waitFor(() => {
      expect(result.current.fallback).toBe(true);
      expect(result.current.isLeader).toBe(true);
    });
  });

  it('disabled=false không tạo BroadcastChannel', () => {
    const ctorSpy = vi.fn();
    class FakeBC {
      constructor(name: string) {
        ctorSpy(name);
      }
      addEventListener() {}
      removeEventListener() {}
      postMessage() {}
      close() {}
    }
    (globalThis as { BroadcastChannel: unknown }).BroadcastChannel = FakeBC as unknown as typeof BroadcastChannel;

    renderHook(() => useTabLeader('ch-1', false));
    expect(ctorSpy).not.toHaveBeenCalled();
  });

  it('1 tab duy nhất → tự thành leader sau timeout', async () => {
    let bcInstances: { postMessage: ReturnType<typeof vi.fn> }[] = [];
    class FakeBC {
      postMessage = vi.fn();
      addEventListener = vi.fn();
      removeEventListener = vi.fn();
      close = vi.fn();
      constructor() { bcInstances.push(this); }
    }
    (globalThis as { BroadcastChannel: unknown }).BroadcastChannel = FakeBC as unknown as typeof BroadcastChannel;

    const { result } = renderHook(() => useTabLeader('ch-2', true));

    // Chờ qua claim timeout 200ms
    await waitFor(() => expect(result.current.isLeader).toBe(true), { timeout: 1000 });
    expect(bcInstances.length).toBeGreaterThan(0);
    expect(bcInstances[0].postMessage).toHaveBeenCalled();

    bcInstances = [];
  });
});

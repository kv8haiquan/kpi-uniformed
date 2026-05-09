import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';

import { useMediaQuery, useIsMobile } from '@/hooks/useMediaQuery';

interface MockMQL {
  matches: boolean;
  media: string;
  onchange: null;
  addEventListener: (ev: string, cb: (e: MediaQueryListEvent) => void) => void;
  removeEventListener: (ev: string, cb: (e: MediaQueryListEvent) => void) => void;
  addListener: (cb: (e: MediaQueryListEvent) => void) => void;
  removeListener: (cb: (e: MediaQueryListEvent) => void) => void;
  dispatchEvent: () => boolean;
  _listeners: Array<(e: MediaQueryListEvent) => void>;
  _trigger: (matches: boolean) => void;
}

const mqlMap = new Map<string, MockMQL>();

beforeEach(() => {
  mqlMap.clear();
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: (query: string) => {
      const mql: MockMQL = {
        matches: false,
        media: query,
        onchange: null,
        _listeners: [],
        addEventListener: (_ev, cb) => mql._listeners.push(cb),
        removeEventListener: (_ev, cb) => {
          mql._listeners = mql._listeners.filter((l) => l !== cb);
        },
        addListener: (cb) => mql._listeners.push(cb),
        removeListener: (cb) => {
          mql._listeners = mql._listeners.filter((l) => l !== cb);
        },
        dispatchEvent: () => true,
        _trigger(matches: boolean) {
          this.matches = matches;
          this._listeners.forEach((l) => l({ matches } as MediaQueryListEvent));
        },
      };
      mqlMap.set(query, mql);
      return mql;
    },
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('useMediaQuery', () => {
  it('match initial false → true sau khi trigger change', () => {
    const { result } = renderHook(() => useMediaQuery('(max-width: 767px)'));
    expect(result.current).toBe(false);

    act(() => { mqlMap.get('(max-width: 767px)')?._trigger(true); });
    expect(result.current).toBe(true);
  });

  it('useIsMobile dùng query 767px', () => {
    renderHook(() => useIsMobile());
    expect(mqlMap.has('(max-width: 767px)')).toBe(true);
  });
});

'use client';

/**
 * useTabLeader — leader election giữa nhiều tab cùng cuộc họp.
 *
 * Phase 4.1 FE_P4.
 *
 * Vấn đề: nếu host mở 2+ tab cùng cuộc họp, mỗi tab sẽ:
 *   - Tự gọi REST /presentation/state (UPSERT row, audit OK nhưng phí)
 *   - Mỗi tab tự kết nối WS → server đếm 2 host_count, khi tab close nhầm
 *     có thể trigger host_disconnected nhầm
 *   - Host action (page_change) bấm ở tab nào sẽ broadcast — không sao về
 *     đúng đắn nhưng dễ gây nhầm lẫn UX (2 tab tự sync, vô tình nhảy trang)
 *
 * Giải pháp: BroadcastChannel-based leader election.
 *  - Tab claim leadership bằng cách gửi message "claim" với random tabId
 *  - Tab khác phản hồi "ack" nếu đang là leader
 *  - Tab không nhận ack trong 200ms → tự nhận leadership
 *  - Visibility hidden → relinquish; visible lại → re-claim
 *  - Khi tab close (beforeunload) → gửi "release" để tab khác nhận
 *
 * Fallback: nếu trình duyệt không hỗ trợ BroadcastChannel (Safari < 15.4),
 * mọi tab đều là leader (tương đương hành vi cũ — chấp nhận được).
 */

import { useEffect, useRef, useState } from 'react';

const CLAIM_TIMEOUT_MS = 200;

type Msg =
  | { type: 'claim'; tabId: string; ts: number }
  | { type: 'ack'; tabId: string }
  | { type: 'release'; tabId: string };

export interface UseTabLeaderResult {
  isLeader: boolean;
  /** True nếu BroadcastChannel không có (mọi tab tự coi là leader). */
  fallback: boolean;
}

export function useTabLeader(channelKey: string, enabled = true): UseTabLeaderResult {
  const [isLeader, setIsLeader] = useState<boolean>(true); // optimistic: tab đầu tiên thường là leader
  const [fallback, setFallback] = useState<boolean>(false);
  const tabIdRef = useRef<string>('');

  useEffect(() => {
    if (!enabled || typeof window === 'undefined') return;
    if (typeof BroadcastChannel === 'undefined') {
      setFallback(true);
      setIsLeader(true);
      return;
    }

    const tabId = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    tabIdRef.current = tabId;
    const bc = new BroadcastChannel(`hkg-leader-${channelKey}`);
    let claimTimer: ReturnType<typeof setTimeout> | null = null;
    let alive = true;

    const onMessage = (evt: MessageEvent<Msg>) => {
      const msg = evt.data;
      if (!msg || msg.tabId === tabId) return;

      if (msg.type === 'claim') {
        // Tab khác đang claim. Nếu mình đang là leader → ack lại.
        if (isLeaderRef.current) {
          bc.postMessage({ type: 'ack', tabId } satisfies Msg);
        }
      } else if (msg.type === 'ack') {
        // Có leader khác → mình không phải leader nữa
        if (claimTimer) {
          clearTimeout(claimTimer);
          claimTimer = null;
        }
        setIsLeader(false);
        isLeaderRef.current = false;
      } else if (msg.type === 'release') {
        // Leader cũ release → claim lại sau random jitter để tránh thunder
        if (alive && document.visibilityState === 'visible') {
          setTimeout(claim, Math.random() * 50);
        }
      }
    };

    const claim = () => {
      if (!alive) return;
      bc.postMessage({ type: 'claim', tabId, ts: Date.now() } satisfies Msg);
      // Nếu không nhận ack trong CLAIM_TIMEOUT_MS → mình là leader
      if (claimTimer) clearTimeout(claimTimer);
      claimTimer = setTimeout(() => {
        if (alive) {
          setIsLeader(true);
          isLeaderRef.current = true;
        }
      }, CLAIM_TIMEOUT_MS);
    };

    const onVisibility = () => {
      if (!alive) return;
      if (document.visibilityState === 'visible') {
        claim();
      } else {
        // Tab hidden → release leadership cho tab khác (nếu mình là leader)
        if (isLeaderRef.current) {
          bc.postMessage({ type: 'release', tabId } satisfies Msg);
          setIsLeader(false);
          isLeaderRef.current = false;
        }
      }
    };

    const onUnload = () => {
      try {
        bc.postMessage({ type: 'release', tabId } satisfies Msg);
      } catch { /* noop */ }
    };

    bc.addEventListener('message', onMessage);
    document.addEventListener('visibilitychange', onVisibility);
    window.addEventListener('beforeunload', onUnload);

    // Initial claim
    claim();

    return () => {
      alive = false;
      if (claimTimer) clearTimeout(claimTimer);
      bc.removeEventListener('message', onMessage);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('beforeunload', onUnload);
      try { bc.postMessage({ type: 'release', tabId } satisfies Msg); } catch { /* noop */ }
      bc.close();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [channelKey, enabled]);

  // Ref song song với state để callbacks dùng giá trị mới nhất (tránh stale closure)
  const isLeaderRef = useRef<boolean>(true);
  useEffect(() => { isLeaderRef.current = isLeader; }, [isLeader]);

  return { isLeader, fallback };
}

export default useTabLeader;

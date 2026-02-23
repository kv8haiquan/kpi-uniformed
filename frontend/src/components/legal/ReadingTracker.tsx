/**
 * src/components/legal/ReadingTracker.tsx
 * =========================================
 * Hook theo dõi thời gian đọc văn bản.
 * Gọi API trackingDoc mỗi 30 giây để cập nhật tích lũy.
 * Tự động dừng khi component unmount.
 *
 * Cách dùng:
 *   useReadingTracker(vanBanId)  // Đặt trong component đọc VB
 */

'use client';

import { useEffect, useRef } from 'react';
import { legalService } from '@/services/legal';

/**
 * Custom hook theo dõi thời gian đọc văn bản.
 * Gọi API mỗi 30 giây để tích lũy thời gian lên server.
 *
 * @param vanBanId - UUID văn bản đang đọc ('' để tắt tracking)
 */
export function useReadingTracker(vanBanId: string) {
  // Đếm số giây đã tracking trong session hiện tại
  const elapsedRef = useRef(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!vanBanId) return;

    // Reset đếm thời gian khi chuyển sang VB khác
    elapsedRef.current = 0;

    // Mỗi 30s: cộng thêm 30s và gửi lên server (silent)
    intervalRef.current = setInterval(async () => {
      elapsedRef.current += 30;
      try {
        await legalService.trackingDoc(vanBanId, {
          thoi_gian_doc_giay: elapsedRef.current,
        });
      } catch {
        // Silent fail — không làm gián đoạn trải nghiệm đọc
      }
    }, 30_000);

    return () => {
      // Cleanup khi component unmount hoặc vanBanId thay đổi
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [vanBanId]);
}

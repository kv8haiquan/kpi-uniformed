'use client';

/**
 * OnboardingHint — banner hướng dẫn lần đầu, dismissable + nhớ qua localStorage.
 *
 * Phase 4.1 FE_P5.
 *
 * Dùng cho 2 ngữ cảnh trong tab Tài liệu:
 *  - Host: hướng dẫn nút "Trình chiếu" → bắt đầu page-sync
 *  - Đại biểu: hướng dẫn nút "Xem độc lập" → tách khỏi sync
 *
 * Flag localStorage: `hkg.tip.<storageKey>.seen=true`
 */

import { useEffect, useState } from 'react';
import { Lightbulb, X } from 'lucide-react';

interface Props {
  /** Phân biệt từng tip — sẽ ghép với prefix `hkg.tip.` để lưu vào localStorage. */
  storageKey: string;
  title: string;
  message: string;
  /** Có hiển thị tip không (vd chỉ hiện khi cuộc họp DA_THONG_BAO/DANG_DIEN_RA). */
  show?: boolean;
}

export function OnboardingHint({ storageKey, title, message, show = true }: Props) {
  const [dismissed, setDismissed] = useState<boolean>(true); // optimistic: hide khi SSR

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const key = `hkg.tip.${storageKey}.seen`;
    const seen = localStorage.getItem(key) === 'true';
    setDismissed(seen);
  }, [storageKey]);

  const handleDismiss = () => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(`hkg.tip.${storageKey}.seen`, 'true');
    }
    setDismissed(true);
  };

  if (!show || dismissed) return null;

  return (
    <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded">
      <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1 text-sm">
        <p className="font-medium text-blue-900">{title}</p>
        <p className="text-blue-800 text-xs mt-0.5">{message}</p>
      </div>
      <button
        onClick={handleDismiss}
        className="text-blue-600 hover:text-blue-800 p-0.5"
        title="Đã hiểu"
        aria-label="Đóng tip"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

export default OnboardingHint;

'use client';

/**
 * IndependentViewBanner — banner cảnh báo đại biểu đang xem độc lập.
 *
 * Phase 4.1 FE_P3.
 *
 * Hiển thị khi đại biểu (!isHost) đã toggle sang independentMode. Nút "Quay về
 * đồng bộ" trigger ConfirmReturnDialog ở component cha.
 */

import { Eye, ArrowLeftCircle } from 'lucide-react';

interface Props {
  /** Trang đại biểu đang xem độc lập */
  localPage: number;
  /** Trang host đang ở (để báo gap) */
  hostPage: number;
  totalPages: number;
  onReturnToSync: () => void;
}

export function IndependentViewBanner({
  localPage,
  hostPage,
  totalPages,
  onReturnToSync,
}: Props) {
  const gap = Math.abs(localPage - hostPage);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-purple-50 border border-purple-300 rounded">
      <div className="flex items-start gap-2">
        <Eye className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-purple-900">Bạn đang xem độc lập</p>
          <p className="text-purple-700 text-xs mt-0.5">
            Trang của bạn: <strong>{localPage}/{totalPages}</strong> · Chủ tọa
            đang ở trang <strong>{hostPage}</strong>
            {gap > 0 && <span className="ml-1">(cách {gap} trang)</span>}
          </p>
        </div>
      </div>
      <button
        onClick={onReturnToSync}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white rounded text-xs font-medium hover:bg-purple-700"
      >
        <ArrowLeftCircle className="w-4 h-4" />
        Quay về đồng bộ
      </button>
    </div>
  );
}

export default IndependentViewBanner;

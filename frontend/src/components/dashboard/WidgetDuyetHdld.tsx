/**
 * src/components/dashboard/WidgetDuyetHdld.tsx
 * ============================================
 * Widget dashboard: TDV/PDV xem nhanh số HĐLĐ 111 đang chờ mình duyệt
 * (Bộ tiêu chí VB714). Click → trang Phê duyệt, tab HĐLĐ.
 *
 * Tự load count cho tháng hiện tại. Chỉ render khi visible (TDV/PDV).
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import hdldService from '@/services/hdld.service';
import { isHdldVb714Active } from '@/types/hdld';

interface Props {
  /** Chỉ render cho TDV/PDV. */
  visible: boolean;
}

export default function WidgetDuyetHdld({ visible }: Props) {
  const router = useRouter();

  const now = new Date();
  const thang = now.getMonth() + 1;
  const nam = now.getFullYear();
  const active = isHdldVb714Active(thang, nam);
  const shouldFetch = visible && active;

  const [count, setCount] = useState(0);
  // Chỉ ở trạng thái loading khi thực sự sẽ fetch (tránh setState đồng bộ trong effect)
  const [loading, setLoading] = useState(shouldFetch);

  useEffect(() => {
    if (!shouldFetch) return;
    let alive = true;
    hdldService
      .getChoDuyet(thang, nam)
      .then((data) => { if (alive) setCount(data.length); })
      .catch(() => { if (alive) setCount(0); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [shouldFetch, thang, nam]);

  // Trước mốc VB714 (T5/2026) thì không hiển thị widget
  if (!visible || !active) return null;

  return (
    <button
      onClick={() => router.push('/xep-loai?tab=hdld')}
      className="w-full text-left bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
    >
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-amber-50 to-orange-50">
        <div className="flex items-center gap-2">
          <span className="text-lg">🧰</span>
          <h3 className="font-medium text-gray-900">Duyệt HĐLĐ 111</h3>
        </div>
        {!loading && count > 0 && (
          <span className="text-xs text-white bg-red-500 px-2 py-1 rounded-full font-medium">
            {count} chờ
          </span>
        )}
      </div>
      <div className="p-5">
        {loading ? (
          <div className="flex items-center justify-center py-6">
            <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-amber-600" />
          </div>
        ) : count > 0 ? (
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-gray-900">{count}</div>
            <div className="text-sm text-gray-600">
              bản tự đánh giá HĐLĐ đang chờ bạn duyệt
              <div className="text-amber-600 text-xs mt-1">Bấm để xử lý →</div>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-2xl">✅</span>
            </div>
            <p className="text-sm text-gray-500">Không có HĐLĐ nào chờ duyệt</p>
          </div>
        )}
      </div>
    </button>
  );
}

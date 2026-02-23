/**
 * WidgetLegal.tsx
 * ================
 * Widget hiển thị tóm tắt văn bản pháp luật (chưa đọc, mới nhất).
 * Fallback: card điều hướng nếu dữ liệu chưa có.
 */

import Link from 'next/link';
import DashboardWidget from './DashboardWidget';
import type { ILegalDashboardSummary } from '@/types/portal';

// =============================================================================
// COMPONENT
// =============================================================================

interface WidgetLegalProps {
  data: ILegalDashboardSummary | null;
  loading: boolean;
}

export default function WidgetLegal({ data, loading }: WidgetLegalProps) {
  return (
    <DashboardWidget
      title="Pháp luật"
      icon="⚖️"
      href="/phap-luat"
      hrefLabel="Xem văn bản"
      loading={loading}
      colorClass="bg-red-100"
    >
      {data ? (
        <div className="space-y-3">
          {/* 2 chỉ số */}
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center bg-red-50 rounded-lg py-3 px-2">
              <div className="text-2xl font-bold text-red-700">
                {data.vb_chua_doc ?? 0}
              </div>
              <div className="text-xs text-gray-500 mt-1">Chưa đọc</div>
            </div>
            <div className="text-center bg-blue-50 rounded-lg py-3 px-2">
              <div className="text-2xl font-bold text-blue-700">
                {data.vb_moi ?? 0}
              </div>
              <div className="text-xs text-gray-500 mt-1">Văn bản mới</div>
            </div>
          </div>

          {/* Cảnh báo nếu có văn bản chưa đọc */}
          {(data.vb_chua_doc ?? 0) > 0 && (
            <Link
              href="/phap-luat"
              className="block text-center text-xs bg-red-600 text-white rounded-lg py-1.5 hover:bg-red-700 transition-colors"
            >
              Đọc ngay {data.vb_chua_doc} văn bản chưa đọc
            </Link>
          )}
        </div>
      ) : (
        /* Fallback */
        <div className="space-y-3">
          <p className="text-xs text-gray-500 text-center">Tra cứu văn bản pháp luật</p>
          <div className="grid grid-cols-2 gap-2">
            <Link
              href="/phap-luat"
              className="block text-center rounded-lg bg-red-50 hover:bg-red-100 border border-red-200 p-2 transition-colors"
            >
              <div className="text-lg">📜</div>
              <div className="text-xs text-red-700 font-medium mt-1">Văn bản</div>
            </Link>
            <Link
              href="/phap-luat/tra-cuu"
              className="block text-center rounded-lg bg-orange-50 hover:bg-orange-100 border border-orange-200 p-2 transition-colors"
            >
              <div className="text-lg">🔍</div>
              <div className="text-xs text-orange-700 font-medium mt-1">Tra cứu</div>
            </Link>
          </div>
        </div>
      )}
    </DashboardWidget>
  );
}

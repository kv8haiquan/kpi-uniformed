/**
 * WidgetThongBao.tsx
 * ===================
 * Widget hiển thị số lượng thông báo chưa đọc (khẩn, quan trọng, bình thường).
 * Fallback: card điều hướng nếu service chưa có.
 */

import Link from 'next/link';
import DashboardWidget from './DashboardWidget';
import type { IThongBaoCount } from '@/types/portal';

// =============================================================================
// COMPONENT
// =============================================================================

interface WidgetThongBaoProps {
  data: IThongBaoCount | null;
  loading: boolean;
}

export default function WidgetThongBao({ data, loading }: WidgetThongBaoProps) {
  return (
    <DashboardWidget
      title="Thông báo"
      icon="🔔"
      href="/thong-bao"
      hrefLabel="Tất cả"
      loading={loading}
      colorClass="bg-orange-100"
    >
      {data && data.count > 0 ? (
        <div className="space-y-3">
          {/* Tổng */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Chưa đọc</span>
            <span className="text-2xl font-bold text-orange-600">{data.count}</span>
          </div>

          {/* Chi tiết */}
          <div className="space-y-2">
            {data.khan > 0 && (
              <div className="flex items-center justify-between bg-red-50 rounded-lg px-3 py-1.5">
                <span className="text-xs font-medium text-red-700">Khẩn</span>
                <span className="text-sm font-bold text-red-700">{data.khan}</span>
              </div>
            )}
            {data.quan_trong > 0 && (
              <div className="flex items-center justify-between bg-yellow-50 rounded-lg px-3 py-1.5">
                <span className="text-xs font-medium text-yellow-700">Quan trọng</span>
                <span className="text-sm font-bold text-yellow-700">{data.quan_trong}</span>
              </div>
            )}
            {data.binh_thuong > 0 && (
              <div className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-1.5">
                <span className="text-xs font-medium text-gray-600">Bình thường</span>
                <span className="text-sm font-bold text-gray-600">{data.binh_thuong}</span>
              </div>
            )}
          </div>
        </div>
      ) : data && data.count === 0 ? (
        <div className="flex flex-col items-center justify-center py-4 text-center">
          <span className="text-2xl mb-2">✅</span>
          <p className="text-xs text-gray-400">Không có thông báo mới</p>
        </div>
      ) : (
        /* Fallback: service chưa có */
        <div className="flex flex-col items-center justify-center py-4 text-center">
          <Link
            href="/thong-bao"
            className="inline-flex items-center gap-2 text-sm text-orange-600 hover:underline"
          >
            <span className="text-2xl">🔔</span>
            <span>Xem thông báo</span>
          </Link>
          <p className="text-xs text-gray-400 mt-2">Hệ thống thông báo đang cập nhật</p>
        </div>
      )}
    </DashboardWidget>
  );
}

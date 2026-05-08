/**
 * WidgetKPI.tsx
 * =============
 * Widget hiển thị tóm tắt KPI cá nhân tháng hiện tại.
 * Fallback: card điều hướng nếu dữ liệu chưa có.
 */

import Link from 'next/link';
import DashboardWidget from './DashboardWidget';
import type { IKPIDashboardSummary } from '@/types/portal';

// =============================================================================
// HELPER: màu xếp loại
// =============================================================================

const XEP_LOAI_STYLE: Record<string, { bg: string; text: string }> = {
  A: { bg: 'bg-green-100', text: 'text-green-700' },
  B: { bg: 'bg-blue-100', text: 'text-blue-700' },
  C: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
  D: { bg: 'bg-red-100', text: 'text-red-700' },
};

// =============================================================================
// COMPONENT
// =============================================================================

interface WidgetKPIProps {
  data: IKPIDashboardSummary | null;
  loading: boolean;
}

export default function WidgetKPI({ data, loading }: WidgetKPIProps) {
  const xepLoai = data?.xep_loai;
  const style = xepLoai ? (XEP_LOAI_STYLE[xepLoai] ?? XEP_LOAI_STYLE['C']) : null;
  const now = new Date();
  const thangNam = `Tháng ${now.getMonth() + 1}/${now.getFullYear()}`;

  return (
    <DashboardWidget
      title="KPI cá nhân"
      icon="📊"
      href="/dashboard"
      hrefLabel="Trang KPI"
      loading={loading}
      colorClass="bg-blue-100"
    >
      {data ? (
        <div className="space-y-3">
          {/* Điểm tổng */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">{thangNam}</span>
            {data.trang_thai_ke_khai && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                {data.trang_thai_ke_khai === 'DA_DUYET' ? 'Đã duyệt'
                  : data.trang_thai_ke_khai === 'CHO_DUYET' ? 'Chờ duyệt'
                  : 'Nháp'}
              </span>
            )}
          </div>

          {data.diem_thang_nay !== undefined && (
            <div className="text-center py-2">
              <div className="text-4xl font-bold text-blue-700">
                {data.diem_thang_nay.toFixed(6).replace(/\.?0+$/, '')}
              </div>
              <div className="text-xs text-gray-400 mt-1">điểm tháng này</div>
            </div>
          )}

          {style && xepLoai && (
            <div className={`${style.bg} ${style.text} rounded-lg px-3 py-2 text-center`}>
              <span className="font-bold text-lg">Loại {xepLoai}</span>
            </div>
          )}

          <Link
            href="/ke-khai-v2"
            className="block text-center text-xs text-blue-600 hover:underline mt-1"
          >
            Kê khai công việc tháng
          </Link>
        </div>
      ) : (
        /* Fallback: chưa kê khai */
        <div className="space-y-3">
          <p className="text-xs text-gray-500 text-center">{thangNam} — Chưa có dữ liệu</p>
          <div className="grid grid-cols-2 gap-2">
            <Link
              href="/ke-khai-v2"
              className="block text-center rounded-lg bg-blue-50 hover:bg-blue-100 border border-blue-200 p-2 transition-colors"
            >
              <div className="text-lg">📝</div>
              <div className="text-xs text-blue-700 font-medium mt-1">Kê khai</div>
            </Link>
            <Link
              href="/danh-gia-v2"
              className="block text-center rounded-lg bg-green-50 hover:bg-green-100 border border-green-200 p-2 transition-colors"
            >
              <div className="text-lg">✅</div>
              <div className="text-xs text-green-700 font-medium mt-1">Đánh giá</div>
            </Link>
          </div>
        </div>
      )}
    </DashboardWidget>
  );
}

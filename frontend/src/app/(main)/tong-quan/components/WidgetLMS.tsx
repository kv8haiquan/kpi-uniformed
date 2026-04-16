/**
 * WidgetLMS.tsx
 * ==============
 * Widget hiển thị tóm tắt học tập (đang học, hoàn thành, chứng chỉ).
 * Fallback: card điều hướng đến module Đào tạo nếu dữ liệu chưa có.
 */

import Link from 'next/link';
import DashboardWidget from './DashboardWidget';
import type { ILMSDashboardSummary } from '@/types/portal';

// =============================================================================
// COMPONENT
// =============================================================================

interface WidgetLMSProps {
  data: ILMSDashboardSummary | null;
  loading: boolean;
}

export default function WidgetLMS({ data, loading }: WidgetLMSProps) {
  return (
    <DashboardWidget
      title="Đào tạo"
      icon="📚"
      href="/dao-tao"
      hrefLabel="Xem khóa học"
      loading={loading}
      colorClass="bg-purple-100"
    >
      {data ? (
        <div className="space-y-3">
          {/* 3 chỉ số */}
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center bg-purple-50 rounded-lg py-2 px-1">
              <div className="text-xl font-bold text-purple-700">
                {data.khoa_dang_hoc ?? 0}
              </div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">Đang học</div>
            </div>
            <div className="text-center bg-green-50 rounded-lg py-2 px-1">
              <div className="text-xl font-bold text-green-700">
                {data.khoa_hoan_thanh ?? 0}
              </div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">Hoàn thành</div>
            </div>
            <div className="text-center bg-yellow-50 rounded-lg py-2 px-1">
              <div className="text-xl font-bold text-yellow-700">
                {data.chung_chi ?? 0}
              </div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">Chứng chỉ</div>
            </div>
          </div>

          {/* CTA nếu có khóa đang học */}
          {(data.khoa_dang_hoc ?? 0) > 0 && (
            <Link
              href="/dao-tao"
              className="block text-center text-xs text-purple-600 hover:underline"
            >
              Tiếp tục học →
            </Link>
          )}
        </div>
      ) : (
        /* Fallback */
        <div className="space-y-3">
          <p className="text-xs text-gray-500 text-center">Khám phá khóa học</p>
          <div className="grid grid-cols-2 gap-2">
            <Link
              href="/dao-tao"
              className="block text-center rounded-lg bg-purple-50 hover:bg-purple-100 border border-purple-200 p-2 transition-colors"
            >
              <div className="text-lg">📖</div>
              <div className="text-xs text-purple-700 font-medium mt-1">Khóa học</div>
            </Link>
            <Link
              href="/dao-tao/khoa-hoc"
              className="block text-center rounded-lg bg-green-50 hover:bg-green-100 border border-green-200 p-2 transition-colors"
            >
              <div className="text-lg">🏅</div>
              <div className="text-xs text-green-700 font-medium mt-1">Của tôi</div>
            </Link>
          </div>
        </div>
      )}
    </DashboardWidget>
  );
}

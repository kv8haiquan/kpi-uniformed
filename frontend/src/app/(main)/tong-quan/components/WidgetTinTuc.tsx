/**
 * WidgetTinTuc.tsx
 * =================
 * Widget hiển thị tin ghim + tin mới nhất từ Portal.
 * Fallback: card điều hướng nếu service chưa có.
 */

import Link from 'next/link';
import DashboardWidget from './DashboardWidget';
import type { IPortalDashboardSummary } from '@/types/portal';

// =============================================================================
// HELPER
// =============================================================================

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
  } catch {
    return '';
  }
}

// =============================================================================
// COMPONENT
// =============================================================================

interface WidgetTinTucProps {
  data: IPortalDashboardSummary | null;
  loading: boolean;
}

export default function WidgetTinTuc({ data, loading }: WidgetTinTucProps) {
  const tinGhim = data?.tin_ghim ?? [];
  const tinMoi = data?.tin_moi_nhat ?? [];

  return (
    <DashboardWidget
      title="Tin tức & Thông báo"
      icon="📰"
      href="/tin-tuc"
      hrefLabel="Xem tất cả"
      loading={loading}
      colorClass="bg-indigo-100"
      className="lg:col-span-2"
    >
      {data ? (
        <div className="space-y-4">
          {/* Tin ghim */}
          {tinGhim.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Tin ghim</span>
              </div>
              <div className="space-y-2">
                {tinGhim.map((tin) => (
                  <Link
                    key={tin.id}
                    href={`/tin-tuc/${tin.id}`}
                    className="flex items-start gap-2 group hover:bg-indigo-50 rounded-lg px-2 py-1.5 -mx-2 transition-colors"
                  >
                    <span className="text-yellow-500 text-sm mt-0.5 flex-shrink-0">📌</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 font-medium group-hover:text-indigo-700 line-clamp-2 leading-snug">
                        {tin.tieu_de}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        {tin.ngay_xuat_ban && (
                          <span className="text-xs text-gray-400">{formatDate(tin.ngay_xuat_ban)}</span>
                        )}
                        <span className="text-xs text-gray-300">{tin.so_luot_xem} lượt xem</span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Divider */}
          {tinGhim.length > 0 && tinMoi.length > 0 && (
            <hr className="border-gray-100" />
          )}

          {/* Tin mới nhất */}
          {tinMoi.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Mới nhất</span>
                {data.bai_viet_moi > 0 && (
                  <span className="text-xs bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded-full">
                    +{data.bai_viet_moi} hôm nay
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {tinMoi.map((tin) => (
                  <Link
                    key={tin.id}
                    href={`/tin-tuc/${tin.id}`}
                    className="flex items-start gap-2 group hover:bg-indigo-50 rounded-lg px-2 py-1.5 -mx-2 transition-colors"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700 group-hover:text-indigo-700 line-clamp-1 leading-snug">
                        {tin.tieu_de}
                      </p>
                      {tin.ngay_xuat_ban && (
                        <span className="text-xs text-gray-400">{formatDate(tin.ngay_xuat_ban)}</span>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {tinGhim.length === 0 && tinMoi.length === 0 && (
            <div className="flex flex-col items-center justify-center py-4 text-center">
              <p className="text-xs text-gray-400">Chưa có tin tức nào</p>
            </div>
          )}
        </div>
      ) : (
        /* Fallback */
        <div className="space-y-3">
          <p className="text-xs text-gray-500 text-center">Cổng thông tin nội bộ</p>
          <div className="grid grid-cols-3 gap-2">
            <Link
              href="/tin-tuc"
              className="block text-center rounded-lg bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 p-2 transition-colors"
            >
              <div className="text-lg">📰</div>
              <div className="text-xs text-indigo-700 font-medium mt-1">Tin tức</div>
            </Link>
            <Link
              href="/tai-lieu"
              className="block text-center rounded-lg bg-blue-50 hover:bg-blue-100 border border-blue-200 p-2 transition-colors"
            >
              <div className="text-lg">📁</div>
              <div className="text-xs text-blue-700 font-medium mt-1">Tài liệu</div>
            </Link>
            <Link
              href="/tin-tuc/tao-moi"
              className="block text-center rounded-lg bg-green-50 hover:bg-green-100 border border-green-200 p-2 transition-colors"
            >
              <div className="text-lg">✍️</div>
              <div className="text-xs text-green-700 font-medium mt-1">Đăng tin</div>
            </Link>
          </div>
        </div>
      )}
    </DashboardWidget>
  );
}

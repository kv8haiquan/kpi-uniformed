/**
 * WidgetHKG.tsx
 * ==============
 * Widget tóm tắt module Họp Không Giấy — số cuộc họp tháng, nhiệm vụ đang làm/quá hạn.
 * Fallback: card điều hướng sang /hop-khong-giay nếu chưa có dữ liệu.
 */

import Link from 'next/link';
import DashboardWidget from './DashboardWidget';
import type { IHKGDashboardSummary } from '@/types/portal';

interface WidgetHKGProps {
  data: IHKGDashboardSummary | null;
  loading: boolean;
}

export default function WidgetHKG({ data, loading }: WidgetHKGProps) {
  const tongHop = data?.so_cuoc_hop_thang_nay ?? 0;
  const thamDu = data?.so_cuoc_hop_tham_du ?? 0;
  const dangLam = data?.nhiem_vu_dang_lam ?? 0;
  const quaHan = data?.nhiem_vu_qua_han ?? 0;

  return (
    <DashboardWidget
      title="Họp không giấy"
      icon="🗓️"
      href="/hop-khong-giay"
      hrefLabel="Xem cuộc họp"
      loading={loading}
      colorClass="bg-indigo-100"
    >
      {data ? (
        <div className="space-y-3">
          {/* 4 chỉ số */}
          <div className="grid grid-cols-2 gap-2">
            <div className="text-center bg-indigo-50 rounded-lg py-2 px-1">
              <div className="text-xl font-bold text-indigo-700">{tongHop}</div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">Họp tháng này</div>
            </div>
            <div className="text-center bg-blue-50 rounded-lg py-2 px-1">
              <div className="text-xl font-bold text-blue-700">{thamDu}</div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">Đã tham dự</div>
            </div>
            <div className="text-center bg-amber-50 rounded-lg py-2 px-1">
              <div className="text-xl font-bold text-amber-700">{dangLam}</div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">Nhiệm vụ đang làm</div>
            </div>
            <div className={`text-center rounded-lg py-2 px-1 ${quaHan > 0 ? 'bg-red-50' : 'bg-gray-50'}`}>
              <div className={`text-xl font-bold ${quaHan > 0 ? 'text-red-700' : 'text-gray-500'}`}>
                {quaHan}
              </div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">Quá hạn</div>
            </div>
          </div>

          {quaHan > 0 && (
            <Link
              href="/hop-khong-giay"
              className="block text-center text-xs text-red-600 hover:underline"
            >
              ⚠️ Có {quaHan} nhiệm vụ quá hạn — xử lý ngay →
            </Link>
          )}
        </div>
      ) : (
        /* Fallback */
        <div className="space-y-3">
          <p className="text-xs text-gray-500 text-center">Quản lý cuộc họp & biên bản</p>
          <div className="grid grid-cols-2 gap-2">
            <Link
              href="/hop-khong-giay"
              className="block text-center rounded-lg bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 p-2 transition-colors"
            >
              <div className="text-lg">📋</div>
              <div className="text-xs text-indigo-700 font-medium mt-1">Cuộc họp</div>
            </Link>
            <Link
              href="/hop-khong-giay/tao-hop"
              className="block text-center rounded-lg bg-blue-50 hover:bg-blue-100 border border-blue-200 p-2 transition-colors"
            >
              <div className="text-lg">➕</div>
              <div className="text-xs text-blue-700 font-medium mt-1">Tạo cuộc họp</div>
            </Link>
          </div>
        </div>
      )}
    </DashboardWidget>
  );
}

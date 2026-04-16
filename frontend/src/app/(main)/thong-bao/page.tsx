/**
 * src/app/(main)/thong-bao/page.tsx
 * ===================================
 * Trang thông báo đầy đủ — danh sách, lọc, phân trang, đánh dấu đã đọc.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { thongBaoApi } from '@/services/common';
import type {
  IThongBaoListItem,
  IThongBaoCount,
  LoaiThongBao,
  MucDoThongBao,
} from '@/types/common';
import {
  LOAI_THONG_BAO_LABELS,
  MUC_DO_CONFIG,
} from '@/types/common';

// =============================================================================
// CONSTANTS
// =============================================================================

const LOAI_FILTERS: { value: LoaiThongBao | ''; label: string }[] = [
  { value: '', label: 'Tất cả' },
  { value: 'KPI', label: 'KPI' },
  { value: 'LMS', label: 'Đào tạo' },
  { value: 'FORUM', label: 'Diễn đàn' },
  { value: 'LEGAL', label: 'Pháp luật' },
  { value: 'PORTAL', label: 'Tin tức' },
  { value: 'HE_THONG', label: 'Hệ thống' },
];

const DA_DOC_FILTERS: { value: string; label: string }[] = [
  { value: '', label: 'Tất cả' },
  { value: 'false', label: 'Chưa đọc' },
  { value: 'true', label: 'Đã đọc' },
];

const LOAI_ICON: Record<string, string> = {
  KPI: '📊',
  LMS: '📚',
  FORUM: '💬',
  LEGAL: '⚖️',
  PORTAL: '📰',
  HE_THONG: '🔔',
};

// =============================================================================
// HELPERS
// =============================================================================

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Vừa xong';
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} ngày trước`;
  return new Date(dateStr).toLocaleDateString('vi-VN');
}

// =============================================================================
// MAIN
// =============================================================================

export default function ThongBaoPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // State
  const [items, setItems] = useState<IThongBaoListItem[]>([]);
  const [count, setCount] = useState<IThongBaoCount | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [loai, setLoai] = useState<LoaiThongBao | ''>(
    (searchParams.get('loai') as LoaiThongBao) || ''
  );
  const [daDoc, setDaDoc] = useState<string>(searchParams.get('da_doc') || '');

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = { page, page_size: 20 };
      if (loai) params.loai = loai;
      if (daDoc !== '') params.da_doc = daDoc === 'true';

      const [listRes, countRes] = await Promise.all([
        thongBaoApi.danhSach(params),
        thongBaoApi.demChuaDoc(),
      ]);

      setItems(listRes.data.data || []);
      setTotalPages(listRes.data.pagination?.total_pages || 1);
      setCount(countRes.data.data);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Không thể tải thông báo');
    } finally {
      setLoading(false);
    }
  }, [page, loai, daDoc]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Mark single as read
  const handleMarkRead = async (id: string) => {
    try {
      await thongBaoApi.danhDauDaDoc(id);
      setItems((prev) =>
        prev.map((it) => (it.id === id ? { ...it, da_doc: true } : it))
      );
      if (count) setCount({ ...count, count: Math.max(0, count.count - 1) });
    } catch {
      // ignore
    }
  };

  // Mark all as read
  const handleMarkAllRead = async () => {
    try {
      await thongBaoApi.danhDauTatCaDaDoc();
      setItems((prev) => prev.map((it) => ({ ...it, da_doc: true })));
      setCount({ count: 0, khan: 0, quan_trong: 0, binh_thuong: 0 });
    } catch {
      // ignore
    }
  };

  // Navigate on click
  const handleClick = (item: IThongBaoListItem) => {
    if (!item.da_doc) handleMarkRead(item.id);
    if (item.link_url) router.push(item.link_url);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Thông báo</h1>
            <p className="text-sm text-gray-500 mt-1">
              {count ? `${count.count} thông báo chưa đọc` : 'Đang tải...'}
            </p>
          </div>
          {count && count.count > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              Đánh dấu tất cả đã đọc
            </button>
          )}
        </div>

        {/* Count badges */}
        {count && (
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-red-700">{count.khan}</div>
              <div className="text-xs text-red-600">Khẩn cấp</div>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-orange-700">{count.quan_trong}</div>
              <div className="text-xs text-orange-600">Quan trọng</div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-gray-700">{count.binh_thuong}</div>
              <div className="text-xs text-gray-600">Bình thường</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[160px]">
              <label className="block text-xs text-gray-500 mb-1">Loại</label>
              <select
                value={loai}
                onChange={(e) => { setLoai(e.target.value as any); setPage(1); }}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {LOAI_FILTERS.map((f) => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>
            <div className="flex-1 min-w-[160px]">
              <label className="block text-xs text-gray-500 mb-1">Trạng thái</label>
              <select
                value={daDoc}
                onChange={(e) => { setDaDoc(e.target.value); setPage(1); }}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {DA_DOC_FILTERS.map((f) => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 text-center">
            <p className="text-red-700">{error}</p>
            <p className="text-sm text-red-500 mt-1">Hãy đảm bảo Common backend đang chạy trên port 8005</p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        )}

        {/* List */}
        {!loading && !error && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {items.length === 0 ? (
              <div className="text-center py-16 text-gray-500">
                <span className="text-4xl block mb-2">📭</span>
                Không có thông báo nào
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {items.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleClick(item)}
                    className={`flex items-start gap-3 p-4 cursor-pointer transition-colors hover:bg-gray-50 ${
                      !item.da_doc ? 'bg-blue-50/50' : ''
                    }`}
                  >
                    {/* Icon */}
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-gray-100 shrink-0 mt-0.5">
                      <span className="text-lg">{LOAI_ICON[item.loai] || '🔔'}</span>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        {!item.da_doc && (
                          <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
                        )}
                        <span className={`text-sm font-medium ${!item.da_doc ? 'text-gray-900' : 'text-gray-600'}`}>
                          {item.tieu_de}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`px-2 py-0.5 text-xs rounded-full ${MUC_DO_CONFIG[item.muc_do]?.cls || 'bg-gray-100 text-gray-600'}`}>
                          {MUC_DO_CONFIG[item.muc_do]?.label || item.muc_do}
                        </span>
                        <span className="text-xs text-gray-400">
                          {LOAI_THONG_BAO_LABELS[item.loai] || item.loai}
                        </span>
                        <span className="text-xs text-gray-400">
                          {timeAgo(item.created_at)}
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    {!item.da_doc && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleMarkRead(item.id);
                        }}
                        className="text-xs text-blue-600 hover:underline shrink-0"
                      >
                        Đã đọc
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Trước
            </button>
            <span className="text-sm text-gray-600">
              Trang {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Tiếp
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

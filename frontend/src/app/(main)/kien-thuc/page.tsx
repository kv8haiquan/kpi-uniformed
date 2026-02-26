/**
 * src/app/(main)/kien-thuc/page.tsx
 * ====================================
 * Kho tri thuc SOP/FAQ — danh sach, tabs, tim kiem, loc theo tags/chuyen de.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { knowledgeBaseApi } from '@/services/common';
import type { IKBListItem, LoaiKB, TrangThaiKB } from '@/types/common';
import { TRANG_THAI_KB_CONFIG } from '@/types/common';

// =============================================================================
// CONSTANTS
// =============================================================================

const LOAI_TABS: { value: LoaiKB | ''; label: string; icon: string }[] = [
  { value: '', label: 'Tat ca', icon: '📋' },
  { value: 'SOP', label: 'SOP (Quy trinh)', icon: '📑' },
  { value: 'FAQ', label: 'FAQ (Hoi dap)', icon: '❓' },
];

// =============================================================================
// MAIN
// =============================================================================

export default function KienThucPage() {
  const searchParams = useSearchParams();

  // State
  const [items, setItems] = useState<IKBListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [loai, setLoai] = useState<LoaiKB | ''>((searchParams.get('loai') as LoaiKB) || '');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState('');

  // All tags extracted from results (for filter chips)
  const [allTags, setAllTags] = useState<string[]>([]);

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = {
        page,
        page_size: 20,
        trang_thai: 'DA_XUAT_BAN',
      };
      if (loai) params.loai = loai;
      if (searchQuery.length >= 2) params.q = searchQuery;
      if (selectedTag) params.tags = selectedTag;

      const res = await knowledgeBaseApi.danhSach(params);
      const data = res.data.data || [];
      setItems(data);
      setTotalPages(res.data.pagination?.total_pages || 1);

      // Extract unique tags
      const tags = new Set<string>();
      data.forEach((item: IKBListItem) => {
        (item.tags || []).forEach((t: string) => tags.add(t));
      });
      setAllTags(Array.from(tags).sort());
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Khong the tai du lieu');
    } finally {
      setLoading(false);
    }
  }, [page, loai, searchQuery, selectedTag]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Debounced search
  const [searchInput, setSearchInput] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(searchInput);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Kho tri thuc</h1>
          <p className="text-sm text-gray-500 mt-1">
            Quy trinh nghiep vu (SOP) va cau hoi thuong gap (FAQ)
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {LOAI_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => { setLoai(tab.value as any); setPage(1); }}
              className={`px-4 py-2 text-sm rounded-lg transition-colors flex items-center gap-1.5 ${
                loai === tab.value
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search + Tag filter */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-xs text-gray-500 mb-1">Tim kiem</label>
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Tim theo tieu de, noi dung..."
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            {allTags.length > 0 && (
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs text-gray-500 mb-1">Tag</label>
                <select
                  value={selectedTag}
                  onChange={(e) => { setSelectedTag(e.target.value); setPage(1); }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Tat ca tags</option>
                  {allTags.map((tag) => (
                    <option key={tag} value={tag}>{tag}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 text-center">
            <p className="text-red-700">{error}</p>
            <p className="text-sm text-red-500 mt-1">Hay dam bao Common backend dang chay tren port 8005</p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        )}

        {/* Grid */}
        {!loading && !error && (
          <>
            {items.length === 0 ? (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm text-center py-16 text-gray-500">
                <span className="text-4xl block mb-2">📭</span>
                Chua co bai viet nao
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {items.map((item) => (
                  <KBCard key={item.id} item={item} />
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Truoc
                </button>
                <span className="text-sm text-gray-600">
                  Trang {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Tiep
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// KB CARD
// =============================================================================

function KBCard({ item }: { item: IKBListItem }) {
  const loaiIcon = item.loai === 'SOP' ? '📑' : '❓';
  const ttConfig = TRANG_THAI_KB_CONFIG[item.trang_thai] || { label: item.trang_thai, cls: 'bg-gray-100 text-gray-600' };

  return (
    <Link
      href={`/kien-thuc/${item.id}`}
      className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 hover:border-blue-300 hover:shadow-md transition-all flex flex-col"
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-blue-50 shrink-0">
          <span className="text-lg">{loaiIcon}</span>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 line-clamp-2 text-sm">{item.tieu_de}</h3>
          <div className="flex items-center gap-2 mt-1">
            <span className={`px-2 py-0.5 text-xs rounded-full ${ttConfig.cls}`}>
              {ttConfig.label}
            </span>
            <span className="text-xs text-gray-400">{item.loai}</span>
            <span className="text-xs text-gray-400">v{item.phien_ban}</span>
          </div>
        </div>
      </div>

      {/* Tags */}
      {item.tags && item.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {item.tags.slice(0, 4).map((tag) => (
            <span key={tag} className="px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded-full">
              {tag}
            </span>
          ))}
          {item.tags.length > 4 && (
            <span className="text-xs text-gray-400">+{item.tags.length - 4}</span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="mt-auto pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
        <span>{item.chu_so_huu?.ho_ten || 'Khong ro'}</span>
        <span>{new Date(item.updated_at).toLocaleDateString('vi-VN')}</span>
      </div>
    </Link>
  );
}

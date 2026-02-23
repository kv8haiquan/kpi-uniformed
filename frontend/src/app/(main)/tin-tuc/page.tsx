/**
 * app/(main)/tin-tuc/page.tsx
 * ============================
 * Danh sách tin tức công khai — tabs chuyên mục, tin ghim, phân trang.
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { chuyenMucApi, baiVietApi, portalDashboardApi } from '@/services/portal';
import type { IChuyenMuc, IBaiVietListItem, IBaiVietListResponse } from '@/types/tin-tuc';
import type { ITinGhimBrief } from '@/types/portal';

// =============================================================================
// HELPERS
// =============================================================================

function formatDate(s?: string | null): string {
  if (!s) return '';
  const d = new Date(s);
  return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
}

// =============================================================================
// PINNED CARD
// =============================================================================

function PinnedCard({ tin }: { tin: ITinGhimBrief }) {
  return (
    <Link
      href={`/tin-tuc/${tin.id}`}
      className="group block bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md overflow-hidden transition-all"
    >
      {tin.anh_dai_dien ? (
        <div className="aspect-video bg-gray-100 overflow-hidden">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={tin.anh_dai_dien}
            alt={tin.tieu_de}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        </div>
      ) : (
        <div className="aspect-video bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
          <span className="text-4xl opacity-40">📰</span>
        </div>
      )}
      <div className="p-4">
        <div className="flex items-center gap-1.5 mb-2">
          <span className="text-yellow-500 text-xs">📌</span>
          <span className="text-xs text-yellow-600 font-medium">Tin ghim</span>
        </div>
        <h3 className="font-semibold text-gray-900 line-clamp-2 group-hover:text-blue-700 transition-colors leading-snug">
          {tin.tieu_de}
        </h3>
        {tin.tom_tat && (
          <p className="text-xs text-gray-500 mt-1.5 line-clamp-2">{tin.tom_tat}</p>
        )}
        <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
          {tin.ngay_xuat_ban && <span>{formatDate(tin.ngay_xuat_ban)}</span>}
          <span>{tin.so_luot_xem} lượt xem</span>
        </div>
      </div>
    </Link>
  );
}

// =============================================================================
// ARTICLE ROW
// =============================================================================

function ArticleRow({ bai }: { bai: IBaiVietListItem }) {
  return (
    <Link
      href={`/tin-tuc/${bai.id}`}
      className="flex items-start gap-3 py-3 px-2 hover:bg-gray-50 rounded-lg -mx-2 group transition-colors"
    >
      {bai.anh_dai_dien && (
        <div className="w-16 h-12 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={bai.anh_dai_dien} alt="" className="w-full h-full object-cover" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800 group-hover:text-blue-700 line-clamp-2 leading-snug transition-colors">
          {bai.tieu_de}
        </p>
        <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
          <span className="text-blue-600">{bai.chuyen_muc.ten}</span>
          <span>·</span>
          {bai.ngay_xuat_ban && <span>{formatDate(bai.ngay_xuat_ban)}</span>}
          <span>·</span>
          <span>{bai.so_luot_xem} xem</span>
        </div>
      </div>
    </Link>
  );
}

// =============================================================================
// PAGE
// =============================================================================

const PAGE_SIZE = 15;

export default function TinTucPage() {
  const [chuyenMucList, setChuyenMucList] = useState<IChuyenMuc[]>([]);
  const [baiVietList, setBaiVietList] = useState<IBaiVietListItem[]>([]);
  const [tinGhim, setTinGhim] = useState<ITinGhimBrief[]>([]);
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total_items: 0 });
  const [selectedTab, setSelectedTab] = useState<string>('all');
  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [loadingBaiViet, setLoadingBaiViet] = useState(true);
  const [loadingInit, setLoadingInit] = useState(true);
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---------------------------------------------------------------------------
  // Fetch chuyên mục + tin ghim (khởi tạo)
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const init = async () => {
      const [cmRes, dashRes] = await Promise.allSettled([
        chuyenMucApi.danhSach(),
        portalDashboardApi.summary(),
      ]);

      if (cmRes.status === 'fulfilled') {
        const items = cmRes.value.data?.data ?? cmRes.value.data;
        setChuyenMucList(Array.isArray(items) ? items : []);
      }
      if (dashRes.status === 'fulfilled') {
        const data = dashRes.value.data?.data ?? dashRes.value.data;
        setTinGhim(data?.tin_ghim ?? []);
      }
      setLoadingInit(false);
    };
    init();
  }, []);

  // ---------------------------------------------------------------------------
  // Fetch bài viết
  // ---------------------------------------------------------------------------

  const fetchBaiViet = useCallback(async (p: number, tab: string, search: string) => {
    setLoadingBaiViet(true);
    try {
      const res = await baiVietApi.danhSach({
        page: p,
        page_size: PAGE_SIZE,
        chuyen_muc_id: tab !== 'all' ? tab : undefined,
        search: search || undefined,
      });
      const raw = res.data?.data ?? res.data;
      const items: IBaiVietListResponse = {
        items: raw?.items ?? [],
        pagination: raw?.pagination ?? { page: 1, page_size: PAGE_SIZE, total_items: 0, total_pages: 1 },
      };
      setBaiVietList(items.items);
      setPagination({
        page: items.pagination.page,
        total_pages: items.pagination.total_pages,
        total_items: items.pagination.total_items,
      });
    } catch {
      setBaiVietList([]);
    } finally {
      setLoadingBaiViet(false);
    }
  }, []);

  useEffect(() => {
    fetchBaiViet(page, selectedTab, searchText);
  }, [page, selectedTab, fetchBaiViet]); // searchText handled by debounce below

  // ---------------------------------------------------------------------------
  // Search debounce
  // ---------------------------------------------------------------------------

  const handleSearchChange = (val: string) => {
    setSearchText(val);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => {
      setPage(1);
      fetchBaiViet(1, selectedTab, val);
    }, 400);
  };

  const handleTabChange = (tab: string) => {
    setSelectedTab(tab);
    setPage(1);
  };

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-6 sm:px-6">

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Tin tức</h1>
          <p className="text-sm text-gray-500 mt-1">Tin tức nội bộ Hải quan Khu vực VIII</p>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <input
            type="text"
            placeholder="Tìm kiếm tin tức..."
            value={searchText}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
        </div>

        {/* Tabs chuyên mục */}
        {!loadingInit && (
          <div className="flex gap-2 overflow-x-auto pb-2 mb-6 scrollbar-hide">
            <button
              onClick={() => handleTabChange('all')}
              className={`flex-shrink-0 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                selectedTab === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              Tất cả
            </button>
            {chuyenMucList.map((cm) => (
              <button
                key={cm.id}
                onClick={() => handleTabChange(cm.id)}
                className={`flex-shrink-0 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  selectedTab === cm.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {cm.ten}
              </button>
            ))}
          </div>
        )}

        {/* Tin ghim (chỉ hiện ở tab "Tất cả") */}
        {selectedTab === 'all' && tinGhim.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Tin nổi bật
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {tinGhim.map((tin) => (
                <PinnedCard key={tin.id} tin={tin} />
              ))}
            </div>
          </div>
        )}

        {/* Danh sách bài viết */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <span className="text-sm font-semibold text-gray-700">
              {selectedTab === 'all' ? 'Tin mới nhất' : chuyenMucList.find(c => c.id === selectedTab)?.ten ?? 'Bài viết'}
            </span>
            <span className="text-xs text-gray-400">{pagination.total_items} bài</span>
          </div>

          {loadingBaiViet ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="animate-pulse flex gap-3">
                  <div className="w-16 h-12 bg-gray-200 rounded-lg flex-shrink-0" />
                  <div className="flex-1 space-y-2 pt-1">
                    <div className="h-3 bg-gray-200 rounded w-4/5" />
                    <div className="h-2 bg-gray-100 rounded w-1/3" />
                  </div>
                </div>
              ))}
            </div>
          ) : baiVietList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <span className="text-3xl mb-3">📭</span>
              <p className="text-sm text-gray-400">
                {searchText ? 'Không có kết quả phù hợp' : 'Chưa có bài viết nào'}
              </p>
            </div>
          ) : (
            <div className="px-4 divide-y divide-gray-50">
              {baiVietList.map((bai) => (
                <ArticleRow key={bai.id} bai={bai} />
              ))}
            </div>
          )}

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-center gap-1 px-4 py-3 border-t border-gray-100">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-2 py-1 text-sm rounded disabled:opacity-40 hover:bg-gray-100 transition-colors"
              >
                ←
              </button>
              {Array.from({ length: pagination.total_pages }, (_, i) => i + 1)
                .filter((p) => p === 1 || p === pagination.total_pages || Math.abs(p - page) <= 1)
                .reduce<(number | '...')[]>((acc, p, idx, arr) => {
                  if (idx > 0 && (p as number) - (arr[idx - 1] as number) > 1) acc.push('...');
                  acc.push(p);
                  return acc;
                }, [])
                .map((p, i) =>
                  p === '...' ? (
                    <span key={`dots-${i}`} className="px-2 py-1 text-sm text-gray-400">...</span>
                  ) : (
                    <button
                      key={p}
                      onClick={() => setPage(p as number)}
                      className={`px-3 py-1 text-sm rounded transition-colors ${
                        page === p
                          ? 'bg-blue-600 text-white'
                          : 'hover:bg-gray-100 text-gray-600'
                      }`}
                    >
                      {p}
                    </button>
                  )
                )}
              <button
                disabled={page >= pagination.total_pages}
                onClick={() => setPage((p) => p + 1)}
                className="px-2 py-1 text-sm rounded disabled:opacity-40 hover:bg-gray-100 transition-colors"
              >
                →
              </button>
            </div>
          )}
        </div>

        {/* Quick link quản lý */}
        <div className="mt-4 text-center">
          <Link href="/tin-tuc/quan-ly" className="text-xs text-gray-400 hover:text-blue-600 transition-colors">
            Quản lý bài viết →
          </Link>
        </div>

      </div>
    </div>
  );
}

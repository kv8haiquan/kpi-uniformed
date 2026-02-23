/**
 * src/app/(main)/phap-luat/page.tsx
 * =====================================
 * Trang chính Module Pháp luật — Dashboard + Danh sách văn bản.
 *
 * Gồm:
 *   1. Dashboard cards: VB mới tuần, chưa đọc, khẩn, sắp hết hạn, quiz chưa làm
 *   2. Quick actions: Chưa đọc, Quản lý (nếu có quyền), Báo cáo
 *   3. Bộ lọc (VanBanFilters) + danh sách VB (VanBanCard)
 *   4. Phân trang
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/stores/useAuthStore';
import { legalService } from '@/services/legal';
import { VanBanCard } from '@/components/legal/VanBanCard';
import { VanBanFilters, DEFAULT_FILTERS } from '@/components/legal/VanBanFilters';
import type {
  IVanBanListItem,
  ILoaiVanBan,
  IDashboardSummary,
  IPagination,
} from '@/types/legal';
import type { LegalFilterState } from '@/components/legal/VanBanFilters';

// =============================================================================
// STAT CARD
// =============================================================================
function StatCard({
  icon, label, value, color, href,
}: {
  icon: string; label: string; value: number; color: string; href?: string;
}) {
  const colorMap: Record<string, string> = {
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    red:    'bg-red-50    text-red-700    border-red-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    blue:   'bg-blue-50   text-blue-700   border-blue-200',
  };
  const inner = (
    <div className={`${colorMap[color] ?? colorMap.purple} rounded-xl border p-4 ${href ? 'hover:shadow-md transition-shadow cursor-pointer' : ''}`}>
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-xs opacity-70 mt-0.5">{label}</div>
        </div>
      </div>
    </div>
  );
  if (href) return <Link href={href}>{inner}</Link>;
  return inner;
}

// =============================================================================
// SKELETON
// =============================================================================
function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" />
      <div className="h-3 bg-gray-200 rounded w-full mb-2" />
      <div className="h-3 bg-gray-200 rounded w-3/4" />
    </div>
  );
}

// =============================================================================
// MAIN PAGE
// =============================================================================
export default function PhapLuatPage() {
  const user = useAuthStore(s => s.user);

  // Platform roles (chưa có trong JWT, dùng as any để tương thích tương lai)
  const platformRoles: string[] = (user as unknown as { platform_roles?: string[] })?.platform_roles ?? [];
  const coQuyenQuanLy =
    user?.is_system_admin === true ||
    platformRoles.includes('BIEN_TAP') ||
    platformRoles.includes('QT_NOI_DUNG');
  const coQuyenBaoCao =
    coQuyenQuanLy || user?.is_lanh_dao === true;

  // Data state
  const [dashboard, setDashboard] = useState<IDashboardSummary | null>(null);
  const [vanBans, setVanBans] = useState<IVanBanListItem[]>([]);
  const [loaiVanBans, setLoaiVanBans] = useState<ILoaiVanBan[]>([]);
  const [pagination, setPagination] = useState<IPagination>({
    page: 1, page_size: 12, total_items: 0, total_pages: 1,
  });
  const [filters, setFilters] = useState<LegalFilterState>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [listLoading, setListLoading] = useState(false);
  const [error, setError] = useState('');

  // Load danh sách văn bản (gọi lại khi filter/page thay đổi)
  const loadVanBan = useCallback(async (f: LegalFilterState, p: number) => {
    setListLoading(true);
    try {
      const res = await legalService.getVanBan({
        search: f.search || undefined,
        loai_van_ban_id: f.loaiVanBanId || undefined,
        trang_thai_hieu_luc: f.trangThaiHieuLuc || undefined,
        muc_do: f.mucDo || undefined,
        sap_xep: (f.sapXep as 'moi_nhat' | 'quan_trong') || 'moi_nhat',
        page: p,
        page_size: 12,
      });
      // Kiểm tra success field theo SHARED_CODING_STANDARDS §5.1
      if (res.data?.success) {
        setVanBans(res.data.data ?? []);
        setPagination(res.data.pagination ?? { page: p, page_size: 12, total_items: 0, total_pages: 1 });
      } else {
        // API trả về success: false — giữ list rỗng, không chặn UI
        console.warn('[Legal] getVanBan:', res.data?.error?.code, res.data?.error?.message);
      }
    } catch {
      // Nếu backend chưa online, giữ list rỗng
    } finally {
      setListLoading(false);
    }
  }, []);

  // Load lần đầu
  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const [dashRes, loaiRes] = await Promise.all([
          legalService.getDashboard(),
          legalService.getLoaiVanBan(),
        ]);
        // Kiểm tra success field theo SHARED_CODING_STANDARDS §5.1
        if (dashRes.data?.success) {
          setDashboard(dashRes.data.data);
        } else {
          console.warn('[Legal] getDashboard:', dashRes.data?.error?.code, dashRes.data?.error?.message);
        }
        if (loaiRes.data?.success) {
          setLoaiVanBans(loaiRes.data.data ?? []);
        } else {
          console.warn('[Legal] getLoaiVanBan:', loaiRes.data?.error?.code, loaiRes.data?.error?.message);
        }
      } catch {
        // Không lộ thông tin kỹ thuật (port, service name) cho end user
        setError('Không thể tải dữ liệu. Vui lòng thử lại sau.');
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  // Load danh sách khi filter/page thay đổi
  useEffect(() => {
    loadVanBan(filters, page);
  }, [filters, page, loadVanBan]);

  const handleFilterChange = (f: LegalFilterState) => {
    setFilters(f);
    setPage(1); // Reset về trang 1 khi đổi filter
  };

  // =============================================================================
  // LOADING SKELETON
  // =============================================================================
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="h-7 bg-gray-200 rounded w-48 mb-6 animate-pulse" />
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="bg-gray-200 rounded-xl h-20 animate-pulse" />
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        </div>
      </div>
    );
  }

  // =============================================================================
  // RENDER
  // =============================================================================
  const d = dashboard;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">⚖️ Phổ biến pháp luật</h1>
          <p className="text-sm text-gray-500 mt-1">Văn bản pháp luật liên quan đến công tác hải quan</p>
        </div>

        {/* Thông báo lỗi kết nối (không chặn UI) */}
        {error && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-xl text-sm text-yellow-800 flex items-center gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Dashboard Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <StatCard icon="📄" label="VB mới tuần này" value={d?.vb_moi_tuan ?? 0} color="purple" />
          <StatCard icon="📬" label="Chưa đọc" value={d?.vb_chua_doc ?? 0} color="blue" href="/phap-luat/chua-doc" />
          <StatCard icon="🚨" label="Khẩn/Rất khẩn" value={d?.vb_khan ?? 0} color="red" />
          <StatCard icon="⏰" label="Sắp hết hạn" value={d?.vb_sap_het_han ?? 0} color="orange" />
          <StatCard icon="📝" label="Quiz chưa làm" value={d?.quiz_chua_lam ?? 0} color="yellow" />
        </div>

        {/* Tab Navigation — "Tất cả VB" luôn active khi đang ở trang này */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-5 overflow-x-auto">
          <div className="flex min-w-max">
            {/* Tab: Tất cả VB — ACTIVE (đây là trang hiện tại) */}
            <div
              className="flex items-center gap-2 px-5 py-3 border-b-2 border-purple-600 text-purple-700 font-semibold text-sm whitespace-nowrap select-none"
            >
              <span>📚</span>
              <span>Tất cả VB</span>
              {pagination.total_items > 0 && (
                <span className="ml-1 text-xs bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded-full">
                  {pagination.total_items}
                </span>
              )}
            </div>

            {/* Tab: Cần xác nhận */}
            <Link
              href="/phap-luat/chua-doc"
              className="flex items-center gap-2 px-5 py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300 font-medium text-sm whitespace-nowrap transition-colors"
            >
              <span>📬</span>
              <span>Cần xác nhận</span>
              {(d?.vb_chua_doc ?? 0) > 0 && (
                <span className="ml-1 text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded-full">
                  {d!.vb_chua_doc}
                </span>
              )}
            </Link>

            {/* Tab: Quản lý VB (chỉ hiện khi có quyền) */}
            {coQuyenQuanLy && (
              <Link
                href="/phap-luat/quan-ly"
                className="flex items-center gap-2 px-5 py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300 font-medium text-sm whitespace-nowrap transition-colors"
              >
                <span>⚙️</span>
                <span>Quản lý VB</span>
              </Link>
            )}

            {/* Tab: Báo cáo (chỉ hiện khi có quyền) */}
            {coQuyenBaoCao && (
              <Link
                href="/phap-luat/bao-cao"
                className="flex items-center gap-2 px-5 py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300 font-medium text-sm whitespace-nowrap transition-colors"
              >
                <span>📊</span>
                <span>Báo cáo</span>
              </Link>
            )}
          </div>
        </div>

        {/* Bộ lọc */}
        <div className="mb-4">
          <VanBanFilters
            loaiVanBans={loaiVanBans}
            filters={filters}
            onFilterChange={handleFilterChange}
          />
        </div>

        {/* Danh sách văn bản */}
        {listLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : vanBans.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <span className="text-5xl block mb-4">📭</span>
            <p className="text-gray-500 font-medium">Chưa có văn bản nào</p>
            <p className="text-gray-400 text-sm mt-1">
              {error ? 'Backend chưa kết nối được' : 'Thử thay đổi bộ lọc hoặc tìm kiếm khác'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {vanBans.map(vb => (
              <VanBanCard key={vb.id} vb={vb} />
            ))}
          </div>
        )}

        {/* Phân trang */}
        {pagination.total_pages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50 transition-colors"
            >
              ← Trước
            </button>

            {Array.from({ length: pagination.total_pages }, (_, i) => i + 1)
              .filter(p => Math.abs(p - page) <= 2 || p === 1 || p === pagination.total_pages)
              .map((p, idx, arr) => (
                <span key={p}>
                  {idx > 0 && arr[idx - 1] !== p - 1 && (
                    <span className="px-1 text-gray-400">...</span>
                  )}
                  <button
                    onClick={() => setPage(p)}
                    className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                      p === page
                        ? 'bg-purple-600 text-white border-purple-600'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    {p}
                  </button>
                </span>
              ))}

            <button
              onClick={() => setPage(p => Math.min(pagination.total_pages, p + 1))}
              disabled={page >= pagination.total_pages}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50 transition-colors"
            >
              Sau →
            </button>
          </div>
        )}

        {/* Tổng số VB */}
        {!listLoading && vanBans.length > 0 && (
          <p className="text-center text-xs text-gray-400 mt-4">
            Hiển thị {vanBans.length}/{pagination.total_items} văn bản
          </p>
        )}

      </div>
    </div>
  );
}

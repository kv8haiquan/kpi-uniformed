/**
 * app/(main)/tong-quan/page.tsx
 * ==============================
 * Trang chủ Nền tảng Số Thống nhất — hiển thị 6 widget tóm tắt.
 *
 * Layout (desktop 3 cột → tablet 2 cột → mobile 1 cột):
 *   [KPI]  [ThôngBáo]  [LMS]
 *   [TinTức (span-2)]  [Pháp Luật]
 *   [DiễnĐàn]
 *
 * Dữ liệu: Promise.allSettled (song song) — mỗi widget tự fallback nếu API lỗi.
 * Auto-refresh: mỗi 5 phút.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useCurrentUser } from '@/stores/useAuthStore';

import {
  fetchKPISummary,
  fetchThongBaoCount,
  fetchLMSSummary,
  fetchPortalSummary,
  fetchLegalSummary,
  fetchForumSummary,
  fetchHKGSummary,
} from '@/lib/dashboard-api';

import type {
  IKPIDashboardSummary,
  IThongBaoCount,
  ILMSDashboardSummary,
  IPortalDashboardSummary,
  ILegalDashboardSummary,
  IForumDashboardSummary,
  IHKGDashboardSummary,
} from '@/types/portal';

import WidgetKPI from './components/WidgetKPI';
import WidgetThongBao from './components/WidgetThongBao';
import WidgetLMS from './components/WidgetLMS';
import WidgetLMSPheDuyet from './components/WidgetLMSPheDuyet';
import WidgetTinTuc from './components/WidgetTinTuc';
import WidgetLegal from './components/WidgetLegal';
import WidgetForum from './components/WidgetForum';
import WidgetHKG from './components/WidgetHKG';

// =============================================================================
// CONSTANTS
// =============================================================================

const AUTO_REFRESH_MS = 5 * 60 * 1000; // 5 phút

// =============================================================================
// TYPES
// =============================================================================

interface DashboardState {
  kpi: IKPIDashboardSummary | null;
  thongBao: IThongBaoCount | null;
  lms: ILMSDashboardSummary | null;
  portal: IPortalDashboardSummary | null;
  legal: ILegalDashboardSummary | null;
  forum: IForumDashboardSummary | null;
  hkg: IHKGDashboardSummary | null;
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function TongQuanPage() {
  const user = useCurrentUser();

  const [data, setData] = useState<DashboardState>({
    kpi: null,
    thongBao: null,
    lms: null,
    portal: null,
    legal: null,
    forum: null,
    hkg: null,
  });
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // ---------------------------------------------------------------------------
  // Fetch tất cả widget song song
  // ---------------------------------------------------------------------------

  const fetchAll = useCallback(async () => {
    setLoading(true);

    const [kpiRes, thongBaoRes, lmsRes, portalRes, legalRes, forumRes, hkgRes] =
      await Promise.allSettled([
        fetchKPISummary(),
        fetchThongBaoCount(),
        fetchLMSSummary(),
        fetchPortalSummary(),
        fetchLegalSummary(),
        fetchForumSummary(),
        fetchHKGSummary(),
      ]);

    setData({
      kpi:      kpiRes.status      === 'fulfilled' ? kpiRes.value      : null,
      thongBao: thongBaoRes.status === 'fulfilled' ? thongBaoRes.value : null,
      lms:      lmsRes.status      === 'fulfilled' ? lmsRes.value      : null,
      portal:   portalRes.status   === 'fulfilled' ? portalRes.value   : null,
      legal:    legalRes.status    === 'fulfilled' ? legalRes.value    : null,
      forum:    forumRes.status    === 'fulfilled' ? forumRes.value    : null,
      hkg:      hkgRes.status      === 'fulfilled' ? hkgRes.value      : null,
    });

    setLastUpdated(new Date());
    setLoading(false);
  }, []);

  // ---------------------------------------------------------------------------
  // Khởi tạo + auto-refresh
  // ---------------------------------------------------------------------------

  useEffect(() => {
    fetchAll();
    const timer = setInterval(fetchAll, AUTO_REFRESH_MS);
    return () => clearInterval(timer);
  }, [fetchAll]);

  // ---------------------------------------------------------------------------
  // Greeting
  // ---------------------------------------------------------------------------

  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return 'Chào buổi sáng';
    if (h < 18) return 'Chào buổi chiều';
    return 'Chào buổi tối';
  })();

  const formatLastUpdated = (d: Date): string => {
    return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  };

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">

        {/* ------------------------------------------------------------------ */}
        {/* Header                                                               */}
        {/* ------------------------------------------------------------------ */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              {greeting}{user?.ho_ten ? `, ${user.ho_ten.split(' ').slice(-1)[0]}` : ''}!
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {user?.don_vi?.ten_don_vi
                ? `${user.don_vi.ten_don_vi} — `
                : ''}
              Nền tảng Số Thống nhất Hải quan KV8
            </p>
          </div>

          {/* Refresh button + timestamp */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {lastUpdated && (
              <span className="text-xs text-gray-400 hidden sm:block">
                Cập nhật lúc {formatLastUpdated(lastUpdated)}
              </span>
            )}
            <button
              onClick={fetchAll}
              disabled={loading}
              className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 bg-white border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Làm mới dữ liệu"
            >
              <svg
                className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              {loading ? 'Đang tải...' : 'Làm mới'}
            </button>
          </div>
        </div>

        {/* ------------------------------------------------------------------ */}
        {/* Widget Grid                                                          */}
        {/* ------------------------------------------------------------------ */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

          {/* Cảnh báo phê duyệt LMS — full-width, chỉ hiện khi có yêu cầu */}
          <WidgetLMSPheDuyet count={data.lms?.cho_phe_duyet ?? 0} />

          {/* Hàng 1: KPI | Thông báo | LMS */}
          <WidgetKPI      data={data.kpi}      loading={loading} />
          <WidgetThongBao data={data.thongBao} loading={loading} />
          <WidgetLMS      data={data.lms}      loading={loading} />

          {/* Hàng 2: Tin tức (2 cột) | Pháp luật (1 cột) */}
          <WidgetTinTuc   data={data.portal}   loading={loading} />
          <WidgetLegal    data={data.legal}    loading={loading} />

          {/* Hàng 3: Diễn đàn | Họp không giấy */}
          <WidgetForum    data={data.forum}    loading={loading} />
          <WidgetHKG      data={data.hkg}      loading={loading} />

        </div>

        {/* ------------------------------------------------------------------ */}
        {/* Footer                                                               */}
        {/* ------------------------------------------------------------------ */}
        <p className="text-center text-xs text-gray-300 mt-8">
          Tự động làm mới mỗi 5 phút
          {lastUpdated && ` · Lần cuối ${formatLastUpdated(lastUpdated)}`}
        </p>

      </div>
    </div>
  );
}

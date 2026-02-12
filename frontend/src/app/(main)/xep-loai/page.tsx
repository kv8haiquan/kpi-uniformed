/**
 * src/app/(main)/xep-loai/page.tsx
 * =================================
 * Trang "Phê duyệt" thống nhất với 5 tabs quản lý.
 * 
 * Version: 3.3.3 - REMOVED DDE TAB (30/01/2026)
 */

'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';

import {
  TabId,
  IPendingCounts,
  TABS_CONFIG,
  getCapBacFromUser,
  getAccessibleTabs,
  canViewAllUnits,
  CapBacVaiTro,
  canApproveInTab,
  getCapBacLabel,
  createDefaultPendingCounts,
} from '@/types/xep-loai';

import { MonthYearSelector, TabBadge, ViewOnlyBadge } from '@/components/xep-loai/shared';
import { TabCongViec, TabTieuChi, TabDanhGiaLD, TabNghiPhep, TabBaoCao } from '@/components/xep-loai/tabs';

const Icons = {
  back: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
    </svg>
  ),
  eye: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  ),
  warning: (
    <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
};

export default function XepLoaiPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated } = useAuthStore();

  const urlTab = searchParams.get('tab') as TabId | null;
  const currentDate = new Date();
  const [selectedThang, setSelectedThang] = useState(currentDate.getMonth() + 1);
  const [selectedNam, setSelectedNam] = useState(currentDate.getFullYear());
  const [pendingCounts, setPendingCounts] = useState<IPendingCounts>(createDefaultPendingCounts());

  const capBac = getCapBacFromUser(user);
  const accessibleTabs = useMemo(() => getAccessibleTabs(capBac, user), [capBac, user]);
  const activeTab = useMemo(() => {
    if (urlTab && accessibleTabs.find((t) => t.id === urlTab)) return urlTab;
    return accessibleTabs[0]?.id || 'cong-viec';
  }, [urlTab, accessibleTabs]);
  const activeTabConfig = useMemo(() => TABS_CONFIG.find((t) => t.id === activeTab) || TABS_CONFIG[0], [activeTab]);
  const canApproveActiveTab = useMemo(() => {
    // v1.1.0: User có can_view_all_units nhưng là CC → KHÔNG được phê duyệt
    if (user && user.can_view_all_units && capBac === CapBacVaiTro.CONG_CHUC) return false;
    return canApproveInTab(capBac, activeTabConfig);
  }, [capBac, activeTabConfig, user]);

  useEffect(() => {
    if (!isAuthenticated) router.push('/login');
  }, [isAuthenticated, router]);

  const handleTabChange = useCallback((tabId: TabId) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('tab', tabId);
    router.push(`/xep-loai?${params.toString()}`);
  }, [router, searchParams]);

  const handlePendingCountChange = useCallback((tabId: TabId, count: number) => {
    setPendingCounts((prev) => {
      if (prev[tabId] === count) return prev;
      return { ...prev, [tabId]: count };
    });
  }, []);

  // Tạo stable callbacks cho từng tab
  const onCongViecCountChange = useCallback((count: number) => handlePendingCountChange('cong-viec', count), [handlePendingCountChange]);
  const onTieuChiCountChange = useCallback((count: number) => handlePendingCountChange('tieu-chi', count), [handlePendingCountChange]);
  const onDanhGiaLDCountChange = useCallback((count: number) => handlePendingCountChange('danh-gia-ld', count), [handlePendingCountChange]);
  const onNghiPhepCountChange = useCallback((count: number) => handlePendingCountChange('nghi-phep', count), [handlePendingCountChange]);
  const onBaoCaoCountChange = useCallback((count: number) => handlePendingCountChange('bao-cao', count), [handlePendingCountChange]);

  if (accessibleTabs.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 text-center max-w-md shadow-sm">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">{Icons.warning}</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Không có quyền truy cập</h2>
          <p className="text-gray-600 mb-4">Trang này chỉ dành cho lãnh đạo (Phó ĐT, ĐT, Phó CCT, CCT).</p>
          <button onClick={() => router.push('/dashboard')} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">Về Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <button onClick={() => router.push('/dashboard')} className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">{Icons.back}</button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">📋 Phê duyệt</h1>
                <p className="text-sm text-gray-500">{getCapBacLabel(capBac)} • {user?.don_vi?.ten_don_vi || 'Chi cục'}</p>
              </div>
            </div>
            <MonthYearSelector thang={selectedThang} nam={selectedNam} onThangChange={setSelectedThang} onNamChange={setSelectedNam} />
          </div>

          <div className="flex gap-1 -mb-px overflow-x-auto pb-px">
            {accessibleTabs.map((tab) => {
              const isActive = tab.id === activeTab;
              const canApprove = canApproveInTab(capBac, tab);
              const pendingCount = pendingCounts[tab.id];
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${isActive ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
                >
                  <span className={isActive ? 'text-blue-600' : 'text-gray-400'}>{tab.icon}</span>
                  <span className="hidden sm:inline">{tab.label}</span>
                  <span className="sm:hidden">{tab.shortLabel}</span>
                  <TabBadge count={pendingCount} />
                  {!canApprove && <span className="text-gray-400">{Icons.eye}</span>}
                </button>
              );
            })}
          </div>
        </div>
      </header>

      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">{activeTabConfig.label}</h2>
              <p className="text-blue-100 text-sm">{activeTabConfig.description}</p>
            </div>
            {!canApproveActiveTab && <ViewOnlyBadge />}
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'cong-viec' && <TabCongViec thang={selectedThang} nam={selectedNam} canApprove={canApproveActiveTab} capBac={capBac} onPendingCountChange={onCongViecCountChange} />}
        {activeTab === 'tieu-chi' && <TabTieuChi thang={selectedThang} nam={selectedNam} canApprove={canApproveActiveTab} capBac={capBac} onPendingCountChange={onTieuChiCountChange} />}
        {activeTab === 'danh-gia-ld' && <TabDanhGiaLD thang={selectedThang} nam={selectedNam} canApprove={canApproveActiveTab} capBac={capBac} onPendingCountChange={onDanhGiaLDCountChange} />}
        {activeTab === 'nghi-phep' && <TabNghiPhep thang={selectedThang} nam={selectedNam} canApprove={canApproveActiveTab} capBac={capBac} onPendingCountChange={onNghiPhepCountChange} />}
        {activeTab === 'bao-cao' && <TabBaoCao thang={selectedThang} nam={selectedNam} canApprove={canApproveActiveTab} capBac={capBac} onPendingCountChange={onBaoCaoCountChange} />}
      </main>

      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <p>💡 Sử dụng bộ lọc trạng thái để xem nhanh các mục cần xử lý</p>
            <p>Deadline xếp loại: <strong className="text-amber-600">Ngày 10 hàng tháng</strong></p>
          </div>
        </div>
      </footer>
    </div>
  );
}
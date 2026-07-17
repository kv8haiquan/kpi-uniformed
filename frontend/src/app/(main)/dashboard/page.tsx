/**
 * src/app/(main)/dashboard/page.tsx
 * ==================================
 * Trang Dashboard - Landing page sau khi đăng nhập.
 * 
 * CẤU TRÚC v3.5.0:
 * - Admin: CHỈ thấy Section Quản trị hệ thống
 * - User thường: Công việc của tôi, Quản lý đơn vị, Phê duyệt, Widgets
 *
 * Version: 3.5.0 (30/01/2026)
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore, useCurrentUser, useIsLanhDao } from '@/stores/useAuthStore';
import { getUserDisplayName, isLanhDaoDonVi } from '@/types/auth';
import { kpiService, IPendingStats } from '@/services/kpi.service';
import { tieuChiChungService } from '@/services/tieu-chi-chung.service';
import { baoCaoXepLoaiService } from '@/services/bao-cao-xep-loai.service';
import { adminService } from '@/services/admin.service';
import { thongBaoApi } from '@/services/common';
import { dieuChinhKqcvService } from '@/services/dieuChinhKqcv.service';
import {
  IKetQuaTieuChiChungResponse,
  TrangThaiTieuChiChung,
} from '@/types/tieu-chi-chung';
import { IAdminStats } from '@/types/admin';
import WidgetPhanCongPhuTrach from '@/components/dashboard/WidgetPhanCongPhuTrach';
import RecentTransfersWidget from '@/components/dashboard/RecentTransfersWidget';
import hdldService from '@/services/hdld.service';
import { isHdldVb714Active } from '@/types/hdld';
import VinhDanhWidget from '@/components/dashboard/VinhDanhWidget';

import { formatScore } from '@/lib/format';
// =============================================================================
// TYPES
// =============================================================================

interface QuickActionCardProps {
  icon: string;
  title: string;
  description: string;
  href: string;
  color: 'blue' | 'green' | 'yellow' | 'purple' | 'red' | 'orange' | 'indigo' | 'pink' | 'cyan';
  badge?: number;
  size?: 'normal' | 'large';
  viewOnly?: boolean;
}

interface SectionHeaderProps {
  icon: string;
  title: string;
  subtitle?: string;
}

// =============================================================================
// SUB COMPONENTS
// =============================================================================

function SectionHeader({ icon, title, subtitle }: SectionHeaderProps) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2">
        <span className="text-xl">{icon}</span>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      {subtitle && <p className="text-sm text-gray-500 mt-1 ml-7">{subtitle}</p>}
    </div>
  );
}

function QuickActionCard({ icon, title, description, href, color, badge, size = 'normal', viewOnly }: QuickActionCardProps) {
  const router = useRouter();
  
  const colorClasses: Record<string, { bg: string; hover: string; icon: string }> = {
    blue: { bg: 'bg-blue-50', hover: 'hover:bg-blue-100 hover:border-blue-300', icon: 'bg-blue-100' },
    green: { bg: 'bg-green-50', hover: 'hover:bg-green-100 hover:border-green-300', icon: 'bg-green-100' },
    yellow: { bg: 'bg-yellow-50', hover: 'hover:bg-yellow-100 hover:border-yellow-300', icon: 'bg-yellow-100' },
    purple: { bg: 'bg-purple-50', hover: 'hover:bg-purple-100 hover:border-purple-300', icon: 'bg-purple-100' },
    red: { bg: 'bg-red-50', hover: 'hover:bg-red-100 hover:border-red-300', icon: 'bg-red-100' },
    orange: { bg: 'bg-orange-50', hover: 'hover:bg-orange-100 hover:border-orange-300', icon: 'bg-orange-100' },
    indigo: { bg: 'bg-indigo-50', hover: 'hover:bg-indigo-100 hover:border-indigo-300', icon: 'bg-indigo-100' },
    pink: { bg: 'bg-pink-50', hover: 'hover:bg-pink-100 hover:border-pink-300', icon: 'bg-pink-100' },
    cyan: { bg: 'bg-cyan-50', hover: 'hover:bg-cyan-100 hover:border-cyan-300', icon: 'bg-cyan-100' },
  };

  const c = colorClasses[color];
  const isLarge = size === 'large';

  return (
    <div
      onClick={() => router.push(href)}
      className={`${c.bg} border border-gray-200 ${c.hover} rounded-xl transition-all cursor-pointer relative group`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') router.push(href); }}
    >
      {badge !== undefined && badge > 0 && (
        <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full min-w-[24px] h-6 flex items-center justify-center px-1.5 shadow-lg animate-pulse">
          {badge > 99 ? '99+' : badge}
        </div>
      )}
      {viewOnly && (
        <div className="absolute top-2 right-2 bg-gray-500 text-white text-[10px] font-medium rounded px-1.5 py-0.5">
          Chỉ xem
        </div>
      )}
      <div className={`${isLarge ? 'p-5' : 'p-4'} flex items-center gap-4`}>
        <div className={`${isLarge ? 'w-14 h-14' : 'w-12 h-12'} ${c.icon} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm`}>
          <span className={`${isLarge ? 'text-2xl' : 'text-xl'}`}>{icon}</span>
        </div>
        <div className="flex-1 min-w-0">
          <h4 className={`font-medium text-gray-900 ${isLarge ? 'text-base' : 'text-sm'}`}>{title}</h4>
          <p className={`text-gray-500 truncate ${isLarge ? 'text-sm mt-1' : 'text-xs mt-0.5'}`}>{description}</p>
        </div>
        <svg className="w-5 h-5 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-1 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </div>
  );
}

function TieuChiChungWidget({ 
  tieuChiChung, 
  isLoading, 
  currentMonth, 
  currentYear, 
  onNavigate 
}: {
  tieuChiChung: IKetQuaTieuChiChungResponse | null;
  isLoading: boolean;
  currentMonth: number;
  currentYear: number;
  onNavigate: () => void;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  const isNew = !tieuChiChung || tieuChiChung.is_new_record;
  
  if (isNew) {
    return (
      <div className="text-center py-6">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">⚠️</span>
        </div>
        <h4 className="font-medium text-gray-900 mb-1">Chưa tự chấm điểm</h4>
        <p className="text-sm text-gray-500 mb-4">Tháng {currentMonth} chưa có bản tự đánh giá</p>
        <button
          onClick={onNavigate}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          Bắt đầu ngay
        </button>
      </div>
    );
  }

  const diem = tieuChiChung.tong_hop?.tong_diem ?? 0;
  const trangThai = tieuChiChung.trang_thai;

  const statusConfig: Record<string, { bg: string; text: string; label: string; btnBg: string }> = {
    [TrangThaiTieuChiChung.NHAP]: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Đang soạn', btnBg: 'bg-yellow-600 hover:bg-yellow-700' },
    [TrangThaiTieuChiChung.CHO_PHE_DUYET]: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Chờ duyệt', btnBg: 'bg-blue-600 hover:bg-blue-700' },
    [TrangThaiTieuChiChung.DA_PHE_DUYET]: { bg: 'bg-green-100', text: 'text-green-700', label: 'Đã duyệt', btnBg: 'bg-green-600 hover:bg-green-700' },
  };

  const config = statusConfig[trangThai] || statusConfig[TrangThaiTieuChiChung.NHAP];

  return (
    <div className="text-center py-4">
      <div className="flex items-center justify-center gap-3 mb-4">
        <div className="text-4xl font-bold text-gray-900">{formatScore(diem)}</div>
        <div className="text-left">
          <div className="text-sm text-gray-500">/ 30 điểm</div>
          <span className={`px-2 py-0.5 ${config.bg} ${config.text} text-xs rounded-full font-medium`}>
            {config.label}
          </span>
        </div>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div 
          className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full transition-all" 
          style={{ width: `${Math.min((diem / 30) * 100, 100)}%` }} 
        />
      </div>
      <button
        onClick={onNavigate}
        className={`px-4 py-2 ${config.btnBg} text-white rounded-lg text-sm font-medium transition-colors`}
      >
        {trangThai === TrangThaiTieuChiChung.DA_PHE_DUYET ? 'Xem chi tiết' : 'Tiếp tục'}
      </button>
    </div>
  );
}

function PheDuyetOverviewWidget({
  pendingSanPham,
  pendingTieuChi,
  pendingXepLoai,
  isLoading,
}: {
  pendingSanPham: number;
  pendingTieuChi: number;
  pendingXepLoai: number;
  isLoading: boolean;
}) {
  const router = useRouter();
  const total = pendingSanPham + pendingTieuChi + pendingXepLoai;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600" />
      </div>
    );
  }

  if (total === 0) {
    return (
      <div className="text-center py-6">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">✅</span>
        </div>
        <h4 className="font-medium text-gray-900 mb-1">Đã xử lý hết</h4>
        <p className="text-sm text-gray-500">Không có đơn nào chờ phê duyệt</p>
      </div>
    );
  }

  const items = [
    { label: 'Công việc', count: pendingSanPham, href: '/xep-loai?tab=cong-viec', color: 'bg-yellow-500' },
    { label: 'Tiêu chí chung', count: pendingTieuChi, href: '/xep-loai?tab=tieu-chi', color: 'bg-orange-500' },
    { label: 'Xếp loại', count: pendingXepLoai, href: '/xep-loai?tab=bao-cao', color: 'bg-pink-500' },
  ];

  return (
    <div className="py-2">
      <div className="text-center mb-4">
        <div className="text-4xl font-bold text-gray-900">{total}</div>
        <div className="text-sm text-gray-500">đơn chờ phê duyệt</div>
      </div>
      <div className="space-y-2">
        {items.map((item) => (
          <div 
            key={item.label}
            onClick={() => item.count > 0 && router.push(item.href)}
            className={`flex items-center justify-between p-3 rounded-lg ${
              item.count > 0 ? 'bg-gray-50 hover:bg-gray-100 cursor-pointer' : 'bg-gray-50 opacity-50'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 ${item.color} rounded-full`} />
              <span className="text-sm text-gray-700">{item.label}</span>
            </div>
            <span className={`text-sm font-semibold ${item.count > 0 ? 'text-gray-900' : 'text-gray-400'}`}>
              {item.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// ADMIN STATS WIDGET
// =============================================================================

function AdminStatsWidget({ 
  stats, 
  isLoading,
  error,
}: { 
  stats: IAdminStats | null;
  isLoading: boolean;
  error?: string | null;
}) {
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {[1,2,3,4,5,6].map(i => (
          <div key={i} className="bg-gray-100 rounded-lg p-4 animate-pulse h-20" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-6">
        <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
          <span className="text-xl">⚠️</span>
        </div>
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-6">
        <p className="text-sm text-gray-500">Không có dữ liệu</p>
      </div>
    );
  }

  const items = [
    { label: 'Tổng người dùng', value: stats.tong_user ?? 0, icon: '👥', color: 'blue', href: '/admin/users' },
    { label: 'Đang hoạt động', value: stats.user_active ?? 0, icon: '✅', color: 'green', href: '/admin/users?status=active' },
    { label: 'Đã vô hiệu', value: stats.user_inactive ?? 0, icon: '🚫', color: 'red', href: '/admin/users?status=inactive' },
    { label: 'Đơn vị', value: stats.tong_don_vi ?? 0, icon: '🏢', color: 'purple', href: '/admin' },
    { label: 'SP Chuẩn', value: stats.tong_sp_chuan ?? 0, icon: '📦', color: 'orange', href: '/admin/sp-chuan' },
    { label: 'Danh mục CV', value: stats.tong_danh_muc_cv ?? 0, icon: '📋', color: 'cyan', href: '/admin/danh-muc-cv' },
  ];

  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
    green: 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100',
    red: 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100',
    purple: 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100',
    orange: 'bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100',
    cyan: 'bg-cyan-50 text-cyan-700 border-cyan-200 hover:bg-cyan-100',
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      {items.map((item, idx) => (
        <div 
          key={idx} 
          onClick={() => router.push(item.href)}
          className={`${colorMap[item.color]} rounded-lg p-4 border cursor-pointer transition-colors`}
        >
          <div className="flex items-center gap-2">
            <span className="text-xl">{item.icon}</span>
            <span className="text-3xl font-bold">{item.value}</span>
          </div>
          <p className="text-xs mt-1 opacity-80">{item.label}</p>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function DashboardPage() {
  const router = useRouter();
  const { logout } = useAuthStore();
  const user = useCurrentUser();
  const isLanhDao = useIsLanhDao();

  // Check if user is admin
  const isAdmin = user?.is_system_admin === true;

  // States for non-admin users
  const [pendingStats, setPendingStats] = useState<IPendingStats | null>(null);
  const [tieuChiChung, setTieuChiChung] = useState<IKetQuaTieuChiChungResponse | null>(null);
  const [isLoadingTC, setIsLoadingTC] = useState(true);
  const [pendingTCCount, setPendingTCCount] = useState(0);
  const [pendingXepLoaiCount, setPendingXepLoaiCount] = useState(0);
  const [pendingDCKqcvCount, setPendingDCKqcvCount] = useState(0);
  const [pendingHdldCount, setPendingHdldCount] = useState(0);
  const [isLoadingPending, setIsLoadingPending] = useState(true);
  
  // Thong bao
  const [thongBaoList, setThongBaoList] = useState<any[]>([]);
  const [thongBaoChuaDoc, setThongBaoChuaDoc] = useState(0);
  const [isLoadingTB, setIsLoadingTB] = useState(true);

  // Admin stats
  const [adminStats, setAdminStats] = useState<IAdminStats | null>(null);
  const [isLoadingAdminStats, setIsLoadingAdminStats] = useState(false);
  const [adminStatsError, setAdminStatsError] = useState<string | null>(null);

  const currentDate = new Date();
  const currentMonth = currentDate.getMonth() + 1;
  const currentYear = currentDate.getFullYear();

  // Computed permissions (for non-admin)
  const maVaiTro = user?.vai_tro?.ma_vai_tro;
  const isPhoDT = maVaiTro === 'PDV';
  const isDoiTruong = maVaiTro === 'TDV';
  const isCCT = maVaiTro === 'CCT';
  const isPhoCCT = maVaiTro === 'PCCT';
  const hasViewAll = user?.can_view_all_units === true;
  
  const canViewManageUnit = isPhoDT || isDoiTruong || isCCT || hasViewAll;
  const canEditManageUnit = isDoiTruong || isCCT;
  const canViewStats = isCCT || isPhoCCT || hasViewAll;
  const canViewChiCuc = isCCT || hasViewAll;
  const canApproveXepLoai = isCCT;

  // Load data for non-admin users only
  useEffect(() => {
    if (isAdmin) return;
    const loadTieuChiChung = async () => {
      setIsLoadingTC(true);
      try {
        const result = await tieuChiChungService.getKetQuaThang(currentMonth, currentYear);
        setTieuChiChung(result);
      } catch (error) {
        console.error('Failed to load tieu chi chung:', error);
        setTieuChiChung(null);
      } finally {
        setIsLoadingTC(false);
      }
    };
    loadTieuChiChung();
  }, [currentMonth, currentYear, isAdmin]);

  useEffect(() => {
    if (isAdmin) return;
    if (isLanhDao) {
      setIsLoadingPending(true);
      // HĐLĐ 111 VB714: chỉ TDV/PDV duyệt, chỉ tính từ T5/2026
      const loadHdld = (isDoiTruong || isPhoDT) && isHdldVb714Active(currentMonth, currentYear)
        ? hdldService.getChoDuyet(currentMonth, currentYear).catch(() => [])
        : Promise.resolve([]);
      Promise.all([
        kpiService.getPendingStats().catch(() => null),
        tieuChiChungService.getChoPheyet(1, 1).catch(() => ({ total: 0 })),
        canApproveXepLoai ? baoCaoXepLoaiService.getChoPeDuyet().catch(() => []) : Promise.resolve([]),
        dieuChinhKqcvService.listChoToiDuyet().catch(() => []),
        loadHdld,
      ]).then(([stats, tcResult, xepLoaiList, dcList, hdldList]) => {
        setPendingStats(stats);
        setPendingTCCount(tcResult?.total || 0);
        setPendingXepLoaiCount(Array.isArray(xepLoaiList) ? xepLoaiList.length : 0);
        setPendingDCKqcvCount(Array.isArray(dcList) ? dcList.length : 0);
        setPendingHdldCount(Array.isArray(hdldList) ? hdldList.length : 0);
      }).finally(() => {
        setIsLoadingPending(false);
      });
    }
  }, [isLanhDao, canApproveXepLoai, isAdmin, isDoiTruong, isPhoDT, currentMonth, currentYear]);

  // Load Thong bao
  useEffect(() => {
    if (isAdmin) { setIsLoadingTB(false); return; }
    setIsLoadingTB(true);
    Promise.all([
      thongBaoApi.danhSach({ page_size: 5 }).catch(() => null),
      thongBaoApi.demChuaDoc().catch(() => null),
    ]).then(([listRes, countRes]) => {
      if (listRes?.data?.data) setThongBaoList(listRes.data.data);
      if (countRes?.data?.data) setThongBaoChuaDoc(countRes.data.data.count || 0);
    }).finally(() => setIsLoadingTB(false));
  }, [isAdmin]);

  // Load Admin Stats
  useEffect(() => {
    if (isAdmin) {
      setIsLoadingAdminStats(true);
      setAdminStatsError(null);
      adminService.getStats()
        .then((data) => {
          console.log('Admin stats:', data);
          setAdminStats(data);
        })
        .catch((err) => {
          console.error('Failed to load admin stats:', err);
          setAdminStatsError(err?.message || 'Không thể tải thống kê');
        })
        .finally(() => setIsLoadingAdminStats(false));
    }
  }, [isAdmin]);

  const handleLogout = () => { logout(); };

  const getRoleDisplayName = (): string => {
    if (!user) return '';
    if (isAdmin) return 'Quản trị hệ thống';
    if (isCCT) return 'Chi cục trưởng';
    if (isPhoCCT) return 'Phó Chi cục trưởng';
    if (isDoiTruong) return 'Đội trưởng';
    if (isPhoDT) return 'Phó Đội trưởng';
    if (isLanhDaoDonVi(user)) return 'Phó Đội trưởng';
    return 'Công chức';
  };

  const pendingSanPham = pendingStats?.tong_cho_duyet || 0;

  // ==========================================================================
  // RENDER: ADMIN DASHBOARD
  // ==========================================================================
  if (isAdmin) {
    return (
      <div className="min-h-screen bg-gray-100">
        <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-red-600 to-orange-600 rounded-xl flex items-center justify-center shadow-lg">
                  <span className="text-white text-lg">⚙️</span>
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-gray-900">Quản trị KPI</h1>
                  <p className="text-xs text-gray-500">Chi cục Hải quan Khu vực VIII</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <span className="hidden sm:inline-flex px-2.5 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">Admin</span>
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-medium text-gray-900">{getUserDisplayName(user)}</p>
                  <p className="text-xs text-gray-500">Quản trị hệ thống</p>
                </div>
                <button onClick={() => router.push('/ho-so')} className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
                  Hồ sơ
                </button>
                <button onClick={handleLogout} className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
                  Đăng xuất
                </button>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Welcome Card */}
          <div className="bg-gradient-to-r from-red-600 to-orange-600 rounded-2xl shadow-lg mb-6 overflow-hidden">
            <div className="p-6 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-white/20 backdrop-blur rounded-2xl flex items-center justify-center">
                  <span className="text-4xl">⚙️</span>
                </div>
                <div className="text-white">
                  <h2 className="text-xl font-semibold">Xin chào, {user?.ho_ten || 'Admin'}!</h2>
                  <p className="text-white/80 mt-1">Bảng điều khiển quản trị hệ thống</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="px-2.5 py-1 bg-white/20 backdrop-blur rounded-full text-xs font-medium">Quản trị viên</span>
                    <span className="text-white/70 text-sm">
                      {new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Admin Stats */}
          <div className="mb-8">
            <SectionHeader icon="📊" title="Tổng quan hệ thống" subtitle="Thống kê nhanh các chỉ số hệ thống" />
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <AdminStatsWidget stats={adminStats} isLoading={isLoadingAdminStats} error={adminStatsError} />
            </div>
          </div>

          {/* Quick Actions */}
          <div className="mb-8">
            <SectionHeader icon="⚡" title="Quản lý nhanh" subtitle="Truy cập nhanh các chức năng quản trị" />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <QuickActionCard icon="👥" title="Quản lý người dùng" description="Tạo, sửa, phân quyền tài khoản" href="/admin/users" color="blue" size="large" />
              <QuickActionCard icon="📦" title="Sản phẩm Chuẩn" description="Cấu hình SP gốc và hệ số quy đổi" href="/admin/sp-chuan" color="green" size="large" />
              <QuickActionCard icon="📊" title="Cấp độ phức tạp" description="Thiết lập các cấp độ và hệ số" href="/admin/cap-do" color="yellow" size="large" />
              <QuickActionCard icon="📋" title="Danh mục công việc" description="Quản lý danh sách công việc" href="/admin/danh-muc-cv" color="purple" size="large" />
              <QuickActionCard icon="🔄" title="Điều chuyển nhân sự" description="Chuyển đơn vị, đổi vai trò" href="/admin/users" color="orange" size="large" />
              <QuickActionCard icon="🔑" title="Reset mật khẩu" description="Đặt lại mật khẩu người dùng" href="/admin/users" color="red" size="large" />
              <QuickActionCard icon="🏆" title="Vinh danh tháng" description="Quản lý công chức tiêu biểu hàng tháng" href="/admin/vinh-danh" color="indigo" size="large" />
            </div>
          </div>

          {/* Điều chuyển & trạng thái gần đây */}
          <div className="mb-8">
            <SectionHeader icon="🔄" title="Điều chuyển & trạng thái gần đây" subtitle="Hoạt động điều chuyển, vô hiệu hóa, kích hoạt mới nhất toàn cơ quan" />
            <RecentTransfersWidget />
          </div>

          {/* System Info */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-medium text-gray-900 mb-4 flex items-center gap-2">
              <span>ℹ️</span> Thông tin hệ thống
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div><p className="text-gray-500">Phiên bản</p><p className="font-medium text-gray-900">3.5.0</p></div>
              <div><p className="text-gray-500">Người dùng</p><p className="font-medium text-gray-900">{user?.ma_cc || 'ADMIN'}</p></div>
              <div><p className="text-gray-500">Vai trò</p><p className="font-medium text-gray-900">System Admin</p></div>
              <div><p className="text-gray-500">Thời gian</p><p className="font-medium text-gray-900">{new Date().toLocaleTimeString('vi-VN')}</p></div>
            </div>
          </div>

          <div className="mt-8 text-center text-xs text-gray-400">
            <p>Hệ thống Quản lý KPI - Chi cục Hải quan Khu vực VIII</p>
            <p className="mt-1">Phiên bản 3.5.0 • © 2026</p>
          </div>
        </main>
      </div>
    );
  }

  // ==========================================================================
  // RENDER: NORMAL USER DASHBOARD
  // ==========================================================================
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-lg">K</span>
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">Hệ thống KPI</h1>
                <p className="text-xs text-gray-500">Chi cục Hải quan Khu vực VIII</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-gray-900">{getUserDisplayName(user)}</p>
                <p className="text-xs text-gray-500">{getRoleDisplayName()}</p>
              </div>
              <button onClick={() => router.push('/ho-so')} className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
                Hồ sơ
              </button>
              <button onClick={handleLogout} className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
                Đăng xuất
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Welcome Card */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-lg mb-6 overflow-hidden">
          <div className="p-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white/20 backdrop-blur rounded-2xl flex items-center justify-center">
                <span className="text-4xl">👋</span>
              </div>
              <div className="text-white">
                <h2 className="text-xl font-semibold">Xin chào, {user?.ho_ten || 'Người dùng'}!</h2>
                <p className="text-blue-100 mt-1">{user?.don_vi?.ten_don_vi || 'Chi cục Hải quan Khu vực VIII'}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="px-2.5 py-1 bg-white/20 backdrop-blur rounded-full text-xs font-medium">{getRoleDisplayName()}</span>
                  <span className="text-blue-200 text-sm">Tháng {currentMonth}/{currentYear}</span>
                </div>
              </div>
            </div>
            <div className="hidden lg:block text-right text-white">
              <div className="text-3xl font-bold">{new Date().getDate()}</div>
              <div className="text-blue-200 text-sm">{new Date().toLocaleDateString('vi-VN', { weekday: 'long' })}</div>
            </div>
          </div>
        </div>

        {/* WIDGET: Vinh danh công chức tiêu biểu (tự ẩn nếu chưa có vinh danh tháng hiện tại) */}
        <VinhDanhWidget />

        {/* SECTION 1: CÔNG VIỆC CỦA TÔI */}
        <div className="mb-8">
          <SectionHeader icon="📌" title="Công việc của tôi" subtitle="Các tác vụ cá nhân hàng tháng" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <QuickActionCard icon="📝" title="Kê khai công việc" description="Kê khai công việc tháng" href="/ke-khai-v2" color="blue" />
            <QuickActionCard icon="✍️" title="Tự chấm điểm" description="Tiêu chí chung (30đ)" href="/danh-gia/tu-cham-diem" color="purple" />
            <QuickActionCard icon="📊" title="Xem đánh giá" description="Kết quả KPI của bạn" href="/danh-gia-v2" color="green" />
            <QuickActionCard icon="🗓️" title="Nghỉ phép" description="Đăng ký và quản lý" href="/nghi-phep" color="cyan" />
            <QuickActionCard icon="🖨️" title="Theo dõi, đánh giá Quý" description="Phiếu đánh giá & bảng kê công việc" href="/in-bang-ke" color="orange" />
          </div>
        </div>

        {/* SECTION: PHÂN CÔNG PHỤ TRÁCH (chỉ PCCT/CCT — Phase 3+, 05/05/2026) */}
        {(maVaiTro === 'PCCT' || maVaiTro === 'CCT') && (
          <div className="mb-8">
            <WidgetPhanCongPhuTrach visible={true} />
          </div>
        )}

        {/* SECTION 2: PHÊ DUYỆT */}
        {isLanhDao && (
          <div className="mb-8">
            <SectionHeader icon="✅" title="Phê duyệt" subtitle="Xử lý các đơn chờ phê duyệt từ nhân viên" />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <QuickActionCard icon="📦" title="Phê duyệt Công việc" description={pendingSanPham > 0 ? `${pendingSanPham} kê khai chờ duyệt` : 'Duyệt kê khai công việc'} href="/xep-loai?tab=cong-viec" color="yellow" badge={pendingSanPham} size="large" />
              {/* HĐLĐ 111 VB714 (01/06/2026): chỉ TDV/PDV duyệt, chỉ hiện từ T5/2026 */}
              {(isDoiTruong || isPhoDT) && isHdldVb714Active(currentMonth, currentYear) && <QuickActionCard icon="🧰" title="Phê duyệt HĐLĐ" description={pendingHdldCount > 0 ? `${pendingHdldCount} bản chờ duyệt` : 'Duyệt đánh giá HĐLĐ 111'} href="/xep-loai?tab=hdld" color="orange" badge={pendingHdldCount} size="large" />}
              <QuickActionCard icon="🏅" title="Phê duyệt Tiêu chí" description={pendingTCCount > 0 ? `${pendingTCCount} đơn chờ duyệt` : 'Duyệt 30 điểm TC chung'} href="/xep-loai?tab=tieu-chi" color="orange" badge={pendingTCCount} size="large" />
              <QuickActionCard icon="🏖️" title="Phê duyệt Nghỉ phép" description="Duyệt đơn nghỉ phép" href="/xep-loai?tab=nghi-phep" color="cyan" size="large" />
              <QuickActionCard icon="✏️" title="Điều chỉnh KQCV" description={pendingDCKqcvCount > 0 ? `${pendingDCKqcvCount} bản chờ duyệt` : 'Duyệt điều chỉnh KQCV cấp dưới'} href="/dieu-chinh-kqcv" color="indigo" badge={pendingDCKqcvCount} size="large" />
              {canApproveXepLoai && <QuickActionCard icon="📋" title="Phê duyệt Xếp loại" description={pendingXepLoaiCount > 0 ? `${pendingXepLoaiCount} báo cáo chờ duyệt` : 'Duyệt báo cáo xếp loại'} href="/xep-loai?tab=bao-cao" color="pink" badge={pendingXepLoaiCount} size="large" />}
            </div>
          </div>
        )}

        {/* SECTION 3: QUẢN LÝ ĐƠN VỊ */}
        {canViewManageUnit && (
          <div className="mb-8">
            <SectionHeader icon="📋" title="Quản lý đơn vị" subtitle={canEditManageUnit ? "Báo cáo và thống kê xếp loại công chức" : "Xem báo cáo xếp loại công chức (chỉ xem)"} />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <QuickActionCard icon="📊" title="Báo cáo đánh giá, xếp loại" description={canEditManageUnit ? "Lập báo cáo đánh giá, xếp loại CC" : "Xem báo cáo đánh giá, xếp loại CC"} href="/xep-loai?tab=bao-cao" color="indigo" size="large" viewOnly={!canEditManageUnit} />
              <QuickActionCard icon="📐" title="Tạm tính KPI" description="Tổng hợp tạm tính điểm KPI tháng" href="/xep-loai?tab=tam-tinh" color="cyan" size="large" viewOnly={!canEditManageUnit} />
              <QuickActionCard icon="🏆" title="Đánh giá Quý" description="Tổng hợp đánh giá và xếp loại quý" href="/xep-loai?tab=quy" color="purple" size="large" viewOnly={!canEditManageUnit} />
            </div>
          </div>
        )}

        {/* SECTION 3b: QUẢN LÝ CHI CỤC (CCT + user có can_view_all_units) */}
        {canViewChiCuc && (
          <div className="mb-8">
            <SectionHeader icon="🏛️" title="Quản lý Chi cục" subtitle={isCCT ? "Tổng hợp và giám sát toàn Chi cục" : "Xem báo cáo và thống kê toàn Chi cục (chỉ xem)"} />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <QuickActionCard icon="📑" title="Báo cáo tất cả đơn vị" description="Xem báo cáo xếp loại tất cả đơn vị" href="/xep-loai?tab=bao-cao" color="purple" size="large" viewOnly={!isCCT} />
              <QuickActionCard icon="📈" title="Thống kê Chi cục" description="Biểu đồ & thống kê toàn Chi cục" href="/xep-loai/thong-ke" color="pink" size="large" viewOnly={!isCCT} />
            </div>
          </div>
        )}

        {/* SECTION 4: WIDGETS */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50">
              <div className="flex items-center gap-2">
                <span className="text-lg">📋</span>
                <h3 className="font-medium text-gray-900">Tiêu chí chung của tôi</h3>
              </div>
              <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded-full">T{currentMonth}/{currentYear}</span>
            </div>
            <div className="p-5">
              <TieuChiChungWidget tieuChiChung={tieuChiChung} isLoading={isLoadingTC} currentMonth={currentMonth} currentYear={currentYear} onNavigate={() => router.push('/danh-gia/tu-cham-diem')} />
            </div>
          </div>

          {isLanhDao ? (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-orange-50 to-yellow-50">
                <div className="flex items-center gap-2">
                  <span className="text-lg">✅</span>
                  <h3 className="font-medium text-gray-900">Tổng quan phê duyệt</h3>
                </div>
                {(pendingSanPham + pendingTCCount + pendingXepLoaiCount) > 0 && (
                  <span className="text-xs text-white bg-red-500 px-2 py-1 rounded-full font-medium">{pendingSanPham + pendingTCCount + pendingXepLoaiCount} chờ</span>
                )}
              </div>
              <div className="p-5">
                <PheDuyetOverviewWidget pendingSanPham={pendingSanPham} pendingTieuChi={pendingTCCount} pendingXepLoai={pendingXepLoaiCount} isLoading={isLoadingPending} />
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-100 bg-gradient-to-r from-green-50 to-teal-50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🔔</span>
                  <h3 className="font-medium text-gray-900">Thông báo</h3>
                  {thongBaoChuaDoc > 0 && (
                    <span className="text-xs text-white bg-red-500 px-2 py-0.5 rounded-full font-medium">{thongBaoChuaDoc}</span>
                  )}
                </div>
                <button onClick={() => router.push('/thong-bao')} className="text-xs text-blue-600 hover:underline">Xem tất cả</button>
              </div>
              <div className="p-5">
                {isLoadingTB ? (
                  <div className="flex items-center justify-center py-6">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
                  </div>
                ) : thongBaoList.length === 0 ? (
                  <div className="text-center py-6">
                    <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                      <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                      </svg>
                    </div>
                    <p className="text-gray-500 text-sm">Chưa có thông báo mới</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {thongBaoList.map((tb: any) => (
                      <div
                        key={tb.id}
                        onClick={() => {
                          if (tb.link_url) router.push(tb.link_url);
                          if (!tb.da_doc) thongBaoApi.danhDauDaDoc(tb.id).catch(() => {});
                        }}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          tb.da_doc ? 'bg-white border-gray-100 hover:bg-gray-50' : 'bg-blue-50 border-blue-200 hover:bg-blue-100'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-sm shrink-0 mt-0.5">
                            {tb.muc_do === 'KHAN' ? '🔴' : tb.muc_do === 'QUAN_TRONG' ? '🟠' : '🔵'}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className={`text-sm truncate ${tb.da_doc ? 'text-gray-700' : 'text-gray-900 font-medium'}`}>{tb.tieu_de}</p>
                            <p className="text-xs text-gray-400 mt-0.5">
                              {new Date(tb.created_at).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>
                          {!tb.da_doc && <span className="w-2 h-2 bg-blue-500 rounded-full shrink-0 mt-1.5" />}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="mt-8 text-center text-xs text-gray-400">
          <p>Hệ thống Quản lý KPI - Chi cục Hải quan Khu vực VIII</p>
          <p className="mt-1">Phiên bản 3.5.0 • © 2026</p>
        </div>
      </main>
    </div>
  );
}
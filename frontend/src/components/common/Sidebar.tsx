/**
 * components/common/Sidebar.tsx
 * ==============================
 * Sidebar navigation cho Nền tảng Số Thống nhất HQKV8.
 *
 * Cấu trúc menu:
 * - Tổng quan (đầu tiên)
 * - KPI (giữ nguyên menu production)
 * - Nền tảng số (LMS, Diễn đàn, Pháp luật, Tin tức, Tài liệu, Kho tri thức)
 * - Hệ thống (Thông báo, Tìm kiếm)
 * - Quản trị (chỉ admin)
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { getPlatformRolesFromToken, userCanAccessHkg } from '@/lib/jwt-claims';
import {
  Home,
  FileText,
  BarChart3,
  CheckSquare,
  Trophy,
  CalendarDays,
  GraduationCap,
  MessageSquare,
  Scale,
  Newspaper,
  FolderOpen,
  BookOpen,
  Bell,
  Search,
  Settings,
  ChevronLeft,
  CalendarCheck,
  ChevronRight,
  Menu,
  X,
  LayoutDashboard,
  LogOut,
  User,
  type LucideIcon,
} from 'lucide-react';
import { useCurrentUser, useIsAdmin, useIsQLDV, useAuthStore } from '@/stores/useAuthStore';
import { thongBaoApi } from '@/services/common';

// =============================================================================
// TYPES
// =============================================================================

interface MenuItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: number;
  comingSoon?: boolean;
}

interface MenuSection {
  title: string | null; // null = không có tiêu đề (item đầu tiên)
  items: MenuItem[];
}

// =============================================================================
// MENU CONFIG
// =============================================================================

function useThongBaoCount(): number {
  const [count, setCount] = useState(0);
  useEffect(() => {
    thongBaoApi.demChuaDoc()
      .then((res) => setCount(res.data?.data?.count || 0))
      .catch(() => {});
    // Refresh mỗi 60s
    const interval = setInterval(() => {
      thongBaoApi.demChuaDoc()
        .then((res) => setCount(res.data?.data?.count || 0))
        .catch(() => {});
    }, 60000);
    return () => clearInterval(interval);
  }, []);
  return count;
}

function useMenuSections(): MenuSection[] {
  const isAdmin = useIsAdmin();
  const isQldv = useIsQLDV();
  const thongBaoCount = useThongBaoCount();
  const { user } = useAuthStore();

  // 05/05/2026: V2_PL3 là chuẩn duy nhất — bỏ link tới các trang V1 cũ.
  const keKhaiHref = '/ke-khai-v2';
  const keKhaiLabel = 'Kê khai công việc';
  const danhGiaHref = '/danh-gia-v2';
  const danhGiaLabel = 'Đánh giá';

  // HKG (01/05/2026 — UAT feature flag): visible cho admin/leadership/HKG-roles.
  // Đọc platform_roles từ user (populate từ /me) hoặc decode JWT làm fallback.
  const platformRoles = user?.platform_roles ?? getPlatformRolesFromToken();
  const hkgVisible = userCanAccessHkg({
    vai_tro: user?.vai_tro?.ma_vai_tro,
    is_admin: user?.is_system_admin,
    platform_roles: platformRoles,
  });

  // KPI menu items — QLDV: ẩn "Kê khai công việc" (không có quyền tạo)
  const kpiItems: MenuItem[] = [
    { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    ...(!isQldv ? [{ label: keKhaiLabel, href: keKhaiHref, icon: FileText }] : []),
    { label: 'Phê duyệt', href: '/phe-duyet', icon: CheckSquare },
    { label: danhGiaLabel, href: danhGiaHref, icon: BarChart3 },
    { label: 'Xếp loại', href: '/xep-loai', icon: Trophy },
    { label: 'Nghỉ phép', href: '/nghi-phep', icon: CalendarDays },
    // Yêu cầu 2 (06/05/2026): điều chỉnh KQCV — chỉ LĐ thật (không phải HĐ 111)
    ...(user?.is_lanh_dao && !user?.is_hd_111
      ? [{ label: 'Điều chỉnh KQCV', href: '/dieu-chinh-kqcv', icon: CheckSquare }]
      : []),
    // HĐLĐ 111 VB714 (01/06/2026): TDV/PDV duyệt đánh giá HĐLĐ trong đơn vị
    ...(user?.is_lanh_dao && !user?.is_hd_111
      ? [{ label: 'Duyệt HĐLĐ', href: '/hdld-duyet', icon: CheckSquare }]
      : []),
  ];

  const sections: MenuSection[] = [
    // --- TỔNG QUAN ---
    {
      title: null,
      items: [
        { label: 'Tổng quan', href: '/tong-quan', icon: Home },
      ],
    },

    // --- KPI ---
    {
      title: 'KPI',
      items: kpiItems,
    },

    // --- NỀN TẢNG SỐ ---
    {
      title: 'Nền tảng số',
      items: [
        { label: 'Đào tạo', href: '/dao-tao', icon: GraduationCap },
        { label: 'Diễn đàn', href: '/dien-dan', icon: MessageSquare },
        { label: 'Pháp luật', href: '/phap-luat', icon: Scale },
        { label: 'Tin tức', href: '/tin-tuc', icon: Newspaper },
        { label: 'Tài liệu', href: '/tai-lieu', icon: FolderOpen },
        { label: 'Kho tri thức', href: '/kien-thuc', icon: BookOpen },
        // HKG (01/05/2026 — UAT): chỉ visible khi user có role HKG hoặc admin/leadership.
        // Sau UAT pass → bỏ điều kiện hkgVisible để mở cho 549 user.
        ...(hkgVisible
          ? [{ label: 'Họp Không Giấy', href: '/hop-khong-giay', icon: CalendarCheck }]
          : []),
      ],
    },

    // --- HỆ THỐNG ---
    {
      title: 'Hệ thống',
      items: [
        { label: 'Thông báo', href: '/thong-bao', icon: Bell, badge: thongBaoCount },
        { label: 'Tìm kiếm', href: '/tim-kiem', icon: Search },
      ],
    },
  ];

  // Admin / CCT section — Quản trị hệ thống (admin), Phân công phụ trách (CCT + admin)
  const isCCT = user?.vai_tro?.ma_vai_tro === 'CCT';
  if (isAdmin || isCCT) {
    const adminItems: MenuItem[] = [];
    if (isAdmin) {
      adminItems.push({ label: 'Quản trị hệ thống', href: '/admin', icon: Settings });
    }
    if (isAdmin || isCCT) {
      adminItems.push({ label: 'Phân công phụ trách', href: '/phan-cong-phu-trach', icon: Settings });
    }
    sections.push({ title: 'Quản trị', items: adminItems });
  }

  return sections;
}

// =============================================================================
// SIDEBAR ITEM
// =============================================================================

function SidebarItem({
  item,
  isActive,
  collapsed,
}: {
  item: MenuItem;
  isActive: boolean;
  collapsed: boolean;
}) {
  const Icon = item.icon;

  if (item.comingSoon) {
    return (
      <div
        className={`
          flex items-center gap-3 px-3 py-2 rounded-lg text-sm
          text-gray-400 cursor-default
          ${collapsed ? 'justify-center' : ''}
        `}
        title={collapsed ? `${item.label} (Sắp ra mắt)` : undefined}
      >
        <Icon className="w-5 h-5 flex-shrink-0" />
        {!collapsed && (
          <>
            <span className="flex-1 truncate">{item.label}</span>
            <span className="text-[10px] bg-gray-100 text-gray-400 px-1.5 py-0.5 rounded">
              Sắp có
            </span>
          </>
        )}
      </div>
    );
  }

  return (
    <Link
      href={item.href}
      className={`
        flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors
        ${isActive
          ? 'bg-blue-50 text-blue-700 font-medium'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        }
        ${collapsed ? 'justify-center relative' : ''}
      `}
      title={collapsed ? item.label : undefined}
    >
      <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-blue-600' : ''}`} />
      {!collapsed && (
        <>
          <span className="flex-1 truncate">{item.label}</span>
          {item.badge !== undefined && item.badge > 0 && (
            <span className="bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
              {item.badge > 99 ? '99+' : item.badge}
            </span>
          )}
        </>
      )}
      {collapsed && item.badge !== undefined && item.badge > 0 && (
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
          {item.badge > 9 ? '9+' : item.badge}
        </span>
      )}
    </Link>
  );
}

// =============================================================================
// SIDEBAR COMPONENT
// =============================================================================

export default function Sidebar() {
  const pathname = usePathname();
  const user = useCurrentUser();
  const { logout } = useAuthStore();
  const sections = useMenuSections();

  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Đóng mobile menu khi navigate
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // Kiểm tra active: match prefix (vd: /ke-khai/* sẽ highlight /ke-khai)
  const isActive = (href: string) => {
    if (href === '/tong-quan') return pathname === '/tong-quan';
    return pathname === href || pathname.startsWith(href + '/');
  };

  // ---------------------------------------------------------------------------
  // Sidebar content (dùng chung cho desktop + mobile)
  // ---------------------------------------------------------------------------
  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className={`flex items-center border-b border-gray-200 ${collapsed ? 'px-2 py-4 justify-center' : 'px-4 py-4 gap-3'}`}>
        <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold text-sm">H</span>
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-900 truncate">HQ Khu vực VIII</p>
            <p className="text-[11px] text-gray-500 truncate">Nền tảng Số Thống nhất</p>
          </div>
        )}
      </div>

      {/* Menu sections */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        {sections.map((section, sIdx) => (
          <div key={sIdx}>
            {section.title && !collapsed && (
              <p className="px-3 mb-1 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                {section.title}
              </p>
            )}
            {section.title && collapsed && (
              <div className="border-t border-gray-200 mx-2 my-1" />
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <SidebarItem
                  key={item.href}
                  item={item}
                  isActive={isActive(item.href)}
                  collapsed={collapsed}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* User info + logout + collapse button */}
      <div className="border-t border-gray-200 p-3">
        {!collapsed && user && (
          <div className="flex items-center gap-2 mb-2 px-1">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-blue-700 text-xs font-bold">
                {user.ho_ten?.charAt(0) || 'U'}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-gray-900 truncate">{user.ho_ten}</p>
              <p className="text-[10px] text-gray-500 truncate">{user.don_vi?.ten_don_vi || user.ma_cc}</p>
            </div>
          </div>
        )}
        <Link
          href="/ho-so"
          className={`flex items-center w-full gap-2 px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors mb-1 ${collapsed ? 'justify-center' : ''} ${pathname === '/ho-so' ? 'bg-blue-50 text-blue-700 font-medium' : ''}`}
          title={collapsed ? 'Hồ sơ' : undefined}
        >
          <User className="w-4 h-4 flex-shrink-0" />
          {!collapsed && <span>Hồ sơ</span>}
        </Link>
        <button
          onClick={logout}
          className={`flex items-center w-full gap-2 px-3 py-1.5 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors mb-1 ${collapsed ? 'justify-center' : ''}`}
          title={collapsed ? 'Đăng xuất' : undefined}
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {!collapsed && <span>Đăng xuất</span>}
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden lg:flex items-center justify-center w-full gap-2 px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          title={collapsed ? 'Mở rộng' : 'Thu gọn'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          {!collapsed && <span>Thu gọn</span>}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-3 left-3 z-40 p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50"
        aria-label="Mở menu"
      >
        <Menu className="w-5 h-5 text-gray-600" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/30"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <div
        className={`
          lg:hidden fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl
          transform transition-transform duration-200
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-3 right-3 p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          aria-label="Đóng menu"
        >
          <X className="w-5 h-5" />
        </button>
        {sidebarContent}
      </div>

      {/* Desktop sidebar */}
      <aside
        className={`
          hidden lg:flex flex-col flex-shrink-0 bg-white border-r border-gray-200
          transition-[width] duration-200
          ${collapsed ? 'w-16' : 'w-60'}
        `}
      >
        {sidebarContent}
      </aside>
    </>
  );
}

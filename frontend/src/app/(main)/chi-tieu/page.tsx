/**
 * src/app/(main)/chi-tieu/page.tsx
 * ================================
 * Trang chủ module Chỉ tiêu đơn vị — điều hướng theo vai trò.
 */

'use client';

import Link from 'next/link';
import { useAuthStore } from '@/stores/useAuthStore';

interface NavCard {
  href: string;
  icon: string;
  title: string;
  desc: string;
  color: string;
  show: boolean;
}

export default function ChiTieuHomePage() {
  const user = useAuthStore((s) => s.user);
  const platformRoles: string[] = user?.platform_roles ?? [];
  const maVaiTro = user?.vai_tro?.ma_vai_tro;
  const isAdmin = user?.is_system_admin === true;

  const laQuanTri = isAdmin || platformRoles.includes('QT_CHI_TIEU');
  const laTheoDoi = isAdmin || platformRoles.includes('THEO_DOI_CHI_TIEU');
  const laTruongDV = isAdmin || ['TDV', 'PCCT', 'CCT'].includes(maVaiTro ?? '');

  const cards: NavCard[] = [
    {
      href: '/chi-tieu/dang-ky', icon: '📝', title: 'Đăng ký & kết quả',
      desc: 'Đăng ký chỉ tiêu đầu tháng, nhập kết quả cuối tháng', color: 'blue', show: laTheoDoi,
    },
    {
      href: '/chi-tieu/duyet', icon: '✅', title: 'Duyệt chỉ tiêu',
      desc: 'Duyệt đăng ký / sửa / kết quả của đơn vị', color: 'green', show: laTruongDV,
    },
    {
      href: '/chi-tieu/bao-cao', icon: '📊', title: 'Báo cáo rà soát',
      desc: 'Rà soát theo tháng, lũy kế năm theo đơn vị', color: 'purple', show: true,
    },
    {
      href: '/chi-tieu/danh-muc', icon: '🗂️', title: 'Danh mục chỉ tiêu',
      desc: 'Quản lý lĩnh vực & chỉ tiêu công tác', color: 'orange', show: laQuanTri,
    },
    {
      href: '/chi-tieu/giao-nam', icon: '🎯', title: 'Giao chỉ tiêu năm',
      desc: 'Giao chỉ tiêu năm (pháp lệnh / phấn đấu) cho đơn vị', color: 'cyan', show: laQuanTri,
    },
  ];

  const colorMap: Record<string, string> = {
    blue: 'hover:border-blue-300 hover:bg-blue-50',
    green: 'hover:border-green-300 hover:bg-green-50',
    purple: 'hover:border-purple-300 hover:bg-purple-50',
    orange: 'hover:border-orange-300 hover:bg-orange-50',
    cyan: 'hover:border-cyan-300 hover:bg-cyan-50',
  };

  const visible = cards.filter((c) => c.show);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Chỉ tiêu đơn vị</h1>
          <p className="text-sm text-gray-500 mt-1">
            Quản lý chỉ tiêu công tác cấp đơn vị — độc lập với KPI cá nhân
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {visible.map((c) => (
            <Link key={c.href} href={c.href}
              className={`bg-white border border-gray-200 rounded-xl p-5 transition-all shadow-sm hover:shadow-md ${colorMap[c.color]}`}>
              <div className="text-3xl mb-3">{c.icon}</div>
              <div className="font-semibold text-gray-900">{c.title}</div>
              <div className="text-sm text-gray-500 mt-1">{c.desc}</div>
            </Link>
          ))}
        </div>

        {visible.length === 0 && (
          <div className="text-center py-16 text-gray-500">
            <span className="text-4xl block mb-2">🔒</span>
            <p>Bạn chưa được phân quyền trong module Chỉ tiêu đơn vị.</p>
          </div>
        )}
      </div>
    </div>
  );
}

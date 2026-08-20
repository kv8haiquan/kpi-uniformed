/**
 * Layout module Lịch công tác.
 *
 * Dùng chung điều kiện truy cập với Họp Không Giấy vì hai module đọc cùng một
 * bảng cuộc họp trên cùng một backend.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';

import { doiSoatApi } from '@/services/doi-soat';
import { ghiChuApi } from '@/services/ghi-chu';
import { useAuthStore } from '@/stores/useAuthStore';
import { getPlatformRolesFromToken, userCanAccessHkg } from '@/lib/jwt-claims';

const TAB = [
  { href: '/lich-cong-tac', nhan: 'Lịch' },
  { href: '/lich-cong-tac/tong-quan', nhan: 'Tổng quan' },
  { href: '/lich-cong-tac/tom-tat', nhan: 'Tóm tắt lịch' },
  { href: '/lich-cong-tac/truc-ban', nhan: 'Trực ban' },
  { href: '/lich-cong-tac/ghi-chu', nhan: 'Ghi chú' },
  { href: '/lich-cong-tac/thong-ke-tai-lieu', nhan: 'Thống kê tài liệu' },
];

// Đối soát là màn hình DÙNG MỘT LẦN của đợt chuyển đổi, chỉ Chánh Văn phòng
// và Quản trị viên thấy. Xong việc thì xoá cả mục này lẫn thư mục doi-soat/.
const TAB_DOI_SOAT = { href: '/lich-cong-tac/doi-soat', nhan: 'Đối soát di trú' };

export default function LichCongTacLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const [thayDoiSoat, setThayDoiSoat] = useState(false);
  // Ghi chú người khác chia sẻ chỉ hiện khi mở đúng tab đó — không có
  // huy hiệu thì thông báo gửi tới cũng chẳng ai thấy.
  const [chuaDoc, setChuaDoc] = useState(0);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace(`/login?redirect=${encodeURIComponent(pathname)}`);
      return;
    }
    const platformRoles = user?.platform_roles ?? getPlatformRolesFromToken();
    const allowed = userCanAccessHkg({
      vai_tro: user?.vai_tro?.ma_vai_tro,
      is_admin: user?.is_system_admin,
      platform_roles: platformRoles,
    });
    if (!allowed) {
      router.replace('/tong-quan');
    }
  }, [isAuthenticated, isLoading, user, router, pathname]);

  useEffect(() => {
    if (!isAuthenticated) return;
    doiSoatApi
      .quyen()
      .then((q) => setThayDoiSoat(q.duoc_xem))
      .catch(() => setThayDoiSoat(false));
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) return;
    ghiChuApi.soChuaDoc().then(setChuaDoc).catch(() => setChuaDoc(0));
    // Đọc lại mỗi lần đổi trang trong module — rẻ hơn nhiều so với hẹn giờ,
    // và người dùng đang ở trong module thì thao tác nào cũng đổi đường dẫn.
  }, [isAuthenticated, pathname]);

  const tab = thayDoiSoat ? [...TAB, TAB_DOI_SOAT] : TAB;

  return (
    <div className="min-h-screen p-6 bg-gray-50">
      <header className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Lịch công tác</h1>
        <p className="text-sm text-gray-600">
          Chương trình công tác Chi cục Hải quan khu vực VIII
        </p>
      </header>

      <nav className="mb-4 flex gap-1 border-b border-gray-200 print:hidden">
        {tab.map((t) => {
          const dangO =
            t.href === '/lich-cong-tac'
              ? pathname === t.href
              : pathname.startsWith(t.href);
          return (
            <Link
              key={t.href}
              href={t.href}
              className={`px-3 py-2 text-sm border-b-2 -mb-px ${
                dangO
                  ? 'border-blue-600 text-blue-700 font-medium'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {t.nhan}
              {t.href === '/lich-cong-tac/ghi-chu' && chuaDoc > 0 && (
                <span className="ml-1.5 rounded-full bg-red-100 px-1.5 text-xs text-red-700">
                  {chuaDoc}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {children}
    </div>
  );
}

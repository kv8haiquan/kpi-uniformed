/**
 * Layout module Lịch công tác.
 *
 * Dùng chung điều kiện truy cập với Họp Không Giấy vì hai module đọc cùng một
 * bảng cuộc họp trên cùng một backend.
 */

'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';

import { useAuthStore } from '@/stores/useAuthStore';
import { getPlatformRolesFromToken, userCanAccessHkg } from '@/lib/jwt-claims';

const TAB = [
  { href: '/lich-cong-tac', nhan: 'Lịch' },
  { href: '/lich-cong-tac/tom-tat', nhan: 'Tóm tắt lịch' },
];

export default function LichCongTacLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useAuthStore();

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

  return (
    <div className="min-h-screen p-6 bg-gray-50">
      <header className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Lịch công tác</h1>
        <p className="text-sm text-gray-600">
          Chương trình công tác Chi cục Hải quan khu vực VIII
        </p>
      </header>

      <nav className="mb-4 flex gap-1 border-b border-gray-200 print:hidden">
        {TAB.map((t) => {
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
            </Link>
          );
        })}
      </nav>

      {children}
    </div>
  );
}

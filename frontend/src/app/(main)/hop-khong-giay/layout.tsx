/**
 * Layout cho module HKG.
 * Permission guard: chỉ user có quyền HKG (UAT feature flag) mới truy cập được.
 */

'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { getPlatformRolesFromToken, userCanAccessHkg } from '@/lib/jwt-claims';

export default function HkgLayout({ children }: { children: React.ReactNode }) {
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
        <h1 className="text-2xl font-bold text-gray-900">Họp Không Giấy</h1>
        <p className="text-sm text-gray-600">
          Module quản lý phòng họp không giấy tờ — Chi cục Hải quan KV VIII
          <span className="ml-2 px-2 py-0.5 rounded text-xs bg-amber-100 text-amber-800">
            UAT
          </span>
        </p>
      </header>
      {children}
    </div>
  );
}

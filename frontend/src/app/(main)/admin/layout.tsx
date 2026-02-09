/**
 * src/app/(main)/admin/layout.tsx
 * ================================
 * Layout cho Admin Module.
 * Kiểm tra quyền System Admin trước khi cho phép truy cập.
 * 
 * Version: 1.0.0 (30/01/2026)
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }

    if (user && !user.is_system_admin) {
      // Không phải admin, redirect về dashboard
      router.replace('/dashboard');
      return;
    }

    setIsChecking(false);
  }, [isAuthenticated, isLoading, user, router]);

  // Loading state
  if (isLoading || isChecking) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-3 text-gray-500">Đang kiểm tra quyền truy cập...</p>
        </div>
      </div>
    );
  }

  // Không phải admin
  if (!user?.is_system_admin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">🚫</span>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Không có quyền truy cập</h2>
          <p className="text-gray-600 mb-6">
            Bạn không có quyền truy cập vào khu vực Quản trị. 
            Vui lòng liên hệ Admin nếu bạn cần quyền này.
          </p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Quay về Dashboard
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * src/providers/AuthProvider.tsx
 * ==============================
 * Provider component để khởi tạo authentication state khi app mount.
 *
 * Chức năng:
 * - Kiểm tra token trong localStorage
 * - Validate token bằng cách gọi GET /auth/me
 * - Cập nhật Zustand store
 * - Hiển thị loading screen trong khi validate
 */

'use client';

import { useEffect, useState } from 'react';
import { initializeAuth, useAuthStore } from '@/stores/useAuthStore';

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isInitialized, setIsInitialized] = useState(false);
  const isLoading = useAuthStore((state) => state.isLoading);

  useEffect(() => {
    // Khởi tạo auth state khi component mount
    const initialize = async () => {
      try {
        await initializeAuth();
      } catch (error) {
        console.error('[AuthProvider] Initialization error:', error);
      } finally {
        setIsInitialized(true);
      }
    };

    initialize();
  }, []);

  // Hiển thị loading screen trong khi khởi tạo
  if (!isInitialized || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          {/* Loading spinner */}
          <div className="inline-flex items-center justify-center">
            <svg
              className="animate-spin h-10 w-10 text-blue-600"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          
          {/* Loading text */}
          <p className="mt-4 text-gray-600 font-medium">
            Đang tải hệ thống...
          </p>
          <p className="mt-1 text-sm text-gray-400">
            Vui lòng chờ trong giây lát
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export default AuthProvider;

/**
 * src/app/(auth)/layout.tsx
 * =========================
 * Layout cho các trang authentication (login, forgot-password, etc.).
 * Không có sidebar, header, chỉ có content chính.
 */

import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Đăng nhập - Hệ thống KPI Hải quan',
  description: 'Đăng nhập vào Hệ thống Đánh giá KPI - Chi cục Hải quan Khu vực VIII',
};

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen">
      {children}
    </div>
  );
}

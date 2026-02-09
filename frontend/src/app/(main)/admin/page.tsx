/**
 * src/app/(main)/admin/page.tsx
 * =============================
 * Trang Dashboard Admin Module.
 * 
 * Hiển thị thống kê tổng quan và các quick actions.
 * 
 * Version: 1.0.0 (30/01/2026)
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { adminService, isApiError } from '@/services/admin.service';
import { IAdminStats } from '@/types/admin';

// =============================================================================
// STAT CARD COMPONENT
// =============================================================================

interface StatCardProps {
  icon: string;
  title: string;
  value: number;
  subtitle?: string;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'red' | 'indigo';
  href?: string;
}

function StatCard({ icon, title, value, subtitle, color, href }: StatCardProps) {
  const router = useRouter();
  
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    green: 'bg-green-50 border-green-200 text-green-700',
    purple: 'bg-purple-50 border-purple-200 text-purple-700',
    orange: 'bg-orange-50 border-orange-200 text-orange-700',
    red: 'bg-red-50 border-red-200 text-red-700',
    indigo: 'bg-indigo-50 border-indigo-200 text-indigo-700',
  };

  const iconBgClasses = {
    blue: 'bg-blue-100',
    green: 'bg-green-100',
    purple: 'bg-purple-100',
    orange: 'bg-orange-100',
    red: 'bg-red-100',
    indigo: 'bg-indigo-100',
  };

  return (
    <div
      onClick={() => href && router.push(href)}
      className={`${colorClasses[color]} border rounded-xl p-5 ${href ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
    >
      <div className="flex items-center gap-4">
        <div className={`w-14 h-14 ${iconBgClasses[color]} rounded-xl flex items-center justify-center`}>
          <span className="text-2xl">{icon}</span>
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium opacity-80">{title}</p>
          <p className="text-3xl font-bold">{value.toLocaleString('vi-VN')}</p>
          {subtitle && <p className="text-xs opacity-60 mt-1">{subtitle}</p>}
        </div>
        {href && (
          <svg className="w-5 h-5 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// QUICK ACTION CARD
// =============================================================================

interface QuickActionProps {
  icon: string;
  title: string;
  description: string;
  href: string;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'indigo' | 'pink';
}

function QuickActionCard({ icon, title, description, href, color }: QuickActionProps) {
  const router = useRouter();
  
  const colorClasses = {
    blue: 'bg-blue-50 hover:bg-blue-100 border-blue-200 hover:border-blue-300',
    green: 'bg-green-50 hover:bg-green-100 border-green-200 hover:border-green-300',
    purple: 'bg-purple-50 hover:bg-purple-100 border-purple-200 hover:border-purple-300',
    orange: 'bg-orange-50 hover:bg-orange-100 border-orange-200 hover:border-orange-300',
    indigo: 'bg-indigo-50 hover:bg-indigo-100 border-indigo-200 hover:border-indigo-300',
    pink: 'bg-pink-50 hover:bg-pink-100 border-pink-200 hover:border-pink-300',
  };

  const iconBgClasses = {
    blue: 'bg-blue-100',
    green: 'bg-green-100',
    purple: 'bg-purple-100',
    orange: 'bg-orange-100',
    indigo: 'bg-indigo-100',
    pink: 'bg-pink-100',
  };

  return (
    <div
      onClick={() => router.push(href)}
      className={`${colorClasses[color]} border rounded-xl p-4 cursor-pointer transition-all group`}
    >
      <div className="flex items-center gap-3">
        <div className={`w-12 h-12 ${iconBgClasses[color]} rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform`}>
          <span className="text-xl">{icon}</span>
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900">{title}</h4>
          <p className="text-sm text-gray-500 truncate">{description}</p>
        </div>
        <svg className="w-5 h-5 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-1 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function AdminDashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  
  const [stats, setStats] = useState<IAdminStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Kiểm tra quyền Admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    
    if (user && !user.is_system_admin) {
      router.replace('/dashboard');
      return;
    }
  }, [isAuthenticated, user, router]);

  // Load thống kê
  useEffect(() => {
    const loadStats = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const data = await adminService.getStats();
        setStats(data);
      } catch (err) {
        setError(isApiError(err) ? err.message : 'Có lỗi xảy ra khi tải dữ liệu');
      } finally {
        setIsLoading(false);
      }
    };

    if (user?.is_system_admin) {
      loadStats();
    }
  }, [user]);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Đang tải dữ liệu...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">❌</span>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Có lỗi xảy ra</h3>
          <p className="text-gray-500 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => router.push('/dashboard')}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Quay lại Dashboard"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">🔧 Quản trị Hệ thống</h1>
              <p className="text-gray-600">Quản lý người dùng, danh mục và cấu hình hệ thống</p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon="👥"
            title="Tổng người dùng"
            value={stats?.tong_user || 0}
            subtitle={`${stats?.user_active || 0} đang hoạt động`}
            color="blue"
            href="/admin/users"
          />
          <StatCard
            icon="🏢"
            title="Đơn vị"
            value={stats?.tong_don_vi || 0}
            color="green"
          />
          <StatCard
            icon="📦"
            title="SP Chuẩn"
            value={stats?.tong_sp_chuan || 0}
            color="purple"
            href="/admin/sp-chuan"
          />
          <StatCard
            icon="📋"
            title="Danh mục CV"
            value={stats?.tong_danh_muc_cv || 0}
            color="orange"
            href="/admin/danh-muc-cv"
          />
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">⚡ Thao tác nhanh</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <QuickActionCard
              icon="👤"
              title="Quản lý Người dùng"
              description="Tạo, sửa, vô hiệu hóa tài khoản"
              href="/admin/users"
              color="blue"
            />
            <QuickActionCard
              icon="🔄"
              title="Điều chuyển nhân sự"
              description="Chuyển đơn vị, vai trò nhân sự"
              href="/admin/users?action=transfer"
              color="green"
            />
            <QuickActionCard
              icon="📦"
              title="Quản lý SP Chuẩn"
              description="Thêm, sửa sản phẩm chuẩn"
              href="/admin/sp-chuan"
              color="purple"
            />
            <QuickActionCard
              icon="📊"
              title="Quản lý Cấp độ"
              description="Cấu hình cấp độ phức tạp"
              href="/admin/cap-do"
              color="orange"
            />
            <QuickActionCard
              icon="📋"
              title="Danh mục Công việc"
              description="Quản lý danh mục SP công việc"
              href="/admin/danh-muc-cv"
              color="indigo"
            />
            <QuickActionCard
              icon="🔑"
              title="Reset mật khẩu"
              description="Đặt lại mật khẩu người dùng"
              href="/admin/users?action=reset-password"
              color="pink"
            />
          </div>
        </div>

        {/* System Info */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">ℹ️ Thông tin hệ thống</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">Phiên bản</span>
              <span className="font-medium text-gray-900">v2.7.0</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">Admin Module</span>
              <span className="font-medium text-gray-900">v1.0.0</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">Người dùng hiện tại</span>
              <span className="font-medium text-gray-900">{user?.ho_ten || 'N/A'}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">Vai trò</span>
              <span className="font-medium text-blue-600">System Admin</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">Số cấp độ</span>
              <span className="font-medium text-gray-900">{stats?.tong_cap_do || 0}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">User không hoạt động</span>
              <span className="font-medium text-red-600">{stats?.user_inactive || 0}</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

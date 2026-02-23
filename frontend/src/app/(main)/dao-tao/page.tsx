/**
 * src/app/(main)/dao-tao/page.tsx
 * ================================
 * Dashboard Đào tạo — Tổng quan cá nhân.
 * Hiển thị: stat cards, khóa đang học, chứng chỉ gần đây.
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { baoCaoApi, dangKyApi } from '@/services/lms';
import type { IBaoCaoCaNhan, IDangKyKhoaHoc } from '@/types/lms';
import { useAuthStore } from '@/stores/useAuthStore';

// =============================================================================
// STAT CARD
// =============================================================================

function StatCard({ icon, label, value, color }: {
  icon: string; label: string; value: number | string; color: string;
}) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
  };
  return (
    <div className={`${colorMap[color]} rounded-xl border p-4`}>
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-xs opacity-80">{label}</div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN
// =============================================================================

export default function DaoTaoPage() {
  const router = useRouter();
  const [report, setReport] = useState<IBaoCaoCaNhan | null>(null);
  const [dangHoc, setDangHoc] = useState<IDangKyKhoaHoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Lấy thông tin user từ store để kiểm tra quyền quản lý
  const user = useAuthStore((state) => state.user);

  // Quyền quản lý đào tạo: GIANG_VIEN, QT_DAO_TAO, hoặc System Admin
  // platform_roles chưa có trong JWT (chưa implement), dùng optional chaining để tương thích tương lai
  const platformRoles: string[] = (user as any)?.platform_roles ?? [];
  const coQuyenQuanLy =
    user?.is_system_admin === true ||
    platformRoles.includes('GIANG_VIEN') ||
    platformRoles.includes('QT_DAO_TAO');

  useEffect(() => {
    const load = async () => {
      try {
        const [rptRes, dkRes] = await Promise.all([
          baoCaoApi.caNhan(),
          dangKyApi.cuaToi({ trang_thai: 'DANG_HOC', page_size: 5 }),
        ]);
        setReport(rptRes.data.data);
        setDangHoc(dkRes.data.data || []);
      } catch (err: any) {
        setError(err?.response?.data?.detail?.error?.message || 'Không thể tải dữ liệu');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <span className="text-3xl">⚠️</span>
          <p className="mt-2 text-red-700">{error}</p>
          <p className="mt-1 text-sm text-red-500">Hãy đảm bảo LMS backend đang chạy trên port 8001</p>
        </div>
      </div>
    );
  }

  const r = report;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Đào tạo trực tuyến</h1>
          <p className="text-sm text-gray-500 mt-1">Tổng quan học tập cá nhân</p>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard icon="📖" label="Khóa đang học" value={r?.khoa_dang_hoc ?? 0} color="blue" />
          <StatCard icon="✅" label="Đã hoàn thành" value={r?.khoa_hoan_thanh ?? 0} color="green" />
          <StatCard icon="🏅" label="Chứng chỉ" value={r?.tong_chung_chi ?? 0} color="purple" />
          <StatCard icon="⏱️" label="Giờ học" value={r?.tong_gio_hoc ?? 0} color="orange" />
        </div>

        {/* Section Quản lý đào tạo — chỉ hiển thị cho GIANG_VIEN, QT_DAO_TAO, Admin */}
        {coQuyenQuanLy && (
          <div className="border-l-4 border-blue-600 bg-blue-50 rounded-xl p-5 mb-6">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              {/* Nội dung trái: icon, tiêu đề, mô tả, quick links */}
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                  <span className="text-xl">⚙️</span>
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900 text-base">Quản lý đào tạo</h2>
                  <p className="text-sm text-gray-600 mt-0.5">
                    Tạo khóa học, quản lý nội dung, giao bài và theo dõi tiến độ học viên
                  </p>
                  {/* Quick action links nhỏ */}
                  <div className="flex flex-wrap gap-4 mt-3">
                    <Link
                      href="/dao-tao/quan-ly"
                      className="text-xs text-blue-700 hover:underline flex items-center gap-1"
                    >
                      <span>➕</span> Tạo khóa học mới
                    </Link>
                    <Link
                      href="/dao-tao/quan-ly"
                      className="text-xs text-blue-700 hover:underline flex items-center gap-1"
                    >
                      <span>⏳</span> Khóa chờ duyệt
                    </Link>
                    <Link
                      href="/dao-tao/quan-ly"
                      className="text-xs text-blue-700 hover:underline flex items-center gap-1"
                    >
                      <span>📋</span> Giao bài cho đơn vị
                    </Link>
                  </div>
                </div>
              </div>
              {/* Nút chính bên phải */}
              <Link
                href="/dao-tao/quan-ly"
                className="shrink-0 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors whitespace-nowrap self-start"
              >
                Đi đến trang quản lý
              </Link>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <Link href="/dao-tao/khoa-hoc" className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl p-4 flex items-center gap-3 transition-colors">
            <span className="text-2xl">📚</span>
            <div>
              <div className="font-medium">Danh sách khóa học</div>
              <div className="text-sm text-blue-100">Tìm và đăng ký khóa học</div>
            </div>
          </Link>
          <Link href="/dao-tao/chung-chi" className="bg-white border border-gray-200 hover:border-green-300 hover:bg-green-50 rounded-xl p-4 flex items-center gap-3 transition-colors">
            <span className="text-2xl">🎓</span>
            <div>
              <div className="font-medium text-gray-900">Chứng chỉ của tôi</div>
              <div className="text-sm text-gray-500">Xem và tải chứng chỉ</div>
            </div>
          </Link>
          <Link href="/dao-tao/khoa-hoc?tab=dang-hoc" className="bg-white border border-gray-200 hover:border-purple-300 hover:bg-purple-50 rounded-xl p-4 flex items-center gap-3 transition-colors">
            <span className="text-2xl">📊</span>
            <div>
              <div className="font-medium text-gray-900">Khóa đang học</div>
              <div className="text-sm text-gray-500">Tiến độ học tập</div>
            </div>
          </Link>
        </div>

        {/* Khóa đang học */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <span>📖</span> Khóa học đang tham gia
            </h2>
            <Link href="/dao-tao/khoa-hoc" className="text-sm text-blue-600 hover:underline">Xem tất cả</Link>
          </div>
          <div className="p-5">
            {dangHoc.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <span className="text-4xl block mb-2">📭</span>
                Chưa đăng ký khóa học nào
              </div>
            ) : (
              <div className="space-y-3">
                {dangHoc.map((dk) => (
                  <Link key={dk.id} href={`/dao-tao/khoa-hoc/${dk.khoa_hoc_id}`}
                    className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center shrink-0">
                      <span className="text-lg">📘</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 truncate">{dk.khoa_hoc_ten}</div>
                      <div className="text-xs text-gray-500">{dk.giang_vien_ho_ten || 'Chưa có giảng viên'}</div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-sm font-semibold text-blue-600">{dk.phan_tram_hoan_thanh}%</div>
                      <div className="w-20 h-1.5 bg-gray-200 rounded-full mt-1">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${dk.phan_tram_hoan_thanh}%` }} />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Chứng chỉ gần đây */}
        {r && r.chung_chi_gan_day.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <span>🏅</span> Chứng chỉ gần đây
              </h2>
            </div>
            <div className="p-5 space-y-3">
              {r.chung_chi_gan_day.map((cc, i) => (
                <div key={i} className="flex items-center gap-4 p-3 bg-green-50 rounded-lg">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-lg">🏅</span>
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{cc.ten_khoa}</div>
                    <div className="text-xs text-gray-500">Mã: {cc.ma}</div>
                  </div>
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                    {cc.xep_loai}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

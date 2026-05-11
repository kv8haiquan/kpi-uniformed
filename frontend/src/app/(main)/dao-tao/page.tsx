/**
 * src/app/(main)/dao-tao/page.tsx
 * ================================
 * Dashboard Đào tạo — Tổng quan cá nhân.
 * Hiển thị: stat cards, khóa đang học, chứng chỉ gần đây.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { baoCaoApi, dangKyApi, khoaHocApi } from '@/services/lms';
import type { IBaoCaoCaNhan, IDangKyKhoaHoc, IKhoaHoc } from '@/types/lms';
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

const TRANG_THAI_LABEL: Record<string, { label: string; bg: string; text: string }> = {
  CHUA_BAT_DAU: { label: 'Chưa bắt đầu', bg: 'bg-gray-100', text: 'text-gray-600' },
  DANG_HOC: { label: 'Đang học', bg: 'bg-blue-100', text: 'text-blue-700' },
  HOAN_THANH: { label: 'Hoàn thành', bg: 'bg-green-100', text: 'text-green-700' },
  QUA_HAN: { label: 'Quá hạn', bg: 'bg-red-100', text: 'text-red-700' },
};

const GRADIENTS = [
  'from-blue-500 to-indigo-600', 'from-green-500 to-teal-600',
  'from-purple-500 to-pink-600', 'from-orange-500 to-red-600', 'from-cyan-500 to-blue-600',
];

// =============================================================================
// MAIN
// =============================================================================

export default function DaoTaoPage() {
  const [report, setReport] = useState<IBaoCaoCaNhan | null>(null);
  const [enrolledCourses, setEnrolledCourses] = useState<IDangKyKhoaHoc[]>([]);
  const [allCourses, setAllCourses] = useState<IKhoaHoc[]>([]);
  const [loading, setLoading] = useState(true);

  const user = useAuthStore((state) => state.user);
  const platformRoles: string[] = (user as any)?.platform_roles ?? [];
  const coQuyenQuanLy =
    user?.is_system_admin === true ||
    platformRoles.includes('GIANG_VIEN') ||
    platformRoles.includes('QT_DAO_TAO');

  useEffect(() => {
    const load = async () => {
      // Load song song, khong de 1 API loi lam crash ca trang
      const [rptRes, dkRes, khRes] = await Promise.allSettled([
        baoCaoApi.caNhan(),
        dangKyApi.cuaToi({ page_size: 50 }),
        khoaHocApi.danhSach({ page_size: 12 }),
      ]);

      if (rptRes.status === 'fulfilled') {
        setReport(rptRes.value.data.data);
      }
      if (dkRes.status === 'fulfilled') {
        setEnrolledCourses(dkRes.value.data.data || []);
      }
      if (khRes.status === 'fulfilled') {
        setAllCourses(khRes.value.data.data || []);
      }
      setLoading(false);
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

  const r = report;
  const dangHoc = enrolledCourses.filter((dk) => dk.trang_thai === 'DANG_HOC');
  const chuaBatDau = enrolledCourses.filter((dk) => dk.trang_thai === 'CHUA_BAT_DAU');
  const hoanThanh = enrolledCourses.filter((dk) => dk.trang_thai === 'HOAN_THANH');

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
          <StatCard icon="📖" label="Đang học" value={(r?.khoa_dang_hoc ?? dangHoc.length) + (r?.khoa_chua_bat_dau ?? chuaBatDau.length)} color="blue" />
          <StatCard icon="✅" label="Hoàn thành" value={r?.khoa_hoan_thanh ?? hoanThanh.length} color="green" />
          <StatCard icon="🏅" label="Chứng chỉ" value={r?.tong_chung_chi ?? 0} color="purple" />
          <StatCard icon="📚" label="Tổng đăng ký" value={r?.tong_khoa_da_dang_ky ?? enrolledCourses.length} color="orange" />
        </div>

        {/* Section Quản lý đào tạo */}
        {coQuyenQuanLy && (
          <div className="border-l-4 border-blue-600 bg-blue-50 rounded-xl p-5 mb-6">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                  <span className="text-xl">⚙️</span>
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900 text-base">Quản lý đào tạo</h2>
                  <p className="text-sm text-gray-600 mt-0.5">
                    Tạo khóa học, quản lý nội dung, giao bài và theo dõi tiến độ học viên
                  </p>
                  <div className="flex flex-wrap gap-4 mt-3">
                    <Link href="/dao-tao/quan-ly" className="text-xs text-blue-700 hover:underline flex items-center gap-1">
                      <span>➕</span> Tạo khóa học mới
                    </Link>
                    <Link href="/dao-tao/quan-ly" className="text-xs text-blue-700 hover:underline flex items-center gap-1">
                      <span>📋</span> Giao bài cho đơn vị
                    </Link>
                    <Link href="/dao-tao/ky-thi/quan-ly" className="text-xs text-purple-700 hover:underline flex items-center gap-1">
                      <span>📝</span> Quản lý kỳ thi ĐGNL
                    </Link>
                  </div>
                </div>
              </div>
              <Link href="/dao-tao/quan-ly"
                className="shrink-0 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors whitespace-nowrap self-start">
                Đi đến trang quản lý
              </Link>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Link href="/dao-tao/khoa-hoc" className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl p-4 flex items-center gap-3 transition-colors">
            <span className="text-2xl">📚</span>
            <div>
              <div className="font-medium">Danh sách khóa học</div>
              <div className="text-sm text-blue-100">Tìm và đăng ký khóa học</div>
            </div>
          </Link>
          <Link href="/dao-tao/ky-thi" className="bg-purple-600 hover:bg-purple-700 text-white rounded-xl p-4 flex items-center gap-3 transition-colors">
            <span className="text-2xl">📝</span>
            <div>
              <div className="font-medium">Kỳ thi ĐGNL</div>
              <div className="text-sm text-purple-100">Đánh giá năng lực</div>
            </div>
          </Link>
          <Link href="/dao-tao/khoa-hoc" className="bg-white border border-gray-200 hover:border-orange-300 hover:bg-orange-50 rounded-xl p-4 flex items-center gap-3 transition-colors">
            <span className="text-2xl">📊</span>
            <div>
              <div className="font-medium text-gray-900">Khóa đang học</div>
              <div className="text-sm text-gray-500">Tiến độ học tập</div>
            </div>
          </Link>
        </div>

        {/* Khóa đang học + Chưa bắt đầu */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <span>📖</span> Khóa học của tôi
              {enrolledCourses.length > 0 && (
                <span className="text-xs font-normal text-gray-400">({enrolledCourses.length} khóa)</span>
              )}
            </h2>
            <Link href="/dao-tao/khoa-hoc" className="text-sm text-blue-600 hover:underline">Xem tất cả</Link>
          </div>
          <div className="p-5">
            {enrolledCourses.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <span className="text-4xl block mb-2">📭</span>
                <p>Chưa đăng ký khóa học nào</p>
                <Link href="/dao-tao/khoa-hoc" className="text-sm text-blue-600 hover:underline mt-2 inline-block">
                  Xem danh sách khóa học
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {enrolledCourses.slice(0, 6).map((dk) => {
                  const st = TRANG_THAI_LABEL[dk.trang_thai] || TRANG_THAI_LABEL.CHUA_BAT_DAU;
                  return (
                    <Link key={dk.id} href={`/dao-tao/khoa-hoc/${dk.khoa_hoc_id}`}
                      className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center shrink-0">
                        <span className="text-lg">📘</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">{dk.khoa_hoc_ten}</div>
                        <div className="text-xs text-gray-500 flex items-center gap-2">
                          <span>{dk.giang_vien_ho_ten || 'Chưa có giảng viên'}</span>
                          <span className={`px-1.5 py-0.5 rounded-full text-xs ${st.bg} ${st.text}`}>{st.label}</span>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-sm font-semibold text-blue-600">{dk.phan_tram_hoan_thanh}%</div>
                        <div className="w-20 h-1.5 bg-gray-200 rounded-full mt-1">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${dk.phan_tram_hoan_thanh}%` }} />
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Danh sách khóa học (tất cả) */}
        {allCourses.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <span>📚</span> Khóa học hiện có
              </h2>
              <Link href="/dao-tao/khoa-hoc" className="text-sm text-blue-600 hover:underline">Xem tất cả</Link>
            </div>
            <div className="p-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {allCourses.slice(0, 6).map((kh, idx) => (
                  <Link key={kh.id} href={`/dao-tao/khoa-hoc/${kh.id}`}
                    className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all overflow-hidden group">
                    <div className={`h-24 bg-gradient-to-br ${GRADIENTS[idx % GRADIENTS.length]} p-3 flex flex-col justify-between`}>
                      <div className="flex justify-between items-start">
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">Đang mở</span>
                      </div>
                      <div className="text-white font-bold text-sm line-clamp-2 group-hover:underline">{kh.ten_khoa_hoc}</div>
                    </div>
                    <div className="p-3">
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span>👨‍🏫 {kh.giang_vien_ho_ten || '—'}</span>
                        <span>📚 {kh.so_bai_hoc}</span>
                        <span>👥 {kh.so_hoc_vien}</span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Chứng chỉ gần đây */}
        {r && r.chung_chi_gan_day && r.chung_chi_gan_day.length > 0 && (
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

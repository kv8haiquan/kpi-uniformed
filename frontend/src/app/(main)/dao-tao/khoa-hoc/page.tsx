/**
 * src/app/(main)/dao-tao/khoa-hoc/page.tsx
 * =========================================
 * Danh sách khóa học — search, filter, pagination.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { khoaHocApi, chuyenDeApi, dangKyApi } from '@/services/lms';
import type { IKhoaHoc, IChuyenDe, IPagination, IDangKyKhoaHoc } from '@/types/lms';

const TRANG_THAI_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  NHAP: { label: 'Nháp', bg: 'bg-gray-100', text: 'text-gray-600' },
  CHO_DUYET: { label: 'Chờ duyệt', bg: 'bg-yellow-100', text: 'text-yellow-700' },
  DA_XUAT_BAN: { label: 'Đang mở', bg: 'bg-green-100', text: 'text-green-700' },
  TAM_DUNG: { label: 'Tạm dừng', bg: 'bg-orange-100', text: 'text-orange-700' },
  DA_DONG: { label: 'Đã đóng', bg: 'bg-red-100', text: 'text-red-700' },
};

const ENROLLMENT_STATUS_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  CHUA_BAT_DAU: { label: 'Chưa bắt đầu', bg: 'bg-gray-100', text: 'text-gray-600' },
  DANG_HOC: { label: 'Đang học', bg: 'bg-blue-100', text: 'text-blue-700' },
  HOAN_THANH: { label: 'Hoàn thành', bg: 'bg-green-100', text: 'text-green-700' },
  QUA_HAN: { label: 'Quá hạn', bg: 'bg-red-100', text: 'text-red-700' },
  CHO_PHE_DUYET: { label: 'Chờ phê duyệt', bg: 'bg-yellow-100', text: 'text-yellow-700' },
  TU_CHOI: { label: 'Bị từ chối', bg: 'bg-red-100', text: 'text-red-700' },
  BI_LOAI: { label: 'Đã bị loại', bg: 'bg-gray-100', text: 'text-gray-700' },
};

const LOAI_CONFIG: Record<string, { label: string; icon: string }> = {
  TU_HOC: { label: 'Tự học', icon: '📖' },
  BAT_BUOC: { label: 'Bắt buộc', icon: '📋' },
  TRUC_TUYEN: { label: 'Trực tuyến', icon: '💻' },
  KET_HOP: { label: 'Kết hợp', icon: '🔄' },
};

const GRADIENTS = [
  'from-blue-500 to-indigo-600', 'from-green-500 to-teal-600',
  'from-purple-500 to-pink-600', 'from-orange-500 to-red-600', 'from-cyan-500 to-blue-600',
];

export default function KhoaHocListPage() {
  const [activeTab, setActiveTab] = useState<'my-courses' | 'all-courses'>('all-courses');

  // All courses tab
  const [khoaHocs, setKhoaHocs] = useState<IKhoaHoc[]>([]);
  const [chuyenDes, setChuyenDes] = useState<IChuyenDe[]>([]);
  const [pagination, setPagination] = useState<IPagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [chuyenDeId, setChuyenDeId] = useState('');
  const [loai, setLoai] = useState('');
  const [page, setPage] = useState(1);

  // My courses tab
  const [enrolledCourses, setEnrolledCourses] = useState<IDangKyKhoaHoc[]>([]);
  const [enrolledLoading, setEnrolledLoading] = useState(false);
  const [enrolledFilter, setEnrolledFilter] = useState<string>('');

  const [enrolledError, setEnrolledError] = useState<string | null>(null);

  const loadEnrolledCourses = useCallback(async () => {
    setEnrolledLoading(true);
    setEnrolledError(null);
    try {
      const res = await dangKyApi.cuaToi();
      setEnrolledCourses(res.data.data || []);
    } catch (err: any) {
      setEnrolledError('Không thể tải khóa học của bạn.');
    } finally {
      setEnrolledLoading(false);
    }
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = { page, page_size: 12 };
      if (search) params.search = search;
      if (chuyenDeId) params.chuyen_de_id = chuyenDeId;
      if (loai) params.loai = loai;

      const [khRes, cdRes] = await Promise.all([
        khoaHocApi.danhSach(params),
        chuyenDes.length === 0 ? chuyenDeApi.danhSach({ is_active: true }) : null,
      ]);
      setKhoaHocs(khRes.data.data || []);
      setPagination(khRes.data.pagination || null);
      if (cdRes) setChuyenDes(cdRes.data.data || []);
    } catch (err: any) {
      setError('Không thể tải danh sách khóa học. Kiểm tra LMS backend (port 8001).');
    } finally {
      setLoading(false);
    }
  }, [page, search, chuyenDeId, loai]);

  // Load ca 2 tab data khi trang mo
  useEffect(() => { loadEnrolledCourses(); }, [loadEnrolledCourses]);
  useEffect(() => { loadData(); }, [loadData]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <span className="text-3xl">⚠️</span>
          <p className="mt-2 text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  const filteredEnrolled = enrolledCourses.filter((ec) => {
    if (!enrolledFilter) return true;
    return ec.trang_thai === enrolledFilter;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Breadcrumb + Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            <Link href="/dao-tao" className="hover:text-blue-600">Đào tạo</Link>
            <span>/</span>
            <span className="text-gray-900">Khóa học</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Danh sách khóa học</h1>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('my-courses')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'my-courses'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Khóa học của tôi
            {enrolledCourses.length > 0 && (
              <span className="ml-1.5 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs">{enrolledCourses.length}</span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('all-courses')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'all-courses'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Tất cả khóa học
          </button>
        </div>

        {/* My Courses Tab */}
        {activeTab === 'my-courses' && (
          <>
            {enrolledError && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-4 text-sm text-yellow-700">
                {enrolledError} Vui lòng kiểm tra kết nối LMS backend.
              </div>
            )}
            {/* Sub-filters */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-6">
              <div className="flex gap-2 flex-wrap">
                {['', 'DANG_HOC', 'CHUA_BAT_DAU', 'HOAN_THANH', 'CHO_PHE_DUYET', 'TU_CHOI'].map((status) => (
                  <button
                    key={status}
                    onClick={() => setEnrolledFilter(status)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      enrolledFilter === status
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {status === '' ? 'Tất cả' : ENROLLMENT_STATUS_CONFIG[status]?.label || status}
                  </button>
                ))}
              </div>
            </div>

            {/* Enrolled courses list */}
            {enrolledLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="bg-white rounded-xl border animate-pulse">
                    <div className="h-28 bg-gray-200 rounded-t-xl" />
                    <div className="p-4 space-y-2"><div className="h-4 bg-gray-200 rounded w-3/4" /><div className="h-3 bg-gray-200 rounded w-1/2" /></div>
                  </div>
                ))}
              </div>
            ) : filteredEnrolled.length === 0 ? (
              <div className="text-center py-16">
                <span className="text-5xl block mb-4">📚</span>
                <h3 className="text-lg font-medium text-gray-900">Chưa có khóa học nào</h3>
                <p className="text-gray-500 mt-1">
                  {enrolledFilter ? 'Không có khóa học với trạng thái này' : 'Bạn chưa đăng ký khóa học nào'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredEnrolled.map((ec, idx) => {
                  const statusCfg = ENROLLMENT_STATUS_CONFIG[ec.trang_thai] || ENROLLMENT_STATUS_CONFIG.CHUA_BAT_DAU;
                  const lo = LOAI_CONFIG[ec.khoa_hoc_loai || 'TU_HOC'] || LOAI_CONFIG.TU_HOC;
                  return (
                    <Link key={ec.id} href={`/dao-tao/khoa-hoc/${ec.khoa_hoc_id}`}
                      className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all overflow-hidden group">
                      <div className={`h-28 bg-gradient-to-br ${GRADIENTS[idx % GRADIENTS.length]} p-4 flex flex-col justify-between`}>
                        <div className="flex justify-between items-start">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusCfg.bg} ${statusCfg.text}`}>
                            {statusCfg.label}
                          </span>
                          <span className="text-white/80 text-xs">{lo.icon} {lo.label}</span>
                        </div>
                        <div className="text-white font-bold text-sm line-clamp-2 group-hover:underline">{ec.khoa_hoc_ten}</div>
                      </div>
                      <div className="p-4">
                        <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                          <span>👨‍🏫 {ec.giang_vien_ho_ten || '—'}</span>
                          <span className="font-medium">{ec.loai_dang_ky === 'TU_NGUYEN' ? '✋ Tự nguyện' : ec.loai_dang_ky === 'BAT_BUOC' ? '📋 Bắt buộc' : '📝 Giao việc'}</span>
                        </div>
                        {ec.trang_thai === 'DANG_HOC' && (
                          <div className="mt-2">
                            <div className="flex justify-between text-xs text-gray-600 mb-1">
                              <span>Tiến độ</span>
                              <span className="font-medium">{ec.phan_tram_hoan_thanh}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className="bg-blue-600 h-2 rounded-full transition-all" style={{ width: `${ec.phan_tram_hoan_thanh}%` }} />
                            </div>
                          </div>
                        )}
                        {ec.han_hoan_thanh && (
                          <div className="text-xs text-orange-600 mt-2">📅 Hạn: {new Date(ec.han_hoan_thanh).toLocaleDateString('vi-VN')}</div>
                        )}
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* All Courses Tab */}
        {activeTab === 'all-courses' && (
          <>
            {/* Filters */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-6">
              <div className="flex flex-col sm:flex-row gap-3">
                <input type="text" placeholder="Tìm kiếm khóa học..." value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && setPage(1)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm" />
                <select value={chuyenDeId} onChange={(e) => { setChuyenDeId(e.target.value); setPage(1); }}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
                  <option value="">Tất cả chuyên đề</option>
                  {chuyenDes.map((cd) => <option key={cd.id} value={cd.id}>{cd.ten_chuyen_de}</option>)}
                </select>
                <select value={loai} onChange={(e) => { setLoai(e.target.value); setPage(1); }}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
                  <option value="">Tất cả loại</option>
                  {Object.entries(LOAI_CONFIG).map(([k, v]) => <option key={k} value={k}>{v.icon} {v.label}</option>)}
                </select>
              </div>
            </div>

            {/* Loading */}
            {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-white rounded-xl border animate-pulse">
                <div className="h-28 bg-gray-200 rounded-t-xl" />
                <div className="p-4 space-y-2"><div className="h-4 bg-gray-200 rounded w-3/4" /><div className="h-3 bg-gray-200 rounded w-1/2" /></div>
              </div>
            ))}
          </div>
        )}

            {/* Empty */}
            {!loading && khoaHocs.length === 0 && (
          <div className="text-center py-16">
            <span className="text-5xl block mb-4">📭</span>
            <h3 className="text-lg font-medium text-gray-900">Không tìm thấy khóa học</h3>
            <p className="text-gray-500 mt-1">Thử thay đổi bộ lọc hoặc từ khóa</p>
          </div>
        )}

            {/* Grid */}
            {!loading && khoaHocs.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {khoaHocs.map((kh, idx) => {
                const tt = TRANG_THAI_CONFIG[kh.trang_thai] || TRANG_THAI_CONFIG.NHAP;
                const lo = LOAI_CONFIG[kh.loai] || LOAI_CONFIG.TU_HOC;
                return (
                  <Link key={kh.id} href={`/dao-tao/khoa-hoc/${kh.id}`}
                    className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all overflow-hidden group">
                    <div className={`h-28 bg-gradient-to-br ${GRADIENTS[idx % GRADIENTS.length]} p-4 flex flex-col justify-between`}>
                      <div className="flex justify-between items-start">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${tt.bg} ${tt.text}`}>{tt.label}</span>
                        <span className="text-white/80 text-xs">{lo.icon} {lo.label}</span>
                      </div>
                      <div className="text-white font-bold text-sm line-clamp-2 group-hover:underline">{kh.ten_khoa_hoc}</div>
                    </div>
                    <div className="p-4">
                      {kh.chuyen_de_ten && <div className="text-xs text-gray-500 mb-2">{kh.chuyen_de_ten}</div>}
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span>👨‍🏫 {kh.giang_vien_ho_ten || '—'}</span>
                        <span>📚 {kh.so_bai_hoc}</span>
                        <span>👥 {kh.so_hoc_vien}</span>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>

            {/* Pagination */}
            {pagination && pagination.total_pages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1}
                  className="px-3 py-1.5 border rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50">Trước</button>
                <span className="text-sm text-gray-500">Trang {page}/{pagination.total_pages} ({pagination.total_items} khóa)</span>
                <button onClick={() => setPage(Math.min(pagination.total_pages, page + 1))} disabled={page >= pagination.total_pages}
                  className="px-3 py-1.5 border rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50">Sau</button>
              </div>
            )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

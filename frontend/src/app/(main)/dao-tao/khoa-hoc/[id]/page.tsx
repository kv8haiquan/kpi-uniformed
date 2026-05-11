/**
 * src/app/(main)/dao-tao/khoa-hoc/[id]/page.tsx
 * ===============================================
 * Chi tiết khóa học — nội dung, bài kiểm tra, học viên, khảo sát.
 * Phân quyền: GV chủ khóa + QT_DAO_TAO thấy thêm tab "Học viên" + management banner.
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { khoaHocApi, baiHocApi, baiKiemTraApi, dangKyApi, chungChiApi } from '@/services/lms';
import type { IKhoaHoc, IBaiHoc, IBaiKiemTra, ILichSuThi, IChungChi } from '@/types/lms';
import KhaoSatForm from '@/components/lms/KhaoSatForm';
import KetQuaKhoaHocPanel from '@/components/lms/KetQuaKhoaHocPanel';
import { useAuthStore } from '@/stores/useAuthStore';

const TIEN_DO_ICON: Record<string, string> = {
  CHUA_XEM: '⚪',
  DANG_XEM: '🔵',
  DA_HOAN_THANH: '✅',
};

const DK_TT_CONFIG: Record<string, { label: string; cls: string }> = {
  HOAN_THANH:    { label: 'Hoàn thành',    cls: 'bg-green-100 text-green-700' },
  QUA_HAN:       { label: 'Quá hạn',       cls: 'bg-red-100 text-red-700' },
  DANG_HOC:      { label: 'Đang học',      cls: 'bg-blue-100 text-blue-700' },
  CHUA_BAT_DAU:  { label: 'Chưa bắt đầu',  cls: 'bg-gray-100 text-gray-600' },
  CHO_PHE_DUYET: { label: 'Chờ phê duyệt', cls: 'bg-yellow-100 text-yellow-700' },
  TU_CHOI:       { label: 'Bị từ chối',    cls: 'bg-red-100 text-red-700' },
  BI_LOAI:       { label: 'Đã bị loại',    cls: 'bg-gray-100 text-gray-700' },
};

type DetailTab = 'noi-dung' | 'kiem-tra' | 'thong-tin' | 'khao-sat' | 'hoc-vien' | 'chung-chi' | 'ket-qua';

const VALID_TABS: ReadonlyArray<DetailTab> = [
  'noi-dung',
  'kiem-tra',
  'thong-tin',
  'khao-sat',
  'hoc-vien',
  'chung-chi',
  'ket-qua',
];

const XEP_LOAI_CC_CONFIG: Record<string, { label: string; bg: string; icon: string }> = {
  XUAT_SAC:  { label: 'Xuất sắc',  bg: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: '🏆' },
  GIOI:      { label: 'Giỏi',      bg: 'bg-blue-100 text-blue-800 border-blue-300',       icon: '🥇' },
  KHA:       { label: 'Khá',       bg: 'bg-green-100 text-green-800 border-green-300',    icon: '🥈' },
  DAT:       { label: 'Đạt',       bg: 'bg-gray-100 text-gray-800 border-gray-300',       icon: '✅' },
  KHONG_DAT: { label: 'Không đạt', bg: 'bg-red-100 text-red-800 border-red-300',          icon: '❌' },
};

export default function KhoaHocDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const id = params.id as string;

  // Cho phép deeplink ?tab=hoc-vien (vd: từ thông báo phê duyệt LMS)
  const initialTab: DetailTab = (() => {
    const t = searchParams.get('tab');
    return t && (VALID_TABS as readonly string[]).includes(t)
      ? (t as DetailTab)
      : 'noi-dung';
  })();

  const user = useAuthStore((s) => s.user);
  const platformRoles: string[] = (user as any)?.platform_roles ?? [];
  const isAdmin    = user?.is_system_admin === true;
  const isQT       = platformRoles.includes('QT_DAO_TAO');
  const isGV       = platformRoles.includes('GIANG_VIEN');
  const isLanhDao  = (user as any)?.is_lanh_dao === true;
  const isManagerRole = isAdmin || isQT;
  const canGiaoBai    = isManagerRole || isLanhDao;

  const [khoaHoc, setKhoaHoc] = useState<IKhoaHoc | null>(null);
  const [baiHocs, setBaiHocs] = useState<IBaiHoc[]>([]);
  const [baiKiemTras, setBaiKiemTras] = useState<IBaiKiemTra[]>([]);
  const [hocViens, setHocViens] = useState<any[]>([]);
  const [hocVienPage, setHocVienPage] = useState(1);
  const HOC_VIEN_PAGE_SIZE = 20;
  const [hocVienPagination, setHocVienPagination] = useState<{
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  } | null>(null);
  const [hocViensLoading, setHocViensLoading] = useState(false);
  // Filter cho tab Học viên
  const [filterTrangThai, setFilterTrangThai] = useState<string>('');
  const [filterLoaiDangKy, setFilterLoaiDangKy] = useState<string>('');
  const [filterQ, setFilterQ] = useState<string>('');
  const [debouncedQ, setDebouncedQ] = useState<string>('');
  // Tab Chứng chỉ
  const [chungChi, setChungChi] = useState<IChungChi | null>(null);
  const [chungChiLoading, setChungChiLoading] = useState(false);
  const [chungChiLoaded, setChungChiLoaded] = useState(false);
  const [chungChiTaiLoading, setChungChiTaiLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dangKyLoading, setDangKyLoading] = useState(false);
  const [tab, setTab] = useState<DetailTab>(initialTab);
  // Lịch sử làm bài: map bktId → ILichSuThi
  const [bktLichSu, setBktLichSu] = useState<Record<string, ILichSuThi>>({});
  const [bktExpanded, setBktExpanded] = useState<string | null>(null);

  // Quyền quản lý — tính sau khi có khoaHoc
  const isGVOfCourse = isGV && khoaHoc?.giang_vien_id != null
    && khoaHoc.giang_vien_id === (user as any)?.id;
  const canManage = isManagerRole || isGVOfCourse;

  useEffect(() => {
    const load = async () => {
      try {
        const [khRes, bhRes, bktRes] = await Promise.all([
          khoaHocApi.chiTiet(id),
          baiHocApi.danhSach(id).catch(() => ({ data: { data: [] } })),
          baiKiemTraApi.danhSach(id).catch(() => ({ data: { data: [] } })),
        ]);
        setKhoaHoc(khRes.data.data);
        setBaiHocs(bhRes.data.data || []);
        setBaiKiemTras(bktRes.data.data || []);
      } catch (err: any) {
        setError(err?.response?.data?.detail?.error?.message || 'Không tìm thấy khóa học');
      } finally {
        setLoading(false);
      }
    };
    if (id) load();
  }, [id]);

  const loadHocViens = async (page: number = hocVienPage) => {
    setHocViensLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: HOC_VIEN_PAGE_SIZE };
      if (filterTrangThai) params.trang_thai = filterTrangThai;
      if (filterLoaiDangKy) params.loai_dang_ky = filterLoaiDangKy;
      if (debouncedQ) params.q = debouncedQ;
      const r = await dangKyApi.hocVien(id, params);
      setHocViens(r.data.data || []);
      setHocVienPagination(r.data.pagination ?? null);
      setHocVienPage(page);
    } catch {
      setHocViens([]);
      setHocVienPagination(null);
    } finally {
      setHocViensLoading(false);
    }
  };

  // Debounce ô search 400ms
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(filterQ.trim()), 400);
    return () => clearTimeout(t);
  }, [filterQ]);

  // Auto-load danh sách học viên — fire khi mở tab, đổi quyền, hoặc đổi filter.
  // Mỗi lần đổi filter sẽ về page 1.
  useEffect(() => {
    if (tab === 'hoc-vien' && canManage) {
      loadHocViens(1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, canManage, filterTrangThai, filterLoaiDangKy, debouncedQ]);

  const handleTabChange = (t: DetailTab) => {
    setTab(t);
  };

  const resetFilters = () => {
    setFilterTrangThai('');
    setFilterLoaiDangKy('');
    setFilterQ('');
  };
  const hasActiveFilter = !!(filterTrangThai || filterLoaiDangKy || debouncedQ);

  const loadChungChi = async () => {
    if (chungChiLoaded) return;
    setChungChiLoading(true);
    try {
      // Backend /chung-chi/cua-toi không filter theo khóa → lọc client-side
      const r = await chungChiApi.cuaToi({ page_size: 100 });
      const list: IChungChi[] = r.data.data || [];
      const found = list.find((c) => c.khoa_hoc_id === id) || null;
      setChungChi(found);
      setChungChiLoaded(true);
    } catch {
      setChungChi(null);
      setChungChiLoaded(true);
    } finally {
      setChungChiLoading(false);
    }
  };

  // Tự load cert khi mở tab chứng chỉ
  useEffect(() => {
    if (tab === 'chung-chi' && !chungChiLoaded && !chungChiLoading) {
      loadChungChi();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const handleTaiChungChi = async () => {
    if (!chungChi) return;
    setChungChiTaiLoading(true);
    try {
      const res = await chungChiApi.tai(chungChi.id);
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chung-chi-${chungChi.ma_chung_chi}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Không thể tải chứng chỉ');
    } finally {
      setChungChiTaiLoading(false);
    }
  };

  const handleDangKy = async () => {
    if (!khoaHoc) return;
    setDangKyLoading(true);
    try {
      await dangKyApi.dangKy(khoaHoc.id);
      // Reload chi tiết để cập nhật dang_ky state — UI sẽ tự chuyển sang progress bar
      const khRes = await khoaHocApi.chiTiet(id);
      setKhoaHoc(khRes.data.data);
    } catch (err: any) {
      const msg = err?.response?.data?.detail?.error?.message || 'Không thể đăng ký';
      alert(msg);
    } finally {
      setDangKyLoading(false);
    }
  };

  const handlePheDuyet = async (dangKyId: string, approve: boolean, hoTen: string) => {
    let ly_do_tu_choi: string | undefined;
    if (!approve) {
      ly_do_tu_choi = prompt('Nhập lý do từ chối:') || undefined;
      if (!ly_do_tu_choi) return;
    }
    if (!confirm(`Xác nhận ${approve ? 'phê duyệt' : 'từ chối'} đăng ký của ${hoTen}?`)) return;
    try {
      await dangKyApi.pheDuyet(dangKyId, { phe_duyet: approve, ly_do_tu_choi });
      alert(approve ? 'Đã phê duyệt thành công' : 'Đã từ chối đăng ký');
      await loadHocViens(hocVienPage);
    } catch (err: any) {
      alert(err?.response?.data?.detail?.error?.message || 'Có lỗi xảy ra');
    }
  };

  const handleLoaiHocVien = async (dangKyId: string, hoTen: string) => {
    const ly_do = prompt(`Lý do loại ${hoTen} khỏi khóa học (tùy chọn):`);
    if (ly_do === null) return;
    if (!confirm(`Xác nhận loại ${hoTen} khỏi khóa học?`)) return;
    try {
      await dangKyApi.loaiHocVien(dangKyId, ly_do || undefined);
      alert('Đã loại học viên khỏi khóa học');
      // Nếu trang hiện tại chỉ còn 1 học viên (item vừa xóa), lùi về trang trước
      const targetPage = hocViens.length === 1 && hocVienPage > 1 ? hocVienPage - 1 : hocVienPage;
      await loadHocViens(targetPage);
    } catch (err: any) {
      alert(err?.response?.data?.detail?.error?.message || 'Có lỗi xảy ra');
    }
  };

  const loadLichSuThi = async (bktId: string) => {
    if (bktLichSu[bktId]) {
      // Toggle accordion nếu đã load
      setBktExpanded((prev) => (prev === bktId ? null : bktId));
      return;
    }
    try {
      const r = await baiKiemTraApi.lichSuThi(bktId);
      const data: ILichSuThi = r.data.data;
      setBktLichSu((prev) => ({ ...prev, [bktId]: data }));
      setBktExpanded(bktId);
    } catch {
      // Im lang neu loi
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error || !khoaHoc) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <span className="text-3xl">⚠️</span>
          <p className="mt-2 text-red-700">{error || 'Không tìm thấy'}</p>
          <Link href="/dao-tao/khoa-hoc" className="text-blue-600 hover:underline mt-2 inline-block">Quay lại</Link>
        </div>
      </div>
    );
  }

  const kh = khoaHoc;

  const daHoanThanh = kh.dang_ky?.trang_thai === 'HOAN_THANH';
  const tabs: { key: DetailTab; label: string; count: number | null }[] = [
    { key: 'noi-dung',  label: '📚 Nội dung',  count: baiHocs.length },
    { key: 'kiem-tra',  label: '📝 Kiểm tra',  count: baiKiemTras.length },
    { key: 'thong-tin', label: 'ℹ️ Thông tin', count: null },
    ...(kh.dang_ky   ? [{ key: 'khao-sat' as DetailTab, label: '⭐ Khảo sát', count: null }] : []),
    ...(daHoanThanh  ? [{ key: 'chung-chi' as DetailTab, label: '🎓 Chứng chỉ', count: null }] : []),
    ...(canManage    ? [{ key: 'hoc-vien' as DetailTab, label: '👥 Học viên', count: kh.so_hoc_vien }] : []),
    ...(canManage    ? [{ key: 'ket-qua' as DetailTab, label: '📊 Kết quả',   count: null }] : []),
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {/* Breadcrumb + Back button */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 flex-wrap">
            <Link href="/dao-tao" className="hover:text-blue-600">Đào tạo</Link>
            <span>/</span>
            <Link href="/dao-tao/khoa-hoc" className="hover:text-blue-600">Khóa học</Link>
            <span>/</span>
            <span className="text-gray-900 truncate max-w-xs">{kh.ten_khoa_hoc}</span>
          </div>
          <button
            onClick={() => router.back()}
            className="shrink-0 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          >
            ← Quay lại
          </button>
        </div>

        {/* Management banner — chỉ hiện cho GV chủ khóa / QT_DAO_TAO / Admin */}
        {canManage && (
          <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 mb-4">
            <div className="flex items-center gap-2 text-sm text-blue-800">
              <span>⚙️</span>
              <span className="font-medium">
                {isGVOfCourse && !isManagerRole
                  ? 'Bạn là giảng viên của khóa học này'
                  : 'Chế độ quản lý — bạn có quyền chỉnh sửa khóa học này'}
              </span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {canGiaoBai && (
                <Link
                  href="/dao-tao/quan-ly"
                  className="px-3 py-1.5 bg-white border border-blue-300 text-blue-700 rounded-lg text-xs font-medium hover:bg-blue-50 transition-colors"
                >
                  📋 Giao bài
                </Link>
              )}
              <Link
                href="/dao-tao/quan-ly"
                className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors"
              >
                ⚙️ Quản lý khóa này
              </Link>
            </div>
          </div>
        )}

        {/* Hero card */}
        <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-6 text-white mb-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <span className="px-2 py-0.5 bg-white/20 rounded-full text-xs font-medium">{kh.loai}</span>
              <h1 className="text-2xl font-bold mt-2">{kh.ten_khoa_hoc}</h1>
              {kh.mo_ta && <p className="text-blue-100 mt-2 text-sm line-clamp-3">{kh.mo_ta}</p>}
              <div className="flex flex-wrap items-center gap-4 mt-4 text-sm text-blue-100">
                <span>👨‍🏫 {kh.giang_vien_ho_ten || 'Chưa có GV'}</span>
                <span>📚 {kh.so_bai_hoc} bài học</span>
                <span>👥 {kh.so_hoc_vien} học viên</span>
                {kh.thoi_luong_phut && <span>⏱️ {kh.thoi_luong_phut} phút</span>}
              </div>
            </div>

            {/* Bên phải: nút đăng ký (khi chưa đăng ký) hoặc progress (khi đã đăng ký) */}
            <div className="shrink-0">
              {!kh.dang_ky ? (
                <button
                  onClick={handleDangKy}
                  disabled={dangKyLoading}
                  className="px-6 py-3 bg-white text-blue-700 rounded-xl font-semibold hover:bg-blue-50 transition-colors disabled:opacity-50"
                >
                  {dangKyLoading ? 'Đang xử lý...' : 'Đăng ký học'}
                </button>
              ) : (
                <div className="text-center px-5 py-3 bg-white/20 rounded-xl min-w-[100px]">
                  <div className="text-2xl font-bold">{kh.dang_ky.phan_tram_hoan_thanh}%</div>
                  <div className="text-xs text-blue-100 mt-0.5">Hoàn thành</div>
                  <div className="w-full h-1.5 bg-white/30 rounded-full mt-2">
                    <div
                      className="h-full bg-white rounded-full transition-all"
                      style={{ width: `${kh.dang_ky.phan_tram_hoan_thanh}%` }}
                    />
                  </div>
                  <div className="text-xs text-blue-100 mt-1">
                    {kh.dang_ky.trang_thai === 'HOAN_THANH' ? '✅ Đã hoàn thành' :
                     kh.dang_ky.trang_thai === 'QUA_HAN'    ? '⚠️ Quá hạn' :
                                                              '📖 Đang học'}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Status banners for student — after hero card */}
        {kh.dang_ky?.trang_thai === 'CHO_PHE_DUYET' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl px-5 py-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-xl">⏳</span>
              <div>
                <p className="font-medium text-yellow-800">Đang chờ phê duyệt</p>
                <p className="text-sm text-yellow-700 mt-0.5">Đăng ký của bạn đang chờ phê duyệt. Bạn sẽ nhận thông báo khi được duyệt.</p>
              </div>
            </div>
          </div>
        )}

        {kh.dang_ky?.trang_thai === 'TU_CHOI' && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-xl">❌</span>
              <div>
                <p className="font-medium text-red-800">Đăng ký bị từ chối</p>
                {kh.dang_ky.ly_do_tu_choi && <p className="text-sm text-red-700 mt-0.5">Lý do: {kh.dang_ky.ly_do_tu_choi}</p>}
              </div>
            </div>
          </div>
        )}

        {kh.dang_ky?.trang_thai === 'BI_LOAI' && (
          <div className="bg-gray-50 border border-gray-300 rounded-xl px-5 py-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-xl">🚫</span>
              <div>
                <p className="font-medium text-gray-800">Bạn đã bị loại khỏi khóa học này</p>
                {kh.dang_ky.ly_do_tu_choi && <p className="text-sm text-gray-600 mt-0.5">Lý do: {kh.dang_ky.ly_do_tu_choi}</p>}
              </div>
            </div>
          </div>
        )}

        {/* Info Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { icon: '📝', label: 'Điểm đạt',  value: `${kh.diem_dat_yeu_cau}%` },
            { icon: '📅', label: 'Bắt đầu',   value: kh.ngay_bat_dau || '—' },
            { icon: '📅', label: 'Kết thúc',  value: kh.ngay_ket_thuc || '—' },
            { icon: '🏷️', label: 'Mã khóa',   value: kh.ma_khoa_hoc },
          ].map((item, i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-3 text-center">
              <span className="text-lg">{item.icon}</span>
              <div className="text-xs text-gray-500 mt-1">{item.label}</div>
              <div className="text-sm font-semibold text-gray-900 mt-0.5 truncate">{item.value}</div>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1 flex-wrap">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => handleTabChange(t.key)}
              className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                tab === t.key
                  ? 'bg-white shadow-sm text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t.label}
              {t.count !== null && (
                <span className="ml-1 text-xs opacity-70">({t.count})</span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">

          {/* ── Nội dung ─────────────────────────────────── */}
          {tab === 'noi-dung' && (
            <div className="p-5">
              {baiHocs.length === 0 ? (
                <div className="text-center py-8 text-gray-500">Chưa có bài học</div>
              ) : (
                <div className="space-y-2">
                  {baiHocs.map((bh) => {
                    const td = bh.tien_do_ca_nhan;
                    const icon = TIEN_DO_ICON[td?.trang_thai || 'CHUA_XEM'] || '⚪';
                    const canAccessLesson = kh.dang_ky && !['CHO_PHE_DUYET', 'TU_CHOI', 'BI_LOAI'].includes(kh.dang_ky.trang_thai);
                    const previewLesson = canManage && !canAccessLesson;
                    const inner = (
                      <>
                        <span className="text-lg shrink-0">{icon}</span>
                        <span className="text-xs text-gray-400 w-6 text-right shrink-0">{bh.thu_tu}.</span>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate">{bh.tieu_de}</div>
                          <div className="text-xs text-gray-500">
                            {bh.loai_noi_dung}
                            {bh.thoi_luong_phut ? ` • ${bh.thoi_luong_phut} phút` : ''}
                          </div>
                        </div>
                        {td?.trang_thai === 'DA_HOAN_THANH' && (
                          <span className="text-xs text-green-600 font-medium shrink-0">✓ Hoàn thành</span>
                        )}
                        {previewLesson && (
                          <span className="text-xs text-yellow-700 font-medium shrink-0 bg-yellow-100 px-1.5 py-0.5 rounded">Xem thử</span>
                        )}
                        {(canAccessLesson || previewLesson) && (
                          <span className="text-gray-300 shrink-0 text-xs">›</span>
                        )}
                      </>
                    );
                    const href = previewLesson
                      ? `/dao-tao/khoa-hoc/${id}/bai-hoc/${bh.id}?preview=1`
                      : `/dao-tao/khoa-hoc/${id}/bai-hoc/${bh.id}`;
                    return (canAccessLesson || previewLesson) ? (
                      <Link
                        key={bh.id}
                        href={href}
                        className="flex items-center gap-3 p-3 rounded-lg hover:bg-blue-50 hover:border-blue-200 border border-transparent transition-colors cursor-pointer"
                      >
                        {inner}
                      </Link>
                    ) : (
                      <div
                        key={bh.id}
                        title={!kh.dang_ky ? "Đăng ký khóa học để xem nội dung" : "Đăng ký của bạn chưa được phê duyệt hoặc bị từ chối"}
                        className="flex items-center gap-3 p-3 rounded-lg opacity-70 cursor-not-allowed"
                      >
                        {inner}
                      </div>
                    );
                  })}
                  {!kh.dang_ky && (
                    <p className="text-xs text-center text-gray-400 pt-2">
                      Đăng ký khóa học để truy cập bài học
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ── Kiểm tra ─────────────────────────────────── */}
          {tab === 'kiem-tra' && (
            <div className="p-5">
              {baiKiemTras.length === 0 ? (
                <div className="text-center py-8 text-gray-500">Chưa có bài kiểm tra</div>
              ) : (
                <div className="space-y-3">
                  {baiKiemTras.map((bkt) => {
                    const soLan = bkt.so_lan_da_lam ?? 0;
                    const soLanMax = bkt.so_lan_lam_toi_da ?? 3;
                    const diemCaoNhat = bkt.diem_cao_nhat;
                    const daDat = bkt.da_dat ?? false;
                    const conLuot = soLan < soLanMax;
                    const lichSu = bktLichSu[bkt.id];
                    const isExpanded = bktExpanded === bkt.id;
                    const laThucHanh = bkt.loai_bai_kiem_tra === 'THUC_HANH';
                    const trangThaiCham = bkt.trang_thai_cham_moi_nhat;

                    return (
                      <div key={bkt.id} className="border rounded-lg overflow-hidden">
                        {/* Header hàng BKT */}
                        <div className="flex items-center gap-4 p-4 hover:bg-gray-50">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                            laThucHanh ? 'bg-orange-100' : 'bg-purple-100'
                          }`}>
                            <span className="text-lg">{
                              daDat ? '✅' :
                              laThucHanh && trangThaiCham === 'CHO_CHAM' ? '⏳' :
                              soLan > 0 ? '🔄' :
                              laThucHanh ? '🎬' : '📝'
                            }</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-medium text-gray-900">{bkt.tieu_de}</span>
                              <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                                laThucHanh ? 'bg-orange-100 text-orange-700' : 'bg-blue-100 text-blue-700'
                              }`}>
                                {laThucHanh ? 'Thực hành' : 'Trắc nghiệm'}
                              </span>
                              {laThucHanh && trangThaiCham === 'CHO_CHAM' && (
                                <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-700">Chờ chấm</span>
                              )}
                              {laThucHanh && trangThaiCham === 'DA_CHAM' && (
                                <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">Đã chấm</span>
                              )}
                            </div>
                            <div className="text-xs text-gray-500 mt-0.5">
                              {laThucHanh
                                ? `Nộp video · ≤ ${bkt.dung_luong_toi_da_mb ?? 500} MB · ${bkt.dinh_dang_cho_phep || 'mp4,mov,webm'}`
                                : `${bkt.so_cau_hoi} câu`}
                              {' • '}
                              {bkt.thoi_gian_lam_bai_phut ? `${bkt.thoi_gian_lam_bai_phut} phút` : 'Không giới hạn'}
                              {' • '}
                              Đạt: {bkt.diem_dat}%
                            </div>
                            {/* Thông kê cá nhân — chỉ hiện khi đã đăng ký */}
                            {kh.dang_ky && soLan > 0 && (
                              <div className="flex items-center gap-2 mt-1 text-xs">
                                <span className="text-gray-500">
                                  Lượt: {soLan}/{soLanMax}
                                </span>
                                {diemCaoNhat != null && (
                                  <span className="text-gray-500">
                                    • Điểm cao nhất: <span className="font-medium text-gray-700">{Number(diemCaoNhat).toFixed(1)}</span>
                                  </span>
                                )}
                                <span className={daDat ? 'text-green-600 font-medium' : 'text-red-500'}>
                                  {daDat ? '✓ Đạt' : '✗ Chưa đạt'}
                                </span>
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            {/* Nút xem lịch sử */}
                            {kh.dang_ky && soLan > 0 && (
                              <button
                                onClick={() => loadLichSuThi(bkt.id)}
                                className="px-3 py-1.5 text-xs text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                                title="Xem lịch sử làm bài"
                              >
                                {isExpanded ? '▲ Ẩn' : `▼ ${soLan} lần`}
                              </button>
                            )}
                            {/* Nút xem thử cho GV / QT / Admin */}
                            {canManage && (
                              <Link
                                href={`/dao-tao/khoa-hoc/${id}/kiem-tra/${bkt.id}?preview=1`}
                                target="_blank"
                                className="px-3 py-1.5 text-xs border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                                title="Xem thử như học viên (không lưu kết quả)"
                              >
                                👁 Xem thử
                              </Link>
                            )}
                            {/* Nút hành động */}
                            {kh.dang_ky ? (
                              conLuot ? (
                                <Link
                                  href={`/dao-tao/khoa-hoc/${id}/kiem-tra/${bkt.id}`}
                                  className={`px-4 py-2 text-white rounded-lg text-sm font-medium transition-colors ${
                                    laThucHanh ? 'bg-orange-600 hover:bg-orange-700' : 'bg-purple-600 hover:bg-purple-700'
                                  }`}
                                >
                                  {laThucHanh
                                    ? (soLan === 0 ? 'Nộp video' : 'Nộp lại')
                                    : (soLan === 0 ? 'Làm bài' : 'Làm lại')}
                                </Link>
                              ) : (
                                <span className="px-4 py-2 bg-gray-100 text-gray-400 rounded-lg text-sm cursor-not-allowed">
                                  Hết lượt
                                </span>
                              )
                            ) : (
                              !canManage && <span className="text-xs text-gray-400">Đăng ký để làm bài</span>
                            )}
                          </div>
                        </div>

                        {/* Accordion lịch sử làm bài */}
                        {isExpanded && lichSu && lichSu.lich_su.length > 0 && (
                          <div className="border-t bg-gray-50 px-4 py-3">
                            <div className="text-xs font-medium text-gray-500 mb-2">Lịch sử làm bài</div>
                            <div className="space-y-2">
                              {lichSu.lich_su.map((ls) => {
                                const choCham = laThucHanh && ls.trang_thai_cham === 'CHO_CHAM';
                                const daCham = laThucHanh && ls.trang_thai_cham === 'DA_CHAM';
                                return (
                                  <div key={ls.id} className="bg-white rounded-lg border border-gray-100 overflow-hidden">
                                    <div className="flex items-center gap-3 text-xs py-1.5 px-3 flex-wrap">
                                      <span className="text-gray-400 w-12 shrink-0">Lần {ls.lan_thu}</span>
                                      <span className="font-medium text-gray-700 w-16 shrink-0">
                                        {ls.diem != null ? `${Number(ls.diem).toFixed(1)} điểm` : '—'}
                                      </span>
                                      {ls.so_cau_dung != null && (
                                        <span className="text-gray-500 shrink-0">
                                          {ls.so_cau_dung} đúng / {(ls.so_cau_dung + (ls.so_cau_sai ?? 0))} câu
                                        </span>
                                      )}
                                      {ls.thoi_gian_lam_giay != null && (
                                        <span className="text-gray-400 shrink-0">
                                          {Math.floor(ls.thoi_gian_lam_giay / 60)}:{String(ls.thoi_gian_lam_giay % 60).padStart(2, '0')} phút
                                        </span>
                                      )}
                                      {laThucHanh && ls.bai_nop_url && (
                                        <a
                                          href={ls.bai_nop_url}
                                          target="_blank"
                                          rel="noreferrer"
                                          className="text-blue-600 hover:underline shrink-0"
                                          title={ls.bai_nop_ten_file || 'Xem bài nộp'}
                                        >
                                          🎬 Xem bài nộp
                                        </a>
                                      )}
                                      {choCham ? (
                                        <span className="shrink-0 px-2 py-0.5 rounded-full font-medium bg-yellow-100 text-yellow-700">
                                          ⏳ Chờ chấm
                                        </span>
                                      ) : (
                                        <span className={`shrink-0 px-2 py-0.5 rounded-full font-medium ${ls.dat_yeu_cau ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                                          {ls.dat_yeu_cau ? '✓ Đạt' : '✗ Không đạt'}
                                        </span>
                                      )}
                                      {(ls.ngay_cham && daCham) ? (
                                        <span className="text-gray-400 ml-auto shrink-0">
                                          Chấm: {new Date(ls.ngay_cham).toLocaleDateString('vi-VN')}
                                        </span>
                                      ) : ls.ngay_lam ? (
                                        <span className="text-gray-400 ml-auto shrink-0">
                                          {new Date(ls.ngay_lam).toLocaleDateString('vi-VN')}
                                        </span>
                                      ) : null}
                                    </div>
                                    {/* Nhận xét của giảng viên — chỉ THỰC HÀNH đã chấm */}
                                    {laThucHanh && ls.nhan_xet && ls.nhan_xet.trim() && (
                                      <div className="border-t border-gray-100 bg-blue-50/60 px-3 py-2">
                                        <div className="flex items-start gap-2 text-xs">
                                          <span className="text-blue-700 font-medium shrink-0">💬 Nhận xét của giảng viên:</span>
                                          <span className="text-gray-800 whitespace-pre-wrap break-words">{ls.nhan_xet}</span>
                                        </div>
                                      </div>
                                    )}
                                    {/* Chờ chấm — báo cho học viên */}
                                    {choCham && !ls.nhan_xet && (
                                      <div className="border-t border-gray-100 bg-yellow-50/60 px-3 py-1.5 text-xs text-yellow-800">
                                        Bài đang chờ giảng viên chấm và nhận xét.
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {!kh.dang_ky && (
                    <p className="text-xs text-center text-gray-400 pt-1">
                      Đăng ký khóa học để làm bài kiểm tra
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ── Thông tin ─────────────────────────────────── */}
          {tab === 'thong-tin' && (
            <div className="p-5 space-y-4">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Thông tin chung</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div><span className="text-gray-500">Mã:</span> <span className="font-medium">{kh.ma_khoa_hoc}</span></div>
                  <div><span className="text-gray-500">Loại:</span> <span className="font-medium">{kh.loai}</span></div>
                  <div><span className="text-gray-500">Giảng viên:</span> <span className="font-medium">{kh.giang_vien_ho_ten || '—'}</span></div>
                  <div><span className="text-gray-500">Chuyên đề:</span> <span className="font-medium">{kh.chuyen_de_ten || '—'}</span></div>
                  {kh.nguoi_duyet_ho_ten && (
                    <div><span className="text-gray-500">Người duyệt:</span> <span className="font-medium">{kh.nguoi_duyet_ho_ten}</span></div>
                  )}
                </div>
              </div>
              {kh.dieu_kien_tien_quyet && kh.dieu_kien_tien_quyet.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Điều kiện tiên quyết</h3>
                  <p className="text-sm text-gray-600">Cần hoàn thành {kh.dieu_kien_tien_quyet.length} khóa học trước.</p>
                </div>
              )}
              {kh.dang_ky && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Trạng thái học của bạn</h3>
                  <div className="flex flex-wrap gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Loại đăng ký: </span>
                      <span className="font-medium">
                        {kh.dang_ky.loai_dang_ky === 'GIAO_BAI' ? 'Được giao bài' : 'Tự nguyện'}
                      </span>
                    </div>
                    {kh.dang_ky.han_hoan_thanh && (
                      <div>
                        <span className="text-gray-500">Hạn hoàn thành: </span>
                        <span className="font-medium">
                          {new Date(kh.dang_ky.han_hoan_thanh).toLocaleDateString('vi-VN')}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Khảo sát ─────────────────────────────────── */}
          {tab === 'khao-sat' && kh.dang_ky && (
            <div className="p-5">
              {kh.dang_ky.trang_thai === 'HOAN_THANH' ? (
                <KhaoSatForm khoaHocId={kh.id} />
              ) : (
                <div className="text-center py-14">
                  <div className="text-5xl mb-4">🔒</div>
                  <h3 className="text-lg font-semibold text-gray-700">Chưa thể khảo sát</h3>
                  <p className="text-gray-500 mt-2 text-sm">
                    Hoàn thành 100% khóa học để mở khóa phần khảo sát.
                  </p>
                  <div className="mt-4 w-48 mx-auto bg-gray-100 rounded-full h-2.5">
                    <div
                      className="bg-blue-500 h-2.5 rounded-full transition-all"
                      style={{ width: `${kh.dang_ky.phan_tram_hoan_thanh ?? 0}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Tiến độ hiện tại: {kh.dang_ky.phan_tram_hoan_thanh ?? 0}%
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ── Học viên (GV/QT only) ─────────────────────── */}
          {tab === 'hoc-vien' && canManage && (
            <div className="p-5">
              {/* Filter bar */}
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <div className="relative flex-1 min-w-[180px]">
                  <input
                    type="text"
                    value={filterQ}
                    onChange={(e) => setFilterQ(e.target.value)}
                    placeholder="🔍 Tìm theo họ tên hoặc mã CC..."
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                  {filterQ && (
                    <button
                      onClick={() => setFilterQ('')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 text-sm"
                      title="Xóa từ khóa"
                    >
                      ✕
                    </button>
                  )}
                </div>
                <select
                  value={filterTrangThai}
                  onChange={(e) => setFilterTrangThai(e.target.value)}
                  className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Tất cả trạng thái</option>
                  <option value="CHO_PHE_DUYET">⏳ Chờ phê duyệt</option>
                  <option value="CHUA_BAT_DAU">⚪ Chưa bắt đầu</option>
                  <option value="DANG_HOC">📖 Đang học</option>
                  <option value="HOAN_THANH">✅ Hoàn thành</option>
                  <option value="QUA_HAN">⚠️ Quá hạn</option>
                  <option value="TU_CHOI">❌ Bị từ chối</option>
                </select>
                <select
                  value={filterLoaiDangKy}
                  onChange={(e) => setFilterLoaiDangKy(e.target.value)}
                  className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Tất cả loại đăng ký</option>
                  <option value="GIAO_BAI">Giao bài</option>
                  <option value="TU_NGUYEN">Tự nguyện</option>
                </select>
                {hasActiveFilter && (
                  <button
                    onClick={resetFilters}
                    className="px-3 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    title="Xóa tất cả filter"
                  >
                    ↺ Xóa lọc
                  </button>
                )}
                {/* Shortcut: lọc nhanh chờ phê duyệt */}
                {filterTrangThai !== 'CHO_PHE_DUYET' && (
                  <button
                    onClick={() => setFilterTrangThai('CHO_PHE_DUYET')}
                    className="px-3 py-2 text-sm bg-yellow-50 text-yellow-800 border border-yellow-200 rounded-lg hover:bg-yellow-100 transition-colors"
                    title="Chỉ hiển thị đăng ký chờ phê duyệt"
                  >
                    ⏳ Chỉ chờ duyệt
                  </button>
                )}
              </div>

              {hocViensLoading && hocViens.length === 0 ? (
                <div className="flex items-center justify-center py-10">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
                </div>
              ) : hocViens.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {hasActiveFilter
                    ? 'Không tìm thấy học viên phù hợp với bộ lọc'
                    : 'Chưa có học viên nào'}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-gray-500">Họ tên</th>
                        <th className="px-4 py-3 text-center font-medium text-gray-500">Loại</th>
                        <th className="px-4 py-3 text-center font-medium text-gray-500">Trạng thái</th>
                        <th className="px-4 py-3 text-center font-medium text-gray-500">Tiến độ</th>
                        <th className="px-4 py-3 text-center font-medium text-gray-500">Hạn HT</th>
                        <th className="px-4 py-3 text-center font-medium text-gray-500">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {hocViens.map((hv: any, i: number) => {
                        const dkTT = DK_TT_CONFIG[hv.trang_thai] ?? DK_TT_CONFIG.CHUA_BAT_DAU;
                        const hoTen = hv.ho_ten ?? hv.cong_chuc_ho_ten ?? '—';
                        const dangKyId = hv.dang_ky_id;
                        return (
                          <tr key={hv.id ?? i} className="hover:bg-gray-50">
                            <td className="px-4 py-3 font-medium text-gray-900">
                              {hoTen}
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                hv.loai_dang_ky === 'GIAO_BAI'
                                  ? 'bg-purple-100 text-purple-700'
                                  : 'bg-blue-100 text-blue-700'
                              }`}>
                                {hv.loai_dang_ky === 'GIAO_BAI' ? 'Giao bài' : 'Tự nguyện'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${dkTT.cls}`}>
                                {dkTT.label}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <div className="flex items-center gap-2 justify-center">
                                <div className="w-20 h-1.5 bg-gray-100 rounded-full">
                                  <div
                                    className="h-full bg-blue-500 rounded-full"
                                    style={{ width: `${hv.phan_tram_hoan_thanh ?? 0}%` }}
                                  />
                                </div>
                                <span className="text-xs text-gray-500 w-8">
                                  {hv.phan_tram_hoan_thanh ?? 0}%
                                </span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-center text-xs text-gray-500">
                              {hv.han_hoan_thanh
                                ? new Date(hv.han_hoan_thanh).toLocaleDateString('vi-VN')
                                : '—'}
                            </td>
                            <td className="px-4 py-3 text-center">
                              <div className="flex items-center gap-1 justify-center">
                                {/* Nút phê duyệt/từ chối cho trạng thái CHO_PHE_DUYET */}
                                {hv.trang_thai === 'CHO_PHE_DUYET' && dangKyId && (
                                  <>
                                    <button
                                      onClick={() => handlePheDuyet(dangKyId, true, hoTen)}
                                      className="px-2 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition-colors"
                                      title="Duyệt"
                                    >
                                      ✓ Duyệt
                                    </button>
                                    <button
                                      onClick={() => handlePheDuyet(dangKyId, false, hoTen)}
                                      className="px-2 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition-colors"
                                      title="Từ chối"
                                    >
                                      ✗ Từ chối
                                    </button>
                                  </>
                                )}
                                {/* Nút loại khỏi khóa cho các trạng thái khác (trừ BI_LOAI) */}
                                {hv.trang_thai !== 'BI_LOAI' && hv.trang_thai !== 'CHO_PHE_DUYET' && dangKyId && (
                                  <button
                                    onClick={() => handleLoaiHocVien(dangKyId, hoTen)}
                                    className="px-2 py-1 bg-gray-600 text-white rounded text-xs hover:bg-gray-700 transition-colors"
                                    title="Loại khỏi khóa"
                                  >
                                    🚫 Loại
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Phân trang học viên */}
              {hocVienPagination && hocVienPagination.total_items > 0 && (
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-4 pt-3 border-t border-gray-100">
                  <div className="text-xs text-gray-500">
                    Hiển thị{' '}
                    <span className="font-medium text-gray-700">
                      {(hocVienPagination.page - 1) * hocVienPagination.page_size + 1}
                      –
                      {Math.min(
                        hocVienPagination.page * hocVienPagination.page_size,
                        hocVienPagination.total_items
                      )}
                    </span>{' '}
                    / <span className="font-medium text-gray-700">{hocVienPagination.total_items}</span> học viên
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => loadHocViens(1)}
                      disabled={hocViensLoading || hocVienPagination.page <= 1}
                      className="px-2 py-1 text-xs border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                      title="Trang đầu"
                    >
                      «
                    </button>
                    <button
                      onClick={() => loadHocViens(hocVienPagination.page - 1)}
                      disabled={hocViensLoading || hocVienPagination.page <= 1}
                      className="px-3 py-1 text-xs border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      ‹ Trước
                    </button>
                    {/* Số trang gần kề (tối đa 5 nút) */}
                    {(() => {
                      const total = hocVienPagination.total_pages;
                      const cur = hocVienPagination.page;
                      const start = Math.max(1, Math.min(cur - 2, total - 4));
                      const end = Math.min(total, start + 4);
                      const pages: number[] = [];
                      for (let p = start; p <= end; p++) pages.push(p);
                      return pages.map((p) => (
                        <button
                          key={p}
                          onClick={() => loadHocViens(p)}
                          disabled={hocViensLoading || p === cur}
                          className={`px-3 py-1 text-xs border rounded transition-colors ${
                            p === cur
                              ? 'bg-blue-600 text-white border-blue-600 cursor-default'
                              : 'border-gray-200 hover:bg-gray-50'
                          }`}
                        >
                          {p}
                        </button>
                      ));
                    })()}
                    <button
                      onClick={() => loadHocViens(hocVienPagination.page + 1)}
                      disabled={hocViensLoading || hocVienPagination.page >= hocVienPagination.total_pages}
                      className="px-3 py-1 text-xs border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Sau ›
                    </button>
                    <button
                      onClick={() => loadHocViens(hocVienPagination.total_pages)}
                      disabled={hocViensLoading || hocVienPagination.page >= hocVienPagination.total_pages}
                      className="px-2 py-1 text-xs border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                      title="Trang cuối"
                    >
                      »
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Chứng chỉ (chỉ học viên đã hoàn thành) ─────────── */}
          {tab === 'chung-chi' && daHoanThanh && (
            <div className="p-5">
              {chungChiLoading ? (
                <div className="flex items-center justify-center py-10">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
                </div>
              ) : !chungChi ? (
                <div className="text-center py-10">
                  <span className="text-5xl block mb-3">⏳</span>
                  <p className="text-gray-700 font-medium">Đang xử lý cấp chứng chỉ...</p>
                  <p className="text-gray-500 text-sm mt-1">
                    Hệ thống sẽ tự động cấp chứng chỉ trong ít phút sau khi bạn hoàn thành khóa.
                  </p>
                </div>
              ) : (
                <div className="max-w-xl mx-auto bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                  <div className="h-3 bg-gradient-to-r from-yellow-400 via-green-400 to-blue-500" />
                  <div className="p-6">
                    {(() => {
                      const xl = XEP_LOAI_CC_CONFIG[chungChi.xep_loai || 'DAT'] || XEP_LOAI_CC_CONFIG.DAT;
                      return (
                        <>
                          <div className="flex items-start justify-between mb-4">
                            <div>
                              <span className="text-3xl">{xl.icon}</span>
                              <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-bold border ${xl.bg}`}>
                                {xl.label}
                              </span>
                            </div>
                            <div className="text-right">
                              <div className="text-3xl font-bold text-gray-900">
                                {chungChi.diem_dat != null ? Number(chungChi.diem_dat).toFixed(2) : '—'}
                              </div>
                              <div className="text-xs text-gray-500">điểm / 100</div>
                            </div>
                          </div>
                          <h3 className="font-medium text-gray-900 mb-3">
                            {chungChi.khoa_hoc_ten || kh.ten_khoa_hoc}
                          </h3>
                          <div className="text-sm text-gray-600 space-y-1 mb-5">
                            <div>
                              Mã chứng chỉ: <span className="font-mono font-semibold text-gray-900">{chungChi.ma_chung_chi}</span>
                            </div>
                            <div>
                              Cấp ngày:{' '}
                              <span className="font-medium">
                                {chungChi.ngay_cap ? new Date(chungChi.ngay_cap).toLocaleDateString('vi-VN') : '—'}
                              </span>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={handleTaiChungChi}
                              disabled={chungChiTaiLoading}
                              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                            >
                              {chungChiTaiLoading ? 'Đang tải...' : '⬇ Tải PDF'}
                            </button>
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(chungChi.ma_chung_chi);
                                alert('Đã sao chép mã chứng chỉ');
                              }}
                              className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
                              title="Sao chép mã để xác minh"
                            >
                              📋 Sao chép mã
                            </button>
                          </div>
                          <p className="text-xs text-gray-400 mt-3 text-center">
                            Có thể xác minh chứng chỉ tại{' '}
                            <Link href="/dao-tao/chung-chi" className="text-blue-600 hover:underline">
                              trang xác minh
                            </Link>
                          </p>
                        </>
                      );
                    })()}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Kết quả (GV/QT/Admin chấm bài) ─────────────────── */}
          {tab === 'ket-qua' && canManage && (
            <div className="p-5">
              <KetQuaKhoaHocPanel khoaHocId={id} />
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

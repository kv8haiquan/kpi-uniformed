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
import { khoaHocApi, baiHocApi, baiKiemTraApi, dangKyApi } from '@/services/lms';
import type { IKhoaHoc, IBaiHoc, IBaiKiemTra, ILichSuThi } from '@/types/lms';
import KhaoSatForm from '@/components/lms/KhaoSatForm';
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

type DetailTab = 'noi-dung' | 'kiem-tra' | 'thong-tin' | 'khao-sat' | 'hoc-vien';

const VALID_TABS: ReadonlyArray<DetailTab> = [
  'noi-dung',
  'kiem-tra',
  'thong-tin',
  'khao-sat',
  'hoc-vien',
];

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
  const [hocViensLoaded, setHocViensLoaded] = useState(false);
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

  const loadHocViens = async () => {
    if (hocViensLoaded) return;
    try {
      const r = await dangKyApi.hocVien(id, { page_size: 100 });
      setHocViens(r.data.data || []);
      setHocViensLoaded(true);
    } catch {
      setHocViens([]);
      setHocViensLoaded(true);
    }
  };

  // Auto-load danh sách học viên khi user vào trang với ?tab=hoc-vien
  // (vd: từ thông báo phê duyệt LMS) — chờ khoaHoc + quyền sẵn sàng.
  useEffect(() => {
    if (tab === 'hoc-vien' && canManage && !hocViensLoaded) {
      loadHocViens();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, canManage, hocViensLoaded]);

  const handleTabChange = (t: DetailTab) => {
    setTab(t);
    if (t === 'hoc-vien') loadHocViens();
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
      // Reload học viên list
      await loadHocViens();
      setHocViensLoaded(false);
      await loadHocViens();
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
      // Reload học viên list
      setHocViensLoaded(false);
      await loadHocViens();
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

  const tabs: { key: DetailTab; label: string; count: number | null }[] = [
    { key: 'noi-dung',  label: '📚 Nội dung',  count: baiHocs.length },
    { key: 'kiem-tra',  label: '📝 Kiểm tra',  count: baiKiemTras.length },
    { key: 'thong-tin', label: 'ℹ️ Thông tin', count: null },
    ...(kh.dang_ky   ? [{ key: 'khao-sat' as DetailTab, label: '⭐ Khảo sát', count: null }] : []),
    ...(canManage    ? [{ key: 'hoc-vien' as DetailTab, label: '👥 Học viên', count: kh.so_hoc_vien }] : []),
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
                              {lichSu.lich_su.map((ls) => (
                                <div key={ls.id} className="flex items-center gap-3 text-xs py-1.5 px-3 bg-white rounded-lg border border-gray-100">
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
                                  <span className={`shrink-0 px-2 py-0.5 rounded-full font-medium ${ls.dat_yeu_cau ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                                    {ls.dat_yeu_cau ? '✓ Đạt' : '✗ Không đạt'}
                                  </span>
                                  {ls.ngay_lam && (
                                    <span className="text-gray-400 ml-auto shrink-0">
                                      {new Date(ls.ngay_lam).toLocaleDateString('vi-VN')}
                                    </span>
                                  )}
                                </div>
                              ))}
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
              {hocViens.length === 0 ? (
                <div className="text-center py-8 text-gray-500">Chưa có học viên nào</div>
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
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

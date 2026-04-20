/**
 * src/app/(main)/in-bang-ke/page.tsx
 * ====================================
 * Trang in bảng kê cá nhân + workflow phê duyệt phiếu đánh giá QUÝ.
 *
 * v3.0.0 (18/04/2026):
 * - Tách thành 2 tab: "Kê khai" (CC) và "Phê duyệt" (TDV/CCT).
 * - Tab "Phê duyệt" hỗ trợ sub-filter CHO_PHE_DUYET / DA_PHE_DUYET, cho phép
 *   TDV tải bảng in của CC và trả lại phiếu đã phê duyệt nhầm.
 * - CC gửi duyệt: hiện cảnh báo nếu còn công việc / tiêu chí chưa được duyệt.
 */

'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuthStore } from '@/stores/useAuthStore';
import apiClient from '@/lib/axios';
import { phieuDanhGiaService } from '@/services/phieu-danh-gia.service';
import type { IUser } from '@/types/auth';
import type {
  KiemTraDuDieuKienResponse,
  PhieuChoPheDuyetItem,
  PhieuDanhGiaQuy,
} from '@/types/phieu-danh-gia';

type LoaiKy = 'thang' | 'quy';
type MainTab = 'ke-khai' | 'phe-duyet';

const TRANG_THAI_BADGE: Record<string, string> = {
  NHAP: 'bg-gray-100 text-gray-700',
  CHO_PHE_DUYET: 'bg-amber-100 text-amber-800',
  DA_PHE_DUYET: 'bg-green-100 text-green-800',
  BI_TU_CHOI: 'bg-red-100 text-red-800',
};

const TRANG_THAI_LABEL: Record<string, string> = {
  NHAP: 'Nháp',
  CHO_PHE_DUYET: 'Chờ duyệt',
  DA_PHE_DUYET: 'Đã duyệt',
  BI_TU_CHOI: 'Bị từ chối',
};

function formatDate(s: string | null): string {
  if (!s) return '';
  const d = new Date(s);
  return d.toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short' });
}

// =============================================================================
// ROOT COMPONENT
// =============================================================================

export default function InBangKePage() {
  const { user } = useAuthStore();

  const currentDate = new Date();
  const [loaiKy, setLoaiKy] = useState<LoaiKy>('thang');
  const [thang, setThang] = useState(currentDate.getMonth() + 1);
  const [quy, setQuy] = useState(Math.ceil((currentDate.getMonth() + 1) / 3));
  const [nam, setNam] = useState(currentDate.getFullYear());

  const canHavePhieu = useMemo(() => {
    return user?.vai_tro?.cap_bac !== 'CHI_CUC_TRUONG';
  }, [user]);

  const isDuyet = useMemo(() => {
    return (
      user?.vai_tro?.cap_bac === 'TRUONG_DON_VI' ||
      user?.vai_tro?.cap_bac === 'CHI_CUC_TRUONG'
    );
  }, [user]);

  const [mainTabRaw, setMainTab] = useState<MainTab>('ke-khai');
  // Nếu user không có quyền duyệt, luôn hiển thị tab kê khai.
  const mainTab: MainTab = isDuyet ? mainTabRaw : 'ke-khai';

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 mb-6 p-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
              <span className="text-2xl text-white">📋</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Theo dõi, đánh giá Quý</h1>
              <p className="text-sm text-gray-600 mt-1">
                Phiếu đánh giá + bảng kê công việc (theo tháng hoặc quý). Với quý, tự nhập mục 4/5 rồi gửi duyệt.
              </p>
            </div>
          </div>

          {/* Main tabs */}
          {isDuyet && (
            <div className="mt-6 flex gap-1 border-b border-gray-200">
              <TabButton
                active={mainTab === 'ke-khai'}
                onClick={() => setMainTab('ke-khai')}
                icon="📝"
                label="Kê khai cá nhân"
              />
              <TabButton
                active={mainTab === 'phe-duyet'}
                onClick={() => setMainTab('phe-duyet')}
                icon="✅"
                label="Phê duyệt"
              />
            </div>
          )}
        </div>

        {mainTab === 'ke-khai' && (
          <KeKhaiTab
            user={user}
            canHavePhieu={canHavePhieu}
            loaiKy={loaiKy}
            setLoaiKy={setLoaiKy}
            thang={thang}
            setThang={setThang}
            quy={quy}
            setQuy={setQuy}
            nam={nam}
            setNam={setNam}
            currentYear={currentDate.getFullYear()}
          />
        )}

        {mainTab === 'phe-duyet' && isDuyet && (
          <PheDuyetTab quy={quy} setQuy={setQuy} nam={nam} setNam={setNam} />
        )}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: string;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
        active
          ? 'border-blue-600 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700'
      }`}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </button>
  );
}

// =============================================================================
// TAB 1: KÊ KHAI CÁ NHÂN
// =============================================================================

interface KeKhaiTabProps {
  user: IUser | null;
  canHavePhieu: boolean;
  loaiKy: LoaiKy;
  setLoaiKy: (v: LoaiKy) => void;
  thang: number;
  setThang: (v: number) => void;
  quy: number;
  setQuy: (v: number) => void;
  nam: number;
  setNam: (v: number) => void;
  currentYear: number;
}

function KeKhaiTab({
  user,
  canHavePhieu,
  loaiKy,
  setLoaiKy,
  thang,
  setThang,
  quy,
  setQuy,
  nam,
  setNam,
  currentYear,
}: KeKhaiTabProps) {
  const [downloading, setDownloading] = useState(false);

  const [phieu, setPhieu] = useState<PhieuDanhGiaQuy | null>(null);
  const [uuDiem, setUuDiem] = useState('');
  const [hanChe, setHanChe] = useState('');
  const [loadingPhieu, setLoadingPhieu] = useState(false);
  const [savingPhieu, setSavingPhieu] = useState(false);

  // Modal cảnh báo khi gửi duyệt nhưng còn CV/TC chưa duyệt
  const [warnOpen, setWarnOpen] = useState(false);
  const [warnInfo, setWarnInfo] = useState<KiemTraDuDieuKienResponse | null>(null);

  // Kết quả kiểm tra tự động: hiện banner cảnh báo nếu còn kê khai tạm tính.
  const [preCheck, setPreCheck] = useState<KiemTraDuDieuKienResponse | null>(null);
  const [checkingPre, setCheckingPre] = useState(false);

  const loadPhieu = useCallback(async () => {
    if (loaiKy !== 'quy' || !canHavePhieu) {
      setPhieu(null);
      return;
    }
    try {
      setLoadingPhieu(true);
      const p = await phieuDanhGiaService.getCuaToi(quy, nam);
      setPhieu(p);
      setUuDiem(p?.uu_diem || '');
      setHanChe(p?.han_che || '');
    } catch (err) {
      console.error('Load phiếu error:', err);
    } finally {
      setLoadingPhieu(false);
    }
  }, [loaiKy, canHavePhieu, quy, nam]);

  useEffect(() => {
    loadPhieu();
  }, [loadPhieu]);

  // Tự động kiểm tra điều kiện (chế độ quý) để hiện cảnh báo nếu cần.
  useEffect(() => {
    if (loaiKy !== 'quy' || !canHavePhieu) {
      setPreCheck(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        setCheckingPre(true);
        const r = await phieuDanhGiaService.kiemTraDuDieuKien(quy, nam);
        if (!cancelled) setPreCheck(r);
      } catch (err) {
        console.error('Pre-check error:', err);
        if (!cancelled) setPreCheck(null);
      } finally {
        if (!cancelled) setCheckingPre(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loaiKy, canHavePhieu, quy, nam]);

  const refreshPreCheck = useCallback(async () => {
    if (loaiKy !== 'quy' || !canHavePhieu) return;
    try {
      setCheckingPre(true);
      const r = await phieuDanhGiaService.kiemTraDuDieuKien(quy, nam);
      setPreCheck(r);
    } catch (err) {
      console.error(err);
    } finally {
      setCheckingPre(false);
    }
  }, [loaiKy, canHavePhieu, quy, nam]);

  const canEditPhieu = useMemo(() => {
    if (!phieu) return true;
    return phieu.trang_thai === 'NHAP' || phieu.trang_thai === 'BI_TU_CHOI';
  }, [phieu]);

  const canSend =
    canEditPhieu && (uuDiem.trim().length > 0 || hanChe.trim().length > 0);

  const handleLuuNhap = async () => {
    try {
      setSavingPhieu(true);
      const p = await phieuDanhGiaService.upsertNhap({
        quy,
        nam,
        uu_diem: uuDiem.trim() || null,
        han_che: hanChe.trim() || null,
      });
      setPhieu(p);
      alert('Đã lưu phiếu nháp');
    } catch (err) {
      console.error(err);
      alert(extractError(err, 'Không thể lưu phiếu nháp'));
    } finally {
      setSavingPhieu(false);
    }
  };

  const doGuiDuyet = async () => {
    try {
      setSavingPhieu(true);
      const saved = await phieuDanhGiaService.upsertNhap({
        quy,
        nam,
        uu_diem: uuDiem.trim() || null,
        han_che: hanChe.trim() || null,
      });
      const sent = await phieuDanhGiaService.guiDuyet(saved.id);
      setPhieu(sent);
      alert('Đã gửi phiếu để phê duyệt');
    } catch (err) {
      console.error(err);
      alert(extractError(err, 'Không thể gửi duyệt'));
    } finally {
      setSavingPhieu(false);
    }
  };

  const handleGuiDuyet = async () => {
    // Kiểm tra điều kiện trước khi gửi duyệt
    try {
      const check = await phieuDanhGiaService.kiemTraDuDieuKien(quy, nam);
      if (check.co_van_de) {
        setWarnInfo(check);
        setWarnOpen(true);
        return;
      }
      await doGuiDuyet();
    } catch (err) {
      console.error(err);
      alert(extractError(err, 'Không kiểm tra được điều kiện gửi duyệt'));
    }
  };

  const downloadFile = async (endpoint: string, filename: string) => {
    try {
      setDownloading(true);
      const response = await apiClient.get(endpoint, { responseType: 'blob' });
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Lỗi tải file:', err);
      alert(extractError(err, 'Không thể tải file. Vui lòng thử lại.'));
    } finally {
      setDownloading(false);
    }
  };

  const handleInPhieuDanhGia = async () => {
    const ma_cc = user?.ma_cc?.replace('/', '-') || 'user';
    if (loaiKy === 'thang') {
      await downloadFile(
        `/in-bang-ke/phieu-danh-gia/${thang}/${nam}`,
        `PhieuDanhGia_${ma_cc}_T${thang}_${nam}.docx`,
      );
    } else {
      await downloadFile(
        `/in-bang-ke/phieu-danh-gia-quy/${quy}/${nam}`,
        `PhieuDanhGia_${ma_cc}_Q${quy}_${nam}.docx`,
      );
    }
  };

  const handleInBangKeCongViec = async () => {
    const ma_cc = user?.ma_cc?.replace('/', '-') || 'user';
    if (loaiKy === 'thang') {
      await downloadFile(
        `/in-bang-ke/bang-ke-cong-viec/${thang}/${nam}`,
        `BangKeCongViec_${ma_cc}_T${thang}_${nam}.docx`,
      );
    } else {
      await downloadFile(
        `/in-bang-ke/bang-ke-cong-viec-quy/${quy}/${nam}`,
        `BangKeCongViec_${ma_cc}_Q${quy}_${nam}.docx`,
      );
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
      {/* Chọn kỳ */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span className="text-xl">📅</span>
          Chọn kỳ đánh giá
        </h2>

        <div className="flex gap-2 mb-6 bg-gray-100 p-1.5 rounded-xl">
          <button
            onClick={() => setLoaiKy('thang')}
            className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
              loaiKy === 'thang'
                ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-md'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Theo Tháng
          </button>
          <button
            onClick={() => setLoaiKy('quy')}
            className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
              loaiKy === 'quy'
                ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-md'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Theo Quý
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {loaiKy === 'thang' ? 'Tháng' : 'Quý'}
            </label>
            {loaiKy === 'thang' ? (
              <select
                value={thang}
                onChange={(e) => setThang(Number(e.target.value))}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>Tháng {m}</option>
                ))}
              </select>
            ) : (
              <select
                value={quy}
                onChange={(e) => setQuy(Number(e.target.value))}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {Array.from({ length: 4 }, (_, i) => i + 1).map((q) => (
                  <option key={q} value={q}>Quý {q}</option>
                ))}
              </select>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Năm</label>
            <select
              value={nam}
              onChange={(e) => setNam(Number(e.target.value))}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {Array.from({ length: 10 }, (_, i) => currentYear - 5 + i).map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Thông tin */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 mb-4 border border-blue-100">
        <p className="text-2xl font-bold text-blue-600">
          {loaiKy === 'thang' ? `Tháng ${thang}/${nam}` : `Quý ${quy}/${nam}`}
        </p>
        <p className="text-sm text-gray-600 mt-2">
          Họ tên: <span className="font-medium text-gray-900">{user?.ho_ten || 'N/A'}</span>
        </p>
        <p className="text-sm text-gray-600">
          Đơn vị: <span className="font-medium text-gray-900">{user?.don_vi?.ten_don_vi || 'N/A'}</span>
        </p>
      </div>

      {/* Banner cảnh báo — chỉ hiện khi thực sự còn CV/TC chưa duyệt trong quý. */}
      {loaiKy === 'quy' && canHavePhieu && preCheck?.co_van_de && (
        <div className="mb-8 bg-amber-50 border border-amber-300 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-amber-900">
                Còn kê khai chưa được phê duyệt trong Quý {quy}/{nam}
              </p>
              <p className="text-xs text-amber-800 mt-1">
                Bảng in chỉ tổng hợp dữ liệu đã phê duyệt. Hiện còn:{' '}
                <strong>{preCheck.so_cv_chua_duyet}</strong> công việc và{' '}
                <strong>{preCheck.so_tc_chua_duyet}</strong> tiêu chí chưa duyệt. Hãy chờ
                cấp trên phê duyệt trước khi gửi phiếu.
              </p>
              {preCheck.chi_tiet_thang.some(
                (ct) => ct.cv_chua_duyet > 0 || ct.tc_chua_duyet > 0,
              ) && (
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-amber-800">
                  {preCheck.chi_tiet_thang
                    .filter((ct) => ct.cv_chua_duyet > 0 || ct.tc_chua_duyet > 0)
                    .map((ct) => (
                      <span key={ct.thang}>
                        Tháng {ct.thang}: <b>{ct.cv_chua_duyet}</b> CV ·{' '}
                        <b>{ct.tc_chua_duyet}</b> TC
                      </span>
                    ))}
                </div>
              )}
              <button
                onClick={refreshPreCheck}
                disabled={checkingPre}
                className="mt-2 text-xs text-amber-800 underline hover:text-amber-900 disabled:opacity-50"
              >
                {checkingPre ? 'Đang kiểm tra…' : '🔄 Kiểm tra lại'}
              </button>
            </div>
          </div>
        </div>
      )}

      {loaiKy === 'quy' && canHavePhieu && preCheck && !preCheck.co_van_de && (
        <div className="mb-8 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
          <p className="text-sm text-green-800">
            ✅ Toàn bộ công việc và tiêu chí của Quý {quy}/{nam} đã được phê duyệt.
          </p>
        </div>
      )}

      {/* Phiếu tự nhập (chỉ quý + có phiếu) */}
      {loaiKy === 'quy' && canHavePhieu && (
        <PhieuTuNhapSection
          phieu={phieu}
          uuDiem={uuDiem}
          setUuDiem={setUuDiem}
          hanChe={hanChe}
          setHanChe={setHanChe}
          loading={loadingPhieu}
          saving={savingPhieu}
          canEdit={canEditPhieu}
          canSend={canSend}
          onSaveNhap={handleLuuNhap}
          onGuiDuyet={handleGuiDuyet}
        />
      )}

      {/* Nút tải file */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span className="text-xl">🖨️</span>
          Tải file về máy
        </h2>

        <button
          onClick={handleInPhieuDanhGia}
          disabled={downloading}
          className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-semibold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
        >
          <span className="text-2xl">📝</span>
          <span>Tải phiếu đánh giá (PL-01A/01B)</span>
          {downloading && <span className="ml-2 animate-spin">⏳</span>}
        </button>

        <button
          onClick={handleInBangKeCongViec}
          disabled={downloading}
          className="w-full bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white font-semibold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
        >
          <span className="text-2xl">📑</span>
          <span>Tải bảng kê công việc (PL-02)</span>
          {downloading && <span className="ml-2 animate-spin">⏳</span>}
        </button>
      </div>

      {/* Modal cảnh báo */}
      {warnOpen && warnInfo && (
        <CanhBaoChuaDuyetModal
          info={warnInfo}
          onClose={() => setWarnOpen(false)}
          onConfirm={async () => {
            setWarnOpen(false);
            await doGuiDuyet();
          }}
        />
      )}
    </div>
  );
}

// =============================================================================
// SECTION: CC tự nhập mục 4/5 cho phiếu quý
// =============================================================================

interface PhieuTuNhapProps {
  phieu: PhieuDanhGiaQuy | null;
  uuDiem: string;
  setUuDiem: (v: string) => void;
  hanChe: string;
  setHanChe: (v: string) => void;
  loading: boolean;
  saving: boolean;
  canEdit: boolean;
  canSend: boolean;
  onSaveNhap: () => void;
  onGuiDuyet: () => void;
}

function PhieuTuNhapSection({
  phieu,
  uuDiem,
  setUuDiem,
  hanChe,
  setHanChe,
  loading,
  saving,
  canEdit,
  canSend,
  onSaveNhap,
  onGuiDuyet,
}: PhieuTuNhapProps) {
  return (
    <div className="mb-8 border border-gray-200 rounded-xl p-6 bg-white">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <span className="text-xl">📄</span>
          Nội dung phiếu đánh giá quý
        </h2>
        {phieu && (
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              TRANG_THAI_BADGE[phieu.trang_thai] || 'bg-gray-100 text-gray-700'
            }`}
          >
            {TRANG_THAI_LABEL[phieu.trang_thai] || phieu.trang_thai}
          </span>
        )}
      </div>

      {loading ? (
        <p className="text-sm text-gray-500">Đang tải…</p>
      ) : (
        <>
          {(phieu?.trang_thai === 'BI_TU_CHOI' ||
            (phieu?.trang_thai === 'NHAP' && phieu.ly_do_tu_choi)) &&
            phieu?.ly_do_tu_choi && (
              <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-amber-800 mb-1">
                  {phieu.trang_thai === 'BI_TU_CHOI'
                    ? 'Lý do bị từ chối:'
                    : 'Ghi chú trả lại từ cấp trên:'}
                </p>
                <p className="text-sm text-amber-700 whitespace-pre-wrap">
                  {phieu.ly_do_tu_choi}
                </p>
                {phieu.nguoi_phe_duyet && (
                  <p className="text-xs text-amber-600 mt-2">
                    {phieu.nguoi_phe_duyet.ho_ten}
                    {phieu.ngay_phe_duyet && <> · {formatDate(phieu.ngay_phe_duyet)}</>}
                  </p>
                )}
              </div>
            )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                4. Ưu điểm
              </label>
              <textarea
                value={uuDiem}
                onChange={(e) => setUuDiem(e.target.value)}
                disabled={!canEdit}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                placeholder="Nhập ưu điểm…"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                5. Hạn chế, khuyết điểm
              </label>
              <textarea
                value={hanChe}
                onChange={(e) => setHanChe(e.target.value)}
                disabled={!canEdit}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                placeholder="Nhập hạn chế, khuyết điểm…"
              />
            </div>

            {phieu?.trang_thai === 'DA_PHE_DUYET' && phieu.y_kien_lanh_dao && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  6. Ý kiến của cấp có thẩm quyền (do {phieu.nguoi_phe_duyet?.ho_ten || 'LĐ'} nhập)
                </label>
                <div className="px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-sm text-green-900 whitespace-pre-wrap">
                  {phieu.y_kien_lanh_dao}
                </div>
              </div>
            )}
          </div>

          {canEdit && (
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                onClick={onSaveNhap}
                disabled={saving}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white font-medium rounded-lg disabled:opacity-50"
              >
                {saving ? 'Đang lưu…' : '💾 Lưu nháp'}
              </button>
              <button
                onClick={onGuiDuyet}
                disabled={saving || !canSend}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg disabled:opacity-50"
                title={!canSend ? 'Cần nhập ít nhất Ưu điểm hoặc Hạn chế' : ''}
              >
                {saving ? 'Đang gửi…' : '📤 Lưu & Gửi duyệt'}
              </button>
            </div>
          )}

          {!canEdit && phieu && (
            <p className="mt-4 text-sm text-gray-500 italic">
              {phieu.trang_thai === 'CHO_PHE_DUYET'
                ? 'Phiếu đang chờ cấp trên duyệt — không thể sửa.'
                : phieu.trang_thai === 'DA_PHE_DUYET'
                  ? 'Phiếu đã được duyệt — không thể sửa. Liên hệ cấp trên nếu cần trả lại.'
                  : 'Không thể sửa phiếu.'}
            </p>
          )}
        </>
      )}
    </div>
  );
}

// =============================================================================
// MODAL: Cảnh báo còn CV / TC chưa phê duyệt
// =============================================================================

function CanhBaoChuaDuyetModal({
  info,
  onClose,
  onConfirm,
}: {
  info: KiemTraDuDieuKienResponse;
  onClose: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl">
        <h3 className="text-lg font-semibold mb-3 text-amber-700 flex items-center gap-2">
          ⚠️ Còn kê khai chưa được phê duyệt
        </h3>
        <p className="text-sm text-gray-700 mb-3">
          Phiếu đánh giá Quý {info.quy}/{info.nam} chỉ tổng hợp dữ liệu đã phê duyệt. Hiện tại:
        </p>
        <ul className="text-sm text-gray-800 list-disc list-inside mb-3 space-y-1">
          <li>
            <strong className="text-amber-700">{info.so_cv_chua_duyet}</strong> công việc chưa phê duyệt
          </li>
          <li>
            <strong className="text-amber-700">{info.so_tc_chua_duyet}</strong> tiêu chí chung chưa phê duyệt
          </li>
        </ul>
        {info.chi_tiet_thang.length > 0 && (
          <div className="text-xs text-gray-600 border border-gray-200 rounded-lg p-3 mb-4 bg-gray-50">
            <p className="font-semibold text-gray-700 mb-1">Chi tiết theo tháng:</p>
            {info.chi_tiet_thang.map((ct) => (
              <div key={ct.thang} className="flex justify-between">
                <span>Tháng {ct.thang}</span>
                <span>
                  CV: <b>{ct.cv_chua_duyet}</b> · TC: <b>{ct.tc_chua_duyet}</b>
                </span>
              </div>
            ))}
          </div>
        )}
        <p className="text-sm text-gray-600 mb-4 italic">
          Bạn nên chờ cấp trên phê duyệt các kê khai này trước khi gửi phiếu. Nếu vẫn muốn gửi
          ngay, phần chưa duyệt sẽ không được tính vào bảng in.
        </p>
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Hủy — tôi đi duyệt trước
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg"
          >
            Vẫn gửi phiếu
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// TAB 2: PHÊ DUYỆT (TDV/CCT)
// =============================================================================

interface PheDuyetTabProps {
  quy: number;
  setQuy: (v: number) => void;
  nam: number;
  setNam: (v: number) => void;
}

function PheDuyetTab({ quy, setQuy, nam, setNam }: PheDuyetTabProps) {
  const [items, setItems] = useState<PhieuChoPheDuyetItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);

  // Modal action
  const [modalItem, setModalItem] = useState<PhieuChoPheDuyetItem | null>(null);
  const [modalMode, setModalMode] = useState<'phe_duyet' | 'tu_choi' | 'tra_lai'>('phe_duyet');
  const [yKien, setYKien] = useState('');
  const [lyDo, setLyDo] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Modal xem chi tiết ưu điểm / hạn chế / ý kiến LĐ
  const [detailItem, setDetailItem] = useState<PhieuChoPheDuyetItem | null>(null);

  const currentYear = new Date().getFullYear();

  const load = useCallback(async () => {
    try {
      setLoading(true);
      // Không truyền trang_thai → backend trả về cả 4 trạng thái
      // (NHAP, CHO_PHE_DUYET, DA_PHE_DUYET, BI_TU_CHOI).
      const res = await phieuDanhGiaService.getChoDuyet({
        quy,
        nam,
        page: 1,
        page_size: 500,
      });
      setItems(res.items);
    } catch (err) {
      console.error(err);
      alert(extractError(err, 'Không lấy được danh sách phiếu'));
    } finally {
      setLoading(false);
    }
  }, [quy, nam]);

  // Thống kê nhanh theo trạng thái (hiển thị ở header).
  const thongKe = useMemo(() => {
    const base = { NHAP: 0, CHO_PHE_DUYET: 0, DA_PHE_DUYET: 0, BI_TU_CHOI: 0 };
    for (const it of items) {
      if (it.trang_thai in base) base[it.trang_thai as keyof typeof base] += 1;
    }
    return base;
  }, [items]);

  useEffect(() => {
    load();
  }, [load]);

  const openPheDuyet = (it: PhieuChoPheDuyetItem) => {
    setModalItem(it);
    setModalMode('phe_duyet');
    setYKien('');
    setLyDo('');
  };

  const openTuChoi = (it: PhieuChoPheDuyetItem) => {
    setModalItem(it);
    setModalMode('tu_choi');
    setYKien('');
    setLyDo('');
  };

  const openTraLai = (it: PhieuChoPheDuyetItem) => {
    setModalItem(it);
    setModalMode('tra_lai');
    setYKien('');
    setLyDo('');
  };

  const closeModal = () => {
    setModalItem(null);
    setYKien('');
    setLyDo('');
  };

  const submit = async () => {
    if (!modalItem || !modalItem.id) return;
    const phieuId = modalItem.id;
    try {
      setSubmitting(true);
      if (modalMode === 'phe_duyet') {
        await phieuDanhGiaService.pheDuyet(phieuId, {
          y_kien_lanh_dao: yKien.trim() || null,
        });
        alert('Đã duyệt phiếu');
      } else if (modalMode === 'tu_choi') {
        if (!lyDo.trim()) {
          alert('Vui lòng nhập lý do từ chối');
          return;
        }
        await phieuDanhGiaService.tuChoi(phieuId, {
          ly_do_tu_choi: lyDo.trim(),
        });
        alert('Đã từ chối phiếu');
      } else {
        await phieuDanhGiaService.traLai(phieuId, {
          ly_do: lyDo.trim() || null,
        });
        alert('Đã trả lại phiếu cho công chức');
      }
      closeModal();
      load();
    } catch (err) {
      console.error(err);
      alert(extractError(err, 'Thao tác thất bại'));
    } finally {
      setSubmitting(false);
    }
  };

  const tailong = async (
    it: PhieuChoPheDuyetItem,
    loai: 'phieu' | 'bang_ke',
  ) => {
    try {
      setDownloading(`${it.id}-${loai}`);
      const blob =
        loai === 'phieu'
          ? await phieuDanhGiaService.downloadPhieuCuaCC(it.cong_chuc_id, it.quy, it.nam)
          : await phieuDanhGiaService.downloadBangKeCuaCC(it.cong_chuc_id, it.quy, it.nam);

      const ma_cc_safe = it.ma_cc.replace('/', '-');
      const filename =
        loai === 'phieu'
          ? `PhieuDanhGia_${ma_cc_safe}_Q${it.quy}_${it.nam}.docx`
          : `BangKeCongViec_${ma_cc_safe}_Q${it.quy}_${it.nam}.docx`;

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert(extractError(err, 'Không thể tải file'));
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
      {/* Bộ lọc quý + năm */}
      <div className="mb-6 flex flex-wrap items-end gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Quý</label>
          <select
            value={quy}
            onChange={(e) => setQuy(Number(e.target.value))}
            className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            {Array.from({ length: 4 }, (_, i) => i + 1).map((q) => (
              <option key={q} value={q}>Quý {q}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Năm</label>
          <select
            value={nam}
            onChange={(e) => setNam(Number(e.target.value))}
            className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            {Array.from({ length: 6 }, (_, i) => currentYear - 3 + i).map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>

        <button
          onClick={load}
          className="ml-auto px-4 py-2.5 text-sm text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50"
        >
          🔄 Tải lại
        </button>
      </div>

      {/* Thống kê tóm tắt trạng thái */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <ThongKeCard label="Nháp" value={thongKe.NHAP} color="gray" />
        <ThongKeCard label="Chờ duyệt" value={thongKe.CHO_PHE_DUYET} color="amber" />
        <ThongKeCard label="Đã duyệt" value={thongKe.DA_PHE_DUYET} color="green" />
        <ThongKeCard label="Từ chối" value={thongKe.BI_TU_CHOI} color="red" />
      </div>

      {/* Danh sách */}
      {loading ? (
        <p className="text-sm text-gray-500">Đang tải…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-gray-500 italic">
          Chưa có phiếu đánh giá nào cho Quý {quy}/{nam} trong phạm vi bạn duyệt.
        </p>
      ) : (
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">Công chức</th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">Đơn vị</th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">Ngày gửi</th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">Ưu điểm</th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">Hạn chế</th>
                <th className="px-3 py-2 text-center text-xs font-semibold text-gray-700">Bảng in</th>
                <th className="px-3 py-2 text-center text-xs font-semibold text-gray-700">Hành động</th>
                <th className="px-3 py-2 text-center text-xs font-semibold text-gray-700">Trạng thái</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {items.map((it) => {
                const isChoDuyet = it.trang_thai === 'CHO_PHE_DUYET';
                const isDaDuyet = it.trang_thai === 'DA_PHE_DUYET';
                const hasContent = Boolean(
                  it.uu_diem || it.han_che || it.y_kien_lanh_dao,
                );
                return (
                  <tr key={it.id ?? `cc-${it.cong_chuc_id}`} className="hover:bg-gray-50">
                    <td className="px-3 py-2 align-top">
                      <div className="font-medium text-gray-900">{it.ho_ten}</div>
                      <div className="text-xs text-gray-500">
                        {it.ma_cc}
                        {it.chuc_vu ? ` · ${it.chuc_vu}` : ''}
                      </div>
                    </td>
                    <td className="px-3 py-2 align-top text-gray-700">{it.don_vi_ten || '-'}</td>
                    <td className="px-3 py-2 align-top text-gray-700 whitespace-nowrap">
                      {formatDate(it.ngay_gui_duyet) || <span className="text-gray-400">—</span>}
                    </td>
                    <td
                      className={`px-3 py-2 align-top text-gray-700 max-w-xs ${
                        hasContent ? 'cursor-pointer hover:bg-blue-50' : ''
                      }`}
                      onClick={() => hasContent && setDetailItem(it)}
                      title={hasContent ? 'Bấm để xem chi tiết' : undefined}
                    >
                      <div className="line-clamp-3 whitespace-pre-wrap">{it.uu_diem || '-'}</div>
                      {hasContent && it.uu_diem && it.uu_diem.length > 120 && (
                        <div className="text-[10px] text-blue-600 mt-1">🔍 Xem đầy đủ</div>
                      )}
                    </td>
                    <td
                      className={`px-3 py-2 align-top text-gray-700 max-w-xs ${
                        hasContent ? 'cursor-pointer hover:bg-blue-50' : ''
                      }`}
                      onClick={() => hasContent && setDetailItem(it)}
                      title={hasContent ? 'Bấm để xem chi tiết' : undefined}
                    >
                      <div className="line-clamp-3 whitespace-pre-wrap">{it.han_che || '-'}</div>
                      {hasContent && it.han_che && it.han_che.length > 120 && (
                        <div className="text-[10px] text-blue-600 mt-1">🔍 Xem đầy đủ</div>
                      )}
                    </td>
                    <td className="px-3 py-2 align-top text-center whitespace-nowrap">
                      <button
                        onClick={() => tailong(it, 'phieu')}
                        disabled={downloading === `${it.id}-phieu`}
                        className="block text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
                        title="Tải phiếu đánh giá (PL-01)"
                      >
                        📝 PL-01
                      </button>
                      <button
                        onClick={() => tailong(it, 'bang_ke')}
                        disabled={downloading === `${it.id}-bang_ke`}
                        className="block text-xs text-purple-600 hover:text-purple-800 disabled:opacity-50 mt-1"
                        title="Tải bảng kê công việc (PL-02)"
                      >
                        📑 PL-02
                      </button>
                    </td>
                    <td className="px-3 py-2 align-top text-center whitespace-nowrap">
                      {isChoDuyet && (
                        <>
                          <button
                            onClick={() => openPheDuyet(it)}
                            className="mr-1 px-2.5 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded"
                          >
                            ✓ Duyệt
                          </button>
                          <button
                            onClick={() => openTuChoi(it)}
                            className="px-2.5 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded"
                          >
                            ✗ Từ chối
                          </button>
                        </>
                      )}
                      {isDaDuyet && (
                        <button
                          onClick={() => openTraLai(it)}
                          className="px-2.5 py-1 text-xs bg-orange-600 hover:bg-orange-700 text-white rounded"
                          title="Chuyển phiếu về trạng thái nháp để CC sửa lại"
                        >
                          ↩️ Trả lại
                        </button>
                      )}
                      {!isChoDuyet && !isDaDuyet && (
                        <span className="text-xs text-gray-400 italic">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 align-top text-center whitespace-nowrap">
                      <span
                        className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold ${
                          TRANG_THAI_BADGE[it.trang_thai] || 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {TRANG_THAI_LABEL[it.trang_thai] || it.trang_thai}
                      </span>
                      {isDaDuyet && it.ngay_phe_duyet && (
                        <div className="text-[10px] text-gray-500 mt-1">
                          {formatDate(it.ngay_phe_duyet)}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal hành động */}
      {modalItem && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">
              {modalMode === 'phe_duyet' && '✓ Duyệt phiếu'}
              {modalMode === 'tu_choi' && '✗ Từ chối phiếu'}
              {modalMode === 'tra_lai' && '↩️ Trả lại phiếu đã duyệt'}
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              <strong>{modalItem.ho_ten}</strong> ({modalItem.ma_cc}) · Quý {modalItem.quy}/{modalItem.nam}
            </p>

            {modalMode === 'phe_duyet' && (
              <>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  6. Ý kiến nhận xét của cấp có thẩm quyền{' '}
                  <span className="text-gray-400">(có thể để trống)</span>
                </label>
                <textarea
                  value={yKien}
                  onChange={(e) => setYKien(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Nhận xét về công chức…"
                />
              </>
            )}

            {modalMode === 'tu_choi' && (
              <>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Lý do từ chối <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={lyDo}
                  onChange={(e) => setLyDo(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="Công chức cần bổ sung nội dung…"
                />
              </>
            )}

            {modalMode === 'tra_lai' && (
              <>
                <p className="mb-3 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
                  Phiếu sẽ chuyển về trạng thái <b>Nháp</b> để công chức sửa và gửi lại. Dùng
                  khi bạn phê duyệt nhầm hoặc phát hiện sai sót sau khi duyệt.
                </p>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ghi chú gửi cho công chức <span className="text-gray-400">(tuỳ chọn)</span>
                </label>
                <textarea
                  value={lyDo}
                  onChange={(e) => setLyDo(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  placeholder="Ví dụ: Cần bổ sung số liệu tháng 3…"
                />
              </>
            )}

            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={closeModal}
                disabled={submitting}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Hủy
              </button>
              <button
                onClick={submit}
                disabled={submitting}
                className={`px-4 py-2 text-white rounded-lg disabled:opacity-50 ${
                  modalMode === 'phe_duyet'
                    ? 'bg-green-600 hover:bg-green-700'
                    : modalMode === 'tu_choi'
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-orange-600 hover:bg-orange-700'
                }`}
              >
                {submitting
                  ? 'Đang xử lý…'
                  : modalMode === 'phe_duyet'
                    ? 'Xác nhận duyệt'
                    : modalMode === 'tu_choi'
                      ? 'Xác nhận từ chối'
                      : 'Xác nhận trả lại'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal xem chi tiết ưu điểm / hạn chế / ý kiến LĐ */}
      {detailItem && (
        <ChiTietPhieuModal item={detailItem} onClose={() => setDetailItem(null)} />
      )}
    </div>
  );
}

// =============================================================================
// MODAL: Xem chi tiết ưu điểm / hạn chế / ý kiến LĐ
// =============================================================================

function ChiTietPhieuModal({
  item,
  onClose,
}: {
  item: PhieuChoPheDuyetItem;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl max-w-2xl w-full p-6 shadow-xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              📄 Chi tiết phiếu đánh giá
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              <strong>{item.ho_ten}</strong> ({item.ma_cc})
              {item.chuc_vu ? ` · ${item.chuc_vu}` : ''} · Quý {item.quy}/{item.nam}
            </p>
            <div className="mt-2 flex items-center gap-2 text-xs">
              <span
                className={`inline-block px-2 py-0.5 rounded-full font-semibold ${
                  TRANG_THAI_BADGE[item.trang_thai] || 'bg-gray-100 text-gray-700'
                }`}
              >
                {TRANG_THAI_LABEL[item.trang_thai] || item.trang_thai}
              </span>
              {item.ngay_gui_duyet && (
                <span className="text-gray-500">
                  Gửi: {formatDate(item.ngay_gui_duyet)}
                </span>
              )}
              {item.ngay_phe_duyet && (
                <span className="text-gray-500">
                  Duyệt: {formatDate(item.ngay_phe_duyet)}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            aria-label="Đóng"
          >
            ×
          </button>
        </div>

        <div className="space-y-4 mt-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              4. Ưu điểm
            </label>
            <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 whitespace-pre-wrap min-h-[60px]">
              {item.uu_diem || <span className="text-gray-400 italic">Chưa nhập</span>}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              5. Hạn chế, khuyết điểm
            </label>
            <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 whitespace-pre-wrap min-h-[60px]">
              {item.han_che || <span className="text-gray-400 italic">Chưa nhập</span>}
            </div>
          </div>

          {item.y_kien_lanh_dao && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                6. Ý kiến của cấp có thẩm quyền
              </label>
              <div className="px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-sm text-green-900 whitespace-pre-wrap">
                {item.y_kien_lanh_dao}
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// UTILS
// =============================================================================

function ThongKeCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: 'gray' | 'amber' | 'green' | 'red';
}) {
  const styles: Record<string, string> = {
    gray: 'bg-gray-50 border-gray-200 text-gray-700',
    amber: 'bg-amber-50 border-amber-200 text-amber-800',
    green: 'bg-green-50 border-green-200 text-green-800',
    red: 'bg-red-50 border-red-200 text-red-800',
  };
  return (
    <div className={`border rounded-xl px-4 py-3 ${styles[color]}`}>
      <div className="text-xs font-medium opacity-80">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  );
}

function extractError(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const ax = err as { response?: { data?: { detail?: unknown } } };
    const detail = ax.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (detail && typeof detail === 'object' && 'message' in detail) {
      const m = (detail as { message?: string }).message;
      if (m) return m;
    }
  }
  return fallback;
}

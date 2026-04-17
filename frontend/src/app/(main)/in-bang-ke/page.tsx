/**
 * src/app/(main)/in-bang-ke/page.tsx
 * ====================================
 * Trang in bảng kê cá nhân + Workflow phiếu đánh giá QUÝ.
 *
 * Tính năng:
 * 1. Chọn tháng/quý + năm
 * 2. Tải phiếu đánh giá (PL-01A/01B) và bảng kê công việc (PL-02)
 * 3. (v4.1.0) Với quý: tự nhập mục 4 (Ưu điểm) + mục 5 (Hạn chế), gửi
 *    duyệt TDV/CCT; khi duyệt → file docx có đủ mục 4/5/6.
 * 4. (v4.1.0) TDV/CCT: section phê duyệt danh sách phiếu chờ duyệt.
 *
 * Version: 2.0.0 (17/04/2026)
 */

'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuthStore } from '@/stores/useAuthStore';
import apiClient from '@/lib/axios';
import { phieuDanhGiaService } from '@/services/phieu-danh-gia.service';
import type { PhieuDanhGiaQuy, PhieuChoPheDuyetItem } from '@/types/phieu-danh-gia';

type LoaiKy = 'thang' | 'quy';

// Badge màu theo trạng thái phiếu
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

export default function InBangKePage() {
  const { user } = useAuthStore();

  // ===== Trạng thái chung =====
  const currentDate = new Date();
  const [loaiKy, setLoaiKy] = useState<LoaiKy>('thang');
  const [thang, setThang] = useState(currentDate.getMonth() + 1);
  const [quy, setQuy] = useState(Math.ceil((currentDate.getMonth() + 1) / 3));
  const [nam, setNam] = useState(currentDate.getFullYear());
  const [downloading, setDownloading] = useState(false);

  // ===== Phiếu đánh giá quý của CC =====
  const canHavePhieu = useMemo(() => {
    // CCT không dùng phiếu
    return user?.vai_tro?.cap_bac !== 'CHI_CUC_TRUONG';
  }, [user]);

  const isDuyet = useMemo(() => {
    // TDV hoặc CCT mới có quyền duyệt phiếu của người khác
    return (
      user?.vai_tro?.cap_bac === 'TRUONG_DON_VI' ||
      user?.vai_tro?.cap_bac === 'CHI_CUC_TRUONG'
    );
  }, [user]);

  const [phieu, setPhieu] = useState<PhieuDanhGiaQuy | null>(null);
  const [uuDiem, setUuDiem] = useState('');
  const [hanChe, setHanChe] = useState('');
  const [loadingPhieu, setLoadingPhieu] = useState(false);
  const [savingPhieu, setSavingPhieu] = useState(false);

  // Load phiếu khi đổi quý/năm (và đang ở chế độ quý)
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

  const canEditPhieu = useMemo(() => {
    if (!phieu) return true; // chưa có phiếu → cho phép tạo mới
    return phieu.trang_thai === 'NHAP' || phieu.trang_thai === 'BI_TU_CHOI';
  }, [phieu]);

  const canSend = canEditPhieu && ((uuDiem.trim().length > 0) || (hanChe.trim().length > 0));

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

  const handleGuiDuyet = async () => {
    try {
      setSavingPhieu(true);
      // Trước tiên save, sau đó gửi duyệt (đảm bảo nội dung trên UI đã lưu)
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

  // ===== Download file helper =====
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 mb-6 p-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
              <span className="text-2xl text-white">📋</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">In Bảng kê</h1>
              <p className="text-sm text-gray-600 mt-1">
                Phiếu đánh giá + bảng kê công việc. Với quý, tự nhập mục 4/5 rồi gửi duyệt.
              </p>
            </div>
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
          {/* Chọn kỳ đánh giá */}
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
                  {Array.from({ length: 10 }, (_, i) => currentDate.getFullYear() - 5 + i).map((y) => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Thông tin kỳ đánh giá */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 mb-8 border border-blue-100">
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

          {/* === Phiếu tự nhận xét (chỉ cho quý + user có phiếu) === */}
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

          {/* === Nút tải file === */}
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

          {/* === Section phê duyệt (TDV/CCT) === */}
          {isDuyet && (
            <PheDuyetPhieuSection quy={quy} nam={nam} onReloadMine={loadPhieu} />
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// SECTION: CC tự nhập mục 4/5 cho phiếu quý
// ============================================================================

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
          {phieu?.trang_thai === 'BI_TU_CHOI' && phieu.ly_do_tu_choi && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm font-semibold text-red-800 mb-1">Lý do bị từ chối:</p>
              <p className="text-sm text-red-700 whitespace-pre-wrap">{phieu.ly_do_tu_choi}</p>
              {phieu.nguoi_phe_duyet && (
                <p className="text-xs text-red-600 mt-2">
                  Người từ chối: {phieu.nguoi_phe_duyet.ho_ten}
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
                  ? 'Phiếu đã được duyệt — không thể sửa.'
                  : 'Không thể sửa phiếu.'}
            </p>
          )}
        </>
      )}
    </div>
  );
}

// ============================================================================
// SECTION: TDV/CCT phê duyệt danh sách phiếu chờ duyệt
// ============================================================================

interface PheDuyetProps {
  quy: number;
  nam: number;
  onReloadMine: () => void;
}

function PheDuyetPhieuSection({ quy, nam, onReloadMine }: PheDuyetProps) {
  const [items, setItems] = useState<PhieuChoPheDuyetItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);

  // Modal duyệt
  const [modalItem, setModalItem] = useState<PhieuChoPheDuyetItem | null>(null);
  const [modalMode, setModalMode] = useState<'phe_duyet' | 'tu_choi'>('phe_duyet');
  const [yKien, setYKien] = useState('');
  const [lyDo, setLyDo] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await phieuDanhGiaService.getChoDuyet({ quy, nam, page: 1, page_size: 50 });
      setItems(res.items);
      setTotal(res.pagination.total_items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [quy, nam]);

  useEffect(() => {
    load();
  }, [load]);

  const openApprove = (it: PhieuChoPheDuyetItem) => {
    setModalItem(it);
    setModalMode('phe_duyet');
    setYKien('');
    setLyDo('');
  };

  const openReject = (it: PhieuChoPheDuyetItem) => {
    setModalItem(it);
    setModalMode('tu_choi');
    setYKien('');
    setLyDo('');
  };

  const closeModal = () => {
    setModalItem(null);
    setYKien('');
    setLyDo('');
  };

  const submit = async () => {
    if (!modalItem) return;
    try {
      setSubmitting(true);
      if (modalMode === 'phe_duyet') {
        await phieuDanhGiaService.pheDuyet(modalItem.id, { y_kien_lanh_dao: yKien.trim() || null });
      } else {
        if (!lyDo.trim()) {
          alert('Vui lòng nhập lý do từ chối');
          return;
        }
        await phieuDanhGiaService.tuChoi(modalItem.id, { ly_do_tu_choi: lyDo.trim() });
      }
      alert(modalMode === 'phe_duyet' ? 'Đã duyệt phiếu' : 'Đã từ chối phiếu');
      closeModal();
      load();
      onReloadMine();
    } catch (err) {
      console.error(err);
      alert(extractError(err, 'Thao tác thất bại'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-10 pt-8 border-t border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <span className="text-xl">🗂️</span>
          Phê duyệt phiếu đánh giá quý
          <span className="ml-2 px-2 py-0.5 text-xs font-semibold bg-amber-100 text-amber-800 rounded-full">
            {total}
          </span>
        </h2>
        <button
          onClick={load}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          🔄 Tải lại
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-gray-500">Đang tải…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-gray-500 italic">
          Không có phiếu nào chờ duyệt cho Quý {quy}/{nam}.
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
                <th className="px-3 py-2 text-center text-xs font-semibold text-gray-700">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {items.map((it) => (
                <tr key={it.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 align-top">
                    <div className="font-medium text-gray-900">{it.ho_ten}</div>
                    <div className="text-xs text-gray-500">{it.ma_cc}{it.chuc_vu ? ` · ${it.chuc_vu}` : ''}</div>
                  </td>
                  <td className="px-3 py-2 align-top text-gray-700">{it.don_vi_ten || '-'}</td>
                  <td className="px-3 py-2 align-top text-gray-700 whitespace-nowrap">
                    {formatDate(it.ngay_gui_duyet)}
                  </td>
                  <td className="px-3 py-2 align-top text-gray-700 max-w-xs">
                    <div className="line-clamp-3 whitespace-pre-wrap">{it.uu_diem || '-'}</div>
                  </td>
                  <td className="px-3 py-2 align-top text-gray-700 max-w-xs">
                    <div className="line-clamp-3 whitespace-pre-wrap">{it.han_che || '-'}</div>
                  </td>
                  <td className="px-3 py-2 align-top text-center whitespace-nowrap">
                    <button
                      onClick={() => openApprove(it)}
                      className="mr-1 px-2.5 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded"
                    >
                      ✓ Duyệt
                    </button>
                    <button
                      onClick={() => openReject(it)}
                      className="px-2.5 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded"
                    >
                      ✗ Từ chối
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal phê duyệt / từ chối */}
      {modalItem && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">
              {modalMode === 'phe_duyet' ? '✓ Duyệt phiếu' : '✗ Từ chối phiếu'}
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              <strong>{modalItem.ho_ten}</strong> ({modalItem.ma_cc}) · Quý {modalItem.quy}/{modalItem.nam}
            </p>

            {modalMode === 'phe_duyet' ? (
              <>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  6. Ý kiến nhận xét của cấp có thẩm quyền <span className="text-gray-400">(có thể để trống)</span>
                </label>
                <textarea
                  value={yKien}
                  onChange={(e) => setYKien(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Nhận xét về công chức…"
                />
              </>
            ) : (
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
                  modalMode === 'phe_duyet' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {submitting
                  ? 'Đang xử lý…'
                  : modalMode === 'phe_duyet'
                    ? 'Xác nhận duyệt'
                    : 'Xác nhận từ chối'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// UTILS
// ============================================================================

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

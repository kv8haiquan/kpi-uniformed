/**
 * src/app/(main)/xep-loai/phe-duyet/page.tsx
 * ============================================
 * Trang Phê duyệt Báo cáo Xếp loại - Dành cho Chi cục trưởng.
 * 
 * Chức năng:
 * - Xem danh sách báo cáo chờ phê duyệt từ các đơn vị
 * - Xem chi tiết báo cáo với điểm từng CC
 * - Điều chỉnh xếp loại quyết định (bắt buộc lý do nếu khác đề xuất)
 * - Phê duyệt hoặc từ chối (chọn CC cụ thể khi từ chối)
 * 
 * Quyền: Chi cục trưởng (CHI_CUC_TRUONG)
 * 
 * Version: 1.0.0 (28/01/2026)
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { baoCaoXepLoaiService } from '@/services/bao-cao-xep-loai.service';
import {
  IBaoCaoXepLoai,
  IBaoCaoXepLoaiSummary,
  IChiTietXepLoai,
  TrangThaiBaoCao,
  XepLoaiChatLuong,
  getXepLoaiColor,
  getTrangThaiTen,
  getTrangThaiColor,
} from '@/types/bao-cao-xep-loai';

// =============================================================================
// CONSTANTS
// =============================================================================

const XEP_LOAI_OPTIONS: XepLoaiChatLuong[] = ['A', 'B', 'C', 'D', 'E'];

// =============================================================================
// SUB COMPONENTS
// =============================================================================

function XepLoaiBadge({ xepLoai, size = 'md' }: { xepLoai: XepLoaiChatLuong; size?: 'sm' | 'md' }) {
  const color = getXepLoaiColor(xepLoai);
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';
  return (
    <span className={`${color.bg} ${color.text} ${color.border} border rounded-full font-semibold ${sizeClass}`}>
      {xepLoai}
    </span>
  );
}

/**
 * Card báo cáo trong danh sách.
 */
function BaoCaoCard({ 
  baoCao, 
  onClick 
}: { 
  baoCao: IBaoCaoXepLoaiSummary;
  onClick: () => void;
}) {
  return (
    <div 
      onClick={onClick}
      className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md cursor-pointer transition-shadow"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">{baoCao.don_vi.ten_don_vi}</h3>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTrangThaiColor(baoCao.trang_thai)}`}>
          {getTrangThaiTen(baoCao.trang_thai)}
        </span>
      </div>

      <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
        <span>Tháng {baoCao.thang}/{baoCao.nam}</span>
        <span>•</span>
        <span>{baoCao.tong_cong_chuc} công chức</span>
        <span>•</span>
        <span>Người lập: {baoCao.nguoi_lap.ho_ten}</span>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <div className="flex gap-2 text-xs">
          <span className="px-2 py-1 bg-green-100 text-green-700 rounded">A: {baoCao.so_loai_a}</span>
          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">B: {baoCao.so_loai_b}</span>
          <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded">C: {baoCao.so_loai_c}</span>
          <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded">D: {baoCao.so_loai_d}</span>
          <span className="px-2 py-1 bg-red-100 text-red-700 rounded">E: {baoCao.so_loai_e}</span>
        </div>
      </div>

      {baoCao.canh_bao_ty_le_a && (
        <div className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-xs text-amber-700">⚠️ Tỷ lệ loại A vượt 20% số loại B</p>
        </div>
      )}

      <p className="text-xs text-gray-400 mt-2">
        Ngày gửi: {new Date(baoCao.ngay_lap).toLocaleString('vi-VN')}
      </p>
    </div>
  );
}

/**
 * Modal điều chỉnh xếp loại quyết định.
 */
function QuyetDinhModal({
  chiTiet,
  onClose,
  onSave,
  isLoading,
}: {
  chiTiet: IChiTietXepLoai;
  onClose: () => void;
  onSave: (xepLoai: XepLoaiChatLuong, lyDo: string) => void;
  isLoading: boolean;
}) {
  const xepLoaiDeXuat = chiTiet.xep_loai_de_xuat || chiTiet.xep_loai_he_thong;
  const [xepLoai, setXepLoai] = useState<XepLoaiChatLuong>(
    chiTiet.xep_loai_quyet_dinh || xepLoaiDeXuat
  );
  const [lyDo, setLyDo] = useState(chiTiet.ly_do_dieu_chinh_cct || '');

  const needLyDo = xepLoai !== xepLoaiDeXuat;
  const canSave = !needLyDo || lyDo.trim().length > 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Quyết định xếp loại - {chiTiet.cong_chuc.ho_ten}
        </h3>

        {/* Thông tin điểm */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-gray-500">Điểm TC chung</p>
              <p className="text-lg font-semibold text-emerald-600">{chiTiet.diem_tieu_chi_chung.toFixed(6).replace(/\.?0+$/, '')}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Điểm KPI</p>
              <p className="text-lg font-semibold text-indigo-600">{chiTiet.diem_kpi.toFixed(6).replace(/\.?0+$/, '')}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Điểm tổng</p>
              <p className="text-lg font-semibold text-gray-900">{chiTiet.diem_tong.toFixed(6).replace(/\.?0+$/, '')}</p>
            </div>
          </div>
          <div className="mt-3 flex justify-center gap-4">
            <div>
              <span className="text-xs text-gray-500">Hệ thống: </span>
              <XepLoaiBadge xepLoai={chiTiet.xep_loai_he_thong} size="sm" />
            </div>
            <div>
              <span className="text-xs text-gray-500">Đề xuất: </span>
              <XepLoaiBadge xepLoai={xepLoaiDeXuat} size="sm" />
            </div>
          </div>
          {chiTiet.ly_do_dieu_chinh_dt && (
            <p className="text-xs text-gray-600 mt-2 text-center italic">
              Lý do đề xuất: "{chiTiet.ly_do_dieu_chinh_dt}"
            </p>
          )}
        </div>

        {/* Chọn xếp loại quyết định */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Xếp loại quyết định <span className="text-red-500">*</span>
          </label>
          <div className="flex gap-2">
            {XEP_LOAI_OPTIONS.map((xl) => {
              const color = getXepLoaiColor(xl);
              const isSelected = xl === xepLoai;
              return (
                <button
                  key={xl}
                  onClick={() => setXepLoai(xl)}
                  className={`flex-1 py-2 rounded-lg font-semibold border-2 transition-all ${
                    isSelected
                      ? `${color.bg} ${color.text} ${color.border}`
                      : 'bg-gray-50 text-gray-400 border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {xl}
                </button>
              );
            })}
          </div>
          {needLyDo && (
            <p className="text-xs text-amber-600 mt-1">
              ⚠️ Khác với đề xuất ({xepLoaiDeXuat}) - Bắt buộc nhập lý do
            </p>
          )}
        </div>

        {/* Lý do */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Lý do điều chỉnh {needLyDo && <span className="text-red-500">*</span>}
          </label>
          <textarea
            value={lyDo}
            onChange={(e) => setLyDo(e.target.value)}
            placeholder={needLyDo ? 'Nhập lý do (bắt buộc)' : 'Nhập lý do nếu có'}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
              needLyDo && !lyDo.trim() ? 'border-red-300' : 'border-gray-300'
            }`}
            rows={3}
          />
        </div>

        <div className="flex justify-end gap-3">
          <button onClick={onClose} disabled={isLoading} className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            Hủy
          </button>
          <button
            onClick={() => onSave(xepLoai, lyDo)}
            disabled={isLoading || !canSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading && <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />}
            Lưu
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Modal phê duyệt/từ chối.
 */
function PheDuyetModal({
  baoCao,
  onClose,
  onApprove,
  onReject,
  isLoading,
}: {
  baoCao: IBaoCaoXepLoai;
  onClose: () => void;
  onApprove: (yKien: string) => void;
  onReject: (yKien: string, chiTietTuChoi: { chi_tiet_id: string; ly_do: string }[]) => void;
  isLoading: boolean;
}) {
  const [action, setAction] = useState<'APPROVE' | 'REJECT'>('APPROVE');
  const [yKien, setYKien] = useState('');
  const [selectedReject, setSelectedReject] = useState<Set<string>>(new Set());
  const [rejectReasons, setRejectReasons] = useState<Record<string, string>>({});

  const canApprove = action === 'APPROVE';
  const canReject = action === 'REJECT' && selectedReject.size > 0 && 
    Array.from(selectedReject).every(id => rejectReasons[id]?.trim());

  const handleReject = () => {
    const chiTietTuChoi = Array.from(selectedReject).map(id => ({
      chi_tiet_id: id,
      ly_do: rejectReasons[id],
    }));
    onReject(yKien, chiTietTuChoi);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Phê duyệt báo cáo - {baoCao.don_vi.ten_don_vi}
        </h3>

        {/* Action tabs */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setAction('APPROVE')}
            className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
              action === 'APPROVE' 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            ✓ Phê duyệt
          </button>
          <button
            onClick={() => setAction('REJECT')}
            className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
              action === 'REJECT' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            ✗ Từ chối
          </button>
        </div>

        {/* Ý kiến chung */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Ý kiến</label>
          <textarea
            value={yKien}
            onChange={(e) => setYKien(e.target.value)}
            placeholder="Nhập ý kiến phê duyệt/từ chối"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            rows={2}
          />
        </div>

        {/* Chọn CC từ chối */}
        {action === 'REJECT' && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Chọn công chức bị từ chối <span className="text-red-500">*</span>
            </label>
            <div className="max-h-60 overflow-y-auto border border-gray-200 rounded-lg">
              {baoCao.chi_tiet.map((ct) => {
                const isSelected = selectedReject.has(ct.id);
                return (
                  <div 
                    key={ct.id} 
                    className={`p-3 border-b border-gray-100 last:border-b-0 ${isSelected ? 'bg-red-50' : ''}`}
                  >
                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => {
                          const newSet = new Set(selectedReject);
                          if (e.target.checked) {
                            newSet.add(ct.id);
                          } else {
                            newSet.delete(ct.id);
                          }
                          setSelectedReject(newSet);
                        }}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">{ct.cong_chuc.ho_ten}</span>
                          <XepLoaiBadge xepLoai={ct.xep_loai_de_xuat || ct.xep_loai_he_thong} size="sm" />
                        </div>
                        {isSelected && (
                          <input
                            type="text"
                            value={rejectReasons[ct.id] || ''}
                            onChange={(e) => setRejectReasons({ ...rejectReasons, [ct.id]: e.target.value })}
                            placeholder="Nhập lý do từ chối *"
                            className="w-full mt-2 px-2 py-1 text-sm border border-red-300 rounded focus:ring-2 focus:ring-red-500"
                          />
                        )}
                      </div>
                    </label>
                  </div>
                );
              })}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Đã chọn: {selectedReject.size} công chức
            </p>
          </div>
        )}

        {/* Buttons */}
        <div className="flex justify-end gap-3">
          <button onClick={onClose} disabled={isLoading} className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            Hủy
          </button>
          {action === 'APPROVE' ? (
            <button
              onClick={() => onApprove(yKien)}
              disabled={isLoading}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading && <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />}
              Phê duyệt
            </button>
          ) : (
            <button
              onClick={handleReject}
              disabled={isLoading || !canReject}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading && <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />}
              Từ chối
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PheDuyetXepLoaiPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  // State
  const [pendingList, setPendingList] = useState<IBaoCaoXepLoaiSummary[]>([]);
  const [selectedBaoCao, setSelectedBaoCao] = useState<IBaoCaoXepLoai | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Month/Year filter
  const currentDate = new Date();
  const [filterThang, setFilterThang] = useState<number | undefined>(undefined);
  const [filterNam, setFilterNam] = useState<number | undefined>(currentDate.getFullYear());

  // Modals
  const [editingChiTiet, setEditingChiTiet] = useState<IChiTietXepLoai | null>(null);
  const [showPheDuyetModal, setShowPheDuyetModal] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Auth check
  useEffect(() => {
    if (!isAuthenticated) router.push('/login');
  }, [isAuthenticated, router]);

  // Check quyền CCT
  const isCCT = user?.vai_tro?.cap_bac === 'CHI_CUC_TRUONG';

  // Load danh sách chờ duyệt
  const loadPendingList = useCallback(async () => {
    if (!isCCT) return;
    
    setIsLoading(true);
    setError(null);

    try {
      const data = await baoCaoXepLoaiService.getChoPeDuyet(filterThang, filterNam);
      setPendingList(data);
    } catch (err: any) {
      setError(err.message || 'Có lỗi xảy ra');
    } finally {
      setIsLoading(false);
    }
  }, [filterThang, filterNam, isCCT]);

  useEffect(() => {
    loadPendingList();
  }, [loadPendingList]);

  // Load chi tiết báo cáo
  const handleSelectBaoCao = async (baoCaoId: string) => {
    setIsLoadingDetail(true);
    try {
      const data = await baoCaoXepLoaiService.getBaoCaoChiTiet(baoCaoId);
      setSelectedBaoCao(data);
    } catch (err: any) {
      alert(err.message || 'Lỗi tải chi tiết báo cáo');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  // Handlers
  const handleSaveQuyetDinh = async (xepLoai: XepLoaiChatLuong, lyDo: string) => {
    if (!editingChiTiet) return;

    setIsProcessing(true);
    try {
      await baoCaoXepLoaiService.quyetDinhXepLoai(editingChiTiet.id, {
        xep_loai_quyet_dinh: xepLoai,
        ly_do_dieu_chinh: lyDo || undefined,
      });
      setEditingChiTiet(null);
      if (selectedBaoCao) {
        handleSelectBaoCao(selectedBaoCao.id);
      }
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Lỗi cập nhật quyết định');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApprove = async (yKien: string) => {
    if (!selectedBaoCao) return;

    setIsProcessing(true);
    try {
      await baoCaoXepLoaiService.pheDuyet(selectedBaoCao.id, {
        action: 'APPROVE',
        y_kien: yKien || undefined,
      });
      setShowPheDuyetModal(false);
      setSelectedBaoCao(null);
      alert('Phê duyệt thành công!');
      loadPendingList();
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Lỗi phê duyệt');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async (yKien: string, chiTietTuChoi: { chi_tiet_id: string; ly_do: string }[]) => {
    if (!selectedBaoCao) return;

    setIsProcessing(true);
    try {
      await baoCaoXepLoaiService.pheDuyet(selectedBaoCao.id, {
        action: 'REJECT',
        y_kien: yKien || undefined,
        chi_tiet_tu_choi: chiTietTuChoi,
      });
      setShowPheDuyetModal(false);
      setSelectedBaoCao(null);
      alert('Đã từ chối báo cáo!');
      loadPendingList();
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Lỗi từ chối');
    } finally {
      setIsProcessing(false);
    }
  };

  // Không có quyền
  if (!isCCT) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Không có quyền truy cập</h2>
          <p className="text-gray-600 mb-4">Chỉ Chi cục trưởng mới có quyền phê duyệt báo cáo xếp loại.</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Về Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/dashboard')}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📋 Phê duyệt Báo cáo Xếp loại</h1>
              <p className="text-gray-600 mt-1">Xử lý báo cáo từ các đơn vị</p>
            </div>
          </div>

          {/* Filter */}
          <div className="flex items-center gap-3">
            <select
              value={filterThang || ''}
              onChange={(e) => setFilterThang(e.target.value ? parseInt(e.target.value) : undefined)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tất cả tháng</option>
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>
              ))}
            </select>
            <select
              value={filterNam || ''}
              onChange={(e) => setFilterNam(e.target.value ? parseInt(e.target.value) : undefined)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tất cả năm</option>
              {[currentDate.getFullYear() - 1, currentDate.getFullYear(), currentDate.getFullYear() + 1].map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Danh sách báo cáo */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Báo cáo chờ phê duyệt ({pendingList.length})
            </h2>

            {isLoading ? (
              <div className="flex justify-center py-10">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
            ) : pendingList.length === 0 ? (
              <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-gray-600">Không có báo cáo nào chờ phê duyệt</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingList.map((bc) => (
                  <BaoCaoCard 
                    key={bc.id} 
                    baoCao={bc} 
                    onClick={() => handleSelectBaoCao(bc.id)} 
                  />
                ))}
              </div>
            )}
          </div>

          {/* Chi tiết báo cáo */}
          <div>
            {isLoadingDetail ? (
              <div className="bg-white rounded-xl border border-gray-200 p-8 flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
              </div>
            ) : selectedBaoCao ? (
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden sticky top-6">
                <div className="px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-white">
                    {selectedBaoCao.don_vi.ten_don_vi}
                  </h2>
                  <button
                    onClick={() => setSelectedBaoCao(null)}
                    className="text-white/80 hover:text-white"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="p-4">
                  {/* Thống kê */}
                  <div className="flex gap-2 mb-4 text-xs">
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded">A: {selectedBaoCao.so_loai_a}</span>
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">B: {selectedBaoCao.so_loai_b}</span>
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded">C: {selectedBaoCao.so_loai_c}</span>
                    <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded">D: {selectedBaoCao.so_loai_d}</span>
                    <span className="px-2 py-1 bg-red-100 text-red-700 rounded">E: {selectedBaoCao.so_loai_e}</span>
                  </div>

                  {selectedBaoCao.canh_bao_ty_le_a && (
                    <div className="mb-4 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
                      <p className="text-xs text-amber-700">⚠️ Tỷ lệ loại A vượt 20% số loại B</p>
                    </div>
                  )}

                  {/* Danh sách CC */}
                  <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-lg">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 text-left">Họ tên</th>
                          <th className="px-3 py-2 text-center">Điểm</th>
                          <th className="px-3 py-2 text-center">Đề xuất</th>
                          <th className="px-3 py-2 text-center">QĐ</th>
                          <th className="px-3 py-2"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {selectedBaoCao.chi_tiet.map((ct) => {
                          const xepLoaiDeXuat = ct.xep_loai_de_xuat || ct.xep_loai_he_thong;
                          const xepLoaiQD = ct.xep_loai_quyet_dinh || xepLoaiDeXuat;
                          return (
                            <tr key={ct.id} className={`hover:bg-gray-50 ${ct.is_lanh_dao ? 'bg-purple-50' : ''}`}>
                              <td className="px-3 py-2">
                                <div>
                                  <span className="font-medium">{ct.cong_chuc.ho_ten}</span>
                                  {ct.is_lanh_dao && (
                                    <span className="ml-1 text-xs text-purple-600">(LĐ)</span>
                                  )}
                                </div>
                              </td>
                              <td className="px-3 py-2 text-center font-medium">{ct.diem_tong.toFixed(6).replace(/\.?0+$/, '')}</td>
                              <td className="px-3 py-2 text-center">
                                <XepLoaiBadge xepLoai={xepLoaiDeXuat} size="sm" />
                              </td>
                              <td className="px-3 py-2 text-center">
                                <XepLoaiBadge xepLoai={xepLoaiQD} size="sm" />
                              </td>
                              <td className="px-3 py-2 text-center">
                                <button
                                  onClick={() => setEditingChiTiet(ct)}
                                  className="text-blue-600 hover:text-blue-800 text-xs"
                                >
                                  Sửa
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Action buttons */}
                  <div className="mt-4 flex gap-3">
                    <button
                      onClick={() => setShowPheDuyetModal(true)}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                    >
                      Xử lý phê duyệt
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-gray-500">Chọn một báo cáo để xem chi tiết</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Modals */}
      {editingChiTiet && (
        <QuyetDinhModal
          chiTiet={editingChiTiet}
          onClose={() => setEditingChiTiet(null)}
          onSave={handleSaveQuyetDinh}
          isLoading={isProcessing}
        />
      )}

      {showPheDuyetModal && selectedBaoCao && (
        <PheDuyetModal
          baoCao={selectedBaoCao}
          onClose={() => setShowPheDuyetModal(false)}
          onApprove={handleApprove}
          onReject={handleReject}
          isLoading={isProcessing}
        />
      )}
    </div>
  );
}
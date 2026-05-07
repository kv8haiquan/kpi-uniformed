/**
 * src/components/ke-khai/LeaderAssessmentDDE.tsx
 * ===============================================
 * Form đánh giá d, đ, e cho Lãnh đạo.
 * 
 * Các chỉ số:
 * - d: Kết quả hoạt động đơn vị (100% / 50%)
 * - đ: Khả năng tổ chức triển khai (100% / 50%)
 * - e: Năng lực đoàn kết nội bộ (100% / 50%)
 * 
 * UI: Checkbox (checked = 100%, unchecked = 50%)
 * 
 * Version: 2.5.8 (27/01/2026)
 * - FIX: Thêm nguoi_phe_duyet_id khi gửi duyệt
 * - FIX: Load danh sách người phê duyệt
 */

'use client';

import { useState, useEffect } from 'react';
import {
  IDanhGiaDDEForm,
  IDanhGiaDDEResponse,
  INguoiPheDuyetLanhDao,
  TrangThaiKeKhaiLD,
  percentToBool,
  boolToPercent,
} from '@/types/leader-kpi';
import { leaderKPIService } from '@/services/leader-kpi.service';

// =============================================================================
// PROPS
// =============================================================================

interface LeaderAssessmentDDEProps {
  thang: number;
  nam: number;
  onSaveSuccess?: () => void;
}

// =============================================================================
// SUB COMPONENTS
// =============================================================================

interface AssessmentItemProps {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  ghiChu: string;
  onChange: (checked: boolean) => void;
  onGhiChuChange: (value: string) => void;
  disabled?: boolean;
}

function AssessmentItem({
  id,
  label,
  description,
  checked,
  ghiChu,
  onChange,
  onGhiChuChange,
  disabled,
}: AssessmentItemProps) {
  return (
    <div className={`p-4 rounded-lg border-2 transition-all ${
      checked 
        ? 'bg-green-50 border-green-300' 
        : 'bg-yellow-50 border-yellow-300'
    }`}>
      <div className="flex items-start gap-4">
        <div className="flex items-center h-6">
          <input
            type="checkbox"
            id={id}
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            disabled={disabled}
            className="w-5 h-5 rounded border-gray-300 text-green-600 focus:ring-green-500 cursor-pointer disabled:cursor-not-allowed"
          />
        </div>

        <div className="flex-1">
          <label htmlFor={id} className="block cursor-pointer">
            <span className="font-medium text-gray-900">{label}</span>
            <p className="text-sm text-gray-600 mt-0.5">{description}</p>
          </label>

          <div className="mt-2 flex items-center gap-2">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              checked ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {checked ? '100%' : '50%'}
            </span>
            {!checked && <span className="text-xs text-yellow-700">(Có vấn đề cần lưu ý)</span>}
          </div>

          {!checked && (
            <div className="mt-3">
              <label className="block text-sm text-yellow-700 mb-1">Ghi chú lý do:</label>
              <textarea
                value={ghiChu}
                onChange={(e) => onGhiChuChange(e.target.value)}
                placeholder="Mô tả vấn đề, tồn tại..."
                rows={2}
                disabled={disabled}
                className="w-full px-3 py-2 text-sm border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 resize-none disabled:bg-gray-100"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LeaderAssessmentDDE({ thang, nam, onSaveSuccess }: LeaderAssessmentDDEProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const [existingData, setExistingData] = useState<IDanhGiaDDEResponse | null>(null);
  
  const [nguoiPheDuyetList, setNguoiPheDuyetList] = useState<INguoiPheDuyetLanhDao[]>([]);
  const [selectedNguoiPheDuyet, setSelectedNguoiPheDuyet] = useState<string>('');
  const [showGuiDuyetModal, setShowGuiDuyetModal] = useState(false);
  
  const [formData, setFormData] = useState<IDanhGiaDDEForm>({
    d_ket_qua_don_vi: true,
    d_ghi_chu: '',
    dd_to_chuc_trien_khai: true,
    dd_ghi_chu: '',
    e_doan_ket_noi_bo: true,
    e_ghi_chu: '',
  });

  const isApproved = existingData?.trang_thai === TrangThaiKeKhaiLD.DA_PHE_DUYET;
  const isPending = existingData?.trang_thai === TrangThaiKeKhaiLD.CHO_PHE_DUYET;

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      // FIX (07/05/2026): RESET state trước khi load để tránh hiển thị
      // data của tháng cũ khi đổi sang tháng chưa có DDE.
      setExistingData(null);
      setSuccessMessage(null);
      setFormData({
        d_ket_qua_don_vi: true,
        d_ghi_chu: '',
        dd_to_chuc_trien_khai: true,
        dd_ghi_chu: '',
        e_doan_ket_noi_bo: true,
        e_ghi_chu: '',
      });

      try {
        const [data, approvers] = await Promise.all([
          leaderKPIService.getDanhGiaDDE(thang, nam),
          leaderKPIService.getNguoiPheDuyetDDE(),
        ]);

        setNguoiPheDuyetList(approvers);
        if (approvers.length > 0) setSelectedNguoiPheDuyet(approvers[0].id);

        if (data) {
          setExistingData(data);
          setFormData({
            d_ket_qua_don_vi: percentToBool(data.d_ket_qua_don_vi),
            d_ghi_chu: data.d_ghi_chu || '',
            dd_to_chuc_trien_khai: percentToBool(data.dd_to_chuc_trien_khai),
            dd_ghi_chu: data.dd_ghi_chu || '',
            e_doan_ket_noi_bo: percentToBool(data.e_doan_ket_noi_bo),
            e_ghi_chu: data.e_ghi_chu || '',
          });
        }
        // Nếu data null (tháng chưa có DDE) → state đã reset ở trên,
        // hiển thị form trống cho user kê khai mới.
      } catch (err) {
        console.error('Error loading DDE:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [thang, nam]);

  const handleSave = async () => {
    setError(null);
    setSuccessMessage(null);
    setIsSaving(true);

    try {
      const result = await leaderKPIService.saveDanhGiaDDE({ ...formData, thang, nam });
      if (result) {
        setExistingData(result);
        setSuccessMessage('Đã lưu đánh giá thành công!');
        onSaveSuccess?.();
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.error?.message || err.message || 'Có lỗi xảy ra.';
      setError(errorMsg);
    } finally {
      setIsSaving(false);
    }
  };

  const handleOpenGuiDuyet = () => {
    if (!existingData) {
      setError('Vui lòng lưu đánh giá trước khi gửi duyệt.');
      return;
    }
    setShowGuiDuyetModal(true);
  };

  const handleGuiDuyet = async () => {
    if (!selectedNguoiPheDuyet) {
      setError('Vui lòng chọn người phê duyệt.');
      return;
    }

    setError(null);
    setIsSaving(true);

    try {
      const success = await leaderKPIService.guiDuyetDDE(thang, nam, selectedNguoiPheDuyet);
      if (success) {
        setSuccessMessage('Đã gửi phê duyệt thành công!');
        setShowGuiDuyetModal(false);
        const data = await leaderKPIService.getDanhGiaDDE(thang, nam);
        if (data) setExistingData(data);
        onSaveSuccess?.();
      } else {
        setError('Không thể gửi phê duyệt.');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.error?.message || err.message || 'Có lỗi xảy ra.';
      setError(errorMsg);
    } finally {
      setIsSaving(false);
    }
  };

  const tongDiem = boolToPercent(formData.d_ket_qua_don_vi) + boolToPercent(formData.dd_to_chuc_trien_khai) + boolToPercent(formData.e_doan_ket_noi_bo);
  const trungBinh = tongDiem / 3;

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8">
        <div className="flex items-center justify-center gap-3 text-gray-500">
          <div className="animate-spin w-5 h-5 border-2 border-gray-300 border-t-purple-600 rounded-full"></div>
          <span>Đang tải đánh giá d, đ, e...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-purple-600 to-pink-600 rounded-t-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">📊 Đánh giá d, đ, e</h3>
            <p className="text-purple-100 text-sm mt-1">Tháng {thang}/{nam} • Tự đánh giá năng lực lãnh đạo</p>
          </div>
          {existingData && (
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              isApproved ? 'bg-green-100 text-green-800' : isPending ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
            }`}>
              {isApproved ? '✅ Đã phê duyệt' : isPending ? '⏳ Chờ phê duyệt' : '📝 Nháp'}
            </span>
          )}
        </div>
      </div>

      <div className="p-6 space-y-4">
        {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3"><p className="text-red-700 text-sm">{error}</p></div>}
        {successMessage && <div className="bg-green-50 border border-green-200 rounded-lg p-3"><p className="text-green-700 text-sm">{successMessage}</p></div>}

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800 text-sm"><strong>Hướng dẫn:</strong> Tích checkbox nếu đạt tiêu chuẩn (100%). Bỏ tích nếu có vấn đề (50%) và ghi chú lý do.</p>
        </div>

        <div className="space-y-4">
          <AssessmentItem id="d_ket_qua" label="d. Kết quả hoạt động đơn vị" description="Đơn vị hoàn thành nhiệm vụ, không có CC bị xếp loại 'Không hoàn thành nhiệm vụ'" checked={formData.d_ket_qua_don_vi} ghiChu={formData.d_ghi_chu || ''} onChange={(c) => setFormData(p => ({ ...p, d_ket_qua_don_vi: c }))} onGhiChuChange={(v) => setFormData(p => ({ ...p, d_ghi_chu: v }))} disabled={isApproved || isPending} />
          <AssessmentItem id="dd_to_chuc" label="đ. Khả năng tổ chức triển khai" description="Triển khai công việc hiệu quả, không có tồn tại kéo dài, chậm trễ nghiêm trọng" checked={formData.dd_to_chuc_trien_khai} ghiChu={formData.dd_ghi_chu || ''} onChange={(c) => setFormData(p => ({ ...p, dd_to_chuc_trien_khai: c }))} onGhiChuChange={(v) => setFormData(p => ({ ...p, dd_ghi_chu: v }))} disabled={isApproved || isPending} />
          <AssessmentItem id="e_doan_ket" label="e. Năng lực đoàn kết nội bộ" description="Nội bộ đoàn kết, không có mâu thuẫn, xung đột" checked={formData.e_doan_ket_noi_bo} ghiChu={formData.e_ghi_chu || ''} onChange={(c) => setFormData(p => ({ ...p, e_doan_ket_noi_bo: c }))} onGhiChuChange={(v) => setFormData(p => ({ ...p, e_ghi_chu: v }))} disabled={isApproved || isPending} />
        </div>

        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Tổng điểm d + đ + e:</p>
              <p className="text-lg font-bold text-gray-900">{boolToPercent(formData.d_ket_qua_don_vi)}% + {boolToPercent(formData.dd_to_chuc_trien_khai)}% + {boolToPercent(formData.e_doan_ket_noi_bo)}% = {tongDiem}%</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Trung bình:</p>
              <p className={`text-2xl font-bold ${trungBinh === 100 ? 'text-green-600' : 'text-yellow-600'}`}>{trungBinh.toFixed(1)}%</p>
            </div>
          </div>
        </div>

        {!isApproved && (
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button onClick={handleSave} disabled={isSaving || isPending} className="px-5 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2">
              {isSaving ? <><div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>Đang lưu...</> : <>💾 Lưu đánh giá</>}
            </button>
            {existingData && !isPending && (
              <button onClick={handleOpenGuiDuyet} disabled={isSaving} className="px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2">✓ Gửi phê duyệt</button>
            )}
          </div>
        )}

        {isApproved && <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center"><p className="text-green-700">✅ Đánh giá đã được phê duyệt.</p></div>}
        {isPending && <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center"><p className="text-yellow-700">⏳ Đang chờ phê duyệt.</p></div>}
      </div>

      {showGuiDuyetModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Gửi phê duyệt đánh giá d, đ, e</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Chọn người phê duyệt <span className="text-red-500">*</span></label>
              {nguoiPheDuyetList.length > 0 ? (
                <select value={selectedNguoiPheDuyet} onChange={(e) => setSelectedNguoiPheDuyet(e.target.value)} className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
                  <option value="">-- Chọn người phê duyệt --</option>
                  {nguoiPheDuyetList.map((p) => <option key={p.id} value={p.id}>{p.ho_ten} - {p.chuc_vu || p.vai_tro?.ten_vai_tro}</option>)}
                </select>
              ) : <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3"><p className="text-yellow-700 text-sm">⚠️ Không tìm thấy người phê duyệt.</p></div>}
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowGuiDuyetModal(false)} className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">Hủy</button>
              <button onClick={handleGuiDuyet} disabled={!selectedNguoiPheDuyet || isSaving} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50">{isSaving ? 'Đang gửi...' : 'Gửi phê duyệt'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
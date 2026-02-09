/**
 * src/components/assessment/TieuChiChungForm.tsx
 * ===============================================
 * Form checkbox Binary Scoring cho Tiêu chí chung (30 điểm).
 *
 * ĐỒNG BỘ VỚI BACKEND v2.5.4
 * 
 * ⚠️ QUAN TRỌNG:
 * - Backend chỉ trả về 10 tiêu chí LỚN (1.1, 1.2, 2.1-2.4, 3.1-3.4)
 * - Form state dùng `ma_tieu_chi` làm key (KHÔNG phải id)
 * - Nhóm 1 & 2: Mặc định đạt (gia_tri_mac_dinh = true)
 * - Nhóm 3: Mặc định không đạt, cần minh chứng nếu tick
 *
 * Version: 2.5.4 (27/01/2026)
 */

'use client';

import { useState, useMemo } from 'react';
import {
  ITieuChiChungMaster,
  ITieuChiChungResponse,
  ITieuChiFormState,
  ITieuChiGhiChu,
  TrangThaiTieuChiChung,
  tinhDiemTuFormState,
  hasLanhDaoAdjustment,
} from '@/types/tieu-chi-chung';

// =============================================================================
// INTERFACES
// =============================================================================

interface TieuChiChungFormProps {
  /** Master Data 10 tiêu chí lớn */
  masterData: ITieuChiChungMaster[];
  
  /** Response tiêu chí (để hiển thị điều chỉnh LĐ) */
  responseData?: ITieuChiChungResponse[];
  
  /** Form state: key = ma_tieu_chi, value = is_achieved */
  formState: ITieuChiFormState;
  
  /** Callback khi thay đổi checkbox */
  onFormChange: (newState: ITieuChiFormState) => void;
  
  /** Ghi chú: key = ma_tieu_chi, value = ghi_chu_cc */
  ghiChu: ITieuChiGhiChu;
  
  /** Callback khi thay đổi ghi chú */
  onGhiChuChange: (newGhiChu: ITieuChiGhiChu) => void;
  
  /** Trạng thái đơn */
  trangThai?: TrangThaiTieuChiChung;
  
  /** Hiển thị cột so sánh LĐ */
  showLanhDaoColumn?: boolean;
}

// =============================================================================
// HELPER
// =============================================================================

function getNhomColor(nhom: number): { bg: string; border: string; light: string; text: string; checkbox: string } {
  const colors: Record<number, { bg: string; border: string; light: string; text: string; checkbox: string }> = {
    1: { bg: 'bg-emerald-600', border: 'border-emerald-200', light: 'bg-emerald-50', text: 'text-emerald-700', checkbox: 'text-emerald-600' },
    2: { bg: 'bg-sky-600', border: 'border-sky-200', light: 'bg-sky-50', text: 'text-sky-700', checkbox: 'text-sky-600' },
    3: { bg: 'bg-amber-600', border: 'border-amber-200', light: 'bg-amber-50', text: 'text-amber-700', checkbox: 'text-amber-600' },
  };
  return colors[nhom] || colors[1];
}

function getNhomLabel(nhom: number): string {
  const labels: Record<number, string> = {
    1: 'Nhóm I: Phẩm chất chính trị, đạo đức',
    2: 'Nhóm II: Năng lực chuyên môn, nghiệp vụ',
    3: 'Nhóm III: Năng lực đổi mới, sáng tạo',
  };
  return labels[nhom] || `Nhóm ${nhom}`;
}

function getNhomDescription(nhom: number): string {
  const descriptions: Record<number, string> = {
    1: 'Mặc định đạt, bỏ tick nếu vi phạm',
    2: 'Mặc định đạt, bỏ tick nếu vi phạm',
    3: 'Tick nếu có thành tích (cần minh chứng)',
  };
  return descriptions[nhom] || '';
}

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

interface TieuChiItemProps {
  tieuChi: ITieuChiChungMaster;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled: boolean;
  responseItem?: ITieuChiChungResponse;
  showLanhDaoColumn: boolean;
  ghiChu: string;
  onGhiChuChange: (value: string) => void;
  color: ReturnType<typeof getNhomColor>;
}

function TieuChiItem({
  tieuChi,
  checked,
  onChange,
  disabled,
  responseItem,
  showLanhDaoColumn,
  ghiChu,
  onGhiChuChange,
  color,
}: TieuChiItemProps) {
  const isNhom3 = tieuChi.nhom_tieu_chi === 3;
  const isViolation = !checked && !isNhom3; // Nhóm 1 & 2: Bỏ tick = vi phạm
  const hasAdjustment = responseItem ? hasLanhDaoAdjustment(responseItem) : false;

  return (
    <div
      className={`rounded-lg border transition-colors ${
        isViolation
          ? 'bg-red-50 border-red-200'
          : 'bg-white border-gray-200 hover:border-gray-300'
      }`}
    >
      <div className="flex items-start gap-3 p-4">
        <input
          type="checkbox"
          id={`tc-${tieuChi.ma_tieu_chi}`}
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className={`mt-1 w-5 h-5 ${color.checkbox} border-gray-300 rounded focus:ring-2 focus:ring-offset-0 disabled:opacity-50`}
        />
        <label htmlFor={`tc-${tieuChi.ma_tieu_chi}`} className="flex-1 cursor-pointer">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-gray-900">TC {tieuChi.ma_tieu_chi}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              checked 
                ? 'bg-green-100 text-green-700' 
                : isNhom3 
                  ? 'bg-gray-100 text-gray-600'
                  : 'bg-red-100 text-red-700'
            }`}>
              {tieuChi.diem_toi_da} điểm
            </span>
            {isViolation && (
              <span className="text-xs text-red-600 font-medium">⚠️ Không đạt</span>
            )}
          </div>
          <p className={`text-sm ${isViolation ? 'text-red-700' : 'text-gray-600'}`}>
            {tieuChi.ten_tieu_chi}
          </p>
        </label>

        {/* Cột LĐ */}
        {showLanhDaoColumn && (
          <div className="flex-shrink-0 w-24 text-center border-l pl-3">
            <div className="text-xs text-gray-500 mb-1">LĐ đánh giá</div>
            {responseItem?.is_achieved_ld === null || responseItem?.is_achieved_ld === undefined ? (
              <span className="text-gray-400">—</span>
            ) : responseItem.is_achieved_ld ? (
              <span className="text-green-600 font-medium">✓ Đạt</span>
            ) : (
              <span className="text-red-600 font-medium">✗ Không</span>
            )}
            {hasAdjustment && (
              <div className="text-orange-500 text-xs mt-1">⚠️ Điều chỉnh</div>
            )}
          </div>
        )}
      </div>

      {/* Ghi chú (Nhóm 3 - hiện khi tick) */}
      {isNhom3 && checked && (
        <div className="px-4 pb-4 pt-0">
          <div className="ml-8">
            <label className="text-xs text-gray-500 block mb-1">
              Minh chứng thành tích <span className="text-red-500">*</span>:
            </label>
            <textarea
              value={ghiChu}
              onChange={(e) => onGhiChuChange(e.target.value)}
              disabled={disabled}
              placeholder="VD: Có sáng kiến cải tiến quy trình kiểm tra hàng hóa, được ghi nhận..."
              className="w-full border border-amber-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 disabled:bg-gray-100"
              rows={2}
            />
          </div>
        </div>
      )}

      {/* Hiển thị điều chỉnh của LĐ */}
      {hasAdjustment && responseItem && (
        <div className="mx-4 mb-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
          <p className="text-sm text-orange-800">
            <strong>⚠️ Lãnh đạo đã điều chỉnh:</strong>{' '}
            {responseItem.is_achieved_ld ? 'Đạt' : 'Không đạt'}
          </p>
          {responseItem.ly_do_dieu_chinh && (
            <p className="text-xs text-orange-700 mt-1">
              Lý do: {responseItem.ly_do_dieu_chinh}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

interface NhomTieuChiSectionProps {
  nhom: number;
  tieuChiList: ITieuChiChungMaster[];
  formState: ITieuChiFormState;
  onFormChange: (newState: ITieuChiFormState) => void;
  ghiChu: ITieuChiGhiChu;
  onGhiChuChange: (newGhiChu: ITieuChiGhiChu) => void;
  disabled: boolean;
  diemNhom: number;
  responseData?: ITieuChiChungResponse[];
  showLanhDaoColumn: boolean;
}

function NhomTieuChiSection({
  nhom,
  tieuChiList,
  formState,
  onFormChange,
  ghiChu,
  onGhiChuChange,
  disabled,
  diemNhom,
  responseData,
  showLanhDaoColumn,
}: NhomTieuChiSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const color = getNhomColor(nhom);
  const label = getNhomLabel(nhom);
  const description = getNhomDescription(nhom);
  const maxDiem = 10;

  const handleCheckboxChange = (maTieuChi: string, checked: boolean) => {
    onFormChange({ ...formState, [maTieuChi]: checked });
  };

  const handleGhiChuItemChange = (maTieuChi: string, value: string) => {
    onGhiChuChange({ ...ghiChu, [maTieuChi]: value });
  };

  if (tieuChiList.length === 0) return null;

  return (
    <div className={`border rounded-xl overflow-hidden shadow-sm ${color.border}`}>
      {/* Header */}
      <div
        className={`px-5 py-4 ${color.light} cursor-pointer flex items-center justify-between`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-4">
          <span
            className={`flex items-center justify-center w-10 h-10 ${color.bg} text-white rounded-full text-lg font-bold`}
          >
            {['I', 'II', 'III'][nhom - 1]}
          </span>
          <div>
            <h3 className="font-semibold text-gray-900">{label}</h3>
            <p className="text-sm text-gray-500">{description}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div
            className={`px-4 py-2 rounded-full font-bold text-lg ${
              diemNhom >= maxDiem
                ? 'bg-green-100 text-green-700'
                : diemNhom > 0
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {diemNhom.toFixed(1)} / {maxDiem} đ
          </div>

          <svg
            className={`w-5 h-5 text-gray-500 transition-transform ${
              isExpanded ? 'rotate-180' : ''
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-5 bg-gray-50 space-y-3">
          {tieuChiList.map((tc: ITieuChiChungMaster) => {
            const responseItem = responseData?.find(
              (r: ITieuChiChungResponse) => r.ma_tieu_chi === tc.ma_tieu_chi
            );
            return (
              <TieuChiItem
                key={tc.ma_tieu_chi}
                tieuChi={tc}
                checked={formState[tc.ma_tieu_chi] ?? tc.gia_tri_mac_dinh}
                onChange={(checked: boolean) => handleCheckboxChange(tc.ma_tieu_chi, checked)}
                disabled={disabled}
                responseItem={responseItem}
                showLanhDaoColumn={showLanhDaoColumn}
                ghiChu={ghiChu[tc.ma_tieu_chi] || ''}
                onGhiChuChange={(value: string) => handleGhiChuItemChange(tc.ma_tieu_chi, value)}
                color={color}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TieuChiChungForm({
  masterData,
  responseData,
  formState,
  onFormChange,
  ghiChu,
  onGhiChuChange,
  trangThai,
  showLanhDaoColumn = false,
}: TieuChiChungFormProps) {
  // Kiểm tra disabled
  const isDisabled =
    trangThai === TrangThaiTieuChiChung.CHO_PHE_DUYET ||
    trangThai === TrangThaiTieuChiChung.DA_PHE_DUYET;

  // Tính điểm từ form state
  const diemPreview = useMemo(
    () => tinhDiemTuFormState(masterData, formState),
    [masterData, formState]
  );

  // Chia theo nhóm - ⚠️ masterData chỉ có 10 TC lớn (không có children)
  const nhom1 = masterData.filter((tc: ITieuChiChungMaster) => tc.nhom_tieu_chi === 1);
  const nhom2 = masterData.filter((tc: ITieuChiChungMaster) => tc.nhom_tieu_chi === 2);
  const nhom3 = masterData.filter((tc: ITieuChiChungMaster) => tc.nhom_tieu_chi === 3);

  // Empty state
  if (masterData.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
        <p className="text-yellow-800">⚠️ Không có dữ liệu tiêu chí để hiển thị.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Disabled Warning */}
      {isDisabled && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-yellow-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <span className="text-yellow-800 font-medium">
              {trangThai === TrangThaiTieuChiChung.CHO_PHE_DUYET
                ? 'Đơn đang chờ phê duyệt - Không thể chỉnh sửa'
                : 'Đã được phê duyệt - Chỉ xem kết quả'}
            </span>
          </div>
        </div>
      )}

      {/* Render 3 nhóm */}
      <NhomTieuChiSection
        nhom={1}
        tieuChiList={nhom1}
        formState={formState}
        onFormChange={onFormChange}
        ghiChu={ghiChu}
        onGhiChuChange={onGhiChuChange}
        disabled={isDisabled}
        diemNhom={diemPreview.nhom_1_diem}
        responseData={responseData}
        showLanhDaoColumn={showLanhDaoColumn}
      />

      <NhomTieuChiSection
        nhom={2}
        tieuChiList={nhom2}
        formState={formState}
        onFormChange={onFormChange}
        ghiChu={ghiChu}
        onGhiChuChange={onGhiChuChange}
        disabled={isDisabled}
        diemNhom={diemPreview.nhom_2_diem}
        responseData={responseData}
        showLanhDaoColumn={showLanhDaoColumn}
      />

      <NhomTieuChiSection
        nhom={3}
        tieuChiList={nhom3}
        formState={formState}
        onFormChange={onFormChange}
        ghiChu={ghiChu}
        onGhiChuChange={onGhiChuChange}
        disabled={isDisabled}
        diemNhom={diemPreview.nhom_3_diem}
        responseData={responseData}
        showLanhDaoColumn={showLanhDaoColumn}
      />
    </div>
  );
}

// Re-export types for convenience
export type { ITieuChiFormState, ITieuChiGhiChu };
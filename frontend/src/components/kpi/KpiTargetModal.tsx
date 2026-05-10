/**
 * src/components/kpi/KpiTargetModal.tsx
 * =====================================
 * Modal form để thêm mới hoặc chỉnh sửa kê khai công việc.
 *
 * Version: 2.7.4 (02/02/2026)
 * UPDATE v2.7.4:
 * - Thêm textarea mô tả lỗi chất lượng / tiến độ riêng biệt
 * - Tách section tự đánh giá: số lỗi + mô tả CL, số lỗi + mô tả TĐ
 * - Gửi ghi_chu_tu_dg_chat_luong, ghi_chu_tu_dg_tien_do lên API
 *
 * UPDATE v2.7.0:
 * - Thêm dropdown Sản phẩm chuẩn (SP1-SP4) - chọn trước
 * - Dropdown Công việc filter theo SP chuẩn đã chọn
 * - Hiển thị mô tả công việc khi đã chọn công việc
 *
 * Features:
 * - Dùng chung cho Create và Edit
 * - React Hook Form + Zod validation
 * - Dropdown chọn SP chuẩn → công việc → cấp độ
 * - Xử lý hệ số thực tế cho cấp độ C5
 */

'use client';

import { useEffect, useState } from 'react';
import { useForm, Controller, Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import { keKhaiFormSchema, KeKhaiFormData, keKhaiFormDefaults } from '@/lib/validations/kpi';
import { kpiService } from '@/services/kpi.service';
import { isApiError } from '@/lib/axios';
import {
  IKeKhaiCongViec,
  IDanhMucCongViec,
  ICapDo,
} from '@/types/kpi';

import { formatScore } from '@/lib/format';
// =============================================================================
// TYPES
// =============================================================================

// v2.7.0: Interface cho Sản phẩm chuẩn (SP1-SP4)
interface ISpChuan {
  id: string;
  ma_sp: string;
  ten_sp: string;
  mo_ta?: string;
  thoi_gian_phut?: number; // v2.8.0: Thêm thời gian để hiển thị trong option
  he_so_quy_doi_sp1?: number; // Hệ số quy đổi về SP1
}

interface KpiTargetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  editData?: IKeKhaiCongViec | null; // Nếu có => Edit mode
  thang: number;
  nam: number;
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function KpiTargetModal({
  isOpen,
  onClose,
  onSuccess,
  editData,
  thang,
  nam,
}: KpiTargetModalProps) {
  // State cho master data
  const [spChuanList, setSpChuanList] = useState<ISpChuan[]>([]); // v2.7.0: Danh sách SP chuẩn
  const [danhMucList, setDanhMucList] = useState<IDanhMucCongViec[]>([]);
  const [capDoList, setCapDoList] = useState<ICapDo[]>([]);
  const [nguoiPheDuyetList, setNguoiPheDuyetList] = useState<
    Array<{ id: string; ho_ten: string; chuc_vu: string }>
  >([]);
  
  // v2.7.0: State cho SP chuẩn đã chọn
  const [selectedSpChuanId, setSelectedSpChuanId] = useState<string>('');

  // State cho loading
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Kiểm tra edit mode
  const isEditMode = !!editData;

  // React Hook Form
const {
  register,
  control,
  handleSubmit,
  watch,
  reset,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setValue,
  formState: { errors },
} = useForm<KeKhaiFormData, unknown, KeKhaiFormData>({
  resolver: zodResolver(keKhaiFormSchema) as Resolver<KeKhaiFormData>,
  // ...
});

  // Watch cấp độ để hiển thị trường hệ số thực tế
  const selectedCapDoId = watch('cap_do_id');
  const selectedCapDo = capDoList.find((c) => c.id === selectedCapDoId);
  const isC5 = selectedCapDo?.is_theo_thuc_te ?? false;

  // v2.7.4: Kiểm tra SP chuẩn đã chọn có phải SP3/SP4 không
  const selectedSpChuan = spChuanList.find(sp => sp.id === selectedSpChuanId);
  const isSp3OrSp4 = selectedSpChuan?.ma_sp === 'SP3' || selectedSpChuan?.ma_sp === 'SP4';
  
  // v2.7.4: Tìm cấp độ C1 để auto-select
  const capDoC1 = capDoList.find(cd => cd.ma_cap_do === 'C1');

  // v2.7.4: Auto-select C1 khi chọn SP3 hoặc SP4
  useEffect(() => {
    if (isSp3OrSp4 && capDoC1) {
      setValue('cap_do_id', capDoC1.id);
    }
  }, [isSp3OrSp4, capDoC1, setValue]);

  // Load master data khi modal mở
  useEffect(() => {
    if (isOpen) {
      loadMasterData();
    }
  }, [isOpen]);

  // Reset form khi modal mở/đóng hoặc editData thay đổi
  // PHẢI CÓ danhMucList trong deps để re-run khi master data load xong
  useEffect(() => {
    if (isOpen) {
      if (editData) {
        // =================================================================
        // v2.7.4 FIX: API response trả nested objects (danh_muc_sp, cap_do)
        // nhưng KHÔNG trả danh_muc_sp_id, cap_do_id trực tiếp.
        // Phải extract ID từ nested object để form select đúng giá trị.
        // =================================================================
        const resolvedDanhMucSpId =
          editData.danh_muc_sp_id || editData.danh_muc_sp?.id || '';
        const resolvedCapDoId =
          editData.cap_do_id || editData.cap_do?.id || '';
        const resolvedNguoiPdId =
          editData.nguoi_phe_duyet_id ||
          (editData as any).nguoi_phe_duyet?.id || '';

        // Edit mode: populate form với dữ liệu có sẵn
        reset({
          danh_muc_sp_id: resolvedDanhMucSpId,
          cap_do_id: resolvedCapDoId,
          so_luong: editData.so_luong,
          thang: editData.thang,
          nam: editData.nam,
          ngay_thuc_hien: editData.ngay_thuc_hien || undefined,
          mo_ta_cong_viec: editData.mo_ta_cong_viec || undefined,
          is_doi_moi_sang_tao: editData.is_doi_moi_sang_tao,
          ngay_deadline: editData.ngay_deadline || undefined,
          ngay_hoan_thanh: editData.ngay_hoan_thanh || undefined,
          he_so_thuc_te: editData.he_so_thuc_te || undefined,
          nguoi_phe_duyet_id: resolvedNguoiPdId || undefined,
          tu_danh_gia_chat_luong: editData.tu_danh_gia_chat_luong,
          tu_danh_gia_tien_do: editData.tu_danh_gia_tien_do,
          ghi_chu_tu_danh_gia: editData.ghi_chu_tu_danh_gia || undefined,
          // v2.7.4: Mô tả lỗi riêng CL/TĐ
          ghi_chu_tu_dg_chat_luong: editData.ghi_chu_tu_dg_chat_luong || '',
          ghi_chu_tu_dg_tien_do: editData.ghi_chu_tu_dg_tien_do || '',
        });

        // v2.7.4 FIX: Set SP chuẩn từ editData
        // API nested danh_muc_sp chỉ trả {id, ma_danh_muc, ten_cong_viec, ma_sp}
        // KHÔNG trả sp_chuan_id. Phải dùng fallback strategies:
        // 1. Match ma_sp (SP1/SP2...) từ nested → tìm trong spChuanList
        // 2. Tìm trong danhMucList đã load (có sp_chuan_id)
        const nestedMaSp = (editData.danh_muc_sp as any)?.ma_sp;
        const matchedSpChuan = nestedMaSp
          ? spChuanList.find(sp => sp.ma_sp === nestedMaSp)
          : null;

        if (matchedSpChuan) {
          setSelectedSpChuanId(matchedSpChuan.id);
        } else if (danhMucList.length > 0) {
          const editDanhMuc = danhMucList.find(dm => dm.id === resolvedDanhMucSpId);
          const spId = editDanhMuc?.sp_chuan_id || (editDanhMuc as any)?.sp_chuan?.id;
          if (spId) {
            setSelectedSpChuanId(spId);
          }
        }
      } else {
        // Create mode: reset TẤT CẢ fields về giá trị mặc định
        // v2.7.3 FIX: KHÔNG dùng ...keKhaiFormDefaults (Partial) vì nó THIẾU
        // danh_muc_sp_id, cap_do_id, nguoi_phe_duyet_id → React Hook Form
        // reset() sẽ GIỮ NGUYÊN giá trị cũ cho các field không được liệt kê!
        // Phải khai báo TOÀN BỘ fields = '' để reset triệt để.
        const now = new Date();
        const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        reset({
          danh_muc_sp_id: '',          // ← QUAN TRỌNG: phải có để reset select
          cap_do_id: '',               // ← QUAN TRỌNG: phải có để reset select
          nguoi_phe_duyet_id: '',      // ← QUAN TRỌNG: phải có để reset select
          so_luong: 1,
          thang,
          nam,
          ngay_thuc_hien: today,
          mo_ta_cong_viec: '',
          is_doi_moi_sang_tao: false,
          ngay_deadline: undefined,
          ngay_hoan_thanh: undefined,
          he_so_thuc_te: undefined,
          tu_danh_gia_chat_luong: 0,
          tu_danh_gia_tien_do: 0,
          ghi_chu_tu_danh_gia: '',
          // v2.7.4: Mô tả lỗi riêng CL/TĐ
          ghi_chu_tu_dg_chat_luong: '',
          ghi_chu_tu_dg_tien_do: '',
        });
        setSelectedSpChuanId(''); // v2.7.0: Reset SP chuẩn
      }
      setSubmitError(null);
    }
  }, [isOpen, editData, thang, nam, reset, danhMucList, spChuanList]);

  // Load danh mục, cấp độ, người phê duyệt
  const loadMasterData = async () => {
    setIsLoadingData(true);
    try {
      const [spChuan, danhMuc, capDo, nguoiPD] = await Promise.all([
        kpiService.getSpChuanList(), // v2.7.0: Load danh sách SP chuẩn
        kpiService.getDanhMucCongViec(),
        kpiService.getCapDoPhucTap(),
        kpiService.getNguoiPheDuyet(),
      ]);

      setSpChuanList(spChuan);
      setDanhMucList(danhMuc);
      setCapDoList(capDo);
      setNguoiPheDuyetList(nguoiPD);
      
      // v2.7.1: Debug log để kiểm tra data
      console.log('[KpiTargetModal] SP Chuẩn:', spChuan);
      console.log('[KpiTargetModal] Danh mục mẫu:', danhMuc[0]);
    } catch (error) {
      console.error('Failed to load master data:', error);
    } finally {
      setIsLoadingData(false);
    }
  };
  
  // v2.7.1: Filter danh mục công việc theo SP chuẩn đã chọn
  // Hỗ trợ cả sp_chuan_id trực tiếp và sp_chuan.id nested
  const filteredDanhMucList = selectedSpChuanId
    ? danhMucList.filter((dm) => {
        const dmAny = dm as any;
        // Ưu tiên sp_chuan_id trực tiếp, nếu không có thì dùng sp_chuan.id
        const spId = dmAny.sp_chuan_id || dmAny.sp_chuan?.id;
        // So sánh cả string để tránh lỗi UUID
        return spId === selectedSpChuanId || String(spId) === String(selectedSpChuanId);
      })
    : danhMucList;
  
  // v2.7.0: Lấy thông tin công việc đã chọn để hiển thị mô tả
  const selectedDanhMucId = watch('danh_muc_sp_id');
  const selectedDanhMuc = danhMucList.find((dm) => dm.id === selectedDanhMucId);

  // Xử lý submit form
  const onSubmit = async (data: KeKhaiFormData) => {
    // v2.7.2: Validate bắt buộc người phê duyệt
    if (!data.nguoi_phe_duyet_id) {
      setSubmitError('Vui lòng chọn người phê duyệt');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      if (isEditMode && editData) {
        // Update
        await kpiService.updateKeKhai(editData.id, {
          danh_muc_sp_id: data.danh_muc_sp_id,
          cap_do_id: data.cap_do_id,
          so_luong: data.so_luong,
          ngay_thuc_hien: data.ngay_thuc_hien || undefined,
          mo_ta_cong_viec: data.mo_ta_cong_viec || undefined,
          is_doi_moi_sang_tao: data.is_doi_moi_sang_tao,
          ngay_deadline: data.ngay_deadline || undefined,
          ngay_hoan_thanh: data.ngay_hoan_thanh || undefined,
          he_so_thuc_te: isC5 ? (data.he_so_thuc_te ?? undefined) : undefined,
          nguoi_phe_duyet_id: data.nguoi_phe_duyet_id || undefined,
          tu_danh_gia_chat_luong: data.tu_danh_gia_chat_luong,
          tu_danh_gia_tien_do: data.tu_danh_gia_tien_do,
          ghi_chu_tu_danh_gia: data.ghi_chu_tu_danh_gia || undefined,
          // v2.7.4: Mô tả lỗi riêng CL/TĐ
          ghi_chu_tu_dg_chat_luong: data.ghi_chu_tu_dg_chat_luong || undefined,
          ghi_chu_tu_dg_tien_do: data.ghi_chu_tu_dg_tien_do || undefined,
        });
      } else {
        // Create
        await kpiService.createKeKhai({
          danh_muc_sp_id: data.danh_muc_sp_id,
          cap_do_id: data.cap_do_id,
          so_luong: data.so_luong,
          thang: data.thang,
          nam: data.nam,
          ngay_thuc_hien: data.ngay_thuc_hien || undefined,
          mo_ta_cong_viec: data.mo_ta_cong_viec || undefined,
          is_doi_moi_sang_tao: data.is_doi_moi_sang_tao,
          ngay_deadline: data.ngay_deadline || undefined,
          ngay_hoan_thanh: data.ngay_hoan_thanh || undefined,
          he_so_thuc_te: isC5 ? (data.he_so_thuc_te ?? undefined) : undefined,
          nguoi_phe_duyet_id: data.nguoi_phe_duyet_id || undefined,
          tu_danh_gia_chat_luong: data.tu_danh_gia_chat_luong,
          tu_danh_gia_tien_do: data.tu_danh_gia_tien_do,
          ghi_chu_tu_danh_gia: data.ghi_chu_tu_danh_gia || undefined,
          // v2.7.4: Mô tả lỗi riêng CL/TĐ
          ghi_chu_tu_dg_chat_luong: data.ghi_chu_tu_dg_chat_luong || undefined,
          ghi_chu_tu_dg_tien_do: data.ghi_chu_tu_dg_tien_do || undefined,
        });
      }

      // Thành công
      onSuccess();
      onClose();
    } catch (error) {
      if (isApiError(error)) {
        setSubmitError(error.message);
      } else {
        setSubmitError('Đã có lỗi xảy ra. Vui lòng thử lại.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Không render nếu modal đóng
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div 
          className="relative w-full max-w-2xl bg-white rounded-lg shadow-xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              {isEditMode ? 'Sửa kê khai công việc' : 'Thêm kê khai công việc'}
            </h3>
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Body */}
          <form onSubmit={handleSubmit(onSubmit)} autoComplete="off">
            <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
              {isLoadingData ? (
                <div className="flex items-center justify-center py-8">
                  <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Error message */}
                  {submitError && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3">
                      <p className="text-sm text-red-600">{submitError}</p>
                    </div>
                  )}

                  {/* v2.7.0: Loại công việc */}
                  <div>
                    <label className="label">
                      Loại công việc <span className="text-red-500">*</span>
                    </label>
                    <select
                      className="input"
                      value={selectedSpChuanId}
                      onChange={(e) => {
                        setSelectedSpChuanId(e.target.value);
                        // Reset công việc đã chọn khi đổi loại CV
                        setValue('danh_muc_sp_id', '');
                      }}
                    >
                      <option value="">-- Chọn loại công việc --</option>
                      {spChuanList.map((sp) => (
                        <option key={sp.id} value={sp.id}>
                          {sp.ma_sp} - {sp.ten_sp}
                          {sp.thoi_gian_phut != null && ` — ${sp.thoi_gian_phut} phút`}
                        </option>
                      ))}
                    </select>

                    {/* Issue #3: Hiển thị thông tin SP đã chọn */}
                    {selectedSpChuan && (
                      <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded text-sm space-y-1">
                        <p className="font-medium text-blue-900">
                          {selectedSpChuan.ten_sp}
                        </p>
                        {selectedSpChuan.mo_ta && (
                          <p className="text-blue-700 text-xs">{selectedSpChuan.mo_ta}</p>
                        )}
                      </div>
                    )}

                    {!selectedSpChuanId && (
                      <p className="text-xs text-gray-500 mt-1">
                        Chọn loại công việc trước, sau đó chọn công việc cụ thể
                      </p>
                    )}
                  </div>

                  {/* Công việc - chỉ hiện khi đã chọn SP chuẩn */}
                  <div>
                    <label className="label">
                      Tên công việc <span className="text-red-500">*</span>
                    </label>
                    <select
                      className={`input ${errors.danh_muc_sp_id ? 'input-error' : ''}`}
                      {...register('danh_muc_sp_id')}
                      disabled={!selectedSpChuanId}
                    >
                      <option value="">
                        {selectedSpChuanId ? '-- Chọn công việc --' : '-- Vui lòng chọn loại công việc trước --'}
                      </option>
                      {filteredDanhMucList.map((dm) => (
                        <option key={dm.id} value={dm.id}>
                          [{dm.ma_danh_muc}] {dm.ten_cong_viec}
                        </option>
                      ))}
                    </select>
                    {errors.danh_muc_sp_id && (
                      <p className="error-text">{errors.danh_muc_sp_id.message}</p>
                    )}
                    {selectedSpChuanId && filteredDanhMucList.length === 0 && (
                      <p className="text-xs text-yellow-600 mt-1">
                        Không có công việc nào thuộc loại này
                      </p>
                    )}
                  </div>
                  
                  {/* v2.7.0: Hiển thị mô tả công việc (readonly) */}
                  {selectedDanhMuc?.mo_ta && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <p className="text-xs font-medium text-blue-700 mb-1">📝 Mô tả công việc:</p>
                      <p className="text-sm text-blue-900">{selectedDanhMuc.mo_ta}</p>
                    </div>
                  )}

                  {/* Cấp độ phức tạp */}
                  <div>
                    <label className="label">
                      Cấp độ phức tạp <span className="text-red-500">*</span>
                    </label>
                    <select
                      className={`input ${errors.cap_do_id ? 'input-error' : ''} ${isSp3OrSp4 ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                      {...register('cap_do_id')}
                      disabled={isSp3OrSp4}
                    >
                      <option value="">-- Chọn cấp độ --</option>
                      {capDoList.map((cd) => {
                        // Tính thời gian phút cho cấp độ này (dựa vào SP đã chọn)
                        let thoiGianPhut: number | string = 0;
                        if (selectedSpChuan && cd.ma_cap_do !== 'C5') {
                          const hesoQuyDoi = selectedSpChuan.thoi_gian_phut || 60;
                          const hesoCapDo = selectedSpChuan.ma_sp === 'SP1'
                            ? (cd.he_so_sp1 || 1)
                            : (cd.he_so_sp2 || 1);
                          thoiGianPhut = hesoQuyDoi * hesoCapDo;
                        } else if (cd.ma_cap_do === 'C5') {
                          thoiGianPhut = 'Tùy biến';
                        }

                        return (
                          <option key={cd.id} value={cd.id}>
                            {cd.ma_cap_do} - {cd.ten_cap_do}
                            {thoiGianPhut !== 0 && ` — ${thoiGianPhut}${typeof thoiGianPhut === 'number' ? ' phút' : ''}`}
                          </option>
                        );
                      })}
                    </select>
                    {errors.cap_do_id && (
                      <p className="error-text">{errors.cap_do_id.message}</p>
                    )}
                    {isSp3OrSp4 && (
                      <p className="text-xs text-blue-600 mt-1">
                        ℹ️ SP3/SP4 chỉ áp dụng cấp độ C1
                      </p>
                    )}

                    {/* Issue #3: Hiển thị thông tin cấp độ đã chọn */}
                    {selectedCapDo && selectedSpChuan && (
                      <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded text-sm space-y-1">
                        {selectedCapDo.ma_cap_do === 'C5' ? (
                          <p className="text-green-700 text-xs">
                            <strong>C5:</strong> Hệ số do lãnh đạo xác định theo tính chất công việc
                          </p>
                        ) : (
                          <>
                            {/* Hiển thị hệ số và phút tương ứng */}
                            {(() => {
                              // Lấy hệ số cấp độ
                              let hesoCapDo = 1;
                              if (selectedSpChuan.ma_sp === 'SP1') {
                                hesoCapDo = selectedCapDo.he_so_sp1 || 1;
                              } else {
                                hesoCapDo = selectedCapDo.he_so_sp2 || 1;
                              }

                              // Tính phút = thoi_gian_phut × hesoCapDo
                              const phut = (selectedSpChuan.thoi_gian_phut || 0) * hesoCapDo;
                              // Tính SP1 = he_so_quy_doi_sp1 × hesoCapDo (khớp backend)
                              const sp1 = (selectedSpChuan.he_so_quy_doi_sp1 || 0) * hesoCapDo;

                              return (
                                <p className="text-green-700 text-xs">
                                  <strong>Hệ số ×{hesoCapDo}</strong> → {phut} phút (= {formatScore(sp1)} điểm)
                                </p>
                              );
                            })()}
                          </>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Hệ số thực tế - chỉ hiện khi C5 */}
                  {isC5 && (
                    <div>
                      <label className="label">
                        Hệ số thực tế (C5) <span className="text-red-500">*</span>
                      </label>
                      <Controller
                        name="he_so_thuc_te"
                        control={control}
                        render={({ field }) => (
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            max="100"
                            className={`input ${errors.he_so_thuc_te ? 'input-error' : ''}`}
                            placeholder="Nhập hệ số"
                            value={field.value ?? ''}
                            onBlur={field.onBlur}
                            name={field.name}
                            ref={field.ref}
                            onChange={(e) => {
                              const val = e.target.valueAsNumber;
                              field.onChange(isNaN(val) ? null : val);
                            }}
                          />
                        )}
                      />
                      {errors.he_so_thuc_te && (
                        <p className="error-text">{errors.he_so_thuc_te.message}</p>
                      )}
                      <p className="text-xs text-gray-500 mt-1">
                        Hệ số do Lãnh đạo xác định theo thực tế
                      </p>
                    </div>
                  )}

                  {/* Số lượng */}
                  <div>
                    <label className="label">
                      Số lượng <span className="text-red-500">*</span>
                    </label>
                    <Controller
                      name="so_luong"
                      control={control}
                      render={({ field: { ref, value, onChange, onBlur, ...rest } }) => (
                        <input
                          type="text"
                          inputMode="numeric"
                          pattern="[0-9]*"
                          className={`input ${errors.so_luong ? 'input-error' : ''}`}
                          placeholder="Nhập số lượng"
                          ref={ref}
                          {...rest}
                          value={value === 0 || value ? String(value) : ''}
                          onChange={(e) => {
                            const raw = e.target.value;
                            // Chỉ cho phép nhập số
                            if (raw === '') {
                              // Cho phép xóa trống tạm thời (hiển thị rỗng)
                              // Gửi NaN để Zod bắt lỗi khi submit
                              onChange(NaN);
                            } else if (/^\d+$/.test(raw)) {
                              onChange(Number(raw));
                            }
                            // Nếu nhập ký tự không phải số → bỏ qua
                          }}
                          onBlur={(e) => {
                            // Khi rời ô: nếu trống hoặc NaN thì giữ nguyên (để Zod validate)
                            onBlur();
                          }}
                        />
                      )}
                    />
                    {errors.so_luong && (
                      <p className="error-text">{errors.so_luong.message}</p>
                    )}

                    {/* Issue #3: Hiển thị tổng SP1 quy đổi */}
                    {(() => {
                      const soLuong = watch('so_luong');
                      if (!selectedSpChuan || !selectedCapDo || !soLuong || isNaN(soLuong)) {
                        return null;
                      }

                      // Lấy hệ số cấp độ
                      let hesoCapDo = 1;
                      if (selectedCapDo.ma_cap_do === 'C5') {
                        const hesoThucTe = watch('he_so_thuc_te');
                        hesoCapDo = hesoThucTe || 1;
                      } else if (selectedSpChuan.ma_sp === 'SP1') {
                        hesoCapDo = selectedCapDo.he_so_sp1 || 1;
                      } else {
                        hesoCapDo = selectedCapDo.he_so_sp2 || 1;
                      }

                      // Tổng SP1 quy đổi = soLuong × he_so_quy_doi_sp1 × hesoCapDo
                      // (khớp backend: so_luong × sp_chuan.he_so_quy_doi_sp1 × he_so_cap_do)
                      const tongSp1 = soLuong * (selectedSpChuan.he_so_quy_doi_sp1 || 0) * hesoCapDo;

                      return (
                        <div className="mt-2 p-2 bg-purple-50 border border-purple-200 rounded text-sm">
                          <p className="text-purple-700 text-xs">
                            <strong>Tổng điểm quy đổi:</strong> {formatScore(tongSp1)} điểm
                          </p>
                        </div>
                      );
                    })()}
                  </div>

                  {/* Ngày thực hiện */}
                  <div>
                    <label className="label">Ngày thực hiện</label>
                    <input
                      type="date"
                      className="input"
                      {...register('ngay_thuc_hien')}
                    />
                  </div>

                  {/* Mô tả công việc */}
                  <div>
                    <label className="label">Mô tả công việc</label>
                    <textarea
                      rows={3}
                      className={`input ${errors.mo_ta_cong_viec ? 'input-error' : ''}`}
                      placeholder="Mô tả chi tiết công việc..."
                      {...register('mo_ta_cong_viec')}
                    />
                    {errors.mo_ta_cong_viec && (
                      <p className="error-text">{errors.mo_ta_cong_viec.message}</p>
                    )}
                  </div>

                  {/* Đổi mới sáng tạo */}
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_doi_moi_sang_tao"
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      {...register('is_doi_moi_sang_tao')}
                    />
                    <label htmlFor="is_doi_moi_sang_tao" className="ml-2 text-sm text-gray-700">
                      Có tính đổi mới sáng tạo
                    </label>
                  </div>

                  {/* Người phê duyệt - BẮT BUỘC v2.7.2 */}
                  <div>
                    <label className="label">
                      Người phê duyệt <span className="text-red-500">*</span>
                    </label>
                    {nguoiPheDuyetList.length > 0 ? (
                      <select
                        className="input"
                        {...register('nguoi_phe_duyet_id')}
                      >
                        <option value="">-- Chọn người phê duyệt --</option>
                        {nguoiPheDuyetList.map((npd) => (
                          <option key={npd.id} value={npd.id}>
                            {npd.ho_ten} ({npd.chuc_vu})
                          </option>
                        ))}
                      </select>
                    ) : (
                      <p className="text-sm text-yellow-600 italic">
                        Không tìm thấy người phê duyệt phù hợp
                      </p>
                    )}
                  </div>

                  {/* Divider - Tự đánh giá chất lượng & tiến độ */}
                  <div className="border-t border-gray-200 pt-4 mt-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">
                      📊 Tự đánh giá chất lượng &amp; tiến độ
                    </h4>

                    {/* === Chất lượng === */}
                    <div className="mb-4">
                      <label className="label">Số lỗi chất lượng</label>
                      <Controller
                        name="tu_danh_gia_chat_luong"
                        control={control}
                        render={({ field }) => (
                          <input
                            type="number"
                            min="0"
                            className="input"
                            {...field}
                            onChange={(e) => field.onChange(e.target.valueAsNumber || 0)}
                          />
                        )}
                      />
                      <p className="text-xs text-gray-400 mt-1">0 = Không có lỗi chất lượng</p>

                      {/* v2.7.4: Mô tả lỗi chất lượng */}
                      <div className="mt-2">
                        <label className="label text-gray-500">
                          Mô tả lỗi chất lượng <span className="text-gray-400">(không bắt buộc)</span>
                        </label>
                        <textarea
                          rows={2}
                          className="input"
                          placeholder="Mô tả chi tiết về lỗi chất lượng (nếu có)..."
                          {...register('ghi_chu_tu_dg_chat_luong')}
                        />
                      </div>
                    </div>

                    <hr className="border-gray-100 my-3" />

                    {/* === Tiến độ === */}
                    <div className="mb-4">
                      <label className="label">Số lỗi tiến độ</label>
                      <Controller
                        name="tu_danh_gia_tien_do"
                        control={control}
                        render={({ field }) => (
                          <input
                            type="number"
                            min="0"
                            className="input"
                            {...field}
                            onChange={(e) => field.onChange(e.target.valueAsNumber || 0)}
                          />
                        )}
                      />
                      <p className="text-xs text-gray-400 mt-1">0 = Không có lỗi tiến độ</p>

                      {/* v2.7.4: Mô tả lỗi tiến độ */}
                      <div className="mt-2">
                        <label className="label text-gray-500">
                          Mô tả lỗi tiến độ <span className="text-gray-400">(không bắt buộc)</span>
                        </label>
                        <textarea
                          rows={2}
                          className="input"
                          placeholder="Mô tả chi tiết về lỗi tiến độ (nếu có)..."
                          {...register('ghi_chu_tu_dg_tien_do')}
                        />
                      </div>
                    </div>

                    {/* Ghi chú tự đánh giá chung (giữ lại) */}
                    <div className="mt-3">
                      <label className="label">Ghi chú / Giải trình chung</label>
                      <textarea
                        rows={2}
                        className="input"
                        placeholder="Giải trình chung về lỗi (nếu có)..."
                        {...register('ghi_chu_tu_danh_gia')}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
              <button
                type="button"
                onClick={onClose}
                className="btn-outline"
                disabled={isSubmitting}
              >
                Hủy
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={isSubmitting || isLoadingData}
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Đang lưu...
                  </>
                ) : isEditMode ? (
                  'Cập nhật'
                ) : (
                  'Thêm mới'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
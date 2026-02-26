/**
 * src/components/kpi/KpiMultiDayModal.tsx
 * ========================================
 * Modal để tạo kê khai công việc cho nhiều ngày cùng lúc.
 *
 * Version: 1.0.0 (25/02/2026)
 *
 * Features:
 * - Chọn công việc, cấp độ, số lượng (giống KpiTargetModal)
 * - Chọn nhiều ngày bằng MultiDayCalendar
 * - Preview tổng số bản kê khai sẽ tạo
 * - Option tự động gửi duyệt sau khi tạo
 * - Loading state và error handling
 */

'use client';

import { useState, useEffect } from 'react';
import { useForm, Controller, Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';

import { kpiService } from '@/services/kpi.service';
import { isApiError } from '@/lib/axios';
import {
  IDanhMucCongViec,
  ICapDo,
} from '@/types/kpi';
import MultiDayCalendar from './MultiDayCalendar';

// =============================================================================
// TYPES
// =============================================================================

interface ISpChuan {
  id: string;
  ma_sp: string;
  ten_sp: string;
  mo_ta?: string;
}

interface KpiMultiDayModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  thang: number;
  nam: number;
}

// Schema validation cho form
const multiDayFormSchema = z.object({
  danh_muc_sp_id: z.string().min(1, 'Vui lòng chọn công việc'),
  cap_do_id: z.string().min(1, 'Vui lòng chọn cấp độ phức tạp'),
  so_luong: z.number().int().positive('Số lượng phải lớn hơn 0'),
  nguoi_phe_duyet_id: z.string().optional(),
  mo_ta_cong_viec: z.string().max(1000, 'Mô tả tối đa 1000 ký tự').optional(),
  he_so_thuc_te: z.number().positive().optional(),
  is_doi_moi_sang_tao: z.boolean().default(false),
  tu_danh_gia_chat_luong: z.number().int().min(0).default(0),
  tu_danh_gia_tien_do: z.number().int().min(0).default(0),
  ghi_chu_tu_danh_gia: z.string().max(500).optional(),
  auto_submit: z.boolean().default(false), // Tự động gửi duyệt
});

type MultiDayFormData = z.infer<typeof multiDayFormSchema>;

// =============================================================================
// COMPONENT
// =============================================================================

export default function KpiMultiDayModal({
  isOpen,
  onClose,
  onSuccess,
  thang,
  nam,
}: KpiMultiDayModalProps) {
  // State cho master data
  const [spChuanList, setSpChuanList] = useState<ISpChuan[]>([]);
  const [danhMucList, setDanhMucList] = useState<IDanhMucCongViec[]>([]);
  const [capDoList, setCapDoList] = useState<ICapDo[]>([]);
  const [nguoiPheDuyetList, setNguoiPheDuyetList] = useState<
    Array<{ id: string; ho_ten: string; chuc_vu: string }>
  >([]);

  const [selectedSpChuanId, setSelectedSpChuanId] = useState<string>('');
  const [selectedDates, setSelectedDates] = useState<Date[]>([]);

  // State cho loading & errors
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // React Hook Form
  const {
    register,
    control,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors },
  } = useForm<MultiDayFormData, unknown, MultiDayFormData>({
    resolver: zodResolver(multiDayFormSchema) as Resolver<MultiDayFormData>,
    defaultValues: {
      danh_muc_sp_id: '',
      cap_do_id: '',
      so_luong: 1,
      nguoi_phe_duyet_id: '',
      mo_ta_cong_viec: '',
      is_doi_moi_sang_tao: false,
      he_so_thuc_te: undefined,
      tu_danh_gia_chat_luong: 0,
      tu_danh_gia_tien_do: 0,
      ghi_chu_tu_danh_gia: '',
      auto_submit: false,
    },
  });

  // Watch để hiển thị mô tả công việc
  const selectedCapDoId = watch('cap_do_id');
  const selectedCapDo = capDoList.find((c) => c.id === selectedCapDoId);
  const isC5 = selectedCapDo?.is_theo_thuc_te ?? false;

  const selectedSpChuan = spChuanList.find((sp) => sp.id === selectedSpChuanId);
  const isSp3OrSp4 = selectedSpChuan?.ma_sp === 'SP3' || selectedSpChuan?.ma_sp === 'SP4';

  const capDoC1 = capDoList.find((cd) => cd.ma_cap_do === 'C1');

  // Auto-select C1 khi chọn SP3/SP4
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

  // Reset form khi modal mở/đóng
  useEffect(() => {
    if (isOpen) {
      reset({
        danh_muc_sp_id: '',
        cap_do_id: '',
        so_luong: 1,
        nguoi_phe_duyet_id: '',
        mo_ta_cong_viec: '',
        is_doi_moi_sang_tao: false,
        he_so_thuc_te: undefined,
        tu_danh_gia_chat_luong: 0,
        tu_danh_gia_tien_do: 0,
        ghi_chu_tu_danh_gia: '',
        auto_submit: false,
      });
      setSelectedSpChuanId('');
      setSelectedDates([]);
      setSubmitError(null);
    }
  }, [isOpen, reset]);

  // Load danh mục, cấp độ, người phê duyệt
  const loadMasterData = async () => {
    setIsLoadingData(true);
    try {
      const [spChuan, danhMuc, capDo, nguoiPD] = await Promise.all([
        kpiService.getSpChuanList(),
        kpiService.getDanhMucCongViec(),
        kpiService.getCapDoPhucTap(),
        kpiService.getNguoiPheDuyet(),
      ]);

      setSpChuanList(spChuan);
      setDanhMucList(danhMuc);
      setCapDoList(capDo);
      setNguoiPheDuyetList(nguoiPD);
    } catch (error) {
      console.error('Failed to load master data:', error);
    } finally {
      setIsLoadingData(false);
    }
  };

  // Filter danh mục theo SP chuẩn đã chọn
  const filteredDanhMucList = selectedSpChuanId
    ? danhMucList.filter((dm) => {
        const dmAny = dm as any;
        const spId = dmAny.sp_chuan_id || dmAny.sp_chuan?.id;
        return spId === selectedSpChuanId || String(spId) === String(selectedSpChuanId);
      })
    : danhMucList;

  const selectedDanhMucId = watch('danh_muc_sp_id');
  const selectedDanhMuc = danhMucList.find((dm) => dm.id === selectedDanhMucId);

  // Tính toán preview
  const soLuong = watch('so_luong');
  const totalDeclarations = selectedDates.length;
  const totalSP = totalDeclarations * soLuong;

  // Xử lý submit form
  const onSubmit = async (data: MultiDayFormData) => {
    if (selectedDates.length === 0) {
      setSubmitError('Vui lòng chọn ít nhất 1 ngày');
      return;
    }

    if (!data.nguoi_phe_duyet_id) {
      setSubmitError('Vui lòng chọn người phê duyệt');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Format dates to ISO strings
      const ngayThucHienList = selectedDates.map((date) =>
        format(date, 'yyyy-MM-dd')
      );

      // Gọi API tạo kê khai nhiều ngày
      const createResponse = await kpiService.keKhaiNhieuNgay({
        danh_muc_sp_id: data.danh_muc_sp_id,
        cap_do_id: data.cap_do_id,
        so_luong: data.so_luong,
        ngay_thuc_hien_list: ngayThucHienList,
        nguoi_phe_duyet_id: data.nguoi_phe_duyet_id,
        mo_ta_cong_viec: data.mo_ta_cong_viec || undefined,
        he_so_thuc_te: isC5 ? (data.he_so_thuc_te ?? undefined) : undefined,
        is_doi_moi_sang_tao: data.is_doi_moi_sang_tao,
        tu_danh_gia_chat_luong: data.tu_danh_gia_chat_luong,
        tu_danh_gia_tien_do: data.tu_danh_gia_tien_do,
        ghi_chu_tu_danh_gia: data.ghi_chu_tu_danh_gia || undefined,
      });

      // Nếu chọn auto submit, gửi duyệt luôn
      if (data.auto_submit && createResponse.ke_khai_ids.length > 0) {
        try {
          await kpiService.guiDuyetBulk({
            ke_khai_ids: createResponse.ke_khai_ids,
            nguoi_phe_duyet_id: data.nguoi_phe_duyet_id,
          });
          alert(
            `✅ Đã tạo và gửi duyệt thành công ${createResponse.total_created} bản kê khai!`
          );
        } catch (submitError) {
          console.error('Lỗi khi gửi duyệt:', submitError);
          alert(
            `✅ Đã tạo ${createResponse.total_created} bản kê khai.\n` +
            `⚠️ Nhưng gửi duyệt thất bại. Vui lòng gửi duyệt thủ công.`
          );
        }
      } else {
        alert(`✅ Đã tạo thành công ${createResponse.total_created} bản kê khai!`);
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
          className="relative w-full max-w-4xl bg-white rounded-lg shadow-xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Kê khai nhiều ngày cùng lúc
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
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Cột trái: Form thông tin công việc */}
                  <div className="space-y-4">
                    {/* Error message */}
                    {submitError && (
                      <div className="bg-red-50 border border-red-200 rounded-md p-3">
                        <p className="text-sm text-red-600">{submitError}</p>
                      </div>
                    )}

                    {/* Sản phẩm chuẩn */}
                    <div>
                      <label className="label">
                        Sản phẩm chuẩn <span className="text-red-500">*</span>
                      </label>
                      <select
                        className="input"
                        value={selectedSpChuanId}
                        onChange={(e) => {
                          setSelectedSpChuanId(e.target.value);
                          setValue('danh_muc_sp_id', '');
                        }}
                      >
                        <option value="">-- Chọn sản phẩm chuẩn --</option>
                        {spChuanList.map((sp) => (
                          <option key={sp.id} value={sp.id}>
                            {sp.ma_sp} - {sp.ten_sp}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Công việc */}
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
                          {selectedSpChuanId ? '-- Chọn công việc --' : '-- Vui lòng chọn SP chuẩn trước --'}
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
                    </div>

                    {/* Mô tả công việc (readonly) */}
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
                        {capDoList.map((cd) => (
                          <option key={cd.id} value={cd.id}>
                            {cd.ma_cap_do} - {cd.ten_cap_do}
                          </option>
                        ))}
                      </select>
                      {errors.cap_do_id && (
                        <p className="error-text">{errors.cap_do_id.message}</p>
                      )}
                      {isSp3OrSp4 && (
                        <p className="text-xs text-blue-600 mt-1">
                          ℹ️ SP3/SP4 chỉ áp dụng cấp độ C1
                        </p>
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
                              if (raw === '') {
                                onChange(NaN);
                              } else if (/^\d+$/.test(raw)) {
                                onChange(Number(raw));
                              }
                            }}
                            onBlur={onBlur}
                          />
                        )}
                      />
                      {errors.so_luong && (
                        <p className="error-text">{errors.so_luong.message}</p>
                      )}
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

                    {/* Người phê duyệt */}
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

                    {/* Tự đánh giá */}
                    <div className="border-t border-gray-200 pt-4 mt-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">
                        📊 Tự đánh giá chất lượng &amp; tiến độ
                      </h4>

                      <div className="space-y-3">
                        {/* Chất lượng */}
                        <div>
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
                        </div>

                        {/* Tiến độ */}
                        <div>
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
                        </div>

                        {/* Ghi chú */}
                        <div>
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
                  </div>

                  {/* Cột phải: Calendar & Preview */}
                  <div className="space-y-4">
                    {/* Calendar */}
                    <MultiDayCalendar
                      month={thang}
                      year={nam}
                      selectedDates={selectedDates}
                      onDatesChange={setSelectedDates}
                    />

                    {/* Preview */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-green-800 mb-2">
                        📄 Xem trước kết quả
                      </h4>
                      <div className="space-y-2 text-sm text-green-700">
                        <p>
                          <span className="font-medium">Số ngày đã chọn:</span>{' '}
                          {totalDeclarations} ngày
                        </p>
                        <p>
                          <span className="font-medium">Số lượng mỗi ngày:</span>{' '}
                          {soLuong}
                        </p>
                        <div className="border-t border-green-300 mt-2 pt-2">
                          <p className="font-semibold">
                            Tổng số bản kê khai sẽ tạo: {totalDeclarations} bản
                          </p>
                          <p className="font-semibold">
                            Tổng SP: {totalSP}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Auto submit checkbox */}
                    <div className="flex items-center bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <input
                        type="checkbox"
                        id="auto_submit"
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        {...register('auto_submit')}
                      />
                      <label htmlFor="auto_submit" className="ml-2 text-sm text-yellow-800">
                        Tự động gửi duyệt sau khi tạo
                      </label>
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
                disabled={isSubmitting || isLoadingData || selectedDates.length === 0}
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Đang xử lý...
                  </>
                ) : (
                  `Tạo ${totalDeclarations} bản kê khai`
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

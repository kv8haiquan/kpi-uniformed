'use client';

/**
 * components/kpi-v2/KpiTargetModalV2.tsx
 * ======================================
 * Modal kê khai 1 ngày V2_PL3.
 *
 * Khác V1:
 * - KHÔNG có dropdown cấp độ C1-C5 (LOCKED 8 — V2 không dùng).
 * - KHÔNG có field "hệ số thực tế" override (LOCKED 14).
 * - Hệ số quy đổi tự lấy từ mục PL3 đã chọn (read-only display).
 * - Search 2.812 mục PL3 với LinhVucNhomFilter + DanhMucSearchCombobox.
 *
 * Submit:
 * - "Lưu nháp": POST /ke-khai-v2 → trạng thái NHAP.
 * - "Lưu và gửi duyệt": POST /ke-khai-v2 → sau đó POST /ke-khai/{id}/gui-duyet
 *   (endpoint cũ V1 hoạt động cho cả V2).
 */

import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { X, AlertCircle } from 'lucide-react';

import apiClient, { isApiError } from '@/lib/axios';
import { kpiV2Service } from '@/services/kpi-v2.service';
import { kpiService } from '@/services/kpi.service';
import { keKhaiV2Schema, KeKhaiV2FormData, KeKhaiV2FormInput } from '@/lib/validations/kpi-v2';
import { IDanhMucPL3, IKeKhaiV2Response } from '@/types/kpi-v2';
import { INguoiPheDuyet } from '@/services/kpi.service';

import { DanhMucPickerTabs } from './DanhMucPickerTabs';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  thang: number;
  nam: number;
  /** Khi truyền vào → modal chuyển sang edit mode (PUT /ke-khai-v2/{id}). */
  editing?: IKeKhaiV2Response | null;
}

export function KpiTargetModalV2({ open, onClose, onSuccess, thang, nam, editing }: Props) {
  const isEdit = !!editing;
  const [selectedDM, setSelectedDM] = useState<IDanhMucPL3 | null>(null);
  const [nguoiPheDuyetList, setNguoiPheDuyetList] = useState<INguoiPheDuyet[]>([]);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<KeKhaiV2FormInput, unknown, KeKhaiV2FormData>({
    resolver: zodResolver(keKhaiV2Schema),
    defaultValues: {
      thang,
      nam,
      so_luong: 1,
      is_doi_moi_sang_tao: false,
      tu_danh_gia_chat_luong: 0,
      tu_danh_gia_tien_do: 0,
    },
  });

  const watchedSoLuong = watch('so_luong');
  const watchedLoiCl = watch('tu_danh_gia_chat_luong');
  const watchedLoiTd = watch('tu_danh_gia_tien_do');

  const tongSpQuyDoi = useMemo(() => {
    if (!selectedDM) return 0;
    const sl = Number(watchedSoLuong);
    if (!Number.isFinite(sl) || sl <= 0) return 0;
    return sl * selectedDM.he_so_quy_doi;
  }, [selectedDM, watchedSoLuong]);

  // SP đạt CL/TĐ = he_so × max(0, sl - 0.25 × min(loi, sl × 4))  (giữ nguyên V1 LOCKED 3)
  const calcSpDat = (sl: number, heSo: number, loi: number): number => {
    if (sl <= 0 || heSo <= 0) return 0;
    const safeLoi = Math.max(0, loi);
    const maxLoi = sl * 4;
    const loiTinh = Math.min(safeLoi, maxLoi);
    return Math.max(0, heSo * (sl - 0.25 * loiTinh));
  };

  const spDatCL = useMemo(() => {
    if (!selectedDM) return 0;
    return calcSpDat(Number(watchedSoLuong) || 0, selectedDM.he_so_quy_doi, Number(watchedLoiCl) || 0);
  }, [selectedDM, watchedSoLuong, watchedLoiCl]);

  const spDatTD = useMemo(() => {
    if (!selectedDM) return 0;
    return calcSpDat(Number(watchedSoLuong) || 0, selectedDM.he_so_quy_doi, Number(watchedLoiTd) || 0);
  }, [selectedDM, watchedSoLuong, watchedLoiTd]);

  // Load người phê duyệt khi mở modal
  useEffect(() => {
    if (!open) return;
    kpiService
      .getNguoiPheDuyet()
      .then(setNguoiPheDuyetList)
      .catch((err) => console.error('getNguoiPheDuyet error', err));
  }, [open]);

  // Reset state khi đóng / mở. Nếu đang edit → prefill từ `editing`.
  useEffect(() => {
    if (!open) {
      setSelectedDM(null);
      setSubmitError(null);
      reset({
        thang,
        nam,
        so_luong: 1,
        is_doi_moi_sang_tao: false,
        tu_danh_gia_chat_luong: 0,
        tu_danh_gia_tien_do: 0,
      });
      return;
    }

    if (editing) {
      const dm = editing.danh_muc_sp;
      if (dm) {
        setSelectedDM(dm);
      }
      reset({
        danh_muc_sp_id: editing.danh_muc_sp?.id ?? '',
        so_luong: editing.so_luong,
        thang: editing.thang,
        nam: editing.nam,
        ngay_thuc_hien: editing.ngay_thuc_hien ?? '',
        mo_ta_cong_viec: editing.mo_ta_cong_viec ?? '',
        is_doi_moi_sang_tao: !!editing.is_doi_moi_sang_tao,
        ngay_deadline: editing.ngay_deadline ?? '',
        ngay_hoan_thanh: editing.ngay_hoan_thanh ?? '',
        nguoi_phe_duyet_id: editing.nguoi_phe_duyet_id ?? '',
        tu_danh_gia_chat_luong: editing.tu_danh_gia_chat_luong ?? 0,
        tu_danh_gia_tien_do: editing.tu_danh_gia_tien_do ?? 0,
        ghi_chu_tu_danh_gia: editing.ghi_chu_tu_danh_gia ?? '',
        ghi_chu_tu_dg_chat_luong: editing.ghi_chu_tu_dg_chat_luong ?? '',
        ghi_chu_tu_dg_tien_do: editing.ghi_chu_tu_dg_tien_do ?? '',
      });
    }
  }, [open, editing, reset, thang, nam]);

  // Khi chọn mục → set danh_muc_sp_id vào form
  useEffect(() => {
    if (selectedDM) {
      setValue('danh_muc_sp_id', selectedDM.id);
    }
  }, [selectedDM, setValue]);

  if (!open) return null;

  const submitWithSendApprove = async (
    data: KeKhaiV2FormData,
    sendApprove: boolean
  ) => {
    setSubmitError(null);
    setSubmitting(true);
    try {
      const payload = {
        danh_muc_sp_id: data.danh_muc_sp_id,
        so_luong: data.so_luong,
        thang: data.thang,
        nam: data.nam,
        ngay_thuc_hien: data.ngay_thuc_hien || undefined,
        mo_ta_cong_viec: data.mo_ta_cong_viec || undefined,
        is_doi_moi_sang_tao: data.is_doi_moi_sang_tao,
        ngay_deadline: data.ngay_deadline || undefined,
        ngay_hoan_thanh: data.ngay_hoan_thanh || undefined,
        nguoi_phe_duyet_id: data.nguoi_phe_duyet_id,
        tu_danh_gia_chat_luong: data.tu_danh_gia_chat_luong,
        tu_danh_gia_tien_do: data.tu_danh_gia_tien_do,
        ghi_chu_tu_danh_gia: data.ghi_chu_tu_danh_gia || undefined,
        ghi_chu_tu_dg_chat_luong: data.ghi_chu_tu_dg_chat_luong || undefined,
        ghi_chu_tu_dg_tien_do: data.ghi_chu_tu_dg_tien_do || undefined,
      };

      const saved = isEdit && editing
        ? await kpiV2Service.updateKeKhai(editing.id, payload)
        : await kpiV2Service.createKeKhai(payload);

      if (sendApprove) {
        // Reuse endpoint V1 /ke-khai/{id}/gui-duyet (hoạt động cho V2)
        await apiClient.post(`/ke-khai/${saved.id}/gui-duyet`, {
          nguoi_phe_duyet_id: data.nguoi_phe_duyet_id,
        });
      }

      onSuccess();
      onClose();
    } catch (err: unknown) {
      console.error('Submit V2 error:', err);
      if (isApiError(err)) {
        if (err.code === 'MIXED_VERSION_NOT_ALLOWED') {
          setSubmitError(
            'Tháng này đã có kê khai V1. Liên hệ TCCB nếu muốn chuyển sang V2.'
          );
        } else if (err.code === 'INVALID_CATALOG_VERSION') {
          setSubmitError(
            'Mục đã chọn không hợp lệ với phiên bản kê khai. Vui lòng chọn lại.'
          );
        } else {
          setSubmitError(err.message);
        }
      } else {
        setSubmitError('Lỗi không xác định khi tạo kê khai.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {isEdit ? 'Sửa kê khai — V2_PL3' : 'Kê khai công việc — V2_PL3'}
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Tháng {thang}/{nam} • {isEdit ? 'Chỉnh sửa bản kê khai' : 'Search 2.812 mục PL3'}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-100"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <form className="px-6 py-4 space-y-5">
          {/* Picker tabs: ⭐ Yêu thích / 🕐 Tháng trước / 📋 Tất cả */}
          <section>
            <h3 className="text-sm font-medium text-gray-900 mb-2">
              1. Tìm mục công việc
            </h3>
            <DanhMucPickerTabs
              thang={thang}
              nam={nam}
              selectedId={selectedDM?.id}
              onSelect={setSelectedDM}
              initialTab={isEdit ? 'all' : undefined}
            />
            {errors.danh_muc_sp_id && (
              <p className="mt-1 text-xs text-red-600">
                {errors.danh_muc_sp_id.message}
              </p>
            )}
          </section>

          {/* Đã chọn */}
          {selectedDM && (
            <section className="rounded-md bg-blue-50 border border-blue-200 px-4 py-3">
              <h3 className="text-sm font-medium text-blue-900 mb-1">Đã chọn</h3>
              <p className="text-sm font-semibold text-gray-900">
                {selectedDM.ten_cong_viec}
              </p>
              <div className="mt-1 text-xs text-gray-700 space-x-4">
                <span>Lĩnh vực: <strong>{selectedDM.linh_vuc}</strong></span>
                <span>Nhóm: <strong>{selectedDM.nhom_pl3}</strong></span>
                <span>
                  Hệ số quy đổi: <strong>{selectedDM.he_so_quy_doi.toFixed(2)}</strong>
                </span>
                <span>Sản phẩm: {selectedDM.san_pham_dau_ra ?? '—'}</span>
              </div>
            </section>
          )}

          {/* Form */}
          <section>
            <h3 className="text-sm font-medium text-gray-900 mb-2">2. Chi tiết</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Số lượng <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  min={1}
                  step={1}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  {...register('so_luong', { valueAsNumber: true })}
                />
                {errors.so_luong && (
                  <p className="mt-1 text-xs text-red-600">{errors.so_luong.message}</p>
                )}
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Ngày thực hiện
                </label>
                <input
                  type="date"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  {...register('ngay_thuc_hien')}
                />
              </div>
            </div>

            <div className="mt-3">
              <label className="block text-sm text-gray-700 mb-1">Mô tả</label>
              <textarea
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                placeholder="Mô tả chi tiết công việc (tùy chọn)"
                {...register('mo_ta_cong_viec')}
              />
            </div>

            <div className="mt-3 flex items-center gap-2">
              <input
                type="checkbox"
                id="is_doi_moi_sang_tao"
                className="h-4 w-4 rounded border-gray-300"
                {...register('is_doi_moi_sang_tao')}
              />
              <label htmlFor="is_doi_moi_sang_tao" className="text-sm text-gray-700">
                Có tính đổi mới, sáng tạo
              </label>
            </div>

            <div className="mt-3">
              <label className="block text-sm text-gray-700 mb-1">
                Người phê duyệt <span className="text-red-500">*</span>
              </label>
              <select
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                {...register('nguoi_phe_duyet_id')}
              >
                <option value="">— Chọn người phê duyệt —</option>
                {nguoiPheDuyetList.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.ho_ten} ({p.chuc_vu})
                  </option>
                ))}
              </select>
              {errors.nguoi_phe_duyet_id && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.nguoi_phe_duyet_id.message}
                </p>
              )}
            </div>
          </section>

          {/* Tự đánh giá lỗi (optional) */}
          <section>
            <h3 className="text-sm font-medium text-gray-900 mb-2">
              3. Tự đánh giá lỗi <span className="text-xs text-gray-500 font-normal">(tùy chọn — để trống nếu không có lỗi)</span>
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Số lỗi chất lượng
                </label>
                <input
                  type="number"
                  min={0}
                  step={1}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  {...register('tu_danh_gia_chat_luong', { valueAsNumber: true })}
                />
                {errors.tu_danh_gia_chat_luong && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.tu_danh_gia_chat_luong.message}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Số lỗi tiến độ
                </label>
                <input
                  type="number"
                  min={0}
                  step={1}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  {...register('tu_danh_gia_tien_do', { valueAsNumber: true })}
                />
                {errors.tu_danh_gia_tien_do && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.tu_danh_gia_tien_do.message}
                  </p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-3">
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Mô tả lỗi chất lượng
                </label>
                <textarea
                  rows={2}
                  maxLength={1000}
                  placeholder="Mô tả ngắn gọn lỗi chất lượng (nếu có)"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  {...register('ghi_chu_tu_dg_chat_luong')}
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Mô tả lỗi tiến độ
                </label>
                <textarea
                  rows={2}
                  maxLength={1000}
                  placeholder="Mô tả ngắn gọn lỗi tiến độ (nếu có)"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  {...register('ghi_chu_tu_dg_tien_do')}
                />
              </div>
            </div>

            <div className="mt-3">
              <label className="block text-sm text-gray-700 mb-1">
                Ghi chú chung (tùy chọn)
              </label>
              <textarea
                rows={2}
                maxLength={2000}
                placeholder="Giải trình chung nếu có nhiều lỗi"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                {...register('ghi_chu_tu_danh_gia')}
              />
            </div>
          </section>

          {/* Tự tính */}
          {selectedDM && (
            <section className="rounded-md bg-green-50 border border-green-200 px-4 py-3 space-y-1">
              <p className="text-sm text-green-900">
                <strong>Tổng SP quy đổi:</strong>{' '}
                {Number(watchedSoLuong) || 0} × {selectedDM.he_so_quy_doi.toFixed(2)} ={' '}
                <strong className="text-lg">{tongSpQuyDoi.toFixed(2)}</strong> SP1
              </p>
              <p className="text-xs text-green-800">
                <strong>SP đạt chất lượng:</strong>{' '}
                <span className="font-mono">{spDatCL.toFixed(2)}</span> SP1
                {' • '}
                <strong>SP đạt tiến độ:</strong>{' '}
                <span className="font-mono">{spDatTD.toFixed(2)}</span> SP1
              </p>
              <p className="text-[11px] text-green-700">
                Mỗi lỗi trừ 25% × hệ số. Cap tối đa 4 lỗi/đơn vị (= -100%).
              </p>
            </section>
          )}

          {/* Error */}
          {submitError && (
            <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 flex gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{submitError}</p>
            </div>
          )}
        </form>

        {/* Footer actions */}
        <div className="sticky bottom-0 bg-gray-50 px-6 py-3 border-t border-gray-200 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-60"
          >
            Hủy
          </button>
          <button
            type="button"
            onClick={handleSubmit((d) => submitWithSendApprove(d, false))}
            disabled={submitting}
            className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-300 rounded-md hover:bg-blue-100 disabled:opacity-60"
          >
            {isEdit ? 'Cập nhật (giữ nháp)' : 'Lưu nháp'}
          </button>
          <button
            type="button"
            onClick={handleSubmit((d) => submitWithSendApprove(d, true))}
            disabled={submitting}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-60"
          >
            {submitting
              ? 'Đang xử lý…'
              : isEdit
                ? 'Cập nhật & gửi duyệt'
                : 'Lưu & gửi duyệt'}
          </button>
        </div>
      </div>
    </div>
  );
}

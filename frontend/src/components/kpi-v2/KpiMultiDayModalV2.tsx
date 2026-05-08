'use client';

/**
 * components/kpi-v2/KpiMultiDayModalV2.tsx
 * ========================================
 * Modal kê khai V2 cho nhiều ngày — tạo N bản kê khai cùng công việc.
 *
 * Validation backend (PROMPT_02D Task D.5):
 * - Tất cả ngày phải cùng tháng/năm.
 * - Không trùng ngày.
 * - Không tương lai.
 * - Tối đa 31 ngày.
 */

import { useEffect, useMemo, useState } from 'react';
import { X, AlertCircle, CalendarPlus, Trash2 } from 'lucide-react';

import { isApiError } from '@/lib/axios';
import { kpiV2Service } from '@/services/kpi-v2.service';
import { kpiService } from '@/services/kpi.service';
import { IDanhMucPL3 } from '@/types/kpi-v2';
import { INguoiPheDuyet } from '@/services/kpi.service';

import { DanhMucPickerTabs } from './DanhMucPickerTabs';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  thang: number;
  nam: number;
}

const MAX_DAYS = 31;

export function KpiMultiDayModalV2({ open, onClose, onSuccess, thang, nam }: Props) {
  const [selectedDM, setSelectedDM] = useState<IDanhMucPL3 | null>(null);
  const [nguoiPheDuyetList, setNguoiPheDuyetList] = useState<INguoiPheDuyet[]>([]);
  const [pheDuyetId, setPheDuyetId] = useState('');
  const [soLuong, setSoLuong] = useState(1);
  const [moTa, setMoTa] = useState('');
  const [isDoiMoiSangTao, setIsDoiMoiSangTao] = useState(false);
  const [dayInput, setDayInput] = useState(''); // YYYY-MM-DD
  const [days, setDays] = useState<string[]>([]);
  const [loiCl, setLoiCl] = useState(0);
  const [loiTd, setLoiTd] = useState(0);
  const [moTaLoiCl, setMoTaLoiCl] = useState('');
  const [moTaLoiTd, setMoTaLoiTd] = useState('');
  const [ghiChuChung, setGhiChuChung] = useState('');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const tongSpQuyDoi = useMemo(() => {
    if (!selectedDM) return 0;
    return Number(soLuong || 0) * selectedDM.he_so_quy_doi;
  }, [selectedDM, soLuong]);

  const calcSpDat = (sl: number, heSo: number, loi: number): number => {
    if (sl <= 0 || heSo <= 0) return 0;
    const safeLoi = Math.max(0, loi);
    const maxLoi = sl * 4;
    const loiTinh = Math.min(safeLoi, maxLoi);
    return Math.max(0, heSo * (sl - 0.25 * loiTinh));
  };
  const spDatCL = useMemo(() => {
    if (!selectedDM) return 0;
    return calcSpDat(Number(soLuong) || 0, selectedDM.he_so_quy_doi, loiCl);
  }, [selectedDM, soLuong, loiCl]);
  const spDatTD = useMemo(() => {
    if (!selectedDM) return 0;
    return calcSpDat(Number(soLuong) || 0, selectedDM.he_so_quy_doi, loiTd);
  }, [selectedDM, soLuong, loiTd]);

  useEffect(() => {
    if (!open) return;
    kpiService
      .getNguoiPheDuyet()
      .then(setNguoiPheDuyetList)
      .catch((err) => console.error(err));
  }, [open]);

  useEffect(() => {
    if (!open) {
      setSelectedDM(null);
      setSoLuong(1);
      setMoTa('');
      setIsDoiMoiSangTao(false);
      setDayInput('');
      setDays([]);
      setPheDuyetId('');
      setLoiCl(0);
      setLoiTd(0);
      setMoTaLoiCl('');
      setMoTaLoiTd('');
      setGhiChuChung('');
      setSubmitError(null);
    }
  }, [open]);

  const addDay = () => {
    setSubmitError(null);
    if (!dayInput) return;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(dayInput)) {
      setSubmitError('Ngày sai định dạng');
      return;
    }
    const d = new Date(dayInput);
    if (isNaN(d.getTime())) {
      setSubmitError('Ngày không hợp lệ');
      return;
    }
    if (d > new Date()) {
      setSubmitError('Không cho phép ngày tương lai');
      return;
    }
    if (d.getMonth() + 1 !== thang || d.getFullYear() !== nam) {
      setSubmitError(`Ngày phải thuộc tháng ${thang}/${nam}`);
      return;
    }
    if (days.includes(dayInput)) {
      setSubmitError('Ngày đã có trong danh sách');
      return;
    }
    if (days.length >= MAX_DAYS) {
      setSubmitError(`Tối đa ${MAX_DAYS} ngày`);
      return;
    }
    setDays([...days, dayInput].sort());
    setDayInput('');
  };

  const removeDay = (d: string) => setDays(days.filter((x) => x !== d));

  const submit = async () => {
    setSubmitError(null);
    if (!selectedDM) {
      setSubmitError('Vui lòng chọn 1 mục công việc');
      return;
    }
    if (!pheDuyetId) {
      setSubmitError('Vui lòng chọn người phê duyệt');
      return;
    }
    if (days.length === 0) {
      setSubmitError('Vui lòng thêm ít nhất 1 ngày');
      return;
    }
    if (Number(soLuong) <= 0) {
      setSubmitError('Số lượng phải > 0');
      return;
    }

    setSubmitting(true);
    try {
      const res = await kpiV2Service.createMultiDay({
        danh_muc_sp_id: selectedDM.id,
        so_luong: Number(soLuong),
        ngay_thuc_hien_list: days,
        nguoi_phe_duyet_id: pheDuyetId,
        mo_ta_cong_viec: moTa || undefined,
        is_doi_moi_sang_tao: isDoiMoiSangTao,
        tu_danh_gia_chat_luong: loiCl,
        tu_danh_gia_tien_do: loiTd,
        ghi_chu_tu_dg_chat_luong: moTaLoiCl || undefined,
        ghi_chu_tu_dg_tien_do: moTaLoiTd || undefined,
        ghi_chu_tu_danh_gia: ghiChuChung || undefined,
      });
      console.log('Created multi-day V2:', res.total_created);
      onSuccess();
      onClose();
    } catch (err: unknown) {
      console.error(err);
      if (isApiError(err)) {
        if (err.code === 'MIXED_VERSION_NOT_ALLOWED') {
          setSubmitError(
            'Tháng này đã có kê khai V1. Liên hệ TCCB nếu muốn chuyển sang V2.'
          );
        } else {
          setSubmitError(err.message);
        }
      } else {
        setSubmitError('Lỗi không xác định');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Kê khai nhiều ngày — V2_PL3
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Tháng {thang}/{nam} • Tạo N bản kê khai cùng công việc
            </p>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-gray-100">
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <div className="px-6 py-4 space-y-5">
          {/* Picker tabs: ⭐ Yêu thích / 🕐 Tháng trước / 📋 Tất cả */}
          <section>
            <h3 className="text-sm font-medium text-gray-900 mb-2">
              1. Chọn công việc
            </h3>
            <DanhMucPickerTabs
              thang={thang}
              nam={nam}
              selectedId={selectedDM?.id}
              onSelect={setSelectedDM}
            />
          </section>

          {selectedDM && (
            <section className="rounded-md bg-blue-50 border border-blue-200 px-4 py-3">
              <p className="text-sm font-semibold text-gray-900">
                {selectedDM.ten_cong_viec}
              </p>
              {selectedDM.cong_tac && (
                <p className="text-xs text-gray-700 whitespace-pre-line mt-1">
                  <span className="text-gray-500">Công tác:</span> {selectedDM.cong_tac}
                </p>
              )}
              {selectedDM.nhiem_vu && (
                <p className="text-xs text-gray-700 whitespace-pre-line mt-1">
                  <span className="text-gray-500">Nhiệm vụ:</span> {selectedDM.nhiem_vu}
                </p>
              )}
              <div className="text-xs text-gray-700 space-x-4 mt-1">
                <span>Lĩnh vực: {selectedDM.linh_vuc}</span>
                <span>Nhóm: {selectedDM.nhom_pl3}</span>
                <span>Hệ số: <strong>{selectedDM.he_so_quy_doi.toFixed(6).replace(/\.?0+$/, '')}</strong></span>
              </div>
            </section>
          )}

          {/* Form chi tiết */}
          <section>
            <h3 className="text-sm font-medium text-gray-900 mb-2">2. Chi tiết</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Số lượng / ngày
                </label>
                <input
                  type="number"
                  min={1}
                  value={soLuong}
                  onChange={(e) => setSoLuong(Number(e.target.value))}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Người phê duyệt
                </label>
                <select
                  value={pheDuyetId}
                  onChange={(e) => setPheDuyetId(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="">— Chọn —</option>
                  {nguoiPheDuyetList.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.ho_ten} ({p.chuc_vu})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-3">
              <label className="block text-sm text-gray-700 mb-1">Mô tả</label>
              <textarea
                rows={2}
                value={moTa}
                onChange={(e) => setMoTa(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>

            <div className="mt-3 flex items-center gap-2">
              <input
                type="checkbox"
                id="md_doimoi"
                checked={isDoiMoiSangTao}
                onChange={(e) => setIsDoiMoiSangTao(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300"
              />
              <label htmlFor="md_doimoi" className="text-sm text-gray-700">
                Đổi mới sáng tạo
              </label>
            </div>
          </section>

          {/* Days */}
          <section>
            <h3 className="text-sm font-medium text-gray-900 mb-2">
              3. Danh sách ngày ({days.length}/{MAX_DAYS})
            </h3>
            <div className="flex gap-2">
              <input
                type="date"
                value={dayInput}
                onChange={(e) => setDayInput(e.target.value)}
                className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
              <button
                type="button"
                onClick={addDay}
                className="inline-flex items-center gap-1 px-3 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                <CalendarPlus className="h-4 w-4" /> Thêm ngày
              </button>
            </div>

            {days.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {days.map((d) => (
                  <span
                    key={d}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-100 text-xs"
                  >
                    {d}
                    <button
                      type="button"
                      onClick={() => removeDay(d)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </section>

          {/* Tự đánh giá lỗi (optional, áp dụng cho mỗi bản) */}
          <section>
            <h3 className="text-sm font-medium text-gray-900 mb-2">
              4. Tự đánh giá lỗi mỗi bản{' '}
              <span className="text-xs text-gray-500 font-normal">
                (tùy chọn — áp dụng giống nhau cho tất cả {days.length || 'N'} bản)
              </span>
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Số lỗi chất lượng / bản
                </label>
                <input
                  type="number"
                  min={0}
                  step={1}
                  value={loiCl}
                  onChange={(e) => setLoiCl(Math.max(0, Number(e.target.value) || 0))}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Số lỗi tiến độ / bản
                </label>
                <input
                  type="number"
                  min={0}
                  step={1}
                  value={loiTd}
                  onChange={(e) => setLoiTd(Math.max(0, Number(e.target.value) || 0))}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
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
                  value={moTaLoiCl}
                  onChange={(e) => setMoTaLoiCl(e.target.value)}
                  placeholder="Mô tả lỗi chất lượng (nếu có)"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Mô tả lỗi tiến độ
                </label>
                <textarea
                  rows={2}
                  maxLength={1000}
                  value={moTaLoiTd}
                  onChange={(e) => setMoTaLoiTd(e.target.value)}
                  placeholder="Mô tả lỗi tiến độ (nếu có)"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div className="mt-3">
              <label className="block text-sm text-gray-700 mb-1">
                Ghi chú chung
              </label>
              <textarea
                rows={2}
                maxLength={2000}
                value={ghiChuChung}
                onChange={(e) => setGhiChuChung(e.target.value)}
                placeholder="Giải trình chung (tùy chọn)"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
          </section>

          {/* Tự tính */}
          {selectedDM && days.length > 0 && (
            <section className="rounded-md bg-green-50 border border-green-200 px-4 py-3 text-sm space-y-1">
              <p className="text-green-900">
                Sẽ tạo <strong>{days.length}</strong> bản kê khai. Mỗi bản:{' '}
                <strong>{Number(soLuong) || 0}</strong> ×{' '}
                <strong>{selectedDM.he_so_quy_doi.toFixed(6).replace(/\.?0+$/, '')}</strong> ={' '}
                <strong>{tongSpQuyDoi.toFixed(6).replace(/\.?0+$/, '')}</strong> điểm.
              </p>
              <p className="text-xs text-green-800">
                <strong>Điểm đạt CL/bản:</strong>{' '}
                <span className="font-mono">{spDatCL.toFixed(6).replace(/\.?0+$/, '')}</span> điểm
                {' • '}
                <strong>Điểm đạt TĐ/bản:</strong>{' '}
                <span className="font-mono">{spDatTD.toFixed(6).replace(/\.?0+$/, '')}</span> điểm
              </p>
              <p className="text-green-900 mt-1">
                Tổng điểm toàn batch:{' '}
                <strong className="text-base">
                  {(tongSpQuyDoi * days.length).toFixed(6).replace(/\.?0+$/, '')}
                </strong>{' '}
                điểm • CL: {(spDatCL * days.length).toFixed(6).replace(/\.?0+$/, '')} • TĐ:{' '}
                {(spDatTD * days.length).toFixed(6).replace(/\.?0+$/, '')}
              </p>
            </section>
          )}

          {submitError && (
            <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 flex gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{submitError}</p>
            </div>
          )}
        </div>

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
            onClick={submit}
            disabled={submitting}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-60"
          >
            {submitting ? 'Đang xử lý…' : `Tạo ${days.length} kê khai`}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * SuaCuocHopModal — modal sửa thông tin cuộc họp (meta).
 *
 * Cho phép chu_toa / thu_ky / admin / TRUONG_CNTT / CHANH_VP sửa:
 * tieu_de, mo_ta, khoi, hinh_thuc, ngay_hop, gio_bat_dau, gio_ket_thuc,
 * dia_diem, thu_ky_id.
 *
 * KHÔNG đổi don_vi_to_chuc_id và chu_toa_id (BE schema CuocHopUpdate không
 * nhận hai field này — đổi đơn vị tổ chức / chủ tọa cần tạo mới).
 *
 * Sửa thành phần dùng SuaThanhPhanModal riêng (đã có) — modal này chỉ lo meta.
 */

'use client';

import { useEffect, useState } from 'react';
import { Loader2, Save, X } from 'lucide-react';
import { congChucApi, cuocHopApi, type ICongChucSearchItem } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { HinhThuc, ICuocHop, ICuocHopUpdate, Khoi } from '@/types/hkg';
import CongChucPicker from './CongChucPicker';

interface IPickerResult {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  don_vi_id: string | null;
  don_vi_ten: string | null;
}

function toPickerResult(it: ICongChucSearchItem): IPickerResult {
  return {
    id: it.id,
    ma_cc: it.ma_cc,
    ho_ten: it.ho_ten,
    chuc_vu: it.chuc_vu,
    don_vi_id: it.don_vi_id,
    don_vi_ten: it.ten_don_vi,
  };
}

interface IProps {
  cuocHopId: string;
  onClose: () => void;
  onSaved: () => void;
}

interface IFormState {
  tieu_de: string;
  mo_ta: string;
  khoi: Khoi;
  hinh_thuc: HinhThuc;
  ngay_hop: string;
  gio_bat_dau: string;
  gio_ket_thuc: string;
  dia_diem: string;
  thu_ky_id: string;
}

const KHOI_OPTIONS: { value: Khoi; label: string }[] = [
  { value: 'CHUYEN_MON', label: 'Chuyên môn' },
  { value: 'DANG', label: 'Đảng' },
  { value: 'HANH_CHINH', label: 'Hành chính' },
  { value: 'BAN_NHOM', label: 'Ban / Nhóm' },
];

const HINH_THUC_OPTIONS: { value: HinhThuc; label: string }[] = [
  { value: 'TRUC_TIEP', label: 'Trực tiếp' },
  { value: 'TRUC_TUYEN', label: 'Trực tuyến' },
  { value: 'HYBRID', label: 'Hybrid' },
];

function timeForInput(t: string | null | undefined): string {
  if (!t) return '';
  // BE trả "HH:MM:SS"; <input type="time"> chỉ cần "HH:MM"
  return t.length >= 5 ? t.slice(0, 5) : t;
}

export default function SuaCuocHopModal({ cuocHopId, onClose, onSaved }: IProps) {
  const [original, setOriginal] = useState<ICuocHop | null>(null);
  const [form, setForm] = useState<IFormState | null>(null);
  const [thuKySeed, setThuKySeed] = useState<IPickerResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const ch = await cuocHopApi.chiTiet(cuocHopId);
        if (cancelled) return;
        setOriginal(ch);
        setForm({
          tieu_de: ch.tieu_de,
          mo_ta: ch.mo_ta || '',
          khoi: ch.khoi,
          hinh_thuc: ch.hinh_thuc,
          ngay_hop: ch.ngay_hop,
          gio_bat_dau: timeForInput(ch.gio_bat_dau),
          gio_ket_thuc: timeForInput(ch.gio_ket_thuc),
          dia_diem: ch.dia_diem || '',
          thu_ky_id: ch.thu_ky_id || '',
        });

        // Hydrate thư ký để picker hiển thị "Họ tên (mã) — Đơn vị" thay vì UUID
        if (ch.thu_ky_id) {
          try {
            const tk = await congChucApi.getById(ch.thu_ky_id);
            if (!cancelled) setThuKySeed([toPickerResult(tk)]);
          } catch {
            // Không hydrate được vẫn cho phép sửa các field khác
          }
        }
      } catch (e: unknown) {
        if (!cancelled) setError(errMsg(e, 'Lỗi tải cuộc họp'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [cuocHopId]);

  const update = <K extends keyof IFormState>(key: K, value: IFormState[K]) => {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const handleSave = async () => {
    if (!form || !original) return;
    if (!form.tieu_de.trim()) {
      setError('Tiêu đề không được để trống');
      return;
    }
    if (!form.ngay_hop) {
      setError('Phải chọn ngày họp');
      return;
    }
    if (!form.gio_bat_dau) {
      setError('Phải nhập giờ bắt đầu');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      // Chỉ gửi field thực sự thay đổi (BE PATCH dùng exclude_unset)
      const payload: ICuocHopUpdate = {};
      if (form.tieu_de.trim() !== original.tieu_de) payload.tieu_de = form.tieu_de.trim();
      const moTaNew = form.mo_ta.trim() || null;
      if (moTaNew !== (original.mo_ta || null)) payload.mo_ta = moTaNew;
      if (form.khoi !== original.khoi) payload.khoi = form.khoi;
      if (form.hinh_thuc !== original.hinh_thuc) payload.hinh_thuc = form.hinh_thuc;
      if (form.ngay_hop !== original.ngay_hop) payload.ngay_hop = form.ngay_hop;
      if (form.gio_bat_dau !== timeForInput(original.gio_bat_dau)) {
        payload.gio_bat_dau = form.gio_bat_dau;
      }
      const gioKetThucNew = form.gio_ket_thuc || null;
      if (gioKetThucNew !== timeForInput(original.gio_ket_thuc) && (gioKetThucNew || original.gio_ket_thuc)) {
        payload.gio_ket_thuc = gioKetThucNew;
      }
      const diaDiemNew = form.dia_diem.trim() || null;
      if (diaDiemNew !== (original.dia_diem || null)) payload.dia_diem = diaDiemNew;
      const thuKyNew = form.thu_ky_id || null;
      if (thuKyNew !== (original.thu_ky_id || null)) payload.thu_ky_id = thuKyNew;

      if (Object.keys(payload).length === 0) {
        onClose();
        return;
      }

      await cuocHopApi.capNhat(cuocHopId, payload);
      onSaved();
      onClose();
    } catch (e: unknown) {
      setError(errMsg(e, 'Lỗi lưu cuộc họp'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="text-lg font-semibold">Sửa cuộc họp</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded" aria-label="Đóng">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading && (
            <div className="flex items-center gap-2 text-gray-500">
              <Loader2 className="w-4 h-4 animate-spin" /> Đang tải...
            </div>
          )}

          {!loading && form && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">Tiêu đề *</label>
                <input
                  value={form.tieu_de}
                  onChange={(e) => update('tieu_de', e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Mô tả</label>
                <textarea
                  value={form.mo_ta}
                  onChange={(e) => update('mo_ta', e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Khối *</label>
                  <select
                    value={form.khoi}
                    onChange={(e) => update('khoi', e.target.value as Khoi)}
                    className="w-full px-3 py-2 border rounded"
                  >
                    {KHOI_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Hình thức *</label>
                  <select
                    value={form.hinh_thuc}
                    onChange={(e) => update('hinh_thuc', e.target.value as HinhThuc)}
                    className="w-full px-3 py-2 border rounded"
                  >
                    {HINH_THUC_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Ngày họp *</label>
                  <input
                    type="date"
                    value={form.ngay_hop}
                    onChange={(e) => update('ngay_hop', e.target.value)}
                    className="w-full px-3 py-2 border rounded"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Giờ bắt đầu *</label>
                  <input
                    type="time"
                    value={form.gio_bat_dau}
                    onChange={(e) => update('gio_bat_dau', e.target.value)}
                    className="w-full px-3 py-2 border rounded"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Giờ kết thúc</label>
                  <input
                    type="time"
                    value={form.gio_ket_thuc}
                    onChange={(e) => update('gio_ket_thuc', e.target.value)}
                    className="w-full px-3 py-2 border rounded"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Địa điểm</label>
                <input
                  value={form.dia_diem}
                  onChange={(e) => update('dia_diem', e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Thư ký</label>
                <CongChucPicker
                  multiple={false}
                  value={form.thu_ky_id || null}
                  onChange={(id) => update('thu_ky_id', id || '')}
                  placeholder="Tìm thư ký..."
                  donViId={null}
                  initialItems={thuKySeed}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Bỏ trống nếu cuộc họp không có thư ký riêng.
                </p>
              </div>

              <div className="text-xs text-gray-500 bg-gray-50 border rounded p-2">
                Lưu ý: <strong>đơn vị tổ chức</strong> và <strong>chủ tọa</strong> không
                đổi được tại đây. Sửa thành phần tham dự dùng nút &quot;Sửa thành phần&quot;
                trong trang chi tiết.
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
                  {error}
                </div>
              )}
            </>
          )}

          {!loading && !form && error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
              {error}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 p-4 border-t">
          <button
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 border rounded text-sm"
          >
            Hủy
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading || !form}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Lưu thay đổi
          </button>
        </div>
      </div>
    </div>
  );
}

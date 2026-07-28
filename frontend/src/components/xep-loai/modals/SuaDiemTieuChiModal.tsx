'use client';

// =============================================================================
// MODAL SỬA ĐIỂM TIÊU CHÍ CHUNG (ĐÁNH GIÁ THÁNG)
// -----------------------------------------------------------------------------
// Cho CCT/LĐ điều chỉnh điểm tiêu chí chung per-tiêu-chí, lưu vào
// diem_danh_gia_thang (giữ nguyên điểm Trưởng duyệt để audit).
// Dùng chung cho tab Báo cáo (xep-loai) và trang /dieu-chinh-tieu-chi.
// =============================================================================

import { useState, useEffect } from 'react';
import { baoCaoXepLoaiService } from '@/services/bao-cao-xep-loai.service';
import type { ITieuChiChungItemDgt } from '@/types/bao-cao-xep-loai';
import { formatScore } from '@/lib/format';

/** Thông tin công chức tối thiểu modal cần (IChiTietXepLoai thỏa mãn shape này). */
export interface ISuaDiemCongChuc {
  cong_chuc_id?: string;
  cong_chuc?: { id?: string; ho_ten?: string; ma_cc?: string } | null;
}

interface SuaDiemTieuChiModalProps {
  congChuc: ISuaDiemCongChuc;
  thang: number;
  nam: number;
  /** Chỉ đọc (báo cáo đã chốt) → ẩn nút Lưu, input disabled. */
  readOnly?: boolean;
  onClose: () => void;
  onSaved: () => void | Promise<void>;
}

export default function SuaDiemTieuChiModal({
  congChuc,
  thang,
  nam,
  readOnly = false,
  onClose,
  onSaved,
}: SuaDiemTieuChiModalProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [danhGiaThangId, setDanhGiaThangId] = useState<string | null>(null);
  const [tieuChi, setTieuChi] = useState<ITieuChiChungItemDgt[]>([]);
  // Giá trị đang nhập cho cột "Đánh giá tháng" (chuỗi để cho phép trống = gỡ điều chỉnh)
  const [diemDgt, setDiemDgt] = useState<Record<string, string>>({});

  // Điểm "Trưởng duyệt" mặc định cho 1 tiêu chí
  const truongDuyet = (tc: ITieuChiChungItemDgt): number =>
    (tc.diem_phe_duyet ?? tc.diem_tu_cham ?? 0);

  const ccId = congChuc.cong_chuc_id || congChuc.cong_chuc?.id || '';

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      const res = ccId ? await baoCaoXepLoaiService.getTieuChiChung(ccId, thang, nam) : null;
      if (!active) return;
      const list = res?.tieu_chi || [];
      setDanhGiaThangId(res?.danh_gia_thang_id || null);
      setTieuChi(list);
      const init: Record<string, string> = {};
      list.forEach((tc) => {
        const v = tc.diem_danh_gia_thang ?? tc.diem_phe_duyet ?? tc.diem_tu_cham ?? 0;
        init[tc.ma_tieu_chi] = String(v);
      });
      setDiemDgt(init);
      setLoading(false);
    })();
    return () => { active = false; };
  }, [ccId, thang, nam]);

  const tongDgt = tieuChi.reduce((s, tc) => {
    const raw = diemDgt[tc.ma_tieu_chi];
    const v = raw === undefined || raw.trim() === '' ? truongDuyet(tc) : Number(raw);
    return s + (Number.isNaN(v) ? 0 : v);
  }, 0);

  const handleSave = async () => {
    if (!danhGiaThangId) {
      alert('Công chức chưa có dữ liệu đánh giá tháng để điều chỉnh.');
      return;
    }
    // Validate từng dòng
    for (const tc of tieuChi) {
      const raw = diemDgt[tc.ma_tieu_chi];
      if (raw === undefined || raw.trim() === '') continue; // để trống = giữ mặc định
      const v = Number(raw);
      if (Number.isNaN(v) || v < 0 || v > tc.diem_toi_da) {
        alert(`Tiêu chí ${tc.ma_tieu_chi}: điểm phải trong khoảng 0 - ${tc.diem_toi_da}`);
        return;
      }
      if (Math.abs(v * 2 - Math.round(v * 2)) > 1e-6) {
        alert(`Tiêu chí ${tc.ma_tieu_chi}: điểm phải là bội số 0.5`);
        return;
      }
    }
    // Chỉ gửi dòng khác giá trị Trưởng duyệt; dòng = Trưởng duyệt → gửi null (gỡ điều chỉnh)
    const payload = tieuChi.map((tc) => {
      const raw = diemDgt[tc.ma_tieu_chi];
      const v = raw === undefined || raw.trim() === '' ? truongDuyet(tc) : Number(raw);
      const diff = Math.abs(v - truongDuyet(tc)) > 1e-6;
      return { ma_tieu_chi: tc.ma_tieu_chi, diem_danh_gia_thang: diff ? v : null };
    });
    setSaving(true);
    try {
      await baoCaoXepLoaiService.dieuChinhDanhGiaThang(danhGiaThangId, payload);
      await onSaved();
    } catch (err) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      alert(e.response?.data?.error?.message || e.message || 'Có lỗi xảy ra');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            {readOnly ? 'Xem điểm tiêu chí chung' : 'Sửa điểm tiêu chí chung'}
          </h3>
          <p className="text-sm text-gray-600 mt-0.5">
            {congChuc.cong_chuc?.ho_ten} ({congChuc.cong_chuc?.ma_cc}) — Tháng {thang}/{nam}
          </p>
        </div>

        <div className="flex-1 overflow-auto px-6 py-4">
          {loading ? (
            <div className="py-10 text-center text-gray-500">Đang tải...</div>
          ) : tieuChi.length === 0 ? (
            <div className="py-10 text-center text-gray-500">Công chức chưa có dữ liệu tiêu chí tháng này.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-700">
                  <th className="px-2 py-2 text-left font-semibold w-14">Mã</th>
                  <th className="px-2 py-2 text-left font-semibold">Tiêu chí</th>
                  <th className="px-2 py-2 text-center font-semibold w-16">Tối đa</th>
                  <th className="px-2 py-2 text-center font-semibold w-20">CC tự chấm</th>
                  <th className="px-2 py-2 text-center font-semibold w-20">Trưởng duyệt</th>
                  <th className="px-2 py-2 text-center font-semibold w-24">Đánh giá tháng</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {tieuChi.map((tc) => {
                  const td = truongDuyet(tc);
                  const raw = diemDgt[tc.ma_tieu_chi] ?? '';
                  const changed = raw.trim() !== '' && Math.abs(Number(raw) - td) > 1e-6;
                  return (
                    <tr key={tc.ma_tieu_chi} className={changed ? 'bg-amber-50' : ''}>
                      <td className="px-2 py-1.5 font-medium text-gray-700">{tc.ma_tieu_chi}</td>
                      <td className="px-2 py-1.5 text-gray-700">{tc.ten_tieu_chi}</td>
                      <td className="px-2 py-1.5 text-center text-gray-500">{tc.diem_toi_da}</td>
                      <td className="px-2 py-1.5 text-center text-gray-600">{tc.diem_tu_cham ?? '-'}</td>
                      <td className="px-2 py-1.5 text-center text-blue-700 font-medium">{formatScore(td)}</td>
                      <td className="px-2 py-1.5 text-center">
                        <input
                          type="number"
                          min={0}
                          max={tc.diem_toi_da}
                          step={0.5}
                          value={raw}
                          disabled={readOnly}
                          onChange={(e) => setDiemDgt((p) => ({ ...p, [tc.ma_tieu_chi]: e.target.value }))}
                          className="w-20 px-2 py-1 text-center border border-gray-300 rounded focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 disabled:bg-gray-100 disabled:text-gray-500"
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-gray-300 font-semibold text-gray-900">
                  <td className="px-2 py-2" colSpan={5}>Tổng điểm tiêu chí chung (0–30)</td>
                  <td className="px-2 py-2 text-center text-emerald-700">{formatScore(tongDgt)}</td>
                </tr>
              </tfoot>
            </table>
          )}
          {!loading && tieuChi.length > 0 && !readOnly && (
            <p className="mt-3 text-xs text-gray-500">
              Cột &quot;Đánh giá tháng&quot; mặc định bằng điểm Trưởng duyệt. Sửa rồi Lưu → điểm tổng và xếp loại trong báo cáo tự cập nhật.
              Điểm Trưởng duyệt gốc được giữ nguyên.
            </p>
          )}
          {!loading && readOnly && (
            <p className="mt-3 text-xs text-amber-600">
              Báo cáo xếp loại của đơn vị này đã chốt — chỉ xem, không sửa được điểm.
            </p>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium">
            {readOnly ? 'Đóng' : 'Hủy'}
          </button>
          {!readOnly && (
            <button
              onClick={handleSave}
              disabled={saving || loading || tieuChi.length === 0}
              className="px-4 py-2 text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg font-medium disabled:opacity-50"
            >
              {saving ? 'Đang lưu...' : 'Lưu'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

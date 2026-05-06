/**
 * src/components/danh-gia-v2/DieuChinhKqcvModal.tsx
 * =================================================
 * Modal LĐ tạo bản đề xuất điều chỉnh CV của cấp dưới.
 * Sau khi tạo + gửi duyệt, gọi onSuccess để parent reload.
 */

'use client';

import { useState } from 'react';
import { dieuChinhKqcvService } from '@/services/dieuChinhKqcv.service';
import { ICongViecLanhDaoV2 } from '@/types/kpiLanhDaoV2';

interface Props {
  open: boolean;
  cv: ICongViecLanhDaoV2 | null;
  onClose: () => void;
  onSuccess: () => void;
}

function getApiErrorMessage(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: { detail?: { error?: { message?: string } } } } };
  return e?.response?.data?.detail?.error?.message ?? fallback;
}

export default function DieuChinhKqcvModal({ open, cv, onClose, onSuccess }: Props) {
  const [loiCl, setLoiCl] = useState(0);
  const [loiTd, setLoiTd] = useState(0);
  const [chuaHt, setChuaHt] = useState(false);
  const [lyDo, setLyDo] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync form state khi cv thay đổi
  if (cv && !submitting) {
    // (chỉ sync khi mở modal — dùng local state init từ cv)
  }

  // Reset state khi mở modal mới
  const wasOpen = (DieuChinhKqcvModal as unknown as { _wasOpen?: boolean })._wasOpen ?? false;
  if (open && !wasOpen && cv) {
    setLoiCl(cv.so_loi_chat_luong);
    setLoiTd(cv.so_loi_tien_do);
    setChuaHt(cv.is_chua_hoan_thanh ?? false);
    setLyDo('');
    setError(null);
  }
  (DieuChinhKqcvModal as unknown as { _wasOpen?: boolean })._wasOpen = open;

  if (!open || !cv) return null;

  const handleSubmit = async (autoSend: boolean) => {
    if (lyDo.trim().length < 5) {
      setError('Lý do phải tối thiểu 5 ký tự');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const dc = await dieuChinhKqcvService.create({
        ke_khai_id: cv.ke_khai_id,
        gia_tri_moi: {
          so_loi_chat_luong: loiCl,
          so_loi_tien_do: loiTd,
          is_chua_hoan_thanh: chuaHt,
        },
        ly_do: lyDo.trim(),
      });
      if (autoSend) {
        await dieuChinhKqcvService.guiDuyet(dc.id);
      }
      onSuccess();
      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Tạo điều chỉnh thất bại'));
    } finally {
      setSubmitting(false);
    }
  };

  const isChanged =
    loiCl !== cv.so_loi_chat_luong ||
    loiTd !== cv.so_loi_tien_do ||
    chuaHt !== (cv.is_chua_hoan_thanh ?? false);

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-xl max-h-[90vh] flex flex-col">
        <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
          <h3 className="font-semibold text-lg">Điều chỉnh KQCV của cấp dưới</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" disabled={submitting}>
            ✕
          </button>
        </div>

        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          {/* Thông tin CV */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm">
            <div className="text-xs text-gray-500 uppercase mb-1">Công việc</div>
            <div className="font-medium text-gray-900">{cv.ten_cong_viec || cv.ma_danh_muc}</div>
            <div className="text-xs text-gray-600 mt-1">
              Người kê: <b>{cv.ho_ten}</b> ({cv.ma_cc}) · Ngày: {cv.ngay_thuc_hien?.split('-').reverse().join('/')} ·
              SL: <b>{cv.so_luong}</b> · SP gốc: <b>{cv.so_sp_goc_quy_doi.toFixed(2)}</b>
            </div>
          </div>

          {/* So sánh trước/sau */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Số lỗi chất lượng
              </label>
              <input
                type="number"
                min={0}
                value={loiCl}
                onChange={(e) => setLoiCl(Math.max(0, parseInt(e.target.value || '0', 10)))}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                disabled={chuaHt}
              />
              <p className="text-[11px] text-gray-500 mt-0.5">CC tự đánh giá: {cv.tu_danh_gia_chat_luong} · Hiện tại: {cv.so_loi_chat_luong}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Số lỗi tiến độ
              </label>
              <input
                type="number"
                min={0}
                value={loiTd}
                onChange={(e) => setLoiTd(Math.max(0, parseInt(e.target.value || '0', 10)))}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                disabled={chuaHt}
              />
              <p className="text-[11px] text-gray-500 mt-0.5">CC tự đánh giá: {cv.tu_danh_gia_tien_do} · Hiện tại: {cv.so_loi_tien_do}</p>
            </div>
          </div>

          {/* Cờ chưa hoàn thành */}
          <label className="flex items-start gap-3 p-3 rounded-lg border border-amber-200 bg-amber-50 cursor-pointer">
            <input
              type="checkbox"
              checked={chuaHt}
              onChange={(e) => setChuaHt(e.target.checked)}
              className="mt-0.5 w-4 h-4"
            />
            <div className="flex-1">
              <div className="text-sm font-medium text-amber-900">Đánh dấu CV CHƯA HOÀN THÀNH</div>
              <p className="text-xs text-amber-700 mt-0.5">
                Khi tích, CV này VẪN tính vào mẫu số (tổng SP kê khai), nhưng đóng <b>0</b> vào
                tử số <b>a / b / c</b> → cả 3 chỉ số đều giảm. Dùng khi CC kê nhưng thực tế chưa làm xong.
              </p>
            </div>
          </label>

          {/* Lý do */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Lý do điều chỉnh <span className="text-red-500">*</span>
            </label>
            <textarea
              value={lyDo}
              onChange={(e) => setLyDo(e.target.value)}
              rows={3}
              placeholder="Ví dụ: CC tự đánh giá quá tích cực, kiểm tra thực tế phát hiện 2 lỗi CL..."
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              maxLength={2000}
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        <div className="px-5 py-3 border-t border-gray-200 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Sau khi gửi duyệt, cấp trên của bạn sẽ phê duyệt rồi mới áp dụng.
          </span>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
              disabled={submitting}
            >
              Hủy
            </button>
            <button
              onClick={() => handleSubmit(true)}
              disabled={submitting || !isChanged || lyDo.trim().length < 5}
              className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50"
            >
              {submitting ? 'Đang gửi...' : 'Gửi duyệt'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * src/components/lms/LichSuResetModal.tsx
 * ========================================
 * Nhật ký reset lượt thi của 1 kỳ thi — ai reset, cho ai, vì sao, xóa mất gì.
 *
 * Reset là thao tác xóa dữ liệu thật; màn hình này là chỗ đối chiếu về sau khi
 * có thắc mắc "vì sao điểm của đồng chí X biến mất".
 */

'use client';

import { useEffect, useState } from 'react';
import { kyThiApi } from '@/services/lms';
import type { ILichSuReset } from '@/types/lms';

function fmtGio(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString('vi-VN', { hour12: false });
}

export default function LichSuResetModal({
  kyThiId,
  onClose,
}: {
  kyThiId: string;
  onClose: () => void;
}) {
  const [items, setItems] = useState<ILichSuReset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await kyThiApi.lichSuReset(kyThiId);
        setItems(res.data?.data || []);
      } catch {
        setError('Lỗi tải nhật ký reset');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [kyThiId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-xl p-6 w-full max-w-4xl max-h-[85vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">📓 Nhật ký reset lượt thi</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        {loading ? (
          <div className="py-8 text-center text-gray-400 text-sm">Đang tải...</div>
        ) : error ? (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        ) : items.length === 0 ? (
          <div className="py-8 text-center text-gray-400 text-sm">
            Kỳ thi này chưa có lượt thi nào bị reset.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs text-gray-500">
                  <th className="py-2 pr-3">Thời gian</th>
                  <th className="py-2 pr-3">Thí sinh</th>
                  <th className="py-2 pr-3">Mức reset</th>
                  <th className="py-2 pr-3">Trước khi reset</th>
                  <th className="py-2 pr-3">Người thực hiện</th>
                  <th className="py-2">Lý do</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr key={r.id} className="border-b align-top">
                    <td className="py-2 pr-3 whitespace-nowrap text-xs text-gray-600">{fmtGio(r.thoi_gian)}</td>
                    <td className="py-2 pr-3">
                      <div className="font-medium">{r.ho_ten || '—'}</div>
                      <div className="font-mono text-xs text-gray-500">{r.ma_cc}</div>
                    </td>
                    <td className="py-2 pr-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs whitespace-nowrap ${
                          r.loai_reset === 'XOA_SACH'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {r.loai_reset === 'XOA_SACH' ? 'Xóa sạch' : 'Mở khóa lượt'}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-xs text-gray-600 whitespace-nowrap">
                      {r.trang_thai_truoc || '—'}
                      {r.lan_thi_truoc ? ` · lượt ${r.lan_thi_truoc}` : ''}
                      {r.diem_truoc !== null && r.diem_truoc !== undefined ? ` · ${r.diem_truoc}%` : ''}
                    </td>
                    <td className="py-2 pr-3">
                      <div>{r.nguoi_reset_ten || '—'}</div>
                      <div className="font-mono text-xs text-gray-500">{r.nguoi_reset_ma_cc}</div>
                    </td>
                    <td className="py-2 text-gray-700">{r.ly_do}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

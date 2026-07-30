/**
 * src/components/lms/ViPhamDetailModal.tsx
 * ========================================
 * Modal xem chi tiết các lần vi phạm của 1 thí sinh trong kỳ thi:
 * lần thi, loại vi phạm, thời gian (giờ VN), lý do giải trình.
 * Dùng chung cho trang Thống kê + Giám sát trực tiếp. Chỉ admin gọi được API.
 */

'use client';

import { useEffect, useState } from 'react';
import { kyThiApi } from '@/services/lms';

interface ViPham {
  id: string;
  lan_thi: number;
  loai_vi_pham: string;
  thoi_gian: string | null;
  ly_do: string | null;
}

const LOAI_LABEL: Record<string, string> = {
  EXIT_FULLSCREEN: 'Thoát toàn màn hình',
  SWITCH_TAB: 'Chuyển tab/cửa sổ',
};

export default function ViPhamDetailModal({
  kyThiId,
  congChucId,
  hoTen,
  onClose,
}: {
  kyThiId: string;
  congChucId: string;
  hoTen?: string;
  onClose: () => void;
}) {
  const [items, setItems] = useState<ViPham[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await kyThiApi.danhSachViPham(kyThiId, congChucId);
        setItems(res.data?.data || []);
      } catch {
        setError('Lỗi tải chi tiết vi phạm');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [kyThiId, congChucId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">
            ⚠️ Chi tiết vi phạm{hoTen ? ` — ${hoTen}` : ''}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        {loading ? (
          <div className="py-8 text-center text-gray-400 text-sm">Đang tải...</div>
        ) : error ? (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        ) : items.length === 0 ? (
          <div className="py-8 text-center text-gray-400 text-sm">
            Không có log vi phạm chi tiết (dữ liệu cũ chỉ có tổng số lần).
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs text-gray-500">
                <th className="py-2 pr-3">#</th>
                <th className="py-2 pr-3">Lần thi</th>
                <th className="py-2 pr-3">Loại</th>
                <th className="py-2 pr-3">Thời gian</th>
                <th className="py-2">Lý do giải trình</th>
              </tr>
            </thead>
            <tbody>
              {items.map((vp, idx) => (
                <tr key={vp.id} className="border-b last:border-0 align-top">
                  <td className="py-2 pr-3 text-gray-400">{idx + 1}</td>
                  <td className="py-2 pr-3 text-center">{vp.lan_thi}</td>
                  <td className="py-2 pr-3">
                    <span className="px-2 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded-full text-xs">
                      {LOAI_LABEL[vp.loai_vi_pham] || vp.loai_vi_pham}
                    </span>
                  </td>
                  <td className="py-2 pr-3 whitespace-nowrap font-mono text-xs">
                    {vp.thoi_gian ? new Date(vp.thoi_gian).toLocaleString('vi-VN') : '—'}
                  </td>
                  <td className="py-2 text-gray-700">
                    {vp.ly_do || <em className="text-gray-400">Không giải trình</em>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="mt-4 text-right">
          <button onClick={onClose} className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}

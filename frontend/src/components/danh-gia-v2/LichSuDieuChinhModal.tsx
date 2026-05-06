/**
 * src/components/danh-gia-v2/LichSuDieuChinhModal.tsx
 * ===================================================
 * Modal hiển thị lịch sử các lần điều chỉnh KQCV của 1 CV.
 * Dùng cho cả CC (xem CV của mình bị sửa) và LĐ (xem lịch sử CV mình quản lý).
 */

'use client';

import { useEffect, useState } from 'react';
import { dieuChinhKqcvService } from '@/services/dieuChinhKqcv.service';
import { IDieuChinhKqcv } from '@/types/dieuChinhKqcv';

interface Props {
  open: boolean;
  keKhaiId: string | null;
  onClose: () => void;
}

const TT_LABEL: Record<string, string> = {
  NHAP: 'Nháp',
  CHO_PHE_DUYET: 'Chờ duyệt',
  DA_PHE_DUYET: 'Đã áp dụng',
  TU_CHOI: 'Bị từ chối',
};

const TT_COLOR: Record<string, string> = {
  NHAP: 'bg-gray-100 text-gray-700',
  CHO_PHE_DUYET: 'bg-yellow-100 text-yellow-800',
  DA_PHE_DUYET: 'bg-green-100 text-green-800',
  TU_CHOI: 'bg-red-100 text-red-800',
};

function fmtDate(s: string | null): string {
  if (!s) return '—';
  const d = new Date(s);
  return d.toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short' });
}

export default function LichSuDieuChinhModal({ open, keKhaiId, onClose }: Props) {
  const [items, setItems] = useState<IDieuChinhKqcv[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !keKhaiId) return;
    setLoading(true);
    setError(null);
    dieuChinhKqcvService
      .listLichSuCV(keKhaiId)
      .then(setItems)
      .catch((e) => {
        const msg = (e as { response?: { data?: { detail?: { error?: { message?: string } } } } })
          ?.response?.data?.detail?.error?.message ?? 'Không tải được lịch sử';
        setError(msg);
      })
      .finally(() => setLoading(false));
  }, [open, keKhaiId]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
          <h3 className="font-semibold text-lg">📜 Lịch sử điều chỉnh</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        <div className="p-5 overflow-y-auto flex-1">
          {loading && <p className="text-sm text-gray-500 text-center py-6">Đang tải...</p>}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              {error}
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p className="text-sm">Công việc này chưa có điều chỉnh nào.</p>
            </div>
          )}

          {!loading && items.length > 0 && (
            <div className="space-y-3">
              {items.map((dc, idx) => {
                const old = dc.gia_tri_cu;
                const neu = dc.gia_tri_moi;
                const change: { label: string; from: string; to: string }[] = [];
                if (old.so_loi_chat_luong !== neu.so_loi_chat_luong) {
                  change.push({
                    label: 'Số lỗi chất lượng',
                    from: String(old.so_loi_chat_luong),
                    to: String(neu.so_loi_chat_luong),
                  });
                }
                if (old.so_loi_tien_do !== neu.so_loi_tien_do) {
                  change.push({
                    label: 'Số lỗi tiến độ',
                    from: String(old.so_loi_tien_do),
                    to: String(neu.so_loi_tien_do),
                  });
                }
                if (old.is_chua_hoan_thanh !== neu.is_chua_hoan_thanh) {
                  change.push({
                    label: 'Đánh dấu chưa hoàn thành',
                    from: old.is_chua_hoan_thanh ? 'CÓ' : 'KHÔNG',
                    to: neu.is_chua_hoan_thanh ? 'CÓ' : 'KHÔNG',
                  });
                }

                return (
                  <div
                    key={dc.id}
                    className="border border-gray-200 rounded-lg p-3 bg-gray-50"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="text-xs text-gray-500">Lần #{items.length - idx}</span>
                        <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${TT_COLOR[dc.trang_thai]}`}>
                          {TT_LABEL[dc.trang_thai]}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">{fmtDate(dc.created_at)}</span>
                    </div>

                    <div className="text-sm mb-2">
                      <span className="text-gray-600">Người điều chỉnh:</span>{' '}
                      <b>{dc.nguoi_dieu_chinh?.ho_ten}</b>
                      <span className="text-gray-500"> ({dc.nguoi_dieu_chinh?.ma_cc})</span>
                    </div>

                    {change.length > 0 ? (
                      <table className="w-full text-xs mb-2 bg-white rounded border border-gray-100">
                        <thead className="bg-gray-100 text-gray-600">
                          <tr>
                            <th className="px-2 py-1 text-left">Trường</th>
                            <th className="px-2 py-1 text-center">Cũ</th>
                            <th className="px-2 py-1 text-center">→</th>
                            <th className="px-2 py-1 text-center">Mới</th>
                          </tr>
                        </thead>
                        <tbody>
                          {change.map((c, i) => (
                            <tr key={i}>
                              <td className="px-2 py-1">{c.label}</td>
                              <td className="px-2 py-1 text-center text-red-600 font-mono">{c.from}</td>
                              <td className="px-2 py-1 text-center text-gray-400">→</td>
                              <td className="px-2 py-1 text-center text-green-700 font-mono font-semibold">{c.to}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <p className="text-xs text-gray-500 italic mb-2">(không có thay đổi giá trị)</p>
                    )}

                    <div className="text-sm bg-white rounded p-2 border border-gray-100">
                      <p className="text-xs text-gray-500 mb-0.5">Lý do:</p>
                      <p className="text-gray-800">{dc.ly_do}</p>
                    </div>

                    {dc.y_kien_phe_duyet && (
                      <div className="text-sm bg-blue-50 rounded p-2 border border-blue-100 mt-2">
                        <p className="text-xs text-gray-500 mb-0.5">
                          Ý kiến của <b>{dc.nguoi_phe_duyet?.ho_ten}</b> ({fmtDate(dc.ngay_phe_duyet)}):
                        </p>
                        <p className="text-gray-800 italic">{dc.y_kien_phe_duyet}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="px-5 py-3 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * ChonNhomModal — modal multi-select nhóm thành phần.
 *
 * Hiển thị checklist các nhóm hiện có. User tick nhiều nhóm rồi bấm "Áp dụng".
 * Caller nhận lại danh sách nhom_ids và tự xử lý (gọi BE merge endpoint cho
 * cuộc họp đã tồn tại, hoặc fetch chi tiết + merge local cho form tạo mới).
 */

'use client';

import { useEffect, useState } from 'react';
import { Check, Loader2, Search, Users, X } from 'lucide-react';
import { nhomThanhPhanApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { INhomListItem } from '@/types/hkg';

interface Props {
  /** Title hiển thị trên header — vd: "Chọn nhóm để thêm vào cuộc họp". */
  title?: string;
  /** Label nút confirm. */
  confirmLabel?: string;
  /** Disable confirm khi processing. */
  busy?: boolean;
  onConfirm: (nhomIds: string[]) => void | Promise<void>;
  onClose: () => void;
}

export default function ChonNhomModal({
  title = 'Chọn nhóm thành phần',
  confirmLabel = 'Áp dụng',
  busy = false,
  onConfirm,
  onClose,
}: Props) {
  const [items, setItems] = useState<INhomListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && !busy) onClose();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose, busy]);

  useEffect(() => {
    const t = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const params: Record<string, string | number> = { page: 1, limit: 100 };
        if (q.trim()) params.q = q.trim();
        const resp = await nhomThanhPhanApi.danhSach(params);
        setItems(resp.data.data);
      } catch (e: unknown) {
        setError(errMsg(e, 'Lỗi tải danh sách nhóm'));
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  const toggle = (id: string) => {
    setSelected((s) => {
      const ns = new Set(s);
      if (ns.has(id)) ns.delete(id);
      else ns.add(id);
      return ns;
    });
  };

  const handleConfirm = async () => {
    if (selected.size === 0) return;
    await onConfirm(Array.from(selected));
  };

  return (
    <div
      className="fixed inset-0 z-[60] bg-black/40 flex items-center justify-center p-4"
      onClick={busy ? undefined : onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-xl max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            onClick={onClose}
            disabled={busy}
            className="text-gray-500 hover:text-gray-800 disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-5 py-3 border-b">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Tìm theo tên nhóm..."
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded text-sm"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-3">
          {error && (
            <div className="p-2 mb-3 bg-red-50 text-red-700 border border-red-200 rounded text-sm">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex items-center gap-2 p-4 text-gray-600">
              <Loader2 className="w-4 h-4 animate-spin" /> Đang tải...
            </div>
          ) : items.length === 0 ? (
            <div className="p-6 text-center text-gray-500 text-sm">
              Chưa có nhóm nào phù hợp.
            </div>
          ) : (
            <ul className="divide-y divide-gray-100">
              {items.map((it) => {
                const checked = selected.has(it.id);
                return (
                  <li key={it.id}>
                    <label className="flex items-start gap-3 py-2 cursor-pointer hover:bg-gray-50 px-1 rounded">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggle(it.id)}
                        className="mt-1"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900">
                          {it.ten_nhom}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                          <span className="inline-flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {it.so_thanh_vien} thành viên
                          </span>
                          {it.loai_nhom && (
                            <span className="px-1.5 py-0.5 bg-gray-100 rounded">
                              {it.loai_nhom}
                            </span>
                          )}
                        </div>
                        {it.mo_ta && (
                          <div className="text-xs text-gray-600 mt-1 line-clamp-1">
                            {it.mo_ta}
                          </div>
                        )}
                      </div>
                    </label>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="px-5 py-3 border-t bg-gray-50 flex items-center justify-between">
          <span className="text-sm text-gray-600">
            Đã chọn: <strong>{selected.size}</strong> nhóm
          </span>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              disabled={busy}
              className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50"
            >
              Huỷ
            </button>
            <button
              onClick={handleConfirm}
              disabled={selected.size === 0 || busy}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {busy && <Loader2 className="w-4 h-4 animate-spin" />}
              {!busy && <Check className="w-4 h-4" />}
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

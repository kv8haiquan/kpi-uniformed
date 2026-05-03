/**
 * NhomFormModal — modal tạo/sửa metadata của nhóm thành phần.
 *
 * Mode "create": tạo nhóm rỗng (chưa có thành viên). User chọn thành viên ở
 * NhomDetailModal sau khi tạo.
 * Mode "edit": chỉ sửa ten_nhom / mo_ta / loai_nhom.
 */

'use client';

import { useEffect, useState } from 'react';
import { Loader2, X } from 'lucide-react';
import { nhomThanhPhanApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { INhomListItem } from '@/types/hkg';

type Mode = 'create' | 'edit';

interface Props {
  mode: Mode;
  initial?: INhomListItem;
  onClose: () => void;
  onSuccess: () => void;
}

export default function NhomFormModal({ mode, initial, onClose, onSuccess }: Props) {
  const [tenNhom, setTenNhom] = useState(initial?.ten_nhom ?? '');
  const [moTa, setMoTa] = useState(initial?.mo_ta ?? '');
  const [loaiNhom, setLoaiNhom] = useState(initial?.loai_nhom ?? '');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tenNhom.trim()) {
      setError('Tên nhóm không được để trống');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      if (mode === 'create') {
        await nhomThanhPhanApi.taoMoi({
          ten_nhom: tenNhom.trim(),
          mo_ta: moTa.trim() || null,
          loai_nhom: loaiNhom.trim() || null,
        });
      } else if (initial) {
        await nhomThanhPhanApi.capNhat(initial.id, {
          ten_nhom: tenNhom.trim(),
          mo_ta: moTa.trim() || null,
          loai_nhom: loaiNhom.trim() || null,
        });
      }
      onSuccess();
    } catch (e: unknown) {
      setError(errMsg(e, 'Lưu thất bại'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <h2 className="text-lg font-semibold">
            {mode === 'create' ? 'Tạo nhóm thành phần' : 'Sửa thông tin nhóm'}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tên nhóm <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={tenNhom}
              onChange={(e) => setTenNhom(e.target.value)}
              autoFocus
              maxLength={200}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
              placeholder="VD: Họp giao ban tuần"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Loại nhóm (tuỳ chọn)
            </label>
            <input
              type="text"
              value={loaiNhom}
              onChange={(e) => setLoaiNhom(e.target.value)}
              maxLength={100}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
              placeholder="VD: Giao ban, Họp Đảng, Hội nghị"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mô tả (tuỳ chọn)
            </label>
            <textarea
              value={moTa}
              onChange={(e) => setMoTa(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
              placeholder="Mô tả ngắn về mục đích của nhóm"
            />
          </div>

          {error && (
            <div className="p-2 bg-red-50 text-red-700 border border-red-200 rounded text-sm">
              {error}
            </div>
          )}

          {mode === 'create' && (
            <div className="text-xs text-gray-500 bg-blue-50 border border-blue-100 rounded px-3 py-2">
              Sau khi tạo, bấm vào tên nhóm trong danh sách để thêm thành viên.
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-100"
            >
              Huỷ
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-60"
            >
              {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
              {mode === 'create' ? 'Tạo nhóm' : 'Lưu thay đổi'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

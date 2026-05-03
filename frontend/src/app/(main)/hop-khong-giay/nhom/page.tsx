/**
 * /hop-khong-giay/nhom — Quản lý nhóm thành phần.
 *
 * Mọi công chức đã đăng nhập đều CRUD được mọi nhóm.
 * Dùng cho việc gộp danh sách thành viên cố định vào nhiều cuộc họp lặp lại.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Loader2,
  Pencil,
  Plus,
  Search,
  Trash2,
  Users,
  UsersRound,
} from 'lucide-react';
import { nhomThanhPhanApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { INhomListItem } from '@/types/hkg';
import NhomFormModal from '@/components/hkg/NhomFormModal';
import NhomDetailModal from '@/components/hkg/NhomDetailModal';

export default function NhomThanhPhanPage() {
  const [items, setItems] = useState<INhomListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [loaiFilter, setLoaiFilter] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  const [creating, setCreating] = useState(false);
  const [editingMeta, setEditingMeta] = useState<INhomListItem | null>(null);
  const [openingDetail, setOpeningDetail] = useState<string | null>(null);

  const reload = useCallback(() => setReloadKey((k) => k + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    const t = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const params: Record<string, string | number> = { page: 1, limit: 100 };
        if (q.trim()) params.q = q.trim();
        if (loaiFilter.trim()) params.loai_nhom = loaiFilter.trim();
        const resp = await nhomThanhPhanApi.danhSach(params);
        if (!controller.signal.aborted) setItems(resp.data.data);
      } catch (e: unknown) {
        if (!controller.signal.aborted) setError(errMsg(e, 'Lỗi tải danh sách'));
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 250);
    return () => {
      controller.abort();
      clearTimeout(t);
    };
  }, [q, loaiFilter, reloadKey]);

  const handleDelete = async (item: INhomListItem) => {
    if (!confirm(`Xoá nhóm "${item.ten_nhom}"? Không thể khôi phục.`)) return;
    try {
      await nhomThanhPhanApi.xoa(item.id);
      reload();
    } catch (e: unknown) {
      alert(errMsg(e, 'Xoá thất bại'));
    }
  };

  // Lấy danh sách loai_nhom có sẵn để gợi ý filter
  const loaiNhomOptions = Array.from(
    new Set(items.map((x) => x.loai_nhom).filter((x): x is string => !!x)),
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-2">
        <Link
          href="/hop-khong-giay"
          className="text-gray-600 hover:text-gray-900"
          title="Quay lại lịch họp"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <UsersRound className="w-6 h-6 text-blue-600" />
          Nhóm thành phần
        </h1>
      </div>
      <p className="text-sm text-gray-600 mb-4">
        Tạo sẵn các nhóm thành viên dùng chung cho nhiều cuộc họp lặp lại. Khi
        tạo cuộc họp, chọn 1 hoặc nhiều nhóm để tự động thêm thành phần.
      </p>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Tìm theo tên nhóm..."
            className="pl-9 pr-3 py-2 border border-gray-300 rounded text-sm bg-white w-72"
          />
        </div>
        <input
          type="text"
          value={loaiFilter}
          onChange={(e) => setLoaiFilter(e.target.value)}
          placeholder="Loại nhóm (tuỳ chọn)"
          list="loai-nhom-list"
          className="px-3 py-2 border border-gray-300 rounded text-sm bg-white w-56"
        />
        <datalist id="loai-nhom-list">
          {loaiNhomOptions.map((l) => (
            <option key={l} value={l} />
          ))}
        </datalist>
        <button
          onClick={() => setCreating(true)}
          className="ml-auto inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Tạo nhóm
        </button>
      </div>

      {error && (
        <div className="p-3 mb-3 bg-red-50 text-red-700 border border-red-200 rounded text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center gap-2 p-6 text-gray-600">
          <Loader2 className="w-4 h-4 animate-spin" /> Đang tải...
        </div>
      ) : items.length === 0 ? (
        <div className="p-8 text-center text-gray-500 bg-gray-50 rounded border border-dashed">
          Chưa có nhóm nào. Bấm <strong>Tạo nhóm</strong> để bắt đầu.
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-700 text-left">
              <tr>
                <th className="px-4 py-2 font-medium">Tên nhóm</th>
                <th className="px-4 py-2 font-medium">Loại</th>
                <th className="px-4 py-2 font-medium">Thành viên</th>
                <th className="px-4 py-2 font-medium">Người tạo</th>
                <th className="px-4 py-2 font-medium">Cập nhật</th>
                <th className="px-4 py-2 font-medium text-right">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-2">
                    <button
                      onClick={() => setOpeningDetail(it.id)}
                      className="text-blue-700 hover:underline font-medium text-left"
                    >
                      {it.ten_nhom}
                    </button>
                    {it.mo_ta && (
                      <div className="text-xs text-gray-500 line-clamp-1 max-w-md">
                        {it.mo_ta}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-2 text-gray-700">{it.loai_nhom || '—'}</td>
                  <td className="px-4 py-2">
                    <span className="inline-flex items-center gap-1 text-gray-700">
                      <Users className="w-3.5 h-3.5" />
                      {it.so_thanh_vien}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-700">
                    {it.nguoi_tao_ho_ten || '—'}
                  </td>
                  <td className="px-4 py-2 text-gray-500 text-xs">
                    {new Date(it.updated_at).toLocaleString('vi-VN')}
                  </td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">
                    <button
                      onClick={() => setEditingMeta(it)}
                      className="inline-flex items-center gap-1 px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-100"
                      title="Sửa thông tin nhóm"
                    >
                      <Pencil className="w-3.5 h-3.5" /> Sửa
                    </button>
                    <button
                      onClick={() => handleDelete(it)}
                      className="ml-2 inline-flex items-center gap-1 px-2 py-1 text-xs border border-red-300 text-red-700 rounded hover:bg-red-50"
                      title="Xoá nhóm"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> Xoá
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {creating && (
        <NhomFormModal
          mode="create"
          onClose={() => setCreating(false)}
          onSuccess={() => {
            setCreating(false);
            reload();
          }}
        />
      )}

      {editingMeta && (
        <NhomFormModal
          mode="edit"
          initial={editingMeta}
          onClose={() => setEditingMeta(null)}
          onSuccess={() => {
            setEditingMeta(null);
            reload();
          }}
        />
      )}

      {openingDetail && (
        <NhomDetailModal
          nhomId={openingDetail}
          onClose={() => {
            setOpeningDetail(null);
            reload();
          }}
        />
      )}
    </div>
  );
}

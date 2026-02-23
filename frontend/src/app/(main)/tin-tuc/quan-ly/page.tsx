/**
 * app/(main)/tin-tuc/quan-ly/page.tsx
 * ======================================
 * Quản lý bài viết — dành cho BIEN_TAP, QT_NOI_DUNG, Lãnh đạo.
 * Workflow: NHAP → KIEM_TRA → DUYET → XUAT_BAN → THU_HOI
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { baiVietApi, chuyenMucApi } from '@/services/portal';
import { useCurrentUser } from '@/stores/useAuthStore';
import type { IChuyenMuc, IBaiVietListItem } from '@/types/tin-tuc';
import {
  TRANG_THAI_LABEL,
  TRANG_THAI_COLOR,
} from '@/types/tin-tuc';

// =============================================================================
// HELPERS
// =============================================================================

function formatDate(s?: string | null): string {
  if (!s) return '—';
  return new Date(s).toLocaleDateString('vi-VN');
}

// =============================================================================
// ACTION BUTTONS
// =============================================================================

interface ActionButtonsProps {
  bai: IBaiVietListItem;
  isLanhDao: boolean;
  onAction: (id: string, trangThaiMoi: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onGhim: (id: string, ghim: boolean) => void;
  loading: string | null;
}

function ActionButtons({
  bai,
  isLanhDao,
  onAction,
  onEdit,
  onDelete,
  onGhim,
  loading,
}: ActionButtonsProps) {
  const isLoading = loading === bai.id;

  const btn = (label: string, action: () => void, color: string) => (
    <button
      key={label}
      onClick={action}
      disabled={isLoading}
      className={`text-xs px-2 py-1 rounded-lg font-medium transition-colors disabled:opacity-50 ${color}`}
    >
      {isLoading ? '...' : label}
    </button>
  );

  switch (bai.trang_thai) {
    case 'NHAP':
      return (
        <div className="flex gap-1 flex-wrap">
          {btn('Sửa', () => onEdit(bai.id), 'bg-gray-100 text-gray-700 hover:bg-gray-200')}
          {btn('Gửi duyệt', () => onAction(bai.id, 'KIEM_TRA'), 'bg-blue-100 text-blue-700 hover:bg-blue-200')}
          {btn('Xóa', () => onDelete(bai.id), 'bg-red-100 text-red-700 hover:bg-red-200')}
        </div>
      );
    case 'KIEM_TRA':
      return (
        <div className="flex gap-1 flex-wrap">
          {btn('Phê duyệt', () => onAction(bai.id, 'DUYET'), 'bg-blue-100 text-blue-700 hover:bg-blue-200')}
          {btn('Từ chối', () => onAction(bai.id, 'NHAP'), 'bg-orange-100 text-orange-700 hover:bg-orange-200')}
        </div>
      );
    case 'DUYET':
      return (
        <div className="flex gap-1 flex-wrap">
          {isLanhDao && btn('Xuất bản', () => onAction(bai.id, 'XUAT_BAN'), 'bg-green-100 text-green-700 hover:bg-green-200')}
          {isLanhDao && btn('Từ chối', () => onAction(bai.id, 'NHAP'), 'bg-orange-100 text-orange-700 hover:bg-orange-200')}
        </div>
      );
    case 'XUAT_BAN':
      return (
        <div className="flex gap-1 flex-wrap">
          {btn('Thu hồi', () => onAction(bai.id, 'THU_HOI'), 'bg-red-100 text-red-700 hover:bg-red-200')}
          {btn(bai.is_ghim ? 'Bỏ ghim' : 'Ghim', () => onGhim(bai.id, !bai.is_ghim), 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200')}
        </div>
      );
    case 'THU_HOI':
      return (
        <div className="flex gap-1 flex-wrap">
          {btn('Soạn lại', () => onAction(bai.id, 'NHAP'), 'bg-gray-100 text-gray-700 hover:bg-gray-200')}
        </div>
      );
    default:
      return null;
  }
}

// =============================================================================
// PAGE
// =============================================================================

const PAGE_SIZE = 20;

export default function TinTucQuanLyPage() {
  const router = useRouter();
  const user = useCurrentUser();
  const isLanhDao = user?.is_lanh_dao ?? false;

  const [baiVietList, setBaiVietList] = useState<IBaiVietListItem[]>([]);
  const [chuyenMucList, setChuyenMucList] = useState<IChuyenMuc[]>([]);
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total_items: 0 });
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterChuyen, setFilterChuyen] = useState('');
  const [page, setPage] = useState(1);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  // ---------------------------------------------------------------------------

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await baiVietApi.quanLy({
        page,
        page_size: PAGE_SIZE,
        trang_thai: filterStatus || undefined,
        chuyen_muc_id: filterChuyen || undefined,
      });
      const raw = res.data?.data ?? res.data;
      setBaiVietList(raw?.items ?? []);
      setPagination({
        page: raw?.pagination?.page ?? 1,
        total_pages: raw?.pagination?.total_pages ?? 1,
        total_items: raw?.pagination?.total_items ?? 0,
      });
    } catch {
      setBaiVietList([]);
    } finally {
      setLoading(false);
    }
  }, [page, filterStatus, filterChuyen]);

  useEffect(() => {
    chuyenMucApi.danhSach().then((res) => {
      const items = res.data?.data ?? res.data;
      setChuyenMucList(Array.isArray(items) ? items : []);
    }).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // ---------------------------------------------------------------------------

  const handleAction = async (id: string, trangThaiMoi: string) => {
    setActionLoading(id);
    try {
      await baiVietApi.doiTrangThai(id, { trang_thai_moi: trangThaiMoi });
      fetchData();
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(e?.message ?? 'Có lỗi xảy ra.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (id: string) => {
    setConfirmDelete(null);
    setActionLoading(id);
    try {
      await baiVietApi.xoa(id);
      fetchData();
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(e?.message ?? 'Có lỗi xảy ra.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleGhim = async (id: string, ghim: boolean) => {
    setActionLoading(id);
    try {
      await baiVietApi.doiGhim(id, ghim);
      fetchData();
    } finally {
      setActionLoading(null);
    }
  };

  // ---------------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-6 sm:px-6">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Quản lý bài viết</h1>
            <p className="text-sm text-gray-500 mt-0.5">{pagination.total_items} bài viết</p>
          </div>
          <Link
            href="/tin-tuc/quan-ly/soan-bai"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <span>+</span> Soạn bài mới
          </Link>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 flex flex-wrap gap-3">
          <select
            value={filterStatus}
            onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          >
            <option value="">Tất cả trạng thái</option>
            <option value="NHAP">Nháp</option>
            <option value="KIEM_TRA">Kiểm tra</option>
            <option value="DUYET">Duyệt</option>
            <option value="XUAT_BAN">Xuất bản</option>
            <option value="THU_HOI">Thu hồi</option>
          </select>

          <select
            value={filterChuyen}
            onChange={(e) => { setFilterChuyen(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          >
            <option value="">Tất cả chuyên mục</option>
            {chuyenMucList.map((cm) => (
              <option key={cm.id} value={cm.id}>{cm.ten}</option>
            ))}
          </select>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-gray-400 mt-2">Đang tải...</p>
            </div>
          ) : baiVietList.length === 0 ? (
            <div className="p-12 text-center">
              <span className="text-3xl">📭</span>
              <p className="text-sm text-gray-400 mt-2">Không có bài viết nào</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Tiêu đề</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600 hidden md:table-cell">Chuyên mục</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Trạng thái</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600 hidden lg:table-cell">Ngày tạo</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Hành động</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {baiVietList.map((bai) => (
                    <tr key={bai.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <Link
                          href={`/tin-tuc/${bai.id}`}
                          className="font-medium text-gray-900 hover:text-blue-700 line-clamp-1 transition-colors"
                        >
                          {bai.is_ghim && <span className="text-yellow-500 mr-1">📌</span>}
                          {bai.tieu_de}
                        </Link>
                        <p className="text-xs text-gray-400 mt-0.5">{bai.nguoi_soan.ho_ten}</p>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell text-gray-600 text-xs">
                        {bai.chuyen_muc.ten}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TRANG_THAI_COLOR[bai.trang_thai] ?? 'bg-gray-100 text-gray-600'}`}>
                          {TRANG_THAI_LABEL[bai.trang_thai] ?? bai.trang_thai}
                        </span>
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell text-xs text-gray-400">
                        {formatDate(bai.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <ActionButtons
                          bai={bai}
                          isLanhDao={isLanhDao}
                          onAction={handleAction}
                          onEdit={(id) => router.push(`/tin-tuc/quan-ly/soan-bai?id=${id}`)}
                          onDelete={(id) => setConfirmDelete(id)}
                          onGhim={handleGhim}
                          loading={actionLoading}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-center gap-1 px-4 py-3 border-t border-gray-100">
              <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 text-sm rounded disabled:opacity-40 hover:bg-gray-100">←</button>
              <span className="text-sm text-gray-500">Trang {page} / {pagination.total_pages}</span>
              <button disabled={page >= pagination.total_pages} onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 text-sm rounded disabled:opacity-40 hover:bg-gray-100">→</button>
            </div>
          )}
        </div>

      </div>

      {/* Confirm delete dialog */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl p-6 w-80">
            <h3 className="text-base font-semibold text-gray-900 mb-2">Xóa bài viết?</h3>
            <p className="text-sm text-gray-500 mb-4">Thao tác này không thể hoàn tác.</p>
            <div className="flex gap-3">
              <button onClick={() => setConfirmDelete(null)}
                className="flex-1 border border-gray-300 text-gray-700 rounded-lg py-2 text-sm hover:bg-gray-50">
                Hủy
              </button>
              <button onClick={() => handleDelete(confirmDelete)}
                className="flex-1 bg-red-600 text-white rounded-lg py-2 text-sm hover:bg-red-700">
                Xóa
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

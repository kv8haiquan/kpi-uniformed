/**
 * src/app/(main)/admin/lich-su-dieu-chuyen/page.tsx
 * =================================================
 * Trang xem TOÀN BỘ lịch sử điều chuyển & thay đổi trạng thái của mọi công chức
 * (bao gồm cả CC đã bị vô hiệu hóa). Chỉ Admin.
 *
 * - Bảng phân trang, lọc theo loại, tìm theo mã CC / họ tên.
 */
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore, useCurrentUser } from '@/stores/useAuthStore';
import { adminService, isApiError } from '@/services/admin.service';
import { ILichSuDieuChuyenResponse, LoaiLichSuDieuChuyen } from '@/types/admin';

const LOAI_META: Record<LoaiLichSuDieuChuyen, { label: string; cls: string }> = {
  DIEU_CHUYEN: { label: 'Điều chuyển', cls: 'bg-blue-100 text-blue-700' },
  VO_HIEU_HOA: { label: 'Vô hiệu hóa', cls: 'bg-red-100 text-red-700' },
  KICH_HOAT: { label: 'Kích hoạt', cls: 'bg-green-100 text-green-700' },
};

const PAGE_SIZE = 20;

function fmtDate(s?: string | null): string {
  return s ? new Date(s).toLocaleDateString('vi-VN') : '—';
}

export default function AdminLichSuDieuChuyenPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const user = useCurrentUser();

  const [items, setItems] = useState<ILichSuDieuChuyenResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  const [loai, setLoai] = useState<'' | LoaiLichSuDieuChuyen>('');
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');

  // Sửa ngày hiệu lực / lý do cho 1 bản ghi
  const [editing, setEditing] = useState<ILichSuDieuChuyenResponse | null>(null);
  const [editNgay, setEditNgay] = useState('');
  const [editLyDo, setEditLyDo] = useState('');
  const [saving, setSaving] = useState(false);

  // Guard: chỉ admin
  useEffect(() => {
    if (!isAuthenticated) { router.replace('/login'); return; }
    if (user && !user.is_system_admin) { router.replace('/dashboard'); }
  }, [isAuthenticated, user, router]);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await adminService.getLichSuDieuChuyen({
        page,
        page_size: PAGE_SIZE,
        loai: loai || undefined,
        search: search || undefined,
      });
      setItems(res.data);
      setTotalPages(res.pagination?.total_pages || 1);
      setTotalItems(res.pagination?.total_items || 0);
    } catch (err) {
      setError(isApiError(err) ? err.message : 'Có lỗi khi tải lịch sử');
    } finally {
      setIsLoading(false);
    }
  }, [page, loai, search]);

  useEffect(() => {
    if (user?.is_system_admin) loadData();
  }, [user, loadData]);

  // Reset về trang 1 khi đổi bộ lọc
  useEffect(() => { setPage(1); }, [loai, search]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput.trim());
  };

  const moSua = (h: ILichSuDieuChuyenResponse) => {
    setEditing(h);
    setEditNgay(h.ngay_hieu_luc ? h.ngay_hieu_luc.slice(0, 10) : '');
    setEditLyDo(h.ly_do || '');
  };

  const luuSua = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    setSaving(true);
    try {
      await adminService.updateTransferHistory(editing.cong_chuc_id, editing.id, {
        ngay_hieu_luc: editNgay || null,
        ly_do: editLyDo.trim() || null,
      });
      setEditing(null);
      await loadData();
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi khi lưu ngày hiệu lực');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => router.push('/dashboard')}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Quay lại Dashboard"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">🔄 Lịch sử điều chuyển &amp; trạng thái</h1>
            <p className="text-gray-600">Toàn bộ điều chuyển, vô hiệu hóa, kích hoạt của mọi công chức</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 flex flex-wrap items-center gap-3">
          <select
            value={loai}
            onChange={(e) => setLoai(e.target.value as '' | LoaiLichSuDieuChuyen)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Tất cả loại --</option>
            <option value="DIEU_CHUYEN">Điều chuyển</option>
            <option value="VO_HIEU_HOA">Vô hiệu hóa</option>
            <option value="KICH_HOAT">Kích hoạt</option>
          </select>

          <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 min-w-[240px]">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Tìm theo mã CC hoặc họ tên..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
              Tìm
            </button>
            {search && (
              <button
                type="button"
                onClick={() => { setSearchInput(''); setSearch(''); }}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                Xóa lọc
              </button>
            )}
          </form>

          <span className="text-sm text-gray-500 ml-auto">{totalItems} bản ghi</span>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {error ? (
            <div className="p-8 text-center text-red-600">{error}</div>
          ) : isLoading ? (
            <div className="p-12 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          ) : items.length === 0 ? (
            <div className="p-8 text-center text-gray-400">Không có bản ghi nào.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-600">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Loại</th>
                    <th className="px-4 py-3 text-left font-medium">Công chức</th>
                    <th className="px-4 py-3 text-left font-medium">Nội dung</th>
                    <th className="px-4 py-3 text-left font-medium">Ngày hiệu lực</th>
                    <th className="px-4 py-3 text-left font-medium">Lý do</th>
                    <th className="px-4 py-3 text-left font-medium">Người thực hiện</th>
                    <th className="px-4 py-3 text-right font-medium">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {items.map((h) => {
                    const meta = LOAI_META[h.loai];
                    return (
                      <tr key={h.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${meta.cls}`}>{meta.label}</span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-medium text-gray-900">{h.cong_chuc_ho_ten || 'N/A'}</div>
                          <div className="text-xs text-gray-400">{h.cong_chuc_ma_cc || ''}</div>
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {h.loai === 'DIEU_CHUYEN' ? (
                            <span>{h.don_vi_cu_ten || '?'} → <span className="text-blue-600 font-medium">{h.don_vi_moi_ten || '?'}</span></span>
                          ) : (
                            <span className="text-gray-500">{meta.label} tài khoản</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {h.ngay_hieu_luc
                            ? fmtDate(h.ngay_hieu_luc)
                            : <span className="text-amber-600 text-xs">Chưa có</span>}
                        </td>
                        <td className="px-4 py-3 text-gray-500 max-w-[220px] truncate" title={h.ly_do || ''}>{h.ly_do || '—'}</td>
                        <td className="px-4 py-3 text-gray-500">{h.nguoi_thuc_hien_ten || '—'}</td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => moSua(h)}
                            className="px-2.5 py-1 text-blue-600 hover:bg-blue-50 rounded text-xs font-medium"
                          >
                            Sửa ngày
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-4">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50"
            >
              ← Trước
            </button>
            <span className="text-sm text-gray-600">Trang {page}/{totalPages}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50"
            >
              Sau →
            </button>
          </div>
        )}

        {/* Modal sửa ngày hiệu lực */}
        {editing && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <form onSubmit={luuSua} className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">Sửa ngày hiệu lực</h3>
              <p className="text-sm text-gray-500 mb-4">
                <span className="font-medium">{LOAI_META[editing.loai].label}</span>
                {' · '}{editing.cong_chuc_ho_ten || 'N/A'}
                {editing.cong_chuc_ma_cc && <span className="text-gray-400"> ({editing.cong_chuc_ma_cc})</span>}
              </p>

              <label className="block text-sm font-medium text-gray-700 mb-1">Ngày hiệu lực</label>
              <input
                type="date"
                value={editNgay}
                onChange={(e) => setEditNgay(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-1 focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mb-4">
                Ảnh hưởng báo cáo thống kê: CC được tính đến hết tháng có ngày hiệu lực này.
              </p>

              <label className="block text-sm font-medium text-gray-700 mb-1">Lý do (tùy chọn)</label>
              <textarea
                value={editLyDo}
                onChange={(e) => setEditLyDo(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
              />

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setEditing(null)}
                  disabled={saving}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Đang lưu...' : 'Lưu'}
                </button>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}

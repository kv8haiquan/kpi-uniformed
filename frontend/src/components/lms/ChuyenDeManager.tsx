/**
 * src/components/lms/ChuyenDeManager.tsx
 * ========================================
 * Component quản lý Chuyên đề đào tạo.
 * Dùng cho tab "Chuyên đề" trong trang /dao-tao/quan-ly.
 * Quyền: QT_DAO_TAO, ADMIN (backend tự kiểm tra 403).
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { chuyenDeApi } from '@/services/lms';
import type { IChuyenDe, IChuyenDeCreate } from '@/types/lms';

// =============================================================================
// FORM STATE
// =============================================================================

interface FormState {
  ma_chuyen_de: string;
  ten_chuyen_de: string;
  mo_ta: string;
  thu_tu: string;
}

const FORM_DEFAULT: FormState = {
  ma_chuyen_de: '',
  ten_chuyen_de: '',
  mo_ta: '',
  thu_tu: '1',
};

// =============================================================================
// MODAL TẠO / SỬA CHUYÊN ĐỀ
// =============================================================================

interface ModalProps {
  mode: 'tao' | 'sua';
  init?: IChuyenDe | null;
  onClose: () => void;
  onSuccess: () => void;
}

function ChuyenDeModal({ mode, init, onClose, onSuccess }: ModalProps) {
  const [form, setForm] = useState<FormState>(
    init
      ? {
          ma_chuyen_de: init.ma_chuyen_de,
          ten_chuyen_de: init.ten_chuyen_de,
          mo_ta: init.mo_ta ?? '',
          thu_tu: String(init.thu_tu),
        }
      : FORM_DEFAULT
  );
  const [submitting, setSubmitting] = useState(false);
  const [errMsg, setErrMsg] = useState('');

  const canSubmit = form.ma_chuyen_de.trim() !== '' && form.ten_chuyen_de.trim() !== '';

  const handleSubmit = async () => {
    if (!canSubmit) {
      setErrMsg('Mã và Tên chuyên đề là bắt buộc');
      return;
    }
    setSubmitting(true);
    setErrMsg('');
    try {
      const payload: IChuyenDeCreate = {
        ma_chuyen_de: form.ma_chuyen_de.trim(),
        ten_chuyen_de: form.ten_chuyen_de.trim(),
        ...(form.mo_ta.trim() && { mo_ta: form.mo_ta.trim() }),
        ...(form.thu_tu && { thu_tu: Number(form.thu_tu) }),
      };
      if (mode === 'tao') {
        await chuyenDeApi.taoMoi(payload);
      } else if (init) {
        await chuyenDeApi.capNhat(init.id, payload);
      }
      onSuccess();
    } catch (err: any) {
      setErrMsg(
        err?.response?.data?.detail?.error?.message || 'Lỗi thao tác. Vui lòng thử lại.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  // Đóng modal khi nhấn Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    /* Overlay toàn màn hình */
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
        {/* Tiêu đề modal */}
        <h3 className="text-lg font-semibold text-gray-900 mb-5">
          {mode === 'tao' ? '➕ Tạo chuyên đề mới' : '✏️ Cập nhật chuyên đề'}
        </h3>

        <div className="space-y-4">
          {/* Mã chuyên đề */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mã chuyên đề <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.ma_chuyen_de}
              onChange={(e) => setForm({ ...form, ma_chuyen_de: e.target.value })}
              placeholder="VD: CD001"
              autoFocus
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Tên chuyên đề */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tên chuyên đề <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.ten_chuyen_de}
              onChange={(e) => setForm({ ...form, ten_chuyen_de: e.target.value })}
              placeholder="VD: Nghiệp vụ hải quan"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Mô tả */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả</label>
            <textarea
              rows={3}
              value={form.mo_ta}
              onChange={(e) => setForm({ ...form, mo_ta: e.target.value })}
              placeholder="Mô tả ngắn về chuyên đề..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          {/* Thứ tự hiển thị */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Thứ tự hiển thị
            </label>
            <input
              type="number"
              min={1}
              value={form.thu_tu}
              onChange={(e) => setForm({ ...form, thu_tu: e.target.value })}
              className="w-32 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-400 mt-1">Số nhỏ hơn hiển thị trước</p>
          </div>

          {/* Thông báo lỗi */}
          {errMsg && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <p className="text-sm text-red-600">{errMsg}</p>
            </div>
          )}
        </div>

        {/* Nút hành động */}
        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
          <button
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Hủy
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !canSubmit}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting
              ? 'Đang lưu...'
              : mode === 'tao'
              ? 'Tạo chuyên đề'
              : 'Lưu thay đổi'}
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// DIALOG XÁC NHẬN XÓA
// =============================================================================

interface DeleteDialogProps {
  ten: string;
  onCancel: () => void;
  onConfirm: () => void;
  loading: boolean;
}

function DeleteDialog({ ten, onCancel, onConfirm, loading }: DeleteDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onCancel} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Xác nhận xóa</h3>
        <p className="text-sm text-gray-600 mb-1">Bạn có chắc muốn xóa chuyên đề:</p>
        <p className="text-sm font-medium text-gray-900 mb-5">"{ten}"?</p>
        <p className="text-xs text-gray-400 mb-5">
          Hành động này không thể hoàn tác. Chuyên đề phải không có khóa học liên kết.
        </p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Hủy
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50"
          >
            {loading ? 'Đang xóa...' : 'Xóa'}
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN: ChuyenDeManager
// =============================================================================

export default function ChuyenDeManager() {
  const [list, setList] = useState<IChuyenDe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal tạo mới
  const [showCreate, setShowCreate] = useState(false);
  // Modal sửa: lưu item đang sửa
  const [editItem, setEditItem] = useState<IChuyenDe | null>(null);
  // Dialog xóa: lưu item cần xóa
  const [deleteTarget, setDeleteTarget] = useState<IChuyenDe | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Tải danh sách chuyên đề từ LMS backend
  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await chuyenDeApi.danhSach();
      setList(res.data.data || []);
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 403) {
        setError('Bạn không có quyền quản lý chuyên đề. Cần vai trò QT_DAO_TAO hoặc ADMIN.');
      } else {
        setError('Không thể tải danh sách chuyên đề. Kiểm tra LMS backend (port 8001).');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadList();
  }, [loadList]);

  // Xóa chuyên đề sau khi user xác nhận
  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await chuyenDeApi.xoa(deleteTarget.id);
      setDeleteTarget(null);
      loadList();
    } catch (err: any) {
      alert(
        err?.response?.data?.detail?.error?.message ||
          'Không thể xóa. Chuyên đề có thể đang có khóa học liên kết.'
      );
    } finally {
      setDeleteLoading(false);
    }
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-14 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <span className="text-3xl block mb-2">🔒</span>
        <p className="text-red-700 text-sm font-medium">{error}</p>
      </div>
    );
  }

  return (
    <>
      {/* Toolbar: tổng số + nút tạo mới */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">
          Tổng <span className="font-semibold text-gray-800">{list.length}</span> chuyên đề
        </p>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center gap-1.5"
        >
          <span>➕</span> Tạo chuyên đề
        </button>
      </div>

      {/* Danh sách trống */}
      {list.length === 0 ? (
        <div className="text-center py-14 text-gray-500 bg-white rounded-xl border border-gray-200">
          <span className="text-5xl block mb-3">📂</span>
          <p className="font-medium">Chưa có chuyên đề nào</p>
          <p className="text-sm mt-1">Nhấn "Tạo chuyên đề" để bắt đầu</p>
        </div>
      ) : (
        /* Bảng danh sách */
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500 w-24">Mã</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Tên chuyên đề</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 max-w-xs">Mô tả</th>
                <th className="px-4 py-3 text-center font-medium text-gray-500 w-24">Khóa học</th>
                <th className="px-4 py-3 text-center font-medium text-gray-500 w-20">Thứ tự</th>
                <th className="px-4 py-3 text-center font-medium text-gray-500 w-28">Trạng thái</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500 w-28">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map((cd) => (
                <tr key={cd.id} className="hover:bg-gray-50 transition-colors">
                  {/* Mã */}
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{cd.ma_chuyen_de}</td>

                  {/* Tên */}
                  <td className="px-4 py-3 font-medium text-gray-900">{cd.ten_chuyen_de}</td>

                  {/* Mô tả */}
                  <td className="px-4 py-3 text-gray-500 max-w-xs">
                    <p className="truncate" title={cd.mo_ta ?? ''}>
                      {cd.mo_ta || <span className="text-gray-300">—</span>}
                    </p>
                  </td>

                  {/* Số khóa học */}
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                      {cd.so_khoa_hoc} khóa
                    </span>
                  </td>

                  {/* Thứ tự */}
                  <td className="px-4 py-3 text-center text-gray-600">{cd.thu_tu}</td>

                  {/* Trạng thái */}
                  <td className="px-4 py-3 text-center">
                    {cd.is_active ? (
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                        Hoạt động
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs font-medium">
                        Ẩn
                      </span>
                    )}
                  </td>

                  {/* Hành động */}
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1.5">
                      <button
                        onClick={() => setEditItem(cd)}
                        className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs hover:bg-yellow-200 transition-colors"
                      >
                        Sửa
                      </button>
                      <button
                        onClick={() => setDeleteTarget(cd)}
                        disabled={cd.so_khoa_hoc > 0}
                        title={
                          cd.so_khoa_hoc > 0
                            ? `Không thể xóa: đang có ${cd.so_khoa_hoc} khóa học liên kết`
                            : 'Xóa chuyên đề'
                        }
                        className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Xóa
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal tạo mới */}
      {showCreate && (
        <ChuyenDeModal
          mode="tao"
          onClose={() => setShowCreate(false)}
          onSuccess={() => {
            setShowCreate(false);
            loadList();
          }}
        />
      )}

      {/* Modal sửa */}
      {editItem && (
        <ChuyenDeModal
          mode="sua"
          init={editItem}
          onClose={() => setEditItem(null)}
          onSuccess={() => {
            setEditItem(null);
            loadList();
          }}
        />
      )}

      {/* Dialog xác nhận xóa */}
      {deleteTarget && (
        <DeleteDialog
          ten={deleteTarget.ten_chuyen_de}
          onCancel={() => setDeleteTarget(null)}
          onConfirm={handleConfirmDelete}
          loading={deleteLoading}
        />
      )}
    </>
  );
}

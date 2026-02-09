/**
 * src/app/(main)/admin/cap-do/page.tsx
 * =====================================
 * Trang Quản lý Cấp độ phức tạp (Admin Module).
 * 
 * Version: 1.0.0 (30/01/2026)
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { adminService, isApiError } from '@/services/admin.service';
import { ICapDoResponse, ICapDoCreateRequest, ICapDoUpdateRequest } from '@/types/admin';

// =============================================================================
// FORM MODAL
// =============================================================================

interface CapDoFormProps {
  editItem?: ICapDoResponse | null;
  onSubmit: (data: ICapDoCreateRequest | ICapDoUpdateRequest) => Promise<void>;
  onClose: () => void;
  isSubmitting: boolean;
}

function CapDoFormModal({ editItem, onSubmit, onClose, isSubmitting }: CapDoFormProps) {
  const [formData, setFormData] = useState({
    ma_cap_do: editItem?.ma_cap_do || '',
    ten_cap_do: editItem?.ten_cap_do || '',
    mo_ta: editItem?.mo_ta || '',
    he_so_sp1: parseFloat(String(editItem?.he_so_sp1 || 1)),
    he_so_sp2: parseFloat(String(editItem?.he_so_sp2 || 1)),
    is_theo_thuc_te: editItem?.is_theo_thuc_te || false,
    thu_tu: editItem?.thu_tu || 1,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.ma_cap_do.trim() || !formData.ten_cap_do.trim()) {
      alert('Vui lòng nhập đầy đủ thông tin bắt buộc');
      return;
    }

    if (formData.he_so_sp1 < 0 || formData.he_so_sp2 < 0) {
      alert('Hệ số phải >= 0');
      return;
    }

    if (formData.thu_tu < 1 || formData.thu_tu > 10) {
      alert('Thứ tự phải từ 1 đến 10');
      return;
    }

    await onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {editItem ? '✏️ Sửa Cấp độ' : '➕ Thêm Cấp độ mới'}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mã cấp độ <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.ma_cap_do}
                onChange={(e) => setFormData({ ...formData, ma_cap_do: e.target.value.toUpperCase() })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="VD: C6"
                disabled={!!editItem}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Thứ tự <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={formData.thu_tu}
                onChange={(e) => setFormData({ ...formData, thu_tu: parseInt(e.target.value) || 1 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min={1}
                max={10}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tên cấp độ <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.ten_cap_do}
              onChange={(e) => setFormData({ ...formData, ten_cap_do: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="VD: Đặc biệt phức tạp"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả</label>
            <textarea
              value={formData.mo_ta}
              onChange={(e) => setFormData({ ...formData, mo_ta: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows={2}
              placeholder="Mô tả chi tiết về cấp độ..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hệ số SP1 <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.he_so_sp1}
                onChange={(e) => setFormData({ ...formData, he_so_sp1: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min={0}
              />
              <p className="text-xs text-gray-500 mt-1">Hệ số quy đổi cho SP1</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hệ số SP2 <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.he_so_sp2}
                onChange={(e) => setFormData({ ...formData, he_so_sp2: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min={0}
              />
              <p className="text-xs text-gray-500 mt-1">Hệ số quy đổi cho SP2</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_theo_thuc_te"
              checked={formData.is_theo_thuc_te}
              onChange={(e) => setFormData({ ...formData, is_theo_thuc_te: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <label htmlFor="is_theo_thuc_te" className="text-sm text-gray-700">
              Tính theo thực tế (không áp dụng hệ số cố định)
            </label>
          </div>

          {formData.is_theo_thuc_te && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-700">
                ⚠️ Khi bật "Theo thực tế", hệ số sẽ được tính dựa trên thời gian thực tế hoàn thành công việc.
              </p>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              disabled={isSubmitting}
            >
              Hủy
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Đang lưu...' : editItem ? 'Cập nhật' : 'Tạo mới'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function AdminCapDoPage() {
  const router = useRouter();
  
  const [capDoList, setCapDoList] = useState<ICapDoResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [includeInactive, setIncludeInactive] = useState(false);
  
  // Modal states
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState<ICapDoResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<ICapDoResponse | null>(null);

  // Load data
  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await adminService.getCapDoList(includeInactive);
      // Sắp xếp theo thứ tự
      data.sort((a, b) => a.thu_tu - b.thu_tu);
      setCapDoList(data);
    } catch (err) {
      setError(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [includeInactive]);

  // Handlers
  const handleCreate = () => {
    setEditItem(null);
    setShowForm(true);
  };

  const handleEdit = (capDo: ICapDoResponse) => {
    setEditItem(capDo);
    setShowForm(true);
  };

  const handleSubmit = async (data: ICapDoCreateRequest | ICapDoUpdateRequest) => {
    setIsSubmitting(true);
    
    try {
      if (editItem) {
        await adminService.updateCapDo(editItem.id, data as ICapDoUpdateRequest);
      } else {
        await adminService.createCapDo(data as ICapDoCreateRequest);
      }
      
      setShowForm(false);
      setEditItem(null);
      loadData();
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeactivate = async () => {
    if (!deleteConfirm) return;
    
    setIsSubmitting(true);
    try {
      await adminService.deactivateCapDo(deleteConfirm.id);
      setDeleteConfirm(null);
      loadData();
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Color mapping cho cấp độ
  const getCapDoColor = (thuTu: number): string => {
    const colors: Record<number, string> = {
      1: 'bg-green-100 text-green-700',
      2: 'bg-blue-100 text-blue-700',
      3: 'bg-yellow-100 text-yellow-700',
      4: 'bg-orange-100 text-orange-700',
      5: 'bg-red-100 text-red-700',
    };
    return colors[thuTu] || 'bg-purple-100 text-purple-700';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/admin')}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📊 Quản lý Cấp độ phức tạp</h1>
              <p className="text-gray-600">Cấu hình các cấp độ và hệ số quy đổi SP</p>
            </div>
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Thêm mới
          </button>
        </div>

        {/* Filter */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <span className="text-sm text-gray-700">Hiển thị cả cấp độ không hoạt động</span>
          </label>
        </div>

        {/* Info Card */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
          <div className="flex items-start gap-3">
            <span className="text-xl">💡</span>
            <div className="text-sm text-blue-700">
              <p className="font-medium mb-1">Hướng dẫn:</p>
              <ul className="list-disc list-inside space-y-1">
                <li><strong>Hệ số SP1</strong>: Số SP1 quy đổi cho mỗi công việc ở cấp độ này</li>
                <li><strong>Hệ số SP2</strong>: Số SP2 quy đổi cho mỗi công việc ở cấp độ này</li>
                <li><strong>Theo thực tế</strong>: Hệ số được tính dựa trên thời gian thực tế</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : capDoList.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">📊</span>
              </div>
              <p className="text-gray-500">Chưa có cấp độ nào</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase w-16">TT</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Mã</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Tên cấp độ</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Mô tả</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Hệ số SP1</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Hệ số SP2</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Loại</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Trạng thái</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {capDoList.map((capDo) => (
                  <tr key={capDo.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-center">
                      <span className={`w-8 h-8 inline-flex items-center justify-center rounded-full text-sm font-bold ${getCapDoColor(capDo.thu_tu)}`}>
                        {capDo.thu_tu}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono font-medium text-gray-900">{capDo.ma_cap_do}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-medium text-gray-900">{capDo.ten_cap_do}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-gray-500 text-sm">{capDo.mo_ta || '-'}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-medium text-blue-600">{capDo.he_so_sp1}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-medium text-purple-600">{capDo.he_so_sp2}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {capDo.is_theo_thuc_te ? (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">Thực tế</span>
                      ) : (
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">Cố định</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        capDo.is_active 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {capDo.is_active ? 'Hoạt động' : 'Vô hiệu'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => handleEdit(capDo)}
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg"
                          title="Sửa"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        {capDo.is_active && (
                          <button
                            onClick={() => setDeleteConfirm(capDo)}
                            className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg"
                            title="Vô hiệu hóa"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* Form Modal */}
      {showForm && (
        <CapDoFormModal
          editItem={editItem}
          onSubmit={handleSubmit}
          onClose={() => { setShowForm(false); setEditItem(null); }}
          isSubmitting={isSubmitting}
        />
      )}

      {/* Delete Confirm Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">🗑️ Vô hiệu hóa Cấp độ</h3>
            <p className="text-gray-600 mb-4">
              Bạn có chắc muốn vô hiệu hóa cấp độ <strong>{deleteConfirm.ten_cap_do}</strong> ({deleteConfirm.ma_cap_do})?
            </p>
            <p className="text-sm text-orange-600 mb-4">
              ⚠️ Lưu ý: Không thể vô hiệu hóa nếu cấp độ đang được sử dụng trong danh mục công việc.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                disabled={isSubmitting}
              >
                Hủy
              </button>
              <button
                onClick={handleDeactivate}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Đang xử lý...' : 'Xác nhận'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

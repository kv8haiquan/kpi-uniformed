/**
 * src/app/(main)/admin/sp-chuan/page.tsx
 * =======================================
 * Trang Quản lý SP Chuẩn (Admin Module).
 * 
 * Version: 1.0.0 (30/01/2026)
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { adminService, isApiError } from '@/services/admin.service';
import { ISpChuanResponse, ISpChuanCreateRequest, ISpChuanUpdateRequest } from '@/types/admin';

// =============================================================================
// FORM MODAL
// =============================================================================

interface SpChuanFormProps {
  editItem?: ISpChuanResponse | null;
  onSubmit: (data: ISpChuanCreateRequest | ISpChuanUpdateRequest) => Promise<void>;
  onClose: () => void;
  isSubmitting: boolean;
}

function SpChuanFormModal({ editItem, onSubmit, onClose, isSubmitting }: SpChuanFormProps) {
  const [formData, setFormData] = useState({
    ma_sp: editItem?.ma_sp || '',
    ten_sp: editItem?.ten_sp || '',
    mo_ta: editItem?.mo_ta || '',
    thoi_gian_phut: editItem?.thoi_gian_phut || 5,
    he_so_quy_doi_sp1: parseFloat(String(editItem?.he_so_quy_doi_sp1 || 1)),
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.ma_sp.trim() || !formData.ten_sp.trim()) {
      alert('Vui lòng nhập đầy đủ thông tin');
      return;
    }

    if (formData.he_so_quy_doi_sp1 <= 0) {
      alert('Hệ số quy đổi phải > 0');
      return;
    }

    await onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {editItem ? '✏️ Sửa SP Chuẩn' : '➕ Thêm SP Chuẩn mới'}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mã SP <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.ma_sp}
              onChange={(e) => setFormData({ ...formData, ma_sp: e.target.value.toUpperCase() })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="VD: SP5"
              disabled={!!editItem}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tên SP <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.ten_sp}
              onChange={(e) => setFormData({ ...formData, ten_sp: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="VD: Báo cáo phân tích chuyên sâu"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả</label>
            <textarea
              value={formData.mo_ta}
              onChange={(e) => setFormData({ ...formData, mo_ta: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows={2}
              placeholder="Mô tả chi tiết..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Thời gian (phút)</label>
              <input
                type="number"
                value={formData.thoi_gian_phut}
                onChange={(e) => setFormData({ ...formData, thoi_gian_phut: parseInt(e.target.value) || 5 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min={1}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hệ số quy đổi SP1 <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.he_so_quy_doi_sp1}
                onChange={(e) => setFormData({ ...formData, he_so_quy_doi_sp1: parseFloat(e.target.value) || 1 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min={0.01}
                disabled={editItem?.is_sp_goc}
              />
              {editItem?.is_sp_goc && (
                <p className="text-xs text-orange-600 mt-1">SP gốc không thể sửa hệ số</p>
              )}
            </div>
          </div>

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

export default function AdminSpChuanPage() {
  const router = useRouter();
  
  const [spList, setSpList] = useState<ISpChuanResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [includeInactive, setIncludeInactive] = useState(false);
  
  // Modal states
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState<ISpChuanResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<ISpChuanResponse | null>(null);

  // Load data
  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await adminService.getSpChuanList(includeInactive);
      setSpList(data);
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

  const handleEdit = (sp: ISpChuanResponse) => {
    setEditItem(sp);
    setShowForm(true);
  };

  const handleSubmit = async (data: ISpChuanCreateRequest | ISpChuanUpdateRequest) => {
    setIsSubmitting(true);
    
    try {
      if (editItem) {
        await adminService.updateSpChuan(editItem.id, data as ISpChuanUpdateRequest);
      } else {
        await adminService.createSpChuan(data as ISpChuanCreateRequest);
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
      await adminService.deactivateSpChuan(deleteConfirm.id);
      setDeleteConfirm(null);
      loadData();
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
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
              <h1 className="text-2xl font-bold text-gray-900">📦 Quản lý SP Chuẩn</h1>
              <p className="text-gray-600">Cấu hình các loại sản phẩm chuẩn và hệ số quy đổi</p>
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
            <span className="text-sm text-gray-700">Hiển thị cả SP không hoạt động</span>
          </label>
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
          ) : spList.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">Chưa có SP Chuẩn nào</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Mã SP</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Tên SP</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Mô tả</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Thời gian</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Hệ số</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Trạng thái</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {spList.map((sp) => (
                  <tr key={sp.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="font-mono font-medium text-gray-900">{sp.ma_sp}</span>
                      {sp.is_sp_goc && (
                        <span className="ml-2 px-1.5 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded">Gốc</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-gray-900">{sp.ten_sp}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-gray-500 text-sm">{sp.mo_ta || '-'}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-gray-700">{sp.thoi_gian_phut} phút</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-medium text-blue-600">{sp.he_so_quy_doi_sp1}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        sp.is_active 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {sp.is_active ? 'Hoạt động' : 'Vô hiệu'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => handleEdit(sp)}
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg"
                          title="Sửa"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        {!sp.is_sp_goc && sp.is_active && (
                          <button
                            onClick={() => setDeleteConfirm(sp)}
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
        <SpChuanFormModal
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
            <h3 className="text-lg font-semibold text-gray-900 mb-2">🗑️ Vô hiệu hóa SP Chuẩn</h3>
            <p className="text-gray-600 mb-4">
              Bạn có chắc muốn vô hiệu hóa <strong>{deleteConfirm.ten_sp}</strong> ({deleteConfirm.ma_sp})?
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

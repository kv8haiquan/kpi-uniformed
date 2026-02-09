/**
 * src/app/(main)/admin/danh-muc-cv/page.tsx
 * ==========================================
 * Trang Quản lý Danh mục Công việc (Admin Module).
 * 
 * Version: 1.0.0 (30/01/2026)
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { adminService, isApiError } from '@/services/admin.service';
import { 
  IDanhMucCvResponse, 
  IDanhMucCvCreateRequest, 
  IDanhMucCvUpdateRequest,
  ISpChuanResponse,
  IDonViOption,
  IPagination,
} from '@/types/admin';

// =============================================================================
// FORM MODAL
// =============================================================================

interface DanhMucCvFormProps {
  editItem?: IDanhMucCvResponse | null;
  spChuanList: ISpChuanResponse[];
  donViList: IDonViOption[];
  onSubmit: (data: IDanhMucCvCreateRequest | IDanhMucCvUpdateRequest) => Promise<void>;
  onClose: () => void;
  isSubmitting: boolean;
}

function DanhMucCvFormModal({ editItem, spChuanList, donViList, onSubmit, onClose, isSubmitting }: DanhMucCvFormProps) {
  const [formData, setFormData] = useState({
    ma_danh_muc: editItem?.ma_danh_muc || '',
    ten_cong_viec: editItem?.ten_cong_viec || '',
    mo_ta: editItem?.mo_ta || '',
    sp_chuan_id: editItem?.sp_chuan_id || '',
    don_vi_ap_dung_id: editItem?.don_vi_ap_dung_id || '',
    nhom_cong_viec: editItem?.nhom_cong_viec || '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.ma_danh_muc.trim() || !formData.ten_cong_viec.trim()) {
      alert('Vui lòng nhập đầy đủ thông tin bắt buộc');
      return;
    }

    if (!formData.sp_chuan_id) {
      alert('Vui lòng chọn SP Chuẩn');
      return;
    }

    const submitData: IDanhMucCvCreateRequest | IDanhMucCvUpdateRequest = {
      ...formData,
      don_vi_ap_dung_id: formData.don_vi_ap_dung_id || null,
    };

    await onSubmit(submitData);
  };

  // Lấy thông tin SP Chuẩn được chọn
  const selectedSp = spChuanList.find(sp => sp.id === formData.sp_chuan_id);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {editItem ? '✏️ Sửa Danh mục công việc' : '➕ Thêm Danh mục mới'}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mã danh mục <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.ma_danh_muc}
                onChange={(e) => setFormData({ ...formData, ma_danh_muc: e.target.value.toUpperCase() })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="VD: DM-050"
                disabled={!!editItem}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nhóm công việc
              </label>
              <input
                type="text"
                value={formData.nhom_cong_viec}
                onChange={(e) => setFormData({ ...formData, nhom_cong_viec: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="VD: Kiểm tra, Phân loại..."
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tên công việc <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.ten_cong_viec}
              onChange={(e) => setFormData({ ...formData, ten_cong_viec: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="VD: Kiểm tra hồ sơ tờ khai xuất khẩu"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả chi tiết</label>
            <textarea
              value={formData.mo_ta}
              onChange={(e) => setFormData({ ...formData, mo_ta: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Mô tả chi tiết về công việc..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                SP Chuẩn <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.sp_chuan_id}
                onChange={(e) => setFormData({ ...formData, sp_chuan_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Chọn SP Chuẩn --</option>
                {spChuanList.filter(sp => sp.is_active).map((sp) => (
                  <option key={sp.id} value={sp.id}>
                    {sp.ma_sp} - {sp.ten_sp}
                  </option>
                ))}
              </select>
              {selectedSp && (
                <p className="text-xs text-blue-600 mt-1">
                  Hệ số quy đổi: {selectedSp.he_so_quy_doi_sp1} | Thời gian: {selectedSp.thoi_gian_phut} phút
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Đơn vị áp dụng
              </label>
              <select
                value={formData.don_vi_ap_dung_id}
                onChange={(e) => setFormData({ ...formData, don_vi_ap_dung_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Toàn Chi cục (tất cả đơn vị)</option>
                {donViList.filter(dv => dv.ma_don_vi !== 'DEPT-ADMIN').map((dv) => (
                  <option key={dv.id} value={dv.id}>
                    {dv.ten_don_vi}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Để trống = áp dụng cho tất cả đơn vị
              </p>
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
// PAGINATION
// =============================================================================

interface PaginationProps {
  pagination: IPagination;
  onPageChange: (page: number) => void;
}

function Pagination({ pagination, onPageChange }: PaginationProps) {
  const { page, total_pages } = pagination;
  
  if (total_pages <= 1) return null;

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
      <div className="text-sm text-gray-500">
        Trang {page} / {total_pages} • Tổng {pagination.total_items} danh mục
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Trước
        </button>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= total_pages}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Sau
        </button>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function AdminDanhMucCvPage() {
  const router = useRouter();
  
  // Data states
  const [danhMucList, setDanhMucList] = useState<IDanhMucCvResponse[]>([]);
  const [pagination, setPagination] = useState<IPagination>({ page: 1, page_size: 20, total_items: 0, total_pages: 0 });
  const [spChuanList, setSpChuanList] = useState<ISpChuanResponse[]>([]);
  const [donViList, setDonViList] = useState<IDonViOption[]>([]);
  
  // Filter states
  const [search, setSearch] = useState('');
  const [filterSpChuan, setFilterSpChuan] = useState('');
  const [filterDonVi, setFilterDonVi] = useState('');
  const [includeInactive, setIncludeInactive] = useState(false);
  
  // UI states
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Modal states
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState<IDanhMucCvResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<IDanhMucCvResponse | null>(null);

  // Load options (SP Chuẩn, Đơn vị)
  useEffect(() => {
    const loadOptions = async () => {
      try {
        const [spList, dvList] = await Promise.all([
          adminService.getSpChuanList(true),
          adminService.getDonViList(),
        ]);
        setSpChuanList(spList);
        setDonViList(dvList);
      } catch (err) {
        console.error('Error loading options:', err);
      }
    };
    loadOptions();
  }, []);

  // Load danh mục
  const loadData = useCallback(async (page: number = 1) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params: any = { page, page_size: 20, include_inactive: includeInactive };
      if (search) params.search = search;
      if (filterSpChuan) params.sp_chuan_id = filterSpChuan;
      if (filterDonVi) params.don_vi_id = filterDonVi;
      
      const response = await adminService.getDanhMucCvList(params);
      setDanhMucList(response.data);
      setPagination(response.pagination);
    } catch (err) {
      setError(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsLoading(false);
    }
  }, [search, filterSpChuan, filterDonVi, includeInactive]);

  useEffect(() => {
    loadData(1);
  }, [loadData]);

  // Handlers
  const handleSearch = () => {
    loadData(1);
  };

  const handlePageChange = (page: number) => {
    loadData(page);
  };

  const handleCreate = () => {
    setEditItem(null);
    setShowForm(true);
  };

  const handleEdit = (dm: IDanhMucCvResponse) => {
    setEditItem(dm);
    setShowForm(true);
  };

  const handleSubmit = async (data: IDanhMucCvCreateRequest | IDanhMucCvUpdateRequest) => {
    setIsSubmitting(true);
    
    try {
      if (editItem) {
        await adminService.updateDanhMucCv(editItem.id, data as IDanhMucCvUpdateRequest);
      } else {
        await adminService.createDanhMucCv(data as IDanhMucCvCreateRequest);
      }
      
      setShowForm(false);
      setEditItem(null);
      loadData(pagination.page);
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
      await adminService.deactivateDanhMucCv(deleteConfirm.id);
      setDeleteConfirm(null);
      loadData(pagination.page);
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 py-6">
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
              <h1 className="text-2xl font-bold text-gray-900">📋 Quản lý Danh mục Công việc</h1>
              <p className="text-gray-600">Cấu hình danh mục công việc và SP tương ứng</p>
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

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="md:col-span-2">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Tìm theo mã hoặc tên công việc..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select
              value={filterSpChuan}
              onChange={(e) => setFilterSpChuan(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tất cả SP Chuẩn</option>
              {spChuanList.filter(sp => sp.is_active).map((sp) => (
                <option key={sp.id} value={sp.id}>{sp.ma_sp} - {sp.ten_sp}</option>
              ))}
            </select>
            <select
              value={filterDonVi}
              onChange={(e) => setFilterDonVi(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tất cả đơn vị</option>
              {donViList.filter(dv => dv.ma_don_vi !== 'DEPT-ADMIN').map((dv) => (
                <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>
              ))}
            </select>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Tìm kiếm
            </button>
          </div>
          <div className="mt-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeInactive}
                onChange={(e) => setIncludeInactive(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <span className="text-sm text-gray-700">Hiển thị cả danh mục không hoạt động</span>
            </label>
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
          ) : danhMucList.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">📋</span>
              </div>
              <p className="text-gray-500">Không tìm thấy danh mục nào</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Mã</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Tên công việc</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Nhóm</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">SP Chuẩn</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Hệ số</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Đơn vị áp dụng</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Trạng thái</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {danhMucList.map((dm) => (
                      <tr key={dm.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <span className="font-mono text-sm font-medium text-gray-900">{dm.ma_danh_muc}</span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="max-w-xs">
                            <p className="font-medium text-gray-900 truncate" title={dm.ten_cong_viec}>
                              {dm.ten_cong_viec}
                            </p>
                            {dm.mo_ta && (
                              <p className="text-xs text-gray-500 truncate" title={dm.mo_ta}>
                                {dm.mo_ta}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {dm.nhom_cong_viec ? (
                            <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                              {dm.nhom_cong_viec}
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                            {dm.sp_chuan_ma}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="font-medium text-purple-600">{dm.he_so_quy_doi}</span>
                        </td>
                        <td className="px-4 py-3">
                          {dm.don_vi_ap_dung_ten ? (
                            <span className="text-sm text-gray-700">{dm.don_vi_ap_dung_ten}</span>
                          ) : (
                            <span className="text-sm text-green-600 font-medium">Toàn Chi cục</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            dm.is_active 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-red-100 text-red-700'
                          }`}>
                            {dm.is_active ? 'Hoạt động' : 'Vô hiệu'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-1">
                            <button
                              onClick={() => handleEdit(dm)}
                              className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg"
                              title="Sửa"
                            >
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                            {dm.is_active && (
                              <button
                                onClick={() => setDeleteConfirm(dm)}
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
              </div>
              <Pagination pagination={pagination} onPageChange={handlePageChange} />
            </>
          )}
        </div>
      </main>

      {/* Form Modal */}
      {showForm && (
        <DanhMucCvFormModal
          editItem={editItem}
          spChuanList={spChuanList}
          donViList={donViList}
          onSubmit={handleSubmit}
          onClose={() => { setShowForm(false); setEditItem(null); }}
          isSubmitting={isSubmitting}
        />
      )}

      {/* Delete Confirm Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">🗑️ Vô hiệu hóa Danh mục</h3>
            <p className="text-gray-600 mb-4">
              Bạn có chắc muốn vô hiệu hóa danh mục <strong>{deleteConfirm.ten_cong_viec}</strong> ({deleteConfirm.ma_danh_muc})?
            </p>
            <p className="text-sm text-orange-600 mb-4">
              ⚠️ Lưu ý: Không thể vô hiệu hóa nếu danh mục đang được sử dụng trong kê khai SP.
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

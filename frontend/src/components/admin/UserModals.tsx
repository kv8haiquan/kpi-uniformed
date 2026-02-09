/**
 * src/components/admin/UserModals.tsx
 * ====================================
 * Modal components cho User Management
 * 
 * Version: 1.0.0 (30/01/2026)
 */

'use client';

import { useState, useEffect } from 'react';
import { adminService, isApiError } from '@/services/admin.service';
import { 
  IUserResponse, 
  IUserCreateRequest, 
  IUserUpdateRequest,
  IUserTransferRequest,
  IDonViOption, 
  IVaiTroOption,
  ILichSuDieuChuyenResponse,
} from '@/types/admin';

// =============================================================================
// USER CREATE MODAL
// =============================================================================

interface UserCreateModalProps {
  donViList: IDonViOption[];
  vaiTroList: IVaiTroOption[];
  onSuccess: () => void;
  onClose: () => void;
}

export function UserCreateModal({ donViList, vaiTroList, onSuccess, onClose }: UserCreateModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<IUserCreateRequest>({
    ma_cc: '',
    ho_ten: '',
    don_vi_id: '',
    vai_tro_id: '',
    email: '',
    so_dien_thoai: '',
    gioi_tinh: null,
    chuc_vu: '',
    is_lanh_dao: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.ma_cc.trim() || !formData.ho_ten.trim()) {
      alert('Vui lòng nhập đầy đủ Mã CC và Họ tên');
      return;
    }
    if (!formData.don_vi_id || !formData.vai_tro_id) {
      alert('Vui lòng chọn Đơn vị và Vai trò');
      return;
    }

    setIsSubmitting(true);
    try {
      await adminService.createUser({
        ...formData,
        email: formData.email || null,
        so_dien_thoai: formData.so_dien_thoai || null,
        chuc_vu: formData.chuc_vu || null,
      });
      alert('Tạo người dùng thành công! Mật khẩu mặc định: 123456');
      onSuccess();
      onClose();
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Auto set is_lanh_dao khi chọn vai trò
  const handleVaiTroChange = (vaiTroId: string) => {
    const vaiTro = vaiTroList.find(v => v.id === vaiTroId);
    setFormData({ 
      ...formData, 
      vai_tro_id: vaiTroId,
      is_lanh_dao: vaiTro?.is_lanh_dao || false,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">➕ Tạo người dùng mới</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mã công chức <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.ma_cc}
                onChange={(e) => setFormData({ ...formData, ma_cc: e.target.value.toUpperCase() })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="VD: 20AB-1234"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Họ và tên <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.ho_ten}
                onChange={(e) => setFormData({ ...formData, ho_ten: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Nguyễn Văn A"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Đơn vị <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.don_vi_id}
                onChange={(e) => setFormData({ ...formData, don_vi_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Chọn đơn vị --</option>
                {donViList.filter(d => d.ma_don_vi !== 'DEPT-ADMIN').map((dv) => (
                  <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Vai trò <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.vai_tro_id}
                onChange={(e) => handleVaiTroChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Chọn vai trò --</option>
                {vaiTroList.map((vt) => (
                  <option key={vt.id} value={vt.id}>
                    {vt.ten_vai_tro} {vt.is_lanh_dao && '(Lãnh đạo)'}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="email@customs.gov.vn"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Số điện thoại</label>
              <input
                type="text"
                value={formData.so_dien_thoai || ''}
                onChange={(e) => setFormData({ ...formData, so_dien_thoai: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="0912345678"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Giới tính</label>
              <select
                value={formData.gioi_tinh || ''}
                onChange={(e) => setFormData({ ...formData, gioi_tinh: e.target.value as 'NAM' | 'NU' | null || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Chọn --</option>
                <option value="NAM">Nam</option>
                <option value="NU">Nữ</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Chức vụ</label>
              <input
                type="text"
                value={formData.chuc_vu || ''}
                onChange={(e) => setFormData({ ...formData, chuc_vu: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="VD: Chuyên viên, Kiểm tra viên..."
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_lanh_dao"
              checked={formData.is_lanh_dao}
              onChange={(e) => setFormData({ ...formData, is_lanh_dao: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <label htmlFor="is_lanh_dao" className="text-sm text-gray-700">
              Là lãnh đạo (được phân công công việc và phê duyệt kê khai)
            </label>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-700">
              ℹ️ Mật khẩu mặc định là <strong>123456</strong>. Người dùng nên đổi mật khẩu sau khi đăng nhập lần đầu.
            </p>
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
              {isSubmitting ? 'Đang tạo...' : 'Tạo người dùng'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// =============================================================================
// USER EDIT MODAL
// =============================================================================

interface UserEditModalProps {
  user: IUserResponse;
  onSuccess: () => void;
  onClose: () => void;
}

export function UserEditModal({ user, onSuccess, onClose }: UserEditModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<IUserUpdateRequest>({
    ho_ten: user.ho_ten,
    email: user.email,
    so_dien_thoai: user.so_dien_thoai,
    gioi_tinh: user.gioi_tinh,
    chuc_vu: user.chuc_vu,
    ngay_sinh: user.ngay_sinh,
    ngay_vao_nganh: user.ngay_vao_nganh,
    ngay_vao_chi_cuc: user.ngay_vao_chi_cuc,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.ho_ten?.trim()) {
      alert('Vui lòng nhập họ tên');
      return;
    }

    setIsSubmitting(true);
    try {
      await adminService.updateUser(user.id, formData);
      alert('Cập nhật thành công!');
      onSuccess();
      onClose();
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">✏️ Sửa thông tin người dùng</h3>
        <p className="text-sm text-gray-500 mb-4">Mã CC: <strong>{user.ma_cc}</strong> | Đơn vị: {user.don_vi_ten}</p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Họ và tên <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.ho_ten || ''}
              onChange={(e) => setFormData({ ...formData, ho_ten: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Số điện thoại</label>
              <input
                type="text"
                value={formData.so_dien_thoai || ''}
                onChange={(e) => setFormData({ ...formData, so_dien_thoai: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Giới tính</label>
              <select
                value={formData.gioi_tinh || ''}
                onChange={(e) => setFormData({ ...formData, gioi_tinh: e.target.value as 'NAM' | 'NU' | null || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Chọn --</option>
                <option value="NAM">Nam</option>
                <option value="NU">Nữ</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Chức vụ</label>
              <input
                type="text"
                value={formData.chuc_vu || ''}
                onChange={(e) => setFormData({ ...formData, chuc_vu: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ngày sinh</label>
              <input
                type="date"
                value={formData.ngay_sinh || ''}
                onChange={(e) => setFormData({ ...formData, ngay_sinh: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ngày vào ngành</label>
              <input
                type="date"
                value={formData.ngay_vao_nganh || ''}
                onChange={(e) => setFormData({ ...formData, ngay_vao_nganh: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ngày vào Chi cục</label>
              <input
                type="date"
                value={formData.ngay_vao_chi_cuc || ''}
                onChange={(e) => setFormData({ ...formData, ngay_vao_chi_cuc: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
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
              {isSubmitting ? 'Đang lưu...' : 'Cập nhật'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// =============================================================================
// USER TRANSFER MODAL
// =============================================================================

interface UserTransferModalProps {
  user: IUserResponse;
  donViList: IDonViOption[];
  vaiTroList: IVaiTroOption[];
  onSuccess: () => void;
  onClose: () => void;
}

export function UserTransferModal({ user, donViList, vaiTroList, onSuccess, onClose }: UserTransferModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [history, setHistory] = useState<ILichSuDieuChuyenResponse[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  
  const [formData, setFormData] = useState<IUserTransferRequest>({
    don_vi_id_moi: '',
    vai_tro_id_moi: '',
    chuc_vu_moi: user.chuc_vu || '',
    is_lanh_dao: user.is_lanh_dao,
    ly_do: '',
    ngay_hieu_luc: new Date().toISOString().split('T')[0],
  });

  // Load lịch sử điều chuyển
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const data = await adminService.getTransferHistory(user.id);
        setHistory(data);
      } catch (err) {
        console.error('Error loading history:', err);
      } finally {
        setLoadingHistory(false);
      }
    };
    loadHistory();
  }, [user.id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.don_vi_id_moi && !formData.vai_tro_id_moi) {
      alert('Vui lòng chọn đơn vị mới hoặc vai trò mới');
      return;
    }

    setIsSubmitting(true);
    try {
      await adminService.transferUser(user.id, formData);
      alert('Điều chuyển thành công!');
      onSuccess();
      onClose();
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🔄 Điều chuyển nhân sự</h3>
        
        {/* Thông tin hiện tại */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h4 className="font-medium text-gray-900 mb-2">Thông tin hiện tại</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Mã CC:</span>{' '}
              <span className="font-medium">{user.ma_cc}</span>
            </div>
            <div>
              <span className="text-gray-500">Họ tên:</span>{' '}
              <span className="font-medium">{user.ho_ten}</span>
            </div>
            <div>
              <span className="text-gray-500">Đơn vị:</span>{' '}
              <span className="font-medium text-blue-600">{user.don_vi_ten}</span>
            </div>
            <div>
              <span className="text-gray-500">Vai trò:</span>{' '}
              <span className="font-medium">{user.vai_tro_ten}</span>
            </div>
          </div>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Đơn vị mới</label>
              <select
                value={formData.don_vi_id_moi}
                onChange={(e) => setFormData({ ...formData, don_vi_id_moi: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Giữ nguyên --</option>
                {donViList.filter(d => d.ma_don_vi !== 'DEPT-ADMIN' && d.id !== user.don_vi_id).map((dv) => (
                  <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Vai trò mới</label>
              <select
                value={formData.vai_tro_id_moi}
                onChange={(e) => setFormData({ ...formData, vai_tro_id_moi: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Giữ nguyên --</option>
                {vaiTroList.map((vt) => (
                  <option key={vt.id} value={vt.id}>
                    {vt.ten_vai_tro} {vt.is_lanh_dao && '(Lãnh đạo)'}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Chức vụ mới</label>
              <input
                type="text"
                value={formData.chuc_vu_moi || ''}
                onChange={(e) => setFormData({ ...formData, chuc_vu_moi: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Để trống = giữ nguyên"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ngày hiệu lực</label>
              <input
                type="date"
                value={formData.ngay_hieu_luc || ''}
                onChange={(e) => setFormData({ ...formData, ngay_hieu_luc: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lý do điều chuyển</label>
            <textarea
              value={formData.ly_do || ''}
              onChange={(e) => setFormData({ ...formData, ly_do: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows={2}
              placeholder="VD: Theo QĐ số 123/QĐ-HQQN ngày..."
            />
          </div>

          {/* Lịch sử điều chuyển */}
          {history.length > 0 && (
            <div className="border-t pt-4">
              <h4 className="font-medium text-gray-900 mb-3">📜 Lịch sử điều chuyển</h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {history.map((h) => (
                  <div key={h.id} className="bg-gray-50 rounded-lg p-3 text-sm">
                    <div className="flex items-center gap-2 text-gray-600">
                      <span>{new Date(h.created_at).toLocaleDateString('vi-VN')}</span>
                      <span>•</span>
                      <span>{h.don_vi_cu_ten || '?'}</span>
                      <span>→</span>
                      <span className="text-blue-600 font-medium">{h.don_vi_moi_ten || '?'}</span>
                    </div>
                    {h.ly_do && <p className="text-gray-500 mt-1">{h.ly_do}</p>}
                  </div>
                ))}
              </div>
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
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Đang xử lý...' : 'Điều chuyển'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
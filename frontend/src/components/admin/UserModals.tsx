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
  ILichSuDieuChuyenUpdateRequest,
  LoaiLichSuDieuChuyen,
} from '@/types/admin';

// Nhãn hiển thị theo loại bản ghi lịch sử
const LOAI_LABEL: Record<LoaiLichSuDieuChuyen, string> = {
  DIEU_CHUYEN: 'Điều chuyển',
  VO_HIEU_HOA: 'Vô hiệu hóa',
  KICH_HOAT: 'Kích hoạt',
};

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

/**
 * Ngày hôm nay theo GIỜ ĐỊA PHƯƠNG, dạng YYYY-MM-DD.
 *
 * KHÔNG dùng `new Date().toISOString().split('T')[0]`: `toISOString()` trả về giờ
 * UTC, nên từ 00:00 đến 07:00 giờ Việt Nam nó cho ra ngày HÔM QUA.
 */
function ngayHomNay(): string {
  const d = new Date();
  const thang = String(d.getMonth() + 1).padStart(2, '0');
  const ngay = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${thang}-${ngay}`;
}

/** Số ngày giữa hai chuỗi YYYY-MM-DD (dương = `a` sau `b`). */
function soNgayLech(a: string, b: string): number {
  const ms = new Date(`${a}T00:00:00`).getTime() - new Date(`${b}T00:00:00`).getTime();
  return Math.round(ms / 86_400_000);
}

// Nhập muộn/sớm quá mốc này thì cảnh báo — không chặn, chỉ nhắc người nhập
// đối chiếu lại ngày trong quyết định.
const NGUONG_CANH_BAO_NGAY = 15;

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

  // Chỉnh sửa lịch sử: id bản ghi đang sửa + dữ liệu form sửa
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<ILichSuDieuChuyenUpdateRequest>({});

  const [formData, setFormData] = useState<IUserTransferRequest>({
    don_vi_id_moi: '',
    vai_tro_id_moi: '',
    chuc_vu_moi: user.chuc_vu || '',
    is_lanh_dao: user.is_lanh_dao,
    ly_do: '',
    // KHÔNG điền sẵn ngày hôm nay — xem ghi chú ở `ngayHomNay` bên dưới.
    ngay_hieu_luc: '',
  });

  // Load lịch sử điều chuyển
  const reloadHistory = async () => {
    try {
      const data = await adminService.getTransferHistory(user.id);
      setHistory(data);
    } catch (err) {
      console.error('Error loading history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    reloadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id]);

  // Bản ghi mới nhất (theo created_at) — chỉ bản này mới cho phép "đồng bộ hiện tại"
  const latestId = history.length > 0
    ? history.reduce((a, b) => (a.created_at >= b.created_at ? a : b)).id
    : null;

  const batDauSua = (h: ILichSuDieuChuyenResponse) => {
    setEditingId(h.id);
    setEditForm({
      loai: h.loai,
      don_vi_cu_id: h.don_vi_cu_id,
      don_vi_moi_id: h.don_vi_moi_id,
      vai_tro_cu_id: h.vai_tro_cu_id,
      vai_tro_moi_id: h.vai_tro_moi_id,
      chuc_vu_cu: h.chuc_vu_cu,
      chuc_vu_moi: h.chuc_vu_moi,
      ngay_hieu_luc: h.ngay_hieu_luc,
      ly_do: h.ly_do,
      dong_bo_hien_tai: false,
    });
  };

  const luuSua = async (historyId: string) => {
    setIsSubmitting(true);
    try {
      await adminService.updateTransferHistory(user.id, historyId, editForm);
      setEditingId(null);
      await reloadHistory();
      if (editForm.dong_bo_hien_tai) onSuccess();
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra khi sửa lịch sử');
    } finally {
      setIsSubmitting(false);
    }
  };

  const xoaLichSu = async (historyId: string, laMoiNhat: boolean) => {
    let dongBo = false;
    if (laMoiNhat) {
      dongBo = window.confirm(
        'Đồng bộ lại hồ sơ hiện tại của công chức về trạng thái TRƯỚC bản ghi này?\n\n' +
        'OK = có đồng bộ (hoàn tác đơn vị/trạng thái) • Cancel = chỉ xóa bản ghi'
      );
    } else if (!window.confirm('Xác nhận xóa bản ghi lịch sử này?')) {
      return;
    }
    setIsSubmitting(true);
    try {
      await adminService.deleteTransferHistory(user.id, historyId, dongBo);
      await reloadHistory();
      if (dongBo) onSuccess();
    } catch (err) {
      alert(isApiError(err) ? err.message : 'Có lỗi xảy ra khi xóa lịch sử');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Cảnh báo khi ngày hiệu lực lệch xa ngày nhập — dấu hiệu nhập muộn (quên cả
  // đợt) hoặc gõ nhầm năm/tháng. Chuỗi rỗng = không có gì để cảnh báo.
  const canhBaoNgay: string | null = (() => {
    if (!formData.ngay_hieu_luc) return null;
    const lech = soNgayLech(formData.ngay_hieu_luc, ngayHomNay());
    if (lech < -NGUONG_CANH_BAO_NGAY) {
      return `Ngày hiệu lực cách hôm nay ${Math.abs(lech)} ngày về trước — bạn đang nhập muộn. `
        + `Kiểm tra lại ngày ghi trong quyết định.`;
    }
    if (lech > NGUONG_CANH_BAO_NGAY) {
      return `Ngày hiệu lực ở ${lech} ngày trong tương lai — kiểm tra lại xem có gõ nhầm tháng/năm không.`;
    }
    return null;
  })();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.don_vi_id_moi && !formData.vai_tro_id_moi) {
      alert('Vui lòng chọn đơn vị mới hoặc vai trò mới');
      return;
    }

    // Ngày hiệu lực BẮT BUỘC. Trước đây ô này điền sẵn ngày hôm nay và backend
    // còn tự lấp `date.today()` khi để trống → 92/95 bản ghi lịch sử ghi ngày
    // NHẬP LIỆU thay vì ngày quyết định, phải đi sửa lại hàng loạt (31/08/2026).
    if (!formData.ngay_hieu_luc) {
      alert('Vui lòng nhập Ngày hiệu lực — lấy đúng ngày ghi trong quyết định, không phải ngày hôm nay');
      return;
    }

    if (canhBaoNgay) {
      const tiepTuc = window.confirm(
        `${canhBaoNgay}\n\nOK = ngày này đúng, cứ lưu • Cancel = để tôi xem lại`
      );
      if (!tiepTuc) return;
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
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ngày hiệu lực <span className="text-red-500">*</span>
              </label>
              <div className="flex gap-2">
                <input
                  type="date"
                  required
                  value={formData.ngay_hieu_luc || ''}
                  onChange={(e) => setFormData({ ...formData, ngay_hieu_luc: e.target.value })}
                  className="flex-1 min-w-0 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, ngay_hieu_luc: ngayHomNay() })}
                  className="px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 whitespace-nowrap"
                  title="Điền ngày hôm nay"
                >
                  Hôm nay
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Lấy đúng ngày ghi trong quyết định, không phải ngày nhập liệu.
              </p>
            </div>
          </div>

          {canhBaoNgay && (
            <div className="flex gap-2 bg-amber-50 border border-amber-300 text-amber-900 rounded-lg px-3 py-2 text-sm">
              <span aria-hidden>⚠️</span>
              <span>{canhBaoNgay}</span>
            </div>
          )}

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

          {/* Lịch sử điều chuyển & trạng thái (sửa được để khắc phục sai sót) */}
          {loadingHistory && (
            <p className="text-sm text-gray-400 border-t pt-4">Đang tải lịch sử...</p>
          )}
          {!loadingHistory && history.length > 0 && (
            <div className="border-t pt-4">
              <h4 className="font-medium text-gray-900 mb-3">📜 Lịch sử điều chuyển &amp; trạng thái</h4>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {history.map((h) => (
                  <div key={h.id} className="bg-gray-50 rounded-lg p-3 text-sm">
                    {editingId === h.id ? (
                      /* ---- Form sửa inline ---- */
                      <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className="block text-xs text-gray-500 mb-1">Loại</label>
                            <select
                              value={editForm.loai || 'DIEU_CHUYEN'}
                              onChange={(e) => setEditForm({ ...editForm, loai: e.target.value as LoaiLichSuDieuChuyen })}
                              className="w-full px-2 py-1 border border-gray-300 rounded"
                            >
                              <option value="DIEU_CHUYEN">Điều chuyển</option>
                              <option value="VO_HIEU_HOA">Vô hiệu hóa</option>
                              <option value="KICH_HOAT">Kích hoạt</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-xs text-gray-500 mb-1">Ngày hiệu lực</label>
                            <input
                              type="date"
                              value={editForm.ngay_hieu_luc || ''}
                              onChange={(e) => setEditForm({ ...editForm, ngay_hieu_luc: e.target.value })}
                              className="w-full px-2 py-1 border border-gray-300 rounded"
                            />
                          </div>
                        </div>
                        {editForm.loai === 'DIEU_CHUYEN' && (
                          <div className="grid grid-cols-2 gap-2">
                            <div>
                              <label className="block text-xs text-gray-500 mb-1">Đơn vị cũ</label>
                              <select
                                value={editForm.don_vi_cu_id || ''}
                                onChange={(e) => setEditForm({ ...editForm, don_vi_cu_id: e.target.value || null })}
                                className="w-full px-2 py-1 border border-gray-300 rounded"
                              >
                                <option value="">-- Không --</option>
                                {donViList.map((dv) => (
                                  <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>
                                ))}
                              </select>
                            </div>
                            <div>
                              <label className="block text-xs text-gray-500 mb-1">Đơn vị mới</label>
                              <select
                                value={editForm.don_vi_moi_id || ''}
                                onChange={(e) => setEditForm({ ...editForm, don_vi_moi_id: e.target.value || null })}
                                className="w-full px-2 py-1 border border-gray-300 rounded"
                              >
                                <option value="">-- Không --</option>
                                {donViList.map((dv) => (
                                  <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>
                                ))}
                              </select>
                            </div>
                          </div>
                        )}
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Lý do</label>
                          <input
                            type="text"
                            value={editForm.ly_do || ''}
                            onChange={(e) => setEditForm({ ...editForm, ly_do: e.target.value })}
                            className="w-full px-2 py-1 border border-gray-300 rounded"
                          />
                        </div>
                        {h.id === latestId && (
                          <label className="flex items-center gap-2 text-xs text-gray-700">
                            <input
                              type="checkbox"
                              checked={editForm.dong_bo_hien_tai || false}
                              onChange={(e) => setEditForm({ ...editForm, dong_bo_hien_tai: e.target.checked })}
                            />
                            Đồng bộ lại đơn vị/vai trò/trạng thái hiện tại của CC theo bản ghi này
                          </label>
                        )}
                        <div className="flex justify-end gap-2 pt-1">
                          <button type="button" onClick={() => setEditingId(null)} disabled={isSubmitting}
                            className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-100">Hủy</button>
                          <button type="button" onClick={() => luuSua(h.id)} disabled={isSubmitting}
                            className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">Lưu</button>
                        </div>
                      </div>
                    ) : (
                      /* ---- Dòng hiển thị ---- */
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2 text-gray-600">
                            <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                              h.loai === 'VO_HIEU_HOA' ? 'bg-red-100 text-red-700'
                              : h.loai === 'KICH_HOAT' ? 'bg-green-100 text-green-700'
                              : 'bg-blue-100 text-blue-700'
                            }`}>{LOAI_LABEL[h.loai]}</span>
                            <span>{h.ngay_hieu_luc ? new Date(h.ngay_hieu_luc).toLocaleDateString('vi-VN') : new Date(h.created_at).toLocaleDateString('vi-VN')}</span>
                            {h.loai === 'DIEU_CHUYEN' && (
                              <>
                                <span>•</span>
                                <span>{h.don_vi_cu_ten || '?'}</span>
                                <span>→</span>
                                <span className="text-blue-600 font-medium">{h.don_vi_moi_ten || '?'}</span>
                              </>
                            )}
                          </div>
                          {h.ly_do && <p className="text-gray-500 mt-1">{h.ly_do}</p>}
                        </div>
                        <div className="flex gap-1 shrink-0">
                          <button type="button" onClick={() => batDauSua(h)} disabled={isSubmitting}
                            className="px-2 py-1 text-blue-600 hover:bg-blue-50 rounded">Sửa</button>
                          <button type="button" onClick={() => xoaLichSu(h.id, h.id === latestId)} disabled={isSubmitting}
                            className="px-2 py-1 text-red-600 hover:bg-red-50 rounded">Xóa</button>
                        </div>
                      </div>
                    )}
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
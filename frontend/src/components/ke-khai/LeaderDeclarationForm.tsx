/**
 * src/components/ke-khai/LeaderDeclarationForm.tsx
 * =================================================
 * Form kê khai công việc cho Lãnh đạo.
 * 
 * Đặc điểm:
 * - Không chọn danh mục SP (Lãnh đạo tự nhập tên công việc)
 * - Mỗi đầu công việc = 1 SP
 * - Người phê duyệt được auto-select theo vai trò
 * 
 * Version: 2.7.4 (02/02/2026)
 * - v2.7.4: Thêm mô tả lỗi chất lượng & tiến độ, redesign layout dọc
 * - v2.7.3: Sửa ngày mặc định dùng local timezone (tránh lệch ngày UTC)
 * - v2.6.0: Thêm trường số lỗi chất lượng và số lỗi tiến độ
 */

'use client';

import { useState, useEffect } from 'react';
import {
  IKeKhaiLanhDaoForm,
  IKeKhaiLanhDaoResponse,
  INguoiPheDuyetLanhDao,
  TrangThaiCongViecLD,
} from '@/types/leader-kpi';
import { leaderKPIService } from '@/services/leader-kpi.service';

// =============================================================================
// PROPS
// =============================================================================

interface LeaderDeclarationFormProps {
  thang: number;
  nam: number;
  editItem?: IKeKhaiLanhDaoResponse | null;
  onSuccess: () => void;
  onCancel: () => void;
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function LeaderDeclarationForm({
  thang,
  nam,
  editItem,
  onSuccess,
  onCancel,
}: LeaderDeclarationFormProps) {
  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nguoiPheDuyetList, setNguoiPheDuyetList] = useState<INguoiPheDuyetLanhDao[]>([]);
  const [loadingApprovers, setLoadingApprovers] = useState(true);

  // Form state
  // v2.7.3: Dùng local date thay vì UTC để tránh lệch ngày ở GMT+7
  const now = new Date();
  const localToday = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  
  const [formData, setFormData] = useState<IKeKhaiLanhDaoForm>({
    ten_cong_viec: '',
    mo_ta: '',
    ngay_thuc_hien: localToday,
    trang_thai_hoan_thanh: TrangThaiCongViecLD.DA_HOAN_THANH,
    so_luong: 1,
    nguoi_phe_duyet_id: '',
    // v2.6.0: Thêm số lỗi
    so_loi_chat_luong: 0,
    so_loi_tien_do: 0,
    // v2.7.4: Mô tả lỗi
    ghi_chu_loi_chat_luong: '',
    ghi_chu_loi_tien_do: '',
  });

  // ---------------------------------------------------------------------------
  // EFFECTS
  // ---------------------------------------------------------------------------

  // Load danh sách người phê duyệt
  useEffect(() => {
    const loadApprovers = async () => {
      setLoadingApprovers(true);
      try {
        const list = await leaderKPIService.getNguoiPheDuyet();
        setNguoiPheDuyetList(list);
        
        // Auto-select người phê duyệt đầu tiên
        if (list.length > 0 && !editItem) {
          setFormData(prev => ({ ...prev, nguoi_phe_duyet_id: list[0].id }));
        }
      } catch (err) {
        console.error('Error loading approvers:', err);
      } finally {
        setLoadingApprovers(false);
      }
    };

    loadApprovers();
  }, [editItem]);

  // Load data khi edit
  useEffect(() => {
    if (editItem) {
      setFormData({
        ten_cong_viec: editItem.ten_cong_viec,
        mo_ta: editItem.mo_ta || '',
        ngay_thuc_hien: editItem.ngay_thuc_hien,
        trang_thai_hoan_thanh: editItem.trang_thai_hoan_thanh,
        so_luong: editItem.so_luong,
        nguoi_phe_duyet_id: editItem.nguoi_phe_duyet_id,
        // v2.6.0: Load số lỗi khi edit
        so_loi_chat_luong: editItem.so_loi_chat_luong || 0,
        so_loi_tien_do: editItem.so_loi_tien_do || 0,
        // v2.7.4: Load mô tả lỗi
        ghi_chu_loi_chat_luong: editItem.ghi_chu_loi_chat_luong || '',
        ghi_chu_loi_tien_do: editItem.ghi_chu_loi_tien_do || '',
      });
    }
  }, [editItem]);

  // ---------------------------------------------------------------------------
  // HANDLERS
  // ---------------------------------------------------------------------------

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    
    let parsedValue: string | number = value;
    if (type === 'number') {
      const num = parseInt(value);
      if (name === 'so_luong') {
        // Số lượng: tối thiểu = 1
        parsedValue = isNaN(num) ? 1 : Math.max(1, num);
      } else {
        // v2.7.3: Số lỗi CL/TĐ: cho phép = 0, tối thiểu = 0
        parsedValue = isNaN(num) ? 0 : Math.max(0, num);
      }
    }
    
    setFormData(prev => ({
      ...prev,
      [name]: parsedValue,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate
    if (!formData.ten_cong_viec.trim()) {
      setError('Vui lòng nhập tên công việc');
      return;
    }
    if (!formData.ngay_thuc_hien) {
      setError('Vui lòng chọn ngày thực hiện');
      return;
    }
    if (!formData.nguoi_phe_duyet_id) {
      setError('Vui lòng chọn người phê duyệt');
      return;
    }
    if (formData.so_luong < 1) {
      setError('Số lượng phải ≥ 1');
      return;
    }

    setIsSubmitting(true);

    try {
      if (editItem) {
        // Cập nhật
        await leaderKPIService.updateKeKhai(editItem.id, formData);
      } else {
        // Tạo mới
        await leaderKPIService.createKeKhai({
          ...formData,
          thang,
          nam,
        });
      }
      
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Có lỗi xảy ra. Vui lòng thử lại.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-t-xl">
        <h3 className="text-lg font-semibold text-white">
          {editItem ? '✏️ Sửa kê khai công việc' : '➕ Thêm công việc mới'}
        </h3>
        <p className="text-indigo-100 text-sm mt-1">
          Tháng {thang}/{nam} • Mỗi đầu công việc = 1 điểm
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="p-6 space-y-5">
        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Tên công việc */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tên công việc <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="ten_cong_viec"
            value={formData.ten_cong_viec}
            onChange={handleChange}
            placeholder="VD: Họp giao ban đầu tuần, Ký duyệt công văn..."
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            required
          />
        </div>

        {/* Mô tả */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Mô tả chi tiết <span className="text-gray-400">(không bắt buộc)</span>
          </label>
          <textarea
            name="mo_ta"
            value={formData.mo_ta}
            onChange={handleChange}
            placeholder="Mô tả chi tiết nội dung công việc..."
            rows={3}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
          />
        </div>

        {/* Row: Ngày thực hiện + Số lượng */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Ngày thực hiện */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Ngày thực hiện <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              name="ngay_thuc_hien"
              value={formData.ngay_thuc_hien}
              onChange={handleChange}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
          </div>

          {/* Số lượng */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Số lượng <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              name="so_luong"
              value={formData.so_luong}
              onChange={handleChange}
              min={1}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Mặc định = 1 (mỗi công việc = 1 điểm)</p>
          </div>
        </div>

        {/* Trạng thái hoàn thành */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Trạng thái <span className="text-red-500">*</span>
          </label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="trang_thai_hoan_thanh"
                value={TrangThaiCongViecLD.DA_HOAN_THANH}
                checked={formData.trang_thai_hoan_thanh === TrangThaiCongViecLD.DA_HOAN_THANH}
                onChange={handleChange}
                className="w-4 h-4 text-green-600 focus:ring-green-500"
              />
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Đã hoàn thành
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="trang_thai_hoan_thanh"
                value={TrangThaiCongViecLD.CHUA_HOAN_THANH}
                checked={formData.trang_thai_hoan_thanh === TrangThaiCongViecLD.CHUA_HOAN_THANH}
                onChange={handleChange}
                className="w-4 h-4 text-yellow-600 focus:ring-yellow-500"
              />
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                Chưa hoàn thành
              </span>
            </label>
          </div>
        </div>

        {/* v2.7.4: Tự đánh giá chất lượng & tiến độ - Layout dọc */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-4">
            📊 Tự đánh giá chất lượng & tiến độ
          </label>
          
          <div className="space-y-5">
            {/* === LỖI CHẤT LƯỢNG === */}
            <div className="space-y-2">
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Số lỗi chất lượng
                </label>
                <input
                  type="number"
                  name="so_loi_chat_luong"
                  value={formData.so_loi_chat_luong || 0}
                  onChange={handleChange}
                  min={0}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="text-xs text-gray-500 mt-1">0 = Không có lỗi chất lượng</p>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Mô tả lỗi chất lượng <span className="text-gray-400">(không bắt buộc)</span>
                </label>
                <textarea
                  name="ghi_chu_loi_chat_luong"
                  value={formData.ghi_chu_loi_chat_luong || ''}
                  onChange={handleChange}
                  placeholder="Mô tả chi tiết về lỗi chất lượng (nếu có)..."
                  rows={2}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                />
              </div>
            </div>

            {/* Divider */}
            <hr className="border-gray-200" />

            {/* === LỖI TIẾN ĐỘ === */}
            <div className="space-y-2">
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Số lỗi tiến độ
                </label>
                <input
                  type="number"
                  name="so_loi_tien_do"
                  value={formData.so_loi_tien_do || 0}
                  onChange={handleChange}
                  min={0}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="text-xs text-gray-500 mt-1">0 = Không có lỗi tiến độ</p>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Mô tả lỗi tiến độ <span className="text-gray-400">(không bắt buộc)</span>
                </label>
                <textarea
                  name="ghi_chu_loi_tien_do"
                  value={formData.ghi_chu_loi_tien_do || ''}
                  onChange={handleChange}
                  placeholder="Mô tả chi tiết về lỗi tiến độ (nếu có)..."
                  rows={2}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Người phê duyệt */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Người phê duyệt <span className="text-red-500">*</span>
          </label>
          {loadingApprovers ? (
            <div className="flex items-center gap-2 text-gray-500 py-2">
              <div className="animate-spin w-4 h-4 border-2 border-gray-300 border-t-indigo-600 rounded-full"></div>
              <span className="text-sm">Đang tải...</span>
            </div>
          ) : nguoiPheDuyetList.length > 0 ? (
            <select
              name="nguoi_phe_duyet_id"
              value={formData.nguoi_phe_duyet_id}
              onChange={handleChange}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              required
            >
              <option value="">-- Chọn người phê duyệt --</option>
              {nguoiPheDuyetList.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.ho_ten} - {person.chuc_vu || person.vai_tro.ten_vai_tro}
                  {person.don_vi ? ` (${person.don_vi.ten_don_vi})` : ''}
                </option>
              ))}
            </select>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-yellow-700 text-sm">
                ⚠️ Không tìm thấy người phê duyệt phù hợp. Vui lòng liên hệ Admin.
              </p>
            </div>
          )}
          <p className="text-xs text-gray-500 mt-1">
            Người phê duyệt được tự động xác định theo vai trò của bạn
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="px-5 py-2.5 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Hủy
          </button>
          <button
            type="submit"
            disabled={isSubmitting || loadingApprovers}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                Đang lưu...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {editItem ? 'Cập nhật' : 'Lưu kê khai'}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
/**
 * src/types/leave.ts
 * ===================
 * Type definitions cho Module Quản lý Nghỉ phép.
 *
 * Tham chiếu: PHASE5A_HANDOVER.md
 * Version: 2.3
 */

// =============================================================================
// ENUMS
// =============================================================================

/**
 * Loại nghỉ phép (9 loại).
 * ⭐ NGHI_TUAN là loại mới dành cho đặc thù làm việc theo CA/KÍP của Hải quan.
 */
export enum LoaiNghi {
  NGHI_TUAN = 'NGHI_TUAN',       // ⭐ MỚI: Nghỉ tuần (thay T7/CN cố định)
  PHEP_NAM = 'PHEP_NAM',         // Phép năm (12-14 ngày/năm)
  NGHI_LE = 'NGHI_LE',           // Nghỉ lễ
  NGHI_OM = 'NGHI_OM',           // Ốm đau (cần giấy xác nhận)
  THAI_SAN = 'THAI_SAN',         // Thai sản (theo BHXH)
  VIEC_RIENG = 'VIEC_RIENG',     // Việc riêng có lương (hiếu, hỉ...)
  KHONG_LUONG = 'KHONG_LUONG',   // Nghỉ không lương
  NGHI_BU = 'NGHI_BU',           // Nghỉ bù (do làm thêm giờ)
  KHAC = 'KHAC',                 // Khác
}

/**
 * Trạng thái đơn nghỉ phép.
 */
export enum TrangThaiNghi {
  CHO_PHE_DUYET = 'CHO_PHE_DUYET',   // Đang chờ phê duyệt
  DA_PHE_DUYET = 'DA_PHE_DUYET',     // Đã được phê duyệt
  TU_CHOI = 'TU_CHOI',               // Bị từ chối
  HUY = 'HUY',                       // Đã hủy
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Lấy label tiếng Việt cho loại nghỉ.
 */
export const getLoaiNghiLabel = (loai: LoaiNghi): string => {
  const labels: Record<LoaiNghi, string> = {
    [LoaiNghi.NGHI_TUAN]: 'Nghỉ tuần',
    [LoaiNghi.PHEP_NAM]: 'Phép năm',
    [LoaiNghi.NGHI_LE]: 'Nghỉ lễ',
    [LoaiNghi.NGHI_OM]: 'Nghỉ ốm',
    [LoaiNghi.THAI_SAN]: 'Thai sản',
    [LoaiNghi.VIEC_RIENG]: 'Việc riêng có lương',
    [LoaiNghi.KHONG_LUONG]: 'Nghỉ không lương',
    [LoaiNghi.NGHI_BU]: 'Nghỉ bù',
    [LoaiNghi.KHAC]: 'Khác',
  };
  return labels[loai] || loai;
};

/**
 * Lấy label tiếng Việt cho trạng thái.
 */
export const getTrangThaiNghiLabel = (trangThai: TrangThaiNghi): string => {
  const labels: Record<TrangThaiNghi, string> = {
    [TrangThaiNghi.CHO_PHE_DUYET]: 'Chờ phê duyệt',
    [TrangThaiNghi.DA_PHE_DUYET]: 'Đã phê duyệt',
    [TrangThaiNghi.TU_CHOI]: 'Từ chối',
    [TrangThaiNghi.HUY]: 'Đã hủy',
  };
  return labels[trangThai] || trangThai;
};

/**
 * Lấy badge class cho trạng thái.
 */
export const getTrangThaiNghiBadgeClass = (trangThai: TrangThaiNghi): string => {
  const classes: Record<TrangThaiNghi, string> = {
    [TrangThaiNghi.CHO_PHE_DUYET]: 'badge-yellow',
    [TrangThaiNghi.DA_PHE_DUYET]: 'badge-green',
    [TrangThaiNghi.TU_CHOI]: 'badge-red',
    [TrangThaiNghi.HUY]: 'badge-gray',
  };
  return classes[trangThai] || 'badge-gray';
};

/**
 * Lấy badge class cho loại nghỉ.
 */
export const getLoaiNghiBadgeClass = (loai: LoaiNghi): string => {
  const classes: Record<LoaiNghi, string> = {
    [LoaiNghi.NGHI_TUAN]: 'bg-blue-100 text-blue-800',
    [LoaiNghi.PHEP_NAM]: 'bg-green-100 text-green-800',
    [LoaiNghi.NGHI_LE]: 'bg-purple-100 text-purple-800',
    [LoaiNghi.NGHI_OM]: 'bg-red-100 text-red-800',
    [LoaiNghi.THAI_SAN]: 'bg-pink-100 text-pink-800',
    [LoaiNghi.VIEC_RIENG]: 'bg-yellow-100 text-yellow-800',
    [LoaiNghi.KHONG_LUONG]: 'bg-gray-100 text-gray-800',
    [LoaiNghi.NGHI_BU]: 'bg-cyan-100 text-cyan-800',
    [LoaiNghi.KHAC]: 'bg-gray-100 text-gray-800',
  };
  return classes[loai] || 'bg-gray-100 text-gray-800';
};

/**
 * Lấy icon cho trạng thái.
 */
export const getTrangThaiNghiIcon = (trangThai: TrangThaiNghi): string => {
  const icons: Record<TrangThaiNghi, string> = {
    [TrangThaiNghi.CHO_PHE_DUYET]: '⏳',
    [TrangThaiNghi.DA_PHE_DUYET]: '✅',
    [TrangThaiNghi.TU_CHOI]: '❌',
    [TrangThaiNghi.HUY]: '🚫',
  };
  return icons[trangThai] || '';
};

// =============================================================================
// INTERFACES - NESTED TYPES
// =============================================================================

/**
 * Thông tin công chức rút gọn.
 */
export interface ICongChucBrief {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu?: string;
  don_vi_ten?: string;
}

// =============================================================================
// INTERFACES - RESPONSE
// =============================================================================

/**
 * Response từ API nghỉ phép.
 */
export interface INghiPhepResponse {
  id: string;
  cong_chuc_id: string;
  loai_nghi: LoaiNghi;
  loai_nghi_ten: string;
  tu_ngay: string;              // ISO date string "2026-01-20"
  den_ngay: string;
  so_ngay: number;              // 1 hoặc 0.5 (nghỉ buổi)
  ly_do: string | null;
  trang_thai: TrangThaiNghi;
  trang_thai_ten: string;
  nguoi_phe_duyet_id: string | null;
  nguoi_phe_duyet: ICongChucBrief | null;
  ly_do_tu_choi: string | null;
  ngay_phe_duyet: string | null;
  ghi_chu_phe_duyet: string | null;
  tai_lieu_dinh_kem: string | null;
  thang_ap_dung: number;
  nam_ap_dung: number;
  da_tinh_kpi: boolean;
  created_at: string;
  updated_at: string | null;
  cong_chuc: ICongChucBrief;
}

/**
 * Response cho người phê duyệt.
 */
export interface INguoiPheDuyetNghi {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string;
  don_vi_ten?: string;
}

/**
 * Response thống kê nghỉ phép cá nhân.
 */
export interface IThongKeNghiPhepCaNhan {
  nam: number;
  tong_ngay_nghi: number;
  nghi_tuan: number;
  phep_nam_da_dung: number;
  phep_nam_con_lai: number;
  nghi_om: number;
  nghi_le: number;
  nghi_khac: number;
  cho_phe_duyet: number;
}

/**
 * Response thống kê nghỉ phép đơn vị.
 */
export interface IThongKeNghiPhepDonVi {
  don_vi_id: string;
  don_vi_ten: string;
  nam: number;
  tong_cong_chuc: number;
  tong_don_nghi: number;
  tong_ngay_nghi: number;
  theo_loai: Record<string, number>;
  theo_trang_thai: Record<string, number>;
}

/**
 * Response bulk create.
 */
export interface IBulkCreateResponse {
  tong_don_tao: number;
  danh_sach_id: string[];
  ngay_da_ton_tai: string[];
}

// =============================================================================
// INTERFACES - REQUEST
// =============================================================================

/**
 * Request tạo đơn nghỉ đơn lẻ.
 * Dùng cho: Phép năm, Nghỉ ốm, Việc riêng, Thai sản...
 */
export interface INghiPhepCreateRequest {
  loai_nghi: LoaiNghi;
  tu_ngay: string;              // "2026-01-20"
  den_ngay: string;             // "2026-01-22"
  so_ngay: number;              // Tổng số ngày (có thể 0.5 cho nghỉ buổi)
  ly_do?: string;
  nguoi_phe_duyet_id?: string;
  tai_lieu_dinh_kem?: string;
}

/**
 * Request tạo đơn nghỉ hàng loạt (Bulk).
 * Dùng cho: Nghỉ tuần (NGHI_TUAN) - chọn nhiều ngày rời rạc.
 */
export interface INghiPhepBulkCreateRequest {
  loai_nghi: LoaiNghi;
  danh_sach_ngay: string[];     // ["2026-01-18", "2026-01-19", "2026-01-25"]
  ly_do?: string;
  nguoi_phe_duyet_id?: string;
}

/**
 * Request cập nhật đơn nghỉ.
 */
export interface INghiPhepUpdateRequest {
  loai_nghi?: LoaiNghi;
  tu_ngay?: string;
  den_ngay?: string;
  so_ngay?: number;
  ly_do?: string;
  nguoi_phe_duyet_id?: string;
  tai_lieu_dinh_kem?: string;
}

/**
 * Request phê duyệt đơn nghỉ.
 */
export interface IPheDuyetNghiRequest {
  ghi_chu?: string;
}

/**
 * Request từ chối đơn nghỉ.
 */
export interface ITuChoiNghiRequest {
  ly_do: string;                // Bắt buộc khi từ chối
}

/**
 * Filter params cho danh sách nghỉ phép.
 */
export interface INghiPhepFilterParams {
  loai_nghi?: LoaiNghi;
  trang_thai?: TrangThaiNghi;
  tu_ngay?: string;
  den_ngay?: string;
  thang?: number;
  nam?: number;
  page?: number;
  page_size?: number;
}

// =============================================================================
// TYPE GUARDS
// =============================================================================

/**
 * Kiểm tra có thể chỉnh sửa/xóa đơn không.
 * Chỉ được sửa/xóa khi trạng thái là CHO_PHE_DUYET hoặc TU_CHOI.
 */
export const canEditNghiPhep = (trangThai: TrangThaiNghi): boolean => {
  return trangThai === TrangThaiNghi.CHO_PHE_DUYET || trangThai === TrangThaiNghi.TU_CHOI;
};

/**
 * Kiểm tra có thể hủy đơn không.
 * Chỉ hủy được khi đang CHO_PHE_DUYET.
 */
export const canCancelNghiPhep = (trangThai: TrangThaiNghi): boolean => {
  return trangThai === TrangThaiNghi.CHO_PHE_DUYET;
};

/**
 * src/types/leave.ts
 * ===================
 * Type definitions cho Module Quản lý Nghỉ phép.
 *
 * Tham chiếu: PHASE5A_HANDOVER.md, nghi_phep.py v2.5
 * Version: 2.6 (29/01/2026) - Hỗ trợ phê duyệt 2 cấp
 *
 * THAY ĐỔI v2.6:
 * - Thêm TrangThaiNghi: CHO_CAP2 (chờ cấp 2 phê duyệt)
 * - Thêm fields phê duyệt 2 cấp trong INghiPhepResponse
 * - Thêm helper functions cho 2-tier approval
 */

// =============================================================================
// ENUMS
// =============================================================================

/**
 * Loại nghỉ phép (10 loại - thêm NGHI_TET).
 * ⭐ NGHI_TUAN là loại mới dành cho đặc thù làm việc theo CA/KÍP của Hải quan.
 * ⭐ NGHI_TET (v2.6) là loại mới cho nghỉ Tết, CCT sẽ tạo hàng loạt cho toàn chi cục.
 */
export enum LoaiNghi {
  NGHI_TUAN = 'NGHI_TUAN',       // ⭐ Nghỉ tuần (thay T7/CN cố định)
  NGHI_TET = 'NGHI_TET',         // ⭐ v2.6: Nghỉ Tết (CCT tạo bulk)
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
 * v2.6: Thêm CHO_CAP2 cho quy trình phê duyệt 2 cấp.
 */
export enum TrangThaiNghi {
  CHO_PHE_DUYET = 'CHO_PHE_DUYET',   // Đang chờ phê duyệt cấp 1
  CHO_CAP2 = 'CHO_CAP2',             // ⭐ v2.6: Đã duyệt cấp 1, chờ cấp 2
  DA_PHE_DUYET = 'DA_PHE_DUYET',     // Đã được phê duyệt hoàn toàn
  TU_CHOI = 'TU_CHOI',               // Bị từ chối
  HUY = 'HUY',                       // Đã hủy
}

/**
 * Trạng thái phê duyệt cấp (v2.6).
 */
export enum TrangThaiPheDuyetCap {
  CHO_DUYET = 'CHO_DUYET',     // Chờ duyệt
  DA_DUYET = 'DA_DUYET',       // Đã duyệt
  TU_CHOI = 'TU_CHOI',         // Từ chối
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
    [LoaiNghi.NGHI_TET]: 'Nghỉ Tết',
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
 * v2.6: Thêm CHO_CAP2
 */
export const getTrangThaiNghiLabel = (trangThai: TrangThaiNghi): string => {
  const labels: Record<TrangThaiNghi, string> = {
    [TrangThaiNghi.CHO_PHE_DUYET]: 'Chờ phê duyệt',
    [TrangThaiNghi.CHO_CAP2]: 'Chờ cấp 2 duyệt',
    [TrangThaiNghi.DA_PHE_DUYET]: 'Đã phê duyệt',
    [TrangThaiNghi.TU_CHOI]: 'Từ chối',
    [TrangThaiNghi.HUY]: 'Đã hủy',
  };
  return labels[trangThai] || trangThai;
};

/**
 * Lấy badge class cho trạng thái.
 * v2.6: Thêm CHO_CAP2
 */
export const getTrangThaiNghiBadgeClass = (trangThai: TrangThaiNghi): string => {
  const classes: Record<TrangThaiNghi, string> = {
    [TrangThaiNghi.CHO_PHE_DUYET]: 'badge-yellow',
    [TrangThaiNghi.CHO_CAP2]: 'badge-blue',
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
    [LoaiNghi.NGHI_TET]: 'bg-red-100 text-red-800',
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
    [TrangThaiNghi.CHO_CAP2]: '🔄',
    [TrangThaiNghi.DA_PHE_DUYET]: '✅',
    [TrangThaiNghi.TU_CHOI]: '❌',
    [TrangThaiNghi.HUY]: '🚫',
  };
  return icons[trangThai] || '';
};

/**
 * v2.6: Lấy label cho trạng thái phê duyệt cấp.
 */
export const getTrangThaiCapLabel = (trangThai: TrangThaiPheDuyetCap | null): string => {
  if (!trangThai) return '—';
  const labels: Record<TrangThaiPheDuyetCap, string> = {
    [TrangThaiPheDuyetCap.CHO_DUYET]: 'Chờ duyệt',
    [TrangThaiPheDuyetCap.DA_DUYET]: 'Đã duyệt',
    [TrangThaiPheDuyetCap.TU_CHOI]: 'Từ chối',
  };
  return labels[trangThai] || trangThai;
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
 * v2.6: Thêm fields phê duyệt 2 cấp.
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
  
  // === PHÊ DUYỆT CẤP 1 (v2.6) ===
  nguoi_phe_duyet_cap1_id: string | null;
  nguoi_phe_duyet_cap1: ICongChucBrief | null;
  trang_thai_cap1: TrangThaiPheDuyetCap | null;
  ngay_phe_duyet_cap1: string | null;
  ly_do_tu_choi_cap1: string | null;
  
  // === PHÊ DUYỆT CẤP 2 (v2.6) ===
  nguoi_phe_duyet_cap2_id: string | null;
  nguoi_phe_duyet_cap2: ICongChucBrief | null;
  trang_thai_cap2: TrangThaiPheDuyetCap | null;
  ngay_phe_duyet_cap2: string | null;
  ly_do_tu_choi_cap2: string | null;
  
  // === LEGACY FIELDS (backward compatible) ===
  nguoi_phe_duyet_id: string | null;
  nguoi_phe_duyet: ICongChucBrief | null;
  ly_do_tu_choi: string | null;
  ngay_phe_duyet: string | null;
  ghi_chu_phe_duyet: string | null;
  
  // === OTHER FIELDS ===
  tai_lieu_dinh_kem: string | null;
  thang_ap_dung: number;
  nam_ap_dung: number;
  da_tinh_kpi: boolean;
  is_khoa: boolean;              // v2.6: Data locked?
  created_at: string;
  updated_at: string | null;
  cong_chuc: ICongChucBrief;
  
  // === QUY TRÌNH PHÊ DUYỆT (v2.6) ===
  quy_trinh: 'TU_PHE_DUYET' | '1_CAP' | '2_CAP';
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
  cap_phe_duyet?: 1 | 2;  // v2.6: Phê duyệt cấp nào
}

/**
 * Response thống kê nghỉ phép cá nhân.
 */
export interface IThongKeNghiPhepCaNhan {
  nam: number;
  tong_ngay_nghi: number;
  nghi_tuan: number;
  nghi_tet: number;              // v2.6
  phep_nam_da_dung: number;
  phep_nam_con_lai: number;
  nghi_om: number;
  nghi_le: number;
  nghi_khac: number;
  cho_phe_duyet: number;
  cho_cap2: number;              // v2.6: Số đơn chờ cấp 2
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
  nguoi_phe_duyet_id?: string;  // v2.6: Sẽ tự động gán theo quy trình
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
// TYPE GUARDS & UTILITIES
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

/**
 * v2.6: Kiểm tra đơn cần phê duyệt 2 cấp không.
 */
export const is2TierApproval = (nghiPhep: INghiPhepResponse): boolean => {
  return nghiPhep.quy_trinh === '2_CAP';
};

/**
 * v2.6: Kiểm tra user có thể phê duyệt cấp 1 không.
 */
export const canApproveLevel1 = (
  nghiPhep: INghiPhepResponse,
  currentUserId: string
): boolean => {
  // Đơn phải ở trạng thái CHO_PHE_DUYET
  if (nghiPhep.trang_thai !== TrangThaiNghi.CHO_PHE_DUYET) return false;
  // User phải là người phê duyệt cấp 1
  return nghiPhep.nguoi_phe_duyet_cap1_id === currentUserId;
};

/**
 * v2.6: Kiểm tra user có thể phê duyệt cấp 2 không.
 */
export const canApproveLevel2 = (
  nghiPhep: INghiPhepResponse,
  currentUserId: string
): boolean => {
  // Đơn phải ở trạng thái CHO_CAP2
  if (nghiPhep.trang_thai !== TrangThaiNghi.CHO_CAP2) return false;
  // User phải là người phê duyệt cấp 2
  return nghiPhep.nguoi_phe_duyet_cap2_id === currentUserId;
};

/**
 * v2.6: Lấy thông tin người phê duyệt hiện tại.
 */
export const getCurrentApprover = (nghiPhep: INghiPhepResponse): ICongChucBrief | null => {
  if (nghiPhep.trang_thai === TrangThaiNghi.CHO_PHE_DUYET) {
    return nghiPhep.nguoi_phe_duyet_cap1 || nghiPhep.nguoi_phe_duyet;
  }
  if (nghiPhep.trang_thai === TrangThaiNghi.CHO_CAP2) {
    return nghiPhep.nguoi_phe_duyet_cap2;
  }
  return null;
};

/**
 * v2.6: Lấy progress của quy trình phê duyệt (0-100%).
 */
export const getApprovalProgress = (nghiPhep: INghiPhepResponse): number => {
  const quyTrinh = nghiPhep.quy_trinh;
  const trangThai = nghiPhep.trang_thai;

  if (quyTrinh === 'TU_PHE_DUYET') {
    return trangThai === TrangThaiNghi.DA_PHE_DUYET ? 100 : 0;
  }

  if (quyTrinh === '1_CAP') {
    return trangThai === TrangThaiNghi.DA_PHE_DUYET ? 100 : 0;
  }

  if (quyTrinh === '2_CAP') {
    if (trangThai === TrangThaiNghi.CHO_PHE_DUYET) return 0;
    if (trangThai === TrangThaiNghi.CHO_CAP2) return 50;
    if (trangThai === TrangThaiNghi.DA_PHE_DUYET) return 100;
  }

  return 0;
};
/**
 * src/types/bao-cao-xep-loai.ts
 * ==============================
 * TypeScript interfaces cho Module Báo cáo Xếp loại Chất lượng Công chức.
 * 
 * Theo Điều 17 - Quy chế đánh giá KPI Chi cục Hải quan KV8.
 * 
 * Version: 1.0.0 (28/01/2026)
 */

// =============================================================================
// ENUMS
// =============================================================================

/**
 * Trạng thái báo cáo xếp loại.
 */
export enum TrangThaiBaoCao {
  NHAP = 'NHAP',
  CHO_PHE_DUYET = 'CHO_PHE_DUYET',
  DA_PHE_DUYET = 'DA_PHE_DUYET',
  TU_CHOI = 'TU_CHOI',
}

/**
 * Xếp loại chất lượng công chức.
 */
export type XepLoaiChatLuong = 'A' | 'B' | 'C' | 'D' | 'E';

// =============================================================================
// NESTED INTERFACES
// =============================================================================

/**
 * Thông tin đơn vị tóm tắt.
 */
export interface IDonViBrief {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
}

/**
 * Thông tin công chức tóm tắt.
 */
export interface ICongChucBrief {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu?: string;
}

// =============================================================================
// TIÊU CHÍ CHUNG — điểm "Đánh giá tháng" (override của LĐ/CCT)
// Dùng chung cho modal SuaDiemTieuChiModal + trang Điều chỉnh tiêu chí chung.
// =============================================================================

export interface ITieuChiChungItemDgt {
  ma_tieu_chi: string;
  ten_tieu_chi: string;
  nhom_tieu_chi?: number;
  diem_toi_da: number;
  diem_tu_cham?: number | null;
  diem_phe_duyet?: number | null;
  // Điểm "Đánh giá tháng" — LĐ/CCT chỉnh ở giai đoạn báo cáo xếp loại.
  diem_danh_gia_thang?: number | null;
  diem?: number;
  trang_thai?: string;
}

export interface ITieuChiChungBrief {
  danh_gia_thang_id?: string | null;
  trang_thai?: string;
  tieu_chi?: ITieuChiChungItemDgt[];
}

// =============================================================================
// CHI TIẾT XẾP LOẠI
// =============================================================================

/**
 * Chi tiết xếp loại 1 công chức trong báo cáo.
 */
export interface IChiTietXepLoai {
  id: string;
  cong_chuc_id: string;
  cong_chuc: ICongChucBrief;
  is_lanh_dao: boolean;
  
  // Điểm từ hệ thống (snapshot)
  diem_tieu_chi_chung: number;
  diem_kpi: number;
  diem_tong: number;
  xep_loai_he_thong: XepLoaiChatLuong;
  
  // Đề xuất của Đội trưởng
  xep_loai_de_xuat: XepLoaiChatLuong | null;
  ly_do_dieu_chinh_dt: string | null;
  
  // Quyết định của CCT
  xep_loai_quyet_dinh: XepLoaiChatLuong | null;
  ly_do_dieu_chinh_cct: string | null;
  
  // Từ chối
  bi_tu_choi: boolean;
  ly_do_tu_choi: string | null;
  
  // Ghi chú
  ghi_chu: string | null;
}

// =============================================================================
// BÁO CÁO XẾP LOẠI
// =============================================================================

/**
 * Báo cáo xếp loại đầy đủ (với chi tiết).
 */
export interface IBaoCaoXepLoai {
  id: string;
  don_vi_id: string;
  don_vi: IDonViBrief;
  thang: number;
  nam: number;
  
  // Người lập
  nguoi_lap: ICongChucBrief;
  ngay_lap: string | null;
  
  // Trạng thái
  trang_thai: TrangThaiBaoCao;
  trang_thai_ten?: string;
  
  // Phê duyệt
  nguoi_phe_duyet?: ICongChucBrief | null;
  ngay_phe_duyet?: string | null;
  y_kien_phe_duyet?: string | null;
  
  // Thống kê
  tong_cong_chuc: number;
  so_loai_a: number;
  so_loai_b: number;
  so_loai_c: number;
  so_loai_d: number;
  so_loai_e: number;
  
  // Cảnh báo
  canh_bao_ty_le_a: boolean;
  
  // Chi tiết
  chi_tiet: IChiTietXepLoai[];
}

/**
 * Báo cáo tóm tắt (danh sách chờ phê duyệt).
 */
export interface IBaoCaoXepLoaiSummary {
  id: string;
  don_vi: IDonViBrief;
  thang: number;
  nam: number;
  nguoi_lap: ICongChucBrief;
  ngay_lap: string;
  trang_thai: TrangThaiBaoCao;
  tong_cong_chuc: number;
  so_loai_a: number;
  so_loai_b: number;
  so_loai_c: number;
  so_loai_d: number;
  so_loai_e: number;
  canh_bao_ty_le_a: boolean;
}

// =============================================================================
// REQUEST INTERFACES
// =============================================================================

/**
 * Request điều chỉnh xếp loại đề xuất (Đội trưởng).
 */
export interface IDeXuatXepLoaiRequest {
  xep_loai_de_xuat: XepLoaiChatLuong;
  ly_do_dieu_chinh?: string;
  ghi_chu?: string;
}

/**
 * Request điều chỉnh xếp loại quyết định (CCT).
 */
export interface IQuyetDinhXepLoaiRequest {
  xep_loai_quyet_dinh: XepLoaiChatLuong;
  ly_do_dieu_chinh?: string;
}

/**
 * Chi tiết từ chối 1 CC.
 */
export interface IChiTietTuChoi {
  chi_tiet_id: string;
  ly_do: string;
}

/**
 * Request phê duyệt/từ chối báo cáo.
 */
export interface IPheDuyetBaoCaoRequest {
  action: 'APPROVE' | 'REJECT';
  y_kien?: string;
  chi_tiet_tu_choi?: IChiTietTuChoi[];
}

// =============================================================================
// RESPONSE INTERFACES
// =============================================================================

/**
 * Response gửi duyệt.
 */
export interface IGuiDuyetResponse {
  id: string;
  trang_thai: TrangThaiBaoCao;
  ngay_lap: string;
  canh_bao_ty_le_a: boolean;
  thong_ke: {
    tong_cong_chuc: number;
    so_loai_a: number;
    so_loai_b: number;
    so_loai_c: number;
    so_loai_d: number;
    so_loai_e: number;
  };
}

/**
 * Response phê duyệt.
 */
export interface IPheDuyetResponse {
  id: string;
  trang_thai: TrangThaiBaoCao;
  ngay_phe_duyet?: string;
  so_cc_bi_tu_choi?: number;
}

// =============================================================================
// THỐNG KÊ
// =============================================================================

/**
 * Thống kê theo đơn vị.
 */
export interface IThongKeTheoDonVi {
  don_vi: IDonViBrief;
  tong: number;
  A: number;
  B: number;
  C: number;
  D: number;
  E: number;
  trang_thai: TrangThaiBaoCao | null;
}

/**
 * Thống kê toàn Chi cục.
 */
export interface IThongKeXepLoai {
  thang: number;
  nam: number;
  tong_cong_chuc: number;
  theo_xep_loai: {
    A: number;
    B: number;
    C: number;
    D: number;
    E: number;
  };
  theo_don_vi: IThongKeTheoDonVi[];
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Lấy màu cho xếp loại.
 */
export function getXepLoaiColor(xepLoai: XepLoaiChatLuong): {
  bg: string;
  text: string;
  border: string;
} {
  const colors: Record<XepLoaiChatLuong, { bg: string; text: string; border: string }> = {
    'A': { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300' },
    'B': { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300' },
    'C': { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-300' },
    'D': { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300' },
    'E': { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300' },
  };
  return colors[xepLoai];
}

/**
 * Lấy tên trạng thái báo cáo.
 */
export function getTrangThaiTen(trangThai: TrangThaiBaoCao): string {
  const names: Record<TrangThaiBaoCao, string> = {
    [TrangThaiBaoCao.NHAP]: 'Đang soạn',
    [TrangThaiBaoCao.CHO_PHE_DUYET]: 'Chờ phê duyệt',
    [TrangThaiBaoCao.DA_PHE_DUYET]: 'Đã phê duyệt',
    [TrangThaiBaoCao.TU_CHOI]: 'Bị từ chối',
  };
  return names[trangThai];
}

/**
 * Lấy màu trạng thái.
 */
export function getTrangThaiColor(trangThai: TrangThaiBaoCao): string {
  const colors: Record<TrangThaiBaoCao, string> = {
    [TrangThaiBaoCao.NHAP]: 'bg-gray-100 text-gray-700',
    [TrangThaiBaoCao.CHO_PHE_DUYET]: 'bg-yellow-100 text-yellow-700',
    [TrangThaiBaoCao.DA_PHE_DUYET]: 'bg-green-100 text-green-700',
    [TrangThaiBaoCao.TU_CHOI]: 'bg-red-100 text-red-700',
  };
  return colors[trangThai];
}

/**
 * Tính xếp loại từ điểm.
 */
export function tinhXepLoai(diemTong: number): XepLoaiChatLuong {
  if (diemTong === 0) return 'E';
  if (diemTong < 50) return 'D';
  if (diemTong < 70) return 'C';
  if (diemTong < 90) return 'B';
  return 'A';
}
/**
 * src/types/chi-tieu.ts
 * =====================
 * Types cho module Chỉ tiêu đơn vị (port 8007, schema chi_tieu).
 */

// ---- Enums (string literal, khớp backend VARCHAR + CHECK) ----
export type KieuDuLieu = 'SO_NGUYEN' | 'THAP_PHAN' | 'PHAN_TRAM';
export type LoaiMuc = 'PHAP_LENH' | 'PHAN_DAU';
export type TrangThaiChiTieu =
  | 'NHAP'
  | 'CHO_DUYET_DANG_KY'
  | 'DA_DUYET_DANG_KY'
  | 'CHO_DUYET_SUA'
  | 'CHO_DUYET_KET_QUA'
  | 'DA_DUYET_KET_QUA';
export type LoaiChoDuyet = 'DANG_KY' | 'SUA' | 'KET_QUA';

// ---- Lĩnh vực ----
export interface ILinhVuc {
  id: string;
  ma_linh_vuc: string;
  ten_linh_vuc: string;
  van_ban_ke_hoach?: string | null;
  thu_tu?: number;
  is_active?: boolean;
}
export interface ILinhVucCreate {
  ma_linh_vuc: string;
  ten_linh_vuc: string;
  van_ban_ke_hoach?: string;
  thu_tu?: number;
}

// ---- Danh mục chỉ tiêu ----
export interface IChiTieu {
  id: string;
  linh_vuc_id: string;
  ma_chi_tieu: string;
  ten_chi_tieu: string;
  don_vi_tinh: string;
  kieu_du_lieu: KieuDuLieu;
  co_phan_dau?: boolean;
  van_ban_giao?: string | null;
  mo_ta?: string | null;
  thu_tu?: number;
  is_active?: boolean;
}
export interface IChiTieuCreate {
  linh_vuc_id: string;
  ma_chi_tieu: string;
  ten_chi_tieu: string;
  don_vi_tinh: string;
  kieu_du_lieu?: KieuDuLieu;
  co_phan_dau?: boolean;
  van_ban_giao?: string;
  mo_ta?: string;
  thu_tu?: number;
}

// ---- Giao năm ----
export interface IGiaoNam {
  id: string;
  don_vi_id: string;
  chi_tieu_id: string;
  nam: number;
  loai_muc: LoaiMuc;
  gia_tri_giao: string;
  luy_ke_dau_ky?: string;
  nguoi_giao_id?: string | null;
  ghi_chu?: string | null;
}
export interface IGiaoNamCreate {
  don_vi_id: string;
  chi_tieu_id: string;
  nam: number;
  loai_muc: LoaiMuc;
  gia_tri_giao: number | string;
  luy_ke_dau_ky?: number | string;
  ghi_chu?: string;
}

// ---- Đăng ký tháng (bản ghi lõi) ----
export interface IDangKy {
  id: string;
  don_vi_id: string;
  chi_tieu_id: string;
  thang: number;
  nam: number;
  khong_dang_ky?: boolean;
  gia_tri_dang_ky?: string | null;
  gia_tri_ket_qua?: string | null;
  danh_gia_tu_dong?: string | null;
  danh_gia_ghi_chu?: string | null;
  trang_thai: TrangThaiChiTieu;
  nguoi_theo_doi_id: string;
  nguoi_duyet_id?: string | null;
  ly_do_tu_choi?: string | null;
  is_khoa?: boolean;
  ngay_gui_dang_ky?: string | null;
  ngay_duyet_dang_ky?: string | null;
  ngay_gui_ket_qua?: string | null;
  ngay_duyet_ket_qua?: string | null;
}

export interface IMucGiao {
  loai_muc: LoaiMuc;
  gia_tri_giao: string | null;
  luy_ke_dau_ky: string | null;
}
/** 1 dòng trong danh sách cần đăng ký tháng (chỉ tiêu + mức giao + bản ghi nếu có). */
export interface IDongDangKy {
  chi_tieu_id: string;
  muc_giao: IMucGiao[];
  dang_ky: IDangKy | null;
}

export interface ILichSu {
  id: string;
  dang_ky_thang_id: string;
  hanh_dong: string;
  nguoi_thuc_hien_id: string;
  ghi_chu?: string | null;
  created_at?: string;
}

// ---- Báo cáo ----
export interface IDongDonViBaoCao {
  don_vi_id: string;
  ten_don_vi: string;
  ma_don_vi: string;
  khong_dang_ky?: boolean;
  gia_tri_dang_ky?: string | null;
  gia_tri_ket_qua?: string | null;
  danh_gia?: string | null;
  trang_thai: TrangThaiChiTieu;
  luy_ke_nam: Record<string, { gia_tri_giao: string; luy_ke: string; dat_phan_tram: string | null }>;
}
export interface IChiTieuBaoCao {
  chi_tieu_id: string;
  ma_chi_tieu: string;
  ten_chi_tieu: string;
  don_vi_tinh: string;
  kieu_du_lieu: KieuDuLieu;
  co_phan_dau?: boolean;
  dong_don_vi: IDongDonViBaoCao[];
}
export interface ILinhVucBaoCao {
  linh_vuc_id: string;
  ma_linh_vuc: string;
  ten_linh_vuc: string;
  van_ban_ke_hoach?: string | null;
  chi_tieu: IChiTieuBaoCao[];
}

// ---- Người theo dõi (gán platform_role) ----
export type RoleChiTieu = 'THEO_DOI_CHI_TIEU' | 'QT_CHI_TIEU';

export interface INguoiTheoDoi {
  cong_chuc_id: string;
  ma_cc?: string | null;
  ho_ten?: string | null;
  chuc_vu?: string | null;
  don_vi_cong_chuc?: string | null;
  role: string;
  don_vi_ids: string[];
  is_active: boolean;
}

export interface IPhamViXem {
  toan_chi_cuc: boolean;
  don_vi_ids: string[];
}

export interface ICongChucSearch {
  id: string;
  ma_cc?: string | null;
  ho_ten?: string | null;
  chuc_vu?: string | null;
  don_vi_id?: string | null;
  ten_don_vi?: string | null;
}

// ---- Nhãn trạng thái (UI) ----
export const TRANG_THAI_LABEL: Record<TrangThaiChiTieu, { label: string; bg: string; text: string }> = {
  NHAP: { label: 'Nháp', bg: 'bg-gray-100', text: 'text-gray-600' },
  CHO_DUYET_DANG_KY: { label: 'Chờ duyệt đăng ký', bg: 'bg-amber-100', text: 'text-amber-700' },
  DA_DUYET_DANG_KY: { label: 'Đã duyệt đăng ký', bg: 'bg-blue-100', text: 'text-blue-700' },
  CHO_DUYET_SUA: { label: 'Chờ duyệt sửa', bg: 'bg-orange-100', text: 'text-orange-700' },
  CHO_DUYET_KET_QUA: { label: 'Chờ duyệt kết quả', bg: 'bg-purple-100', text: 'text-purple-700' },
  DA_DUYET_KET_QUA: { label: 'Đã chốt', bg: 'bg-green-100', text: 'text-green-700' },
};

export const LOAI_MUC_LABEL: Record<LoaiMuc, string> = {
  PHAP_LENH: 'Pháp lệnh',
  PHAN_DAU: 'Phấn đấu',
};

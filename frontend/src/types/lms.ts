/**
 * src/types/lms.ts
 * ================
 * TypeScript interfaces cho module Đào tạo (LMS).
 * Map từ backend lms_service/schemas/*.py
 */

// =============================================================================
// CHUYÊN ĐỀ
// =============================================================================

export interface IChuyenDe {
  id: string;
  ma_chuyen_de: string;
  ten_chuyen_de: string;
  mo_ta: string | null;
  thu_tu: number;
  is_active: boolean;
  so_khoa_hoc: number;
  created_at: string;
}

export interface IChuyenDeCreate {
  ma_chuyen_de: string;
  ten_chuyen_de: string;
  mo_ta?: string;
  thu_tu?: number;
}

export interface IChuyenDeUpdate {
  ma_chuyen_de?: string;
  ten_chuyen_de?: string;
  mo_ta?: string;
  thu_tu?: number;
  is_active?: boolean;
}

// =============================================================================
// KHÓA HỌC
// =============================================================================

export interface IDangKyInfo {
  trang_thai: string;            // CHUA_BAT_DAU | DANG_HOC | HOAN_THANH | QUA_HAN
  phan_tram_hoan_thanh: number;
  loai_dang_ky: string;          // TU_NGUYEN | GIAO_BAI
  han_hoan_thanh: string | null;
}

export interface IKhoaHoc {
  id: string;
  ma_khoa_hoc: string;
  ten_khoa_hoc: string;
  mo_ta: string | null;
  loai: string;
  trang_thai: string;
  anh_dai_dien: string | null;
  chuyen_de_id: string | null;
  chuyen_de_ten: string | null;
  giang_vien_id: string | null;
  giang_vien_ho_ten: string | null;
  nguoi_duyet_ho_ten: string | null;
  so_bai_hoc: number;
  so_hoc_vien: number;
  thoi_luong_phut: number | null;
  diem_dat_yeu_cau: number;
  ngay_bat_dau: string | null;
  ngay_ket_thuc: string | null;
  dieu_kien_tien_quyet: string[] | null;
  created_at: string;
  dang_ky?: IDangKyInfo | null;
}

// =============================================================================
// BÀI HỌC
// =============================================================================

export interface IBaiHocCreate {
  tieu_de: string;
  thu_tu: number;
  loai_noi_dung: string;   // HTML | VIDEO | PDF | SLIDE
  noi_dung?: string;
  thoi_luong_phut?: number;
  phai_xem_het?: boolean;
}

export interface IBaiHoc {
  id: string;
  khoa_hoc_id: string;
  tieu_de: string;
  loai_noi_dung: string;
  noi_dung: string | null;
  file_url: string | null;
  pdf_url: string | null;
  thoi_luong_phut: number | null;
  thu_tu: number;
  phai_xem_het: boolean;
  is_active: boolean;
  tien_do_ca_nhan: ITienDoBaiHoc | null;
}

export interface ITienDoBaiHoc {
  trang_thai: string;
  thoi_gian_xem_giay: number;
  ngay_hoan_thanh: string | null;
}

// =============================================================================
// ĐĂNG KÝ
// =============================================================================

export interface IDangKyKhoaHoc {
  id: string;
  cong_chuc_id: string;
  khoa_hoc_id: string;
  loai_dang_ky: string;
  trang_thai: string;
  phan_tram_hoan_thanh: number;
  han_hoan_thanh: string | null;
  ngay_bat_dau_hoc: string | null;
  ngay_hoan_thanh: string | null;
  khoa_hoc_ten: string | null;
  khoa_hoc_ma: string | null;
  khoa_hoc_loai: string | null;
  giang_vien_ho_ten: string | null;
}

// =============================================================================
// CÂU HỎI (Ngân hàng câu hỏi)
// =============================================================================

/** Câu hỏi response từ API */
export interface ICauHoi {
  id: string;
  noi_dung: string;
  loai: string;              // TRAC_NGHIEM_1 | TRAC_NGHIEM_NHIEU | DUNG_SAI | GHEP_DOI | TU_LUAN
  do_kho: string;            // DE | TRUNG_BINH | KHO
  diem: number;
  khoa_hoc_id: string | null;
  khoa_hoc_ten: string | null;
  bai_kiem_tra_id?: string | null;
  bai_kiem_tra_ten?: string | null;
  dap_an: Record<string, unknown>;   // dynamic object tuỳ loại
  giai_thich: string | null;
  created_at: string;
}

/** Câu hỏi tạo inline trong BKT (không qua ngân hàng) */
export interface ICauHoiInline {
  noi_dung: string;
  loai: string;
  do_kho: string;
  diem: number;
  dap_an: Record<string, unknown>;
  giai_thich?: string;
}

/** Body tạo/sửa câu hỏi */
export interface ICauHoiCreate {
  noi_dung: string;
  loai: string;
  do_kho: string;
  diem: number;
  khoa_hoc_id?: string | null;
  dap_an: Record<string, unknown>;
  giai_thich?: string;
}

// =============================================================================
// BÀI KIỂM TRA
// =============================================================================

/** Body tạo/sửa bài kiểm tra */
export interface IBaiKiemTraCreate {
  tieu_de: string;
  thoi_gian_lam_bai_phut?: number;   // null = không giới hạn
  so_lan_lam_toi_da?: number;        // default 3
  diem_dat?: number;                 // default 70
  tron_de?: boolean;                 // default true
  // Cấu hình hiển thị kết quả sau khi nộp bài
  che_do_xem_ket_qua?: string;       // XEM_DIEM_VA_DAP_AN | CHI_XEM_DIEM | CHI_XEM_CAU_SAI | XEM_KHI_LAN_CUOI | KHONG_CHO_XEM
  hien_giai_thich?: boolean;         // default true
  cau_hoi_ids?: string[];            // danh sách UUID câu hỏi từ ngân hàng
  cau_hoi_moi?: ICauHoiInline[];     // câu hỏi tạo mới inline
}

export interface IBaiKiemTra {
  id: string;
  khoa_hoc_id: string;
  tieu_de: string;
  mo_ta?: string | null;
  so_cau_hoi: number;
  thoi_gian_lam_bai_phut: number | null;
  so_lan_lam_toi_da: number;
  diem_dat: number;
  tron_de?: boolean;
  tron_dap_an?: boolean;
  // Cấu hình hiển thị kết quả
  che_do_xem_ket_qua?: string;
  hien_giai_thich?: boolean;
  is_active: boolean;
  // Thống kê cá nhân (chỉ có khi đã đăng ký)
  so_lan_da_lam?: number | null;
  diem_cao_nhat?: number | null;
  da_dat?: boolean | null;
}

export interface ILichSuThiItem {
  id: string;
  lan_thu: number;
  diem: number | null;
  so_cau_dung: number | null;
  so_cau_sai: number | null;
  thoi_gian_lam_giay: number | null;
  dat_yeu_cau: boolean | null;
  ngay_lam: string | null;
}

export interface ILichSuThi {
  bai_kiem_tra_id: string;
  tieu_de: string;
  so_lan_lam_toi_da: number;
  diem_dat: number | null;
  so_lan_da_lam: number;
  diem_cao_nhat: number | null;
  da_dat: boolean;
  lich_su: ILichSuThiItem[];
}

export interface ICauHoiForExam {
  id: string;
  thu_tu: number;
  noi_dung: string;
  loai: string;
  diem: number;
  lua_chon: { key: string; noi_dung: string }[] | null;
}

export interface IBatDauResponse {
  ket_qua_id: string;
  lan_thu: number;
  thoi_gian_phut: number | null;
  so_cau: number;
  cau_hoi: ICauHoiForExam[];
}

export interface IKetQuaResponse {
  id: string;
  lan_thu: number;
  diem: number;
  so_cau_dung: number;
  so_cau_sai: number;
  dat_yeu_cau: boolean;
  // Chế độ hiển thị (từ BKT config)
  che_do_xem?: string;
  // Thông báo khi XEM_KHI_LAN_CUOI chưa đến lần cuối
  thong_bao?: string;
  chi_tiet: any[] | null;
}

// =============================================================================
// CHỨNG CHỈ
// =============================================================================

export interface IChungChi {
  id: string;
  ma_chung_chi: string;
  khoa_hoc_ten: string | null;
  khoa_hoc_ma: string | null;
  diem_dat: number;
  xep_loai: string | null;
  ngay_cap: string;
  ho_ten: string | null;
}

// =============================================================================
// BÁO CÁO & DASHBOARD
// =============================================================================

export interface IDashboardSummary {
  khoa_dang_hoc: number;
  khoa_sap_het_han: { ten: string; han: string; phan_tram: number }[];
  chung_chi_moi: { ma: string; ten_khoa: string; ngay_cap: string }[];
}

export interface IBaoCaoCaNhan {
  tong_khoa_da_dang_ky: number;
  khoa_dang_hoc: number;
  khoa_hoan_thanh: number;
  khoa_chua_bat_dau: number;
  tong_chung_chi: number;
  tong_gio_hoc: number;
  khoa_hoc_gan_day: { ten: string; trang_thai: string; phan_tram: number }[];
  chung_chi_gan_day: { ma: string; ten_khoa: string; xep_loai: string; ngay_cap: string }[];
}

// =============================================================================
// COMMON
// =============================================================================

export interface IPagination {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

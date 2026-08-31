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
  trang_thai: string;            // CHUA_BAT_DAU | DANG_HOC | HOAN_THANH | QUA_HAN | CHO_PHE_DUYET | TU_CHOI | BI_LOAI
  phan_tram_hoan_thanh: number;
  loai_dang_ky: string;          // TU_NGUYEN | GIAO_BAI
  han_hoan_thanh: string | null;
  nguoi_phe_duyet_id?: string | null;
  ngay_phe_duyet?: string | null;
  ly_do_tu_choi?: string | null;
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
  nguoi_phe_duyet_id?: string | null;
  ngay_phe_duyet?: string | null;
  ly_do_tu_choi?: string | null;
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
  bai_kiem_tra_id: string;
  dap_an: Record<string, unknown>;
  giai_thich?: string;
}

// =============================================================================
// BÀI KIỂM TRA
// =============================================================================

/** Body tạo/sửa bài kiểm tra */
export interface IBaiKiemTraCreate {
  tieu_de: string;
  mo_ta?: string;
  /** TRAC_NGHIEM (default) | THUC_HANH */
  loai_bai_kiem_tra?: string;
  /** Bắt buộc nếu loai_bai_kiem_tra=THUC_HANH */
  yeu_cau_bai_lam?: string;
  dung_luong_toi_da_mb?: number;     // default 500
  dinh_dang_cho_phep?: string;       // CSV: "mp4,mov,webm"
  thoi_gian_lam_bai_phut?: number;   // null = không giới hạn
  so_lan_lam_toi_da?: number;        // default 3
  diem_dat?: number;                 // default 70
  tron_de?: boolean;                 // default true
  gio_mo?: string;                   // HH:MM format
  gio_dong?: string;                 // HH:MM format
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
  loai_bai_kiem_tra?: string;        // TRAC_NGHIEM | THUC_HANH
  yeu_cau_bai_lam?: string | null;
  dung_luong_toi_da_mb?: number | null;
  dinh_dang_cho_phep?: string | null;
  so_cau_hoi: number;
  thoi_gian_lam_bai_phut: number | null;
  so_lan_lam_toi_da: number;
  diem_dat: number;
  tron_de?: boolean;
  tron_dap_an?: boolean;
  gio_mo?: string | null;
  gio_dong?: string | null;
  // Cấu hình hiển thị kết quả
  che_do_xem_ket_qua?: string;
  hien_giai_thich?: boolean;
  is_active: boolean;
  // Thống kê cá nhân (chỉ có khi đã đăng ký)
  so_lan_da_lam?: number | null;
  diem_cao_nhat?: number | null;
  da_dat?: boolean | null;
  /** THUC_HANH: trang thai cham lan nop moi nhat cua ca nhan */
  trang_thai_cham_moi_nhat?: string | null;
  bai_nop_url?: string | null;
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
  // THUC_HANH
  bai_nop_url?: string | null;
  bai_nop_ten_file?: string | null;
  trang_thai_cham?: string | null;   // CHO_CHAM | DA_CHAM | null
  nhan_xet?: string | null;
  ngay_nop?: string | null;
  ngay_cham?: string | null;
}

export interface ILichSuThi {
  bai_kiem_tra_id: string;
  tieu_de: string;
  loai_bai_kiem_tra?: string;
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
  ket_qua_id: string | null;
  lan_thu: number;
  thoi_gian_phut: number | null;
  loai_bai_kiem_tra?: string;        // TRAC_NGHIEM | THUC_HANH
  so_cau: number;
  cau_hoi: ICauHoiForExam[];
  // THUC_HANH fields
  yeu_cau_bai_lam?: string | null;
  dung_luong_toi_da_mb?: number | null;
  dinh_dang_cho_phep?: string | null;
  dang_tiep_tuc?: boolean;
  chi_tiet_nhap?: any[] | null;
  thoi_gian_da_lam_giay?: number;
  so_lan_vi_pham?: number;
  so_lan_con_lai?: number | null;
  is_preview?: boolean;
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
  so_lan_con_lai?: number | null;
  // THUC_HANH
  loai_bai_kiem_tra?: string;
  bai_nop_url?: string | null;
  bai_nop_ten_file?: string | null;
  trang_thai_cham?: string | null;   // CHO_CHAM | DA_CHAM
  nhan_xet?: string | null;
  ngay_nop?: string | null;
  ngay_cham?: string | null;
}

export interface IKetQuaChamItem {
  id: string;
  cong_chuc_id: string;
  ho_ten: string | null;
  ma_cc: string | null;
  don_vi_ten: string | null;
  lan_thu: number;
  diem: number | null;
  dat_yeu_cau: boolean | null;
  ngay_lam: string | null;
  ngay_nop: string | null;
  ngay_cham: string | null;
  bai_nop_url: string | null;
  bai_nop_ten_file: string | null;
  bai_nop_size_bytes: number | null;
  bai_nop_content_type: string | null;
  trang_thai_cham: string | null;   // CHO_CHAM | DA_CHAM
  nhan_xet: string | null;
  so_lan_vi_pham?: number | null;
}

// =============================================================================
// CHỨNG CHỈ
// =============================================================================

export interface IChungChi {
  id: string;
  ma_chung_chi: string;
  khoa_hoc_id: string;
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
// ĐGNL — LĨNH VỰC
// =============================================================================

export interface ILinhVuc {
  id: string;
  ma_linh_vuc: string;
  ten_linh_vuc: string;
  mo_ta: string | null;
  thu_tu: number;
  is_active: boolean;
}

// =============================================================================
// ĐGNL — VỊ TRÍ VIỆC LÀM
// =============================================================================

export interface IViTriViecLam {
  id: string;
  ma_vi_tri: string;
  ten_vi_tri: string;
  mo_ta: string | null;
  linh_vuc_ids: string[];
  thu_tu: number;
  is_active: boolean;
}

// =============================================================================
// ĐGNL — KỲ THI
// =============================================================================

export interface IKyThi {
  id: string;
  ma_ky_thi: string;
  ten_ky_thi: string;
  mo_ta: string | null;
  ngay_bat_dau: string;
  ngay_ket_thuc: string;
  thoi_gian_lam_bai_phut: number;
  diem_dat: number;
  so_lan_thi_toi_da: number;
  tron_cau_hoi: boolean;
  tron_dap_an: boolean;
  hien_ket_qua: boolean;
  hien_dap_an: boolean;
  yeu_cau_toan_man_hinh?: boolean;
  trang_thai: string; // NHAP | CHO_DUYET | DANG_MO | DA_DONG
  nguoi_tao_id: string;
  nguoi_duyet_id: string | null;
  ngay_duyet: string | null;
  nguoi_tao_ho_ten: string | null;
  nguoi_duyet_ho_ten: string | null;
  tong_thi_sinh: number;
  so_vi_tri: number;
  created_at: string;
  // Trang thai thi sinh cua user hien tai (CHUA_THI | DANG_THI | DA_NOP | VANG | null)
  trang_thai_thi_sinh?: string | null;
  lan_thi_hien_tai?: number;
}

export interface IKyThiCreate {
  ma_ky_thi: string;
  ten_ky_thi: string;
  mo_ta?: string;
  ngay_bat_dau: string;
  ngay_ket_thuc: string;
  thoi_gian_lam_bai_phut?: number;
  diem_dat?: number;
  so_lan_thi_toi_da?: number;
  tron_cau_hoi?: boolean;
  tron_dap_an?: boolean;
  hien_ket_qua?: boolean;
  hien_dap_an?: boolean;
  yeu_cau_toan_man_hinh?: boolean;
}

// =============================================================================
// ĐGNL — CẤU TRÚC ĐỀ
// =============================================================================

export interface ICauTrucDeItem {
  linh_vuc_id: string;
  so_cau_de: number;
  so_cau_trung_binh: number;
  so_cau_kho: number;
}

export interface ICauTrucDeResponse {
  id: string;
  ky_thi_id: string;
  vi_tri_id: string;
  linh_vuc_id: string;
  so_cau_de: number;
  so_cau_trung_binh: number;
  so_cau_kho: number;
  vi_tri_ten: string | null;
  linh_vuc_ten: string | null;
}

export interface ICauTrucDeByViTri {
  vi_tri_id: string;
  vi_tri_ten: string;
  tong_cau: number;
  chi_tiet: ICauTrucDeResponse[];
}

/** Mẫu cấu trúc đề — lưu lại để áp dụng nhanh cho kỳ thi sau. */
export interface ICauTrucDeTemplate {
  id: string;
  ten_template: string;
  mo_ta: string | null;
  nguoi_tao_id: string;
  nguoi_tao_ho_ten: string | null;
  cau_truc: {
    vi_tri_id: string;
    linh_vuc_id: string;
    so_cau_de: number;
    so_cau_trung_binh: number;
    so_cau_kho: number;
  }[];
  created_at: string | null;
  updated_at: string | null;
}

// =============================================================================
// ĐGNL — THÍ SINH
// =============================================================================

export interface ILichSuThiSummary {
  lan: number;
  diem: number;
  xep_loai: string | null;
  so_cau_dung: number | null;
  so_cau_sai: number | null;
  tong_so_cau: number | null;
  thoi_gian_bat_dau: string | null;
  thoi_gian_nop: string | null;
  thoi_gian_lam_giay: number | null;
  has_chi_tiet: boolean;
}

export interface IThiSinh {
  id: string;
  ky_thi_id: string;
  cong_chuc_id: string;
  vi_tri_id: string;
  trang_thai: string; // CHUA_THI | DANG_THI | DA_NOP | VANG
  lan_thi_hien_tai: number;
  diem_tong: number | null;
  xep_loai: string | null;
  so_cau_dung: number | null;
  so_cau_sai: number | null;
  tong_so_cau: number | null;
  so_lan_vi_pham?: number;
  diem_theo_linh_vuc: Record<string, { dung: number; tong: number; phan_tram: number }> | null;
  thoi_gian_bat_dau: string | null;
  thoi_gian_nop: string | null;
  thoi_gian_lam_giay: number | null;
  /** Đã chốt ca thi -> không được thi lại dù còn lượt (tự động sau 10' kể từ khi nộp). */
  da_xac_nhan?: boolean;
  thoi_gian_xac_nhan?: string | null;
  ho_ten: string | null;
  ma_cc: string | null;
  don_vi_ten: string | null;
  vi_tri_ten: string | null;
  lich_su_thi?: ILichSuThiSummary[] | null;
}

/** 1 dòng nhật ký reset lượt thi (ai reset, cho ai, vì sao, trạng thái trước đó). */
export interface ILichSuReset {
  id: string;
  ky_thi_id: string | null;
  cong_chuc_id: string;
  nguoi_reset_id: string;
  loai_reset: 'XOA_SACH' | 'MO_KHOA_LUOT';
  ly_do: string;
  trang_thai_truoc: string | null;
  lan_thi_truoc: number | null;
  diem_truoc: number | string | null;
  thoi_gian: string | null;
  ho_ten: string | null;
  ma_cc: string | null;
  nguoi_reset_ten: string | null;
  nguoi_reset_ma_cc: string | null;
}

// =============================================================================
// ĐGNL — GIÁM SÁT TRỰC TIẾP
// =============================================================================

export interface IGiamSatThiSinh {
  cong_chuc_id: string;
  ho_ten: string | null;
  ma_cc: string | null;
  don_vi_ten: string | null;
  vi_tri_ten: string | null;
  trang_thai: string; // CHUA_THI | DANG_THI | DA_NOP | VANG
  lan_thi_hien_tai: number;
  so_cau_da_lam: number;
  tong_so_cau: number;
  so_lan_vi_pham: number;
  thoi_gian_bat_dau: string | null;
  thoi_gian_con_lai_giay: number | null;
  diem_tong: number | null;
  xep_loai: string | null;
  last_seen: string | null;
  online: boolean;
  thiet_bi: string | null;
}

export interface IGiamSatResponse {
  tong_quan: {
    tong_thi_sinh: number;
    dang_thi: number;
    da_nop: number;
    chua_thi: number;
    vang: number;
    online: number;
    co_vi_pham: number;
  };
  thi_sinh: IGiamSatThiSinh[];
}

export interface IDgnlBatDauResponse {
  thi_sinh_id: string;
  thoi_gian_con_lai_giay: number;
  tong_so_cau: number;
  cau_hoi: IDgnlCauHoi[];
}

export interface IDgnlCauHoi {
  id: string;
  thu_tu: number;
  noi_dung: string;
  loai: string;
  diem: number;
  lua_chon: { key: string; noi_dung: string }[] | null;
  linh_vuc: string | null;
}

export interface IDgnlKetQua {
  ky_thi: { id: string; ten_ky_thi: string; diem_dat: number };
  thi_sinh: { ho_ten: string; ma_cc: string; don_vi: string; vi_tri_thi: string };
  ket_qua: {
    diem_tong: number;
    xep_loai: string;
    so_cau_dung: number;
    so_cau_sai: number;
    tong_so_cau: number;
    thoi_gian_lam_giay: number;
    lan_thi: number;
  };
  diem_theo_linh_vuc: { linh_vuc: string; so_cau_dung: number; tong_cau: number; phan_tram: number }[];
  chi_tiet: IDgnlKetQuaChiTiet[] | null;
  lich_su_thi: ILichSuThiSummary[] | null;
}

export interface IDgnlKetQuaChiTiet {
  cau_hoi_id: string;
  tra_loi: any;
  dap_an_dung: any;
  dung: boolean;
  noi_dung?: string;
  loai?: string;
  giai_thich?: string | null;
  diem_toi_da?: number;
  diem_dat?: number;
}

export interface IDgnlValidateResponse {
  ky_thi_id: string;
  tat_ca_du: boolean;
  theo_vi_tri: {
    vi_tri_ten: string;
    du_cau_hoi: boolean;
    chi_tiet: { linh_vuc_ten: string; do_kho: string; yeu_cau: number; co_san: number; du: boolean }[];
  }[];
}

export interface IDgnlThongKe {
  tong_quan: {
    tong_thi_sinh: number;
    da_thi: number;
    chua_thi: number;
    dang_thi: number;
    vang: number;
    dat: number;
    khong_dat: number;
    ti_le_dat: number;
    diem_trung_binh: number;
    diem_cao_nhat: number;
    diem_thap_nhat: number;
  };
  theo_vi_tri: { vi_tri: string; tong: number; dat: number; khong_dat: number; diem_tb: number }[];
  theo_don_vi: { don_vi: string; tong: number; dat: number; ti_le_dat: number; diem_tb: number }[];
}

// =============================================================================
// ĐGNL — NGÂN HÀNG CÂU HỎI
// =============================================================================

export interface ICauHoiDgnl {
  id: string;
  linh_vuc_id: string;
  noi_dung: string;
  giai_thich: string | null;
  loai: string;
  dap_an: Record<string, unknown>;
  diem: number;
  do_kho: string;
  nguoi_tao_id: string | null;
  is_active: boolean;
  created_at: string;
  linh_vuc_ten: string | null;
  nguoi_tao_ho_ten: string | null;
}

export interface IThongKeNganHang {
  linh_vuc_id: string;
  linh_vuc_ten: string;
  so_cau_de: number;
  so_cau_trung_binh: number;
  so_cau_kho: number;
  tong: number;
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

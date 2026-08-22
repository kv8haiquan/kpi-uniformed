/**
 * src/types/hkg.ts
 * ================
 * Types cho module HKG (Họp Không Giấy) — backend port 8006.
 * Các shape khớp với Pydantic schema BE.
 */

// ════════════════════════════════════════════════════════════
// COMMON
// ════════════════════════════════════════════════════════════

export type Khoi = 'DANG' | 'CHUYEN_MON' | 'HANH_CHINH' | 'BAN_NHOM';
export type HinhThuc = 'TRUC_TIEP' | 'TRUC_TUYEN' | 'HYBRID';
export type TrangThaiCuocHop =
  | 'LEN_KE_HOACH'
  | 'DA_THONG_BAO'
  | 'DANG_DIEN_RA'
  | 'HOAN_THANH'
  | 'HUY';

export type LoaiThamDu = 'BAT_BUOC' | 'THAM_KHAO';
export type XacNhan = 'CHUA_PHAN_HOI' | 'THAM_DU' | 'KHONG_THAM_DU' | 'UY_QUYEN';

/**
 * Mức hạn chế người xem tài liệu họp (G5.4) — có thứ bậc tăng dần.
 * `HAN_CHE` của bản cũ đã bị loại bỏ (migration meeting_023): nhãn đó chưa
 * từng được kiểm ở bất kỳ đâu nên không có hiệu lực.
 */
export type PhanQuyenTaiLieu =
  | 'CONG_KHAI'
  | 'LANH_DAO_DON_VI'
  | 'LANH_DAO_CHI_CUC';

export interface IMucPhanQuyen {
  ma: PhanQuyenTaiLieu;
  ten: string;
  mo_ta: string;
  /** Người đang đăng nhập có được ĐẶT mức này không. */
  dat_duoc: boolean;
}
export type HinhThucDiemDanh = 'QR' | 'BAM_TAY';
export type TrangThaiDiemDanh = 'CO_MAT' | 'DEN_MUON' | 'VANG_CO_PHEP' | 'VANG_KHONG_PHEP';

export type TrangThaiXinPhep = 'CHO_DUYET' | 'DA_DUYET' | 'TU_CHOI' | 'TU_DONG_DUYET';
export type TrangThaiBienBan = 'DANG_SOAN' | 'TRINH_KY' | 'DA_KY' | 'CONG_BO';
export type MucUuTien = 'CAO' | 'TRUNG_BINH' | 'THAP';
export type TrangThaiKetLuan =
  | 'CHUA_BAT_DAU'
  | 'DANG_LAM'
  | 'HOAN_THANH'
  | 'TRE_HAN'
  | 'HUY';

// ════════════════════════════════════════════════════════════
// MODULE 1 — CUỘC HỌP
// ════════════════════════════════════════════════════════════

export interface IThanhPhanInput {
  cong_chuc_id: string;
  loai_tham_du: LoaiThamDu;
}

export interface ICuocHopCreate {
  tieu_de: string;
  mo_ta?: string | null;
  khoi: Khoi;
  hinh_thuc: HinhThuc;
  ngay_hop: string; // YYYY-MM-DD
  gio_bat_dau: string; // HH:MM
  gio_ket_thuc?: string | null;
  dia_diem?: string | null;
  don_vi_to_chuc_id: string;
  chu_toa_id: string;
  thu_ky_id?: string | null;
  thanh_phan: IThanhPhanInput[];
}

export interface ICuocHopUpdate {
  tieu_de?: string;
  mo_ta?: string | null;
  khoi?: Khoi;
  hinh_thuc?: HinhThuc;
  ngay_hop?: string;
  gio_bat_dau?: string;
  gio_ket_thuc?: string | null;
  dia_diem?: string | null;
  thu_ky_id?: string | null;
}

export interface ICuocHop {
  id: string;
  tieu_de: string;
  mo_ta: string | null;
  khoi: Khoi;
  hinh_thuc: HinhThuc;
  ngay_hop: string;
  gio_bat_dau: string;
  gio_ket_thuc: string | null;
  dia_diem: string | null;
  don_vi_to_chuc_id: string;
  chu_toa_id: string;
  thu_ky_id: string | null;
  trang_thai: TrangThaiCuocHop;
  created_at: string;
  updated_at: string;
  created_by: string;
  is_deleted: boolean;
}

export interface ICuocHopListItem extends Omit<ICuocHop, 'mo_ta' | 'gio_ket_thuc' | 'dia_diem' | 'updated_at' | 'created_by' | 'is_deleted'> {
  so_thanh_phan: number;
}

// ════════════════════════════════════════════════════════════
// MODULE 3 — TÀI LIỆU
// ════════════════════════════════════════════════════════════

export interface ITaiLieu {
  id: string;
  cuoc_hop_id: string;
  ten_tai_lieu: string;
  mo_ta: string | null;
  /** MÃ trong danh mục LOAI_TAI_LIEU. Lưu mã chứ không lưu nhãn để đổi tên
   *  loại trên màn hình Quản trị danh mục không làm mồ côi tài liệu. */
  loai_tai_lieu: string | null;
  minio_bucket: string;
  minio_key: string;
  file_size: number;
  mime_type: string | null;
  extension: string | null;
  phan_quyen: PhanQuyenTaiLieu;
  cho_phep_tai: boolean;
  cho_phep_in: boolean;
  created_at: string;
  created_by: string;
}

// `mo_ta` CÓ trong phản hồi của backend (schema TaiLieuListItem) — trước đây
// khai thiếu ở đây nên phía giao diện không đọc được, dù dữ liệu vẫn về.
export interface ITaiLieuListItem extends Omit<ITaiLieu, 'cuoc_hop_id' | 'created_by' | 'minio_bucket' | 'minio_key'> {
  /** Nhãn của `loai_tai_lieu`, máy chủ tra sẵn để màn hình khỏi gọi thêm một
   *  lượt danh mục chỉ để dịch mã sang chữ. */
  loai_nhan: string | null;
  url_xem?: string;
}

// ════════════════════════════════════════════════════════════
// MODULE 4 — ĐIỂM DANH
// ════════════════════════════════════════════════════════════

export interface IDiemDanh {
  id: string;
  cuoc_hop_id: string;
  cong_chuc_id: string;
  hinh_thuc: HinhThucDiemDanh;
  trang_thai: TrangThaiDiemDanh;
  gio_diem_danh: string | null;
  ghi_chu: string | null;
  nguoi_diem_danh_id: string | null;
}

export interface IQRTokenResponse {
  token: string;
  qr_url: string;
  expires_in_seconds: number;
}

export interface IDiemDanhSummary {
  tong_so: number;
  co_mat: number;
  den_muon: number;
  vang_co_phep: number;
  vang_khong_phep: number;
  chua_diem_danh: number;
  chi_tiet: IDiemDanh[];
}

// ════════════════════════════════════════════════════════════
// MODULE 5 — XIN PHÉP VẮNG
// ════════════════════════════════════════════════════════════

export interface IXinPhepVangCreate {
  cuoc_hop_id: string;
  ly_do: string;
  nguoi_du_thay_id?: string | null;
  minio_key?: string | null;
}

export interface IXinPhepVang {
  id: string;
  cuoc_hop_id: string;
  cong_chuc_id: string;
  ly_do: string;
  nguoi_du_thay_id: string | null;
  minio_key: string | null;
  trang_thai: TrangThaiXinPhep;
  auto_approved: boolean;
  nguoi_duyet_id: string | null;
  thoi_gian_duyet: string | null;
  ly_do_tu_choi: string | null;
  created_at: string;
}

// ════════════════════════════════════════════════════════════
// MODULE 9 — BIÊN BẢN
// ════════════════════════════════════════════════════════════

export interface IBienBan {
  id: string;
  cuoc_hop_id: string;
  noi_dung_json: Record<string, unknown> | null;
  noi_dung_html: string | null;
  trang_thai: TrangThaiBienBan;
  file_pdf_minio_key: string | null;
  file_docx_minio_key: string | null;
  is_mock_signed: boolean;
  qr_xac_thuc: string | null;
  hash_noi_dung: string | null;
  nguoi_soan_id: string;
  nguoi_ky_id: string | null;
  thoi_gian_ky: string | null;
  created_at: string;
  updated_at: string;
}

export interface IXuatBienBan {
  minio_key: string;
  url_tai: string;
  file_size: number;
  hash_noi_dung: string | null;
}

// ════════════════════════════════════════════════════════════
// MODULE 10 — KẾT LUẬN + DASHBOARD
// ════════════════════════════════════════════════════════════

export interface IKetLuanCreate {
  noi_dung: string;
  nguoi_phu_trach_id: string;
  don_vi_phu_trach_id?: string | null;
  han_hoan_thanh?: string | null;
  muc_uu_tien?: MucUuTien;
}

export interface IKetLuan {
  id: string;
  cuoc_hop_id: string;
  noi_dung: string;
  nguoi_phu_trach_id: string;
  don_vi_phu_trach_id: string | null;
  han_hoan_thanh: string | null;
  muc_uu_tien: MucUuTien;
  tien_do_phan_tram: number;
  trang_thai: TrangThaiKetLuan;
  created_at: string;
  updated_at: string;
}

export interface ITienDoCreate {
  phan_tram_sau: number;
  mo_ta: string;
  file_minh_chung_minio_key?: string | null;
}

export interface IDashboardCaNhan {
  so_cuoc_hop_thang_nay: number;
  so_cuoc_hop_tham_du: number;
  so_lan_vang: number;
  ty_le_tham_du: number;
  nhiem_vu_dang_lam: number;
  nhiem_vu_qua_han: number;
}

export interface IDashboardDonVi {
  don_vi_id: string;
  so_cuoc_hop: number;
  so_nhiem_vu_giao: number;
  so_nhiem_vu_hoan_thanh: number;
  so_nhiem_vu_qua_han: number;
  ty_le_hoan_thanh: number;
}

// ════════════════════════════════════════════════════════════
// NHÓM THÀNH PHẦN (dùng chung cho nhiều cuộc họp)
// ════════════════════════════════════════════════════════════

export type VaiTroNhom = 'CHU_TRI' | 'THU_KY' | 'THANH_VIEN';

export interface INhomChiTiet {
  id: string;
  nhom_id: string;
  cong_chuc_id: string;
  vai_tro: VaiTroNhom;
  loai_tham_du: LoaiThamDu;
  created_at: string;
  ho_ten?: string | null;
  ma_cc?: string | null;
  don_vi_id?: string | null;
  ten_don_vi?: string | null;
  chuc_vu?: string | null;
}

export interface INhomChiTietInput {
  cong_chuc_id: string;
  vai_tro?: VaiTroNhom;
  loai_tham_du?: LoaiThamDu;
}

export interface INhomChiTietUpdate {
  vai_tro?: VaiTroNhom;
  loai_tham_du?: LoaiThamDu;
}

export interface INhomCreate {
  ten_nhom: string;
  mo_ta?: string | null;
  loai_nhom?: string | null;
  chi_tiet?: INhomChiTietInput[];
}

export interface INhomUpdate {
  ten_nhom?: string;
  mo_ta?: string | null;
  loai_nhom?: string | null;
}

export interface INhom {
  id: string;
  ten_nhom: string;
  mo_ta: string | null;
  loai_nhom: string | null;
  nguoi_tao_id: string;
  created_at: string;
  updated_at: string;
  chi_tiet: INhomChiTiet[];
}

export interface INhomListItem {
  id: string;
  ten_nhom: string;
  mo_ta: string | null;
  loai_nhom: string | null;
  nguoi_tao_id: string;
  nguoi_tao_ho_ten?: string | null;
  created_at: string;
  updated_at: string;
  so_thanh_vien: number;
}

export interface IThemTuNhomResponse {
  so_them: number;
  so_bo_qua_trung: number;
  tong_thanh_phan: number;
  chu_toa_auto_filled: boolean;
  thu_ky_auto_filled: boolean;
}

// ════════════════════════════════════════════════════════════
// HKG PLATFORM ROLES (chuỗi const cho check inline)
// ════════════════════════════════════════════════════════════

export const HKG_PLATFORM_ROLES = {
  CHU_TOA_HOP: 'CHU_TOA_HOP',
  THU_KY_HOP: 'THU_KY_HOP',
  CHANH_VP: 'CHANH_VP',
  TRUONG_CNTT: 'TRUONG_CNTT',
  DANG_VIEN: 'DANG_VIEN',
  BI_THU_CHI_BO: 'BI_THU_CHI_BO',
  PHO_BI_THU: 'PHO_BI_THU',
} as const;

/** Roles có quyền truy cập module HKG ở giai đoạn UAT (feature flag). */
export const HKG_UAT_VISIBLE_ROLES = [
  'TRUONG_CNTT',
  'CHANH_VP',
  'THU_KY_HOP',
  'BI_THU_CHI_BO',
];

// ── Kho tài liệu chung (mục "HKG + Lịch công tác" trong Thư viện tài liệu) ──

export type NguonKhoTaiLieu = 'HKG' | 'LICH_CONG_TAC';

/**
 * Một tài liệu trong kho chung, kèm cuộc họp mà nó thuộc về.
 *
 * Duyệt cả kho thì phải biết file này của cuộc họp nào — nếu không, 866 file
 * chỉ là một danh sách tên rời rạc không tra cứu được.
 */
export interface ITaiLieuKhoItem {
  id: string;
  ten_tai_lieu: string;
  mo_ta: string | null;
  loai_tai_lieu: string | null;
  loai_nhan: string | null;
  extension: string | null;
  file_size: number;
  mime_type: string | null;
  phan_quyen: PhanQuyenTaiLieu;
  cho_phep_tai: boolean;
  created_at: string;

  cuoc_hop_id: string;
  nguon: NguonKhoTaiLieu;
  ma_lich: string | null;
  tieu_de: string;
  ngay_hop: string | null;
  /** Đường dẫn tới màn hình của cuộc họp — khác nhau giữa hai nguồn. */
  duong_dan_cuoc_hop: string;
  url_xem?: string;
}

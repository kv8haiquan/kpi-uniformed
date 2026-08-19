/**
 * src/types/lich-cong-tac.ts
 * ==========================
 * Kiểu dữ liệu cho module Lịch công tác (di trú từ lichkv8).
 *
 * Sự kiện trên lịch dùng chung bảng cuộc họp với Họp Không Giấy, phân biệt
 * bằng `nguon`. Sự kiện `nguon='HKG'` mở được sang màn hình chi tiết cuộc họp
 * — cờ `co_the_mo_hkg` do backend tính sẵn.
 */

export type LoaiLich =
  | 'HOP'
  | 'TRUC_BAN'
  | 'HOI_NGHI'
  | 'LAM_VIEC'
  | 'CONG_TAC'
  | 'LICH_KHAC';

export type NguonSuKien = 'HKG' | 'LICH_CONG_TAC';

export type TrangThaiLich =
  | 'LEN_KE_HOACH'
  | 'DA_THONG_BAO'
  | 'DANG_DIEN_RA'
  | 'HOAN_THANH'
  | 'HUY';

/** Nhãn tiếng Việt — giữ đúng cách gọi của lichkv8 để người dùng không phải học lại. */
export const NHAN_LOAI_LICH: Record<LoaiLich, string> = {
  HOP: 'Họp',
  TRUC_BAN: 'Trực ban',
  HOI_NGHI: 'Hội nghị',
  LAM_VIEC: 'Làm việc',
  CONG_TAC: 'Đi công tác',
  LICH_KHAC: 'Lịch khác',
};

export const NHAN_TRANG_THAI: Record<TrangThaiLich, string> = {
  LEN_KE_HOACH: 'Nháp',
  DA_THONG_BAO: 'Đã đăng',
  DANG_DIEN_RA: 'Đang diễn ra',
  HOAN_THANH: 'Hoàn thành',
  HUY: 'Đã hủy',
};

export interface INguoiTomTat {
  id: string;
  ho_ten: string;
  chuc_vu?: string | null;
}

export interface ISuKienLich {
  id: string;
  nguon: NguonSuKien;
  ma_lich?: string | null;
  tieu_de: string;
  loai_lich?: LoaiLich | null;
  loai_lich_nhan?: string | null;

  ngay_hien_thi?: string | null;
  ngay_hop: string;
  ngay_ket_thuc?: string | null;
  gio_bat_dau: string;
  gio_ket_thuc?: string | null;

  dia_diem?: string | null;
  trang_thai: TrangThaiLich;

  /** Khớp được công chức thì có chu_toa; không thì đọc chu_tri_text. */
  chu_toa?: INguoiTomTat | null;
  chu_tri_text?: string | null;

  don_vi_chuan_bi?: string | null;
  so_van_ban?: string | null;
  lanh_dao_lien_quan: INguoiTomTat[];
  so_tai_lieu: number;

  /** Bấm vào mở được sang chi tiết cuộc họp trong Họp Không Giấy. */
  co_the_mo_hkg: boolean;
}

export interface ISuKienChiTiet extends ISuKienLich {
  /** Người tạo — giao diện dựa vào đây để ẩn/hiện nút Sửa, Xoá. */
  created_by?: string | null;
  mo_ta?: string | null;
  thanh_phan_text?: string | null;
  ly_do_huy?: string | null;
}

export interface ILichThang {
  nam: number;
  thang: number;
  tong: number;
  /** Khóa là ngày dạng YYYY-MM-DD; sự kiện nhiều ngày lặp ở mọi ngày nó kéo dài. */
  theo_ngay: Record<string, ISuKienLich[]>;
}

export interface ITomTatNgay {
  ngay: string;
  thu: string;
  su_kien: ISuKienLich[];
  truc_ban: string[];
}

export interface ITomTatLich {
  tu_ngay: string;
  den_ngay: string;
  theo_ngay: ITomTatNgay[];
  /** Bản text sẵn để dán sang Zalo hoặc email. */
  van_ban_thuan: string;
}

export interface ILichLanhDaoNgay {
  ngay: string;
  su_kien: ISuKienLich[];
}

export interface ILichLanhDao {
  lanh_dao: INguoiTomTat;
  tong_su_kien: number;
  theo_ngay: ILichLanhDaoNgay[];
}

export interface IThongKeLich {
  hom_nay: number;
  ngay_mai: number;
  trong_tuan: number;
  trong_thang: number;
  trong_nam: number;
  theo_loai_thang_nay: Record<string, number>;
  theo_lanh_dao_thang_nay: {
    cong_chuc_id: string;
    ho_ten: string;
    chuc_vu: string | null;
    so_su_kien: number;
  }[];
  /** Mốc ngày của từng chỉ số — để bấm thẻ là mở lịch đúng khoảng đó. */
  moc: {
    hom_nay: string;
    ngay_mai: string;
    dau_tuan: string;
    cuoi_tuan: string;
    dau_thang: string;
    cuoi_thang: string;
    dau_nam: string;
    cuoi_nam: string;
  };
}

export interface IDanhMucLoai {
  ma: LoaiLich;
  ten: string;
}

// ─── Thống kê tài liệu họp (G4.6) ───────────────────────────────────────

/**
 * Năm mức tình trạng tài liệu, giữ đúng của lichkv8.
 *
 * `TAT_CA` là giá trị BỘ LỌC, không phải tình trạng của một dòng — dòng chỉ
 * nhận ba mức cuối. `CO_GIAO_CHUAN_BI` cũng chỉ dùng để lọc (= đã gắn + thiếu).
 */
export type TinhTrangTaiLieu =
  | 'TAT_CA'
  | 'CO_GIAO_CHUAN_BI'
  | 'DA_GAN_TAI_LIEU'
  | 'THIEU_TAI_LIEU'
  | 'CHUA_GIAO_CHUAN_BI';

export interface IDongThongKeTaiLieu {
  id: string;
  ma_lich: string | null;
  ngay: string | null;
  gio_bat_dau: string | null;
  tieu_de: string;
  loai_lich: string | null;
  trang_thai: string;
  lanh_dao: string[];
  chu_tri: string;
  don_vi_chuan_bi: string | null;
  so_van_ban: string | null;
  /** Tổng số file đính kèm. */
  so_tai_lieu: number;
  /** Số file tính là tài liệu chuẩn bị — giấy mời thuần KHÔNG được tính. */
  so_tai_lieu_chuan_bi: number;
  so_giay_moi: number;
  tinh_trang: TinhTrangTaiLieu;
  tinh_trang_nhan: string;
}

export interface ITongHopTaiLieu {
  tong: number;
  CO_GIAO_CHUAN_BI: number;
  DA_GAN_TAI_LIEU: number;
  THIEU_TAI_LIEU: number;
  CHUA_GIAO_CHUAN_BI: number;
}

export interface IBaoCaoTaiLieu {
  dong: IDongThongKeTaiLieu[];
  tong_hop: ITongHopTaiLieu;
}

export interface IDanhMucTinhTrang {
  ma: TinhTrangTaiLieu;
  ten: string;
}

// ─── Quản lý lịch (G4.3) ────────────────────────────────────────────────

/**
 * Dữ liệu ghi khi tạo hoặc sửa. Tạo thì các trường bắt buộc phải có; sửa thì
 * chỉ gửi những trường thật sự đổi (backend dùng PATCH, `exclude_unset`).
 */
export interface ILichCongTacGhi {
  tieu_de?: string;
  loai_lich?: LoaiLich;
  ngay_hop?: string;
  ngay_ket_thuc?: string | null;
  ngay_hien_thi?: string | null;
  gio_bat_dau?: string;
  gio_ket_thuc?: string | null;
  dia_diem?: string | null;
  mo_ta?: string | null;
  trang_thai?: TrangThaiLich;
  chu_toa_id?: string | null;
  chu_tri_text?: string | null;
  thanh_phan_text?: string | null;
  don_vi_chuan_bi?: string | null;
  so_van_ban?: string | null;
  lanh_dao_lien_quan_ids?: string[];
}

export interface IQuyenLich {
  /** Sửa được MỌI sự kiện. Người thường chỉ sửa được lịch mình tạo. */
  la_quan_tri_lich: boolean;
  cong_chuc_id: string;
}

export interface IDongNhatKy {
  hanh_dong: string;
  thoi_diem: string;
  nguoi_thuc_hien: string | null;
  chi_tiet: {
    ma_lich?: string;
    tieu_de?: string;
    ly_do?: string;
    thay_doi?: { truong: string; nhan: string; cu: string; moi: string }[];
  } | null;
}

// ─── Trực ban (G4.7) ────────────────────────────────────────────────────

export interface ITruSo {
  id: string;
  ma_tru_so: string;
  ten_tru_so: string;
  don_vi_id: string | null;
  thu_tu: number;
}

export interface INguoiTruc {
  id: string;
  ho_ten: string;
  chuc_vu: string | null;
  so_dien_thoai: string | null;
  cong_chuc_id: string | null;
  ca_truc: string;
  loai_truc: string;
  ghi_chu: string | null;
  trang_thai: string;
}

export interface IOTruc {
  tru_so_id: string;
  nguoi: INguoiTruc[];
  /** NHAP = còn sửa được; DA_NOP = đã chốt. */
  trang_thai: string;
  /** Đã nộp thì khoá — muốn sửa phải nhờ Văn phòng mở khoá. */
  is_locked: boolean;
  /** Người đang đăng nhập có sửa được ô này không. */
  sua_duoc: boolean;
}

export interface IHangTruc {
  ngay: string;
  thu: string;
  cuoi_tuan: boolean;
  o: IOTruc[];
}

export interface IMaTranTruc {
  tu_ngay: string;
  den_ngay: string;
  tru_so: ITruSo[];
  hang: IHangTruc[];
  la_quan_tri: boolean;
}

export interface ITrucBanGhi {
  ngay_truc?: string;
  tru_so_id?: string;
  ho_ten?: string;
  chuc_vu?: string | null;
  so_dien_thoai?: string | null;
  ca_truc?: string;
  loai_truc?: string;
  ghi_chu?: string | null;
}

// ─── Nhập trực ban từ Excel (G4.8) ──────────────────────────────────────

export interface IDongNhapExcel {
  dong: number;
  ngay_truc: string | null;
  ma_tru_so: string | null;
  tru_so_id: string | null;
  ten_tru_so: string | null;
  ho_ten: string | null;
  chuc_vu: string | null;
  so_dien_thoai: string | null;
  ca_truc: string;
  loai_truc: string;
  ghi_chu: string | null;
  hop_le: boolean;
  /** Lý do dòng này không dùng được — hiện thẳng cho người nhập sửa file. */
  loi: string[];
}

export interface IKetQuaXemTruoc {
  tong_dong: number;
  so_hop_le: number;
  so_loi: number;
  dong: IDongNhapExcel[];
}

// ─── Đối soát tài liệu di trú (G4.9 — dùng một lần) ─────────────────────

export interface IFileTrongThuMuc {
  drive_file_id: string;
  ten: string;
  so_byte: number | null;
  /** Đường dẫn con so với thư mục gốc; rỗng nếu nằm ngay trong. */
  thu_muc_con: string;
}

export type QuyetDinhDoiSoat =
  | 'GAN_CUOC_HOP'
  | 'TAO_CUOC_HOP_LICH_SU'
  | 'KHO_LUU_TRU'
  | 'KHONG_DI_TRU';

export interface IThuMucDoiSoat {
  id: string;
  nhom: string;
  duong_dan_thu_muc: string;
  ten_thu_muc: string;
  drive_folder_id: string;
  so_file: number;
  ngay_suy_ra: string | null;
  so_gm_suy_ra: string | null;
  danh_sach_file: IFileTrongThuMuc[];
  quyet_dinh: QuyetDinhDoiSoat | null;
  quyet_dinh_nhan: string | null;
  cuoc_hop_id: string | null;
  nguoi_quyet_dinh: string | null;
  thoi_diem_quyet_dinh: string | null;
  ghi_chu: string | null;
}

export interface IDanhSachDoiSoat {
  dong: IThuMucDoiSoat[];
  tong_hop: {
    tong_thu_muc: number;
    tong_file: number;
    da_quyet_dinh: number;
    con_lai: number;
  };
}

export interface IUngVienDoiSoat {
  cuoc_hop_id: string;
  ma_lich: string | null;
  tieu_de: string;
  ngay: string | null;
  gio_bat_dau: string | null;
  so_van_ban: string | null;
  don_vi_chuan_bi: string | null;
  diem: number;
  tu_trung: string[];
}

export interface IGoiYDoiSoat {
  thu_muc: string;
  ngay_suy_ra: string | null;
  so_ung_vien: number;
  /**
   * Có ứng viên nào vượt hẳn không. Sai thì đừng tin ứng viên đầu bảng —
   * ngày nào cũng có 2–8 cuộc họp nên rất hay hoà điểm.
   */
  co_ung_vien_noi_troi: boolean;
  ung_vien: IUngVienDoiSoat[];
}

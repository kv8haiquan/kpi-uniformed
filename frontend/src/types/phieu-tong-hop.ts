/**
 * src/types/phieu-tong-hop.ts
 * ============================
 * Bảng tổng hợp phiếu đánh giá quý (Mẫu 02A/02B) toàn Chi cục — CHỈ ĐỌC.
 *
 * Khớp với `PhieuTongHopItem` ở backend (app/schemas/phieu_danh_gia.py).
 */

export type TrangThaiPhieu = 'NHAP' | 'CHO_PHE_DUYET' | 'DA_PHE_DUYET' | 'BI_TU_CHOI';

export type MaXepLoai = 'HTXSNV' | 'HTTNV' | 'HTNV' | 'KHTNV';

export interface IPhieuTongHopItem {
  /** null nghĩa là người này CHƯA soạn phiếu (dòng giả trạng thái NHAP). */
  id: string | null;
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  don_vi_id: string | null;
  don_vi_ten: string | null;
  vai_tro: string | null;
  is_lanh_dao: boolean;
  quy: number;
  nam: number;
  trang_thai: TrangThaiPhieu;
  ngay_gui_duyet: string | null;
  ngay_phe_duyet: string | null;
  nguoi_phe_duyet_ten: string | null;
  uu_diem: string | null;
  han_che: string | null;
  y_kien_lanh_dao: string | null;
  tu_de_xuat_xep_loai: MaXepLoai | null;
  de_xuat_xep_loai: MaXepLoai | null;
  quyet_dinh_xep_loai: MaXepLoai | null;
  y_kien_cap_tham_quyen: string | null;
  // SỐ LIỆU CŨ — "kê khai lại tiêu chí đ cấp quý" đã gỡ 29/09/2026, chỉ để tra cứu.
  dd_quy_ke_khai: number | null;
  dd_quy_ghi_chu: string | null;
  dd_quy_phe_duyet: number | null;
}

export interface IPhieuTongHopThongKe {
  tong_so: number;
  theo_trang_thai: Record<string, number>;
  theo_xep_loai: Record<string, number>;
  chua_quyet_dinh_xep_loai: number;
}

export interface IPhieuTongHopData {
  items: IPhieuTongHopItem[];
  tong_hop: IPhieuTongHopThongKe;
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}

export interface IPhieuTongHopFilter {
  quy: number;
  nam: number;
  don_vi_id?: string;
  trang_thai?: TrangThaiPhieu;
  xep_loai?: MaXepLoai;
  tim?: string;
  page?: number;
  page_size?: number;
}

export const NHAN_TRANG_THAI_PHIEU: Record<TrangThaiPhieu, string> = {
  NHAP: 'Chưa gửi',
  CHO_PHE_DUYET: 'Chờ duyệt',
  DA_PHE_DUYET: 'Đã duyệt',
  BI_TU_CHOI: 'Bị từ chối',
};

export const NHAN_XEP_LOAI: Record<MaXepLoai, string> = {
  HTXSNV: 'Hoàn thành xuất sắc nhiệm vụ',
  HTTNV: 'Hoàn thành tốt nhiệm vụ',
  HTNV: 'Hoàn thành nhiệm vụ',
  KHTNV: 'Không hoàn thành nhiệm vụ',
};

/** Nhãn ngắn để nhét vừa một ô bảng. */
export const NHAN_XEP_LOAI_NGAN: Record<MaXepLoai, string> = {
  HTXSNV: 'HT xuất sắc',
  HTTNV: 'HT tốt',
  HTNV: 'Hoàn thành',
  KHTNV: 'Không HT',
};

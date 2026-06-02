/**
 * src/types/hdld.ts
 * =================
 * Types cho Bộ tiêu chí đánh giá HĐLĐ 111 theo VB714 (QĐ 714/QĐ-CHQ, 08/5/2026).
 * Áp dụng từ tháng 5/2026.
 */

export type HdldNhom = 'I' | 'II' | 'III' | 'IV' | 'V' | 'VI';

export type HdldTrangThai = 'NHAP' | 'CHO_DUYET' | 'DA_DUYET' | 'TRA_LAI';

export const HDLD_TRANG_THAI_LABEL: Record<HdldTrangThai, string> = {
  NHAP: 'Nháp',
  CHO_DUYET: 'Chờ duyệt',
  DA_DUYET: 'Đã duyệt',
  TRA_LAI: 'Bị trả lại',
};

export const HDLD_NHOM_LABEL: Record<HdldNhom, string> = {
  I: 'Nhân viên lái xe',
  II: 'Nhân viên bảo vệ',
  III: 'Nhân viên lễ tân, phục vụ',
  IV: 'Nhân viên tạp vụ',
  V: 'Nhân viên kỹ thuật (bảo trì, bảo dưỡng, vận hành)',
  VI: 'Nhân viên HĐLĐ làm công việc khác',
};

export interface IHdldTieuChi {
  id: string;
  nhom: string;
  ten_nhom: string;
  so_tt: number;
  ten_tieu_chi: string;
  mo_ta_chi_tiet: string;
  diem_toi_da: number;
}

export interface IHdldTieuChiResponse {
  nhom: string;
  ten_nhom: string;
  tieu_chi: IHdldTieuChi[];
}

export interface IHdldChiTiet {
  so_tt: number;
  diem_tu: number | null;
  ghi_chu_tu: string | null;
  diem_ql: number | null;
  ghi_chu_ql: string | null;
  ly_do_sua: string | null;
  ten_tieu_chi: string | null;
  mo_ta_chi_tiet: string | null;
}

export interface ICongChucBrief {
  id: string;
  ma_cc: string | null;
  ho_ten: string | null;
  chuc_vu: string | null;
}

export interface IHdldDanhGia {
  id: string;
  cong_chuc_id: string;
  thang: number;
  nam: number;
  nhom_nghe: string | null;
  ten_nhom: string | null;
  trang_thai: HdldTrangThai;
  nguoi_duyet_id: string | null;
  nguoi_duyet: ICongChucBrief | null;
  cong_chuc: ICongChucBrief | null;
  diem_tc_tb_tu: number | null;
  diem_tc_tb_ql: number | null;
  diem_kpi_70: number | null;
  ghi_chu: string | null;
  ly_do_tra_lai: string | null;
  ngay_nop: string | null;
  ngay_duyet: string | null;
  chi_tiets: IHdldChiTiet[];
}

export interface INguoiDuyetOption {
  id: string;
  ma_cc: string | null;
  ho_ten: string | null;
  chuc_vu: string | null;
  cap_bac: string | null;
}

// ============================ REQUESTS ============================ //

export interface IHdldChiTietTuDanhGia {
  so_tt: number;
  diem_tu: number;
  ghi_chu_tu?: string | null;
}

export interface IHdldTuDanhGiaRequest {
  nhom_nghe: string;
  chi_tiets: IHdldChiTietTuDanhGia[];
  ghi_chu?: string | null;
}

export interface IHdldNopRequest {
  nguoi_duyet_id: string;
}

export interface IHdldChiTietDuyet {
  so_tt: number;
  diem_ql: number;
  ghi_chu_ql?: string | null;
  ly_do_sua?: string | null;
}

export interface IHdldDuyetRequest {
  chi_tiets: IHdldChiTietDuyet[];
  ghi_chu?: string | null;
}

export interface IHdldTraLaiRequest {
  ly_do: string;
}

// Mốc áp dụng VB714 (đồng bộ backend) — 01/06/2026: đổi về T1/2026
// (HĐLĐ kê khai lại toàn bộ T1–T6 theo VB714)
export const HDLD_VB714_FROM = { nam: 2026, thang: 1 };

export function isHdldVb714Active(thang: number, nam: number): boolean {
  return nam > HDLD_VB714_FROM.nam
    || (nam === HDLD_VB714_FROM.nam && thang >= HDLD_VB714_FROM.thang);
}

/** Trích message lỗi từ response axios (FastAPI HTTPException detail hoặc error.message). */
export function getHdldErrorMessage(err: unknown, fallback: string): string {
  const e = err as {
    response?: { data?: { detail?: string | { message?: string }; error?: { message?: string } } };
    message?: string;
  };
  const detail = e?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  return detail?.message
    ?? e?.response?.data?.error?.message
    ?? e?.message
    ?? fallback;
}

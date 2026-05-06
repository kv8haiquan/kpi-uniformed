/**
 * src/types/dieuChinhKqcv.ts
 * ==========================
 * Types cho điều chỉnh KQCV (Yêu cầu 2 — 06/05/2026).
 */

export interface IGiaTriKQCV {
  so_loi_chat_luong: number;
  so_loi_tien_do: number;
  is_chua_hoan_thanh: boolean;
}

export interface ICongChucBriefDC {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
}

export interface IDieuChinhKqcv {
  id: string;
  ke_khai_id: string;
  nguoi_dieu_chinh_id: string;
  nguoi_phe_duyet_id: string;
  gia_tri_cu: IGiaTriKQCV;
  gia_tri_moi: IGiaTriKQCV;
  ly_do: string;
  trang_thai: 'NHAP' | 'CHO_PHE_DUYET' | 'DA_PHE_DUYET' | 'TU_CHOI';
  y_kien_phe_duyet: string | null;
  ngay_phe_duyet: string | null;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  nguoi_dieu_chinh?: ICongChucBriefDC | null;
  nguoi_phe_duyet?: ICongChucBriefDC | null;
}

export interface IDieuChinhCreateRequest {
  ke_khai_id: string;
  gia_tri_moi: IGiaTriKQCV;
  ly_do: string;
}

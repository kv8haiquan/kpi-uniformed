/**
 * src/types/kpi-v2.ts
 * ===================
 * TypeScript types cho Phiên bản KPI V2_PL3 (28/04/2026).
 *
 * Khác V1:
 * - KHÔNG có cap_do_id (V2 bỏ C1-C5).
 * - KHÔNG có he_so_thuc_te (LOCKED 14 — không cho override).
 * - Mục PL3 có sẵn he_so_quy_doi.
 * - Snapshot fields: he_so_quy_doi_snapshot, nhom_pl3_snapshot, linh_vuc_snapshot.
 */

export type KpiVersion = 'V1' | 'V2_PL3';

// =============================================================================
// DANH MỤC PL3
// =============================================================================

/**
 * 1 mục PL3 (đã bỏ 4 fields chấm chi tiết theo decision Phase A).
 */
export interface IDanhMucPL3 {
  id: string;
  ma_danh_muc: string;
  ten_cong_viec: string;
  cong_viec_chi_tiet: string | null;
  san_pham_dau_ra: string | null;
  nhiem_vu: string | null;
  mo_ta?: string | null;  // ghi chú thêm (cột M trong Excel hoặc admin nhập)
  nguon_du_lieu?: string;  // 'V1' | 'PL3'
  linh_vuc: string;        // 'I'..'XV'
  ten_linh_vuc: string;
  nhom_pl3: number;        // 1..5
  khung_diem_toi_da: number; // 100/200/300/400/500
  diem_cham: number;
  he_so_quy_doi: number;   // = diem_cham / 25
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * Lĩnh vực (cho dropdown filter).
 */
export interface ILinhVuc {
  ma: string;   // 'I'..'XV'
  ten: string;
}

/**
 * Nhiệm vụ (cột B Excel PL3) — distinct theo lĩnh vực.
 */
export interface INhiemVu {
  nhiem_vu: string;
}

// =============================================================================
// REQUEST PAYLOADS
// =============================================================================

/**
 * Tạo kê khai V2 mới.
 */
export interface IKeKhaiV2CreateRequest {
  danh_muc_sp_id: string;
  so_luong: number;        // > 0, integer
  thang: number;           // 1-12
  nam: number;             // >= 2025
  ngay_thuc_hien?: string; // YYYY-MM-DD
  mo_ta_cong_viec?: string;
  is_doi_moi_sang_tao?: boolean;
  ngay_deadline?: string;
  ngay_hoan_thanh?: string;
  nguoi_phe_duyet_id: string;
  tu_danh_gia_chat_luong?: number;
  tu_danh_gia_tien_do?: number;
  ghi_chu_tu_danh_gia?: string;
  ghi_chu_tu_dg_chat_luong?: string;
  ghi_chu_tu_dg_tien_do?: string;
  // KHÔNG có cap_do_id, KHÔNG có he_so_thuc_te (LOCKED 14)
}

/**
 * Sửa kê khai V2 (NHAP/TU_CHOI).
 */
export type IKeKhaiV2UpdateRequest = Partial<IKeKhaiV2CreateRequest>;

/**
 * Tạo nhiều ngày V2.
 */
export interface IKeKhaiV2MultiDayRequest {
  danh_muc_sp_id: string;
  so_luong: number;
  ngay_thuc_hien_list: string[]; // YYYY-MM-DD[]
  nguoi_phe_duyet_id: string;
  mo_ta_cong_viec?: string;
  is_doi_moi_sang_tao?: boolean;
  tu_danh_gia_chat_luong?: number;
  tu_danh_gia_tien_do?: number;
  ghi_chu_tu_danh_gia?: string;
  ghi_chu_tu_dg_chat_luong?: string;
  ghi_chu_tu_dg_tien_do?: string;
}

// =============================================================================
// RESPONSE
// =============================================================================

/**
 * 1 bản kê khai V2 (response).
 */
export interface IKeKhaiV2Response {
  id: string;
  cong_chuc_id: string;
  thang: number;
  nam: number;
  ngay_thuc_hien: string | null;

  // Snapshot (immutable)
  version_kekhai: 'V2_PL3';
  he_so_quy_doi_snapshot: number | null;
  nhom_pl3_snapshot: number | null;
  linh_vuc_snapshot: string | null;

  danh_muc_sp: IDanhMucPL3 | null;

  so_luong: number;
  nguoi_phe_duyet_id: string | null;
  nguoi_phe_duyet: {
    id: string;
    ho_ten: string;
    chuc_vu: string | null;
  } | null;
  mo_ta_cong_viec: string | null;
  is_doi_moi_sang_tao: boolean;
  ngay_deadline: string | null;
  ngay_hoan_thanh: string | null;
  trang_thai: string;

  tu_danh_gia_chat_luong: number;
  tu_danh_gia_tien_do: number;
  ghi_chu_tu_danh_gia: string | null;
  ghi_chu_tu_dg_chat_luong: string | null;
  ghi_chu_tu_dg_tien_do: string | null;

  so_loi_chat_luong: number;
  so_loi_tien_do: number;
  y_kien_lanh_dao: string | null;
  ghi_chu_loi_chat_luong: string | null;
  ghi_chu_loi_tien_do: string | null;

  so_sp_goc_quy_doi: number | null;
  so_sp_chat_luong: number | null;
  so_sp_tien_do: number | null;

  is_khoa: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Thống kê tháng V2 (banner UI).
 */
export interface IThongKeKeKhaiThangV2 {
  thang: number;
  nam: number;
  version_kekhai: KpiVersion;
  tong_sp_da_duyet: number;     // mẫu số chính thức
  tong_sp_cho_duyet: number;
  tong_sp_du_kien: number;
  // Trang /danh-gia-v2: tổng SP đạt CL/TĐ chính thức (DA_PHE_DUYET)
  tong_sp_chat_luong_da_duyet?: number;
  tong_sp_tien_do_da_duyet?: number;
  // Trang /danh-gia-v2: tổng SP đạt CL/TĐ tạm tính (NHAP + CHO + DA)
  tong_sp_chat_luong_tam_tinh?: number;
  tong_sp_tien_do_tam_tinh?: number;
  so_kekhai_da_duyet: number;
  so_kekhai_cho_duyet: number;
  so_kekhai_nhap: number;
}

/**
 * Response sau tạo nhiều ngày.
 */
export interface IKeKhaiV2MultiDayResponse {
  total_created: number;
  ke_khai_ids: string[];
  thang: number;
  nam: number;
}

// =============================================================================
// FILTER PARAMS
// =============================================================================

export interface ISearchPL3Params {
  linh_vuc?: string;
  nhiem_vu?: string;
  nhom_pl3?: number;
  search?: string;
  page?: number;
  size?: number;
}

export interface IListMyKeKhaiV2Params {
  thang?: number;
  nam?: number;
  trang_thai?: string;
  page?: number;
  page_size?: number;
}

// =============================================================================
// FAVORITES + RECENT (30/04/2026)
// =============================================================================

/**
 * 1 mục công việc yêu thích.
 */
export interface IFavoriteItem {
  id: string;
  danh_muc_sp_id: string;
  danh_muc_sp: IDanhMucPL3;
  created_at: string;
}

/**
 * 1 mục đã dùng gần đây (look-back tối đa 3 tháng có data).
 */
export interface IRecentItem {
  danh_muc_sp_id: string;
  danh_muc_sp: IDanhMucPL3;
  last_used_thang: number;
  last_used_nam: number;
  used_count_3m: number;
}

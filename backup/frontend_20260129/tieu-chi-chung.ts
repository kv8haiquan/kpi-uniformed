/**
 * src/types/tieu-chi-chung.ts
 * ============================
 * Types cho Module Tiêu chí chung - ĐỒNG BỘ VỚI BACKEND v2.5.0
 * 
 * ⚠️ QUAN TRỌNG:
 * - Backend dùng `ma_tieu_chi` (string) cho POST, KHÔNG phải `tieu_chi_id` (UUID)
 * - Master Data trả về 10 TC lớn, chia theo nhóm { nhom_1, nhom_2, nhom_3 }
 * - Người phê duyệt trả về `danh_sach`, không phải `data`
 * 
 * Version: 2.5.4 (27/01/2026)
 */

// =============================================================================
// ENUMS
// =============================================================================

export enum TrangThaiTieuChiChung {
  CHUA_DANH_GIA = 'CHUA_DANH_GIA',
  NHAP = 'NHAP',
  CHO_PHE_DUYET = 'CHO_PHE_DUYET',
  DA_PHE_DUYET = 'DA_PHE_DUYET',
}

export enum TrangThaiDanhGiaThang {
  CHUA_DANH_GIA = 'CHUA_DANH_GIA',
  DANG_DANH_GIA = 'DANG_DANH_GIA',
  CHO_TONG_HOP = 'CHO_TONG_HOP',
  DA_TONG_HOP = 'DA_TONG_HOP',
  CHO_PHE_DUYET = 'CHO_PHE_DUYET',
  HOAN_THANH = 'HOAN_THANH',
}

export enum LogicChamDiem {
  ALL_OR_NOTHING = 'ALL_OR_NOTHING',
  BONUS = 'BONUS',
}

// =============================================================================
// MASTER DATA INTERFACES
// =============================================================================

/** Một tiêu chí trong Master Data */
export interface ITieuChiChungMaster {
  id: string;
  ma_tieu_chi: string;           // "1.1", "1.2", ..., "3.4"
  ma_tieu_chi_con: string | null;
  nhom_tieu_chi: 1 | 2 | 3;
  ten_tieu_chi: string;
  mo_ta?: string | null;
  diem_toi_da: number;
  gia_tri_mac_dinh: boolean;
  loai_logic: string;            // "ALL_OR_NOTHING" | "BONUS"
  parent_ma_tieu_chi: string | null;
  thu_tu: number;
}

/** Response danh mục tiêu chí (chia theo nhóm) */
export interface IDanhMucTieuChiResponse {
  nhom_1: ITieuChiChungMaster[];
  nhom_2: ITieuChiChungMaster[];
  nhom_3: ITieuChiChungMaster[];
  tong_diem_toi_da?: number;
}

// =============================================================================
// RESPONSE INTERFACES
// =============================================================================

/** Tổng hợp điểm theo nhóm */
export interface ITieuChiChungTongHop {
  nhom_1_diem: number;
  nhom_2_diem: number;
  nhom_3_diem: number;
  tong_diem: number;
}

/** Một tiêu chí trong response đánh giá */
export interface ITieuChiChungResponse {
  id?: string | null;
  danh_gia_thang_id?: string | null;
  tieu_chi_id?: string | null;
  ma_tieu_chi: string;
  ten_tieu_chi: string;
  nhom_tieu_chi: number;
  diem_toi_da: number;
  gia_tri_mac_dinh: boolean;
  is_achieved_cc: boolean;
  is_achieved_ld?: boolean | null;
  is_achieved: boolean;          // Kết quả cuối cùng
  diem_tu_cham: number;
  diem_phe_duyet?: number | null;
  diem: number;                  // Điểm cuối cùng
  trang_thai: TrangThaiTieuChiChung;
  ghi_chu_cc?: string | null;
  ghi_chu_ld?: string | null;
  ly_do_dieu_chinh?: string | null;
  ngay_gui?: string | null;
  ngay_phe_duyet?: string | null;
}

/** Response kết quả đánh giá tháng (có Virtual Record) */
export interface IKetQuaTieuChiChungResponse {
  danh_gia_thang_id?: string | null;
  cong_chuc_id: string;
  thang: number;
  nam: number;
  is_new_record: boolean;         // Virtual Record flag
  so_ngay_trong_thang: number;
  so_ngay_nghi_phep: number;
  so_ngay_lam_viec: number;
  target_kpi: number;
  trang_thai: TrangThaiTieuChiChung;
  trang_thai_danh_gia_thang?: TrangThaiDanhGiaThang;
  tong_hop: ITieuChiChungTongHop;
  tieu_chi: ITieuChiChungResponse[];
  nguoi_phe_duyet_id?: string | null;
  nguoi_phe_duyet_ten?: string | null;
  ngay_gui?: string | null;
  ngay_phe_duyet?: string | null;
}

// =============================================================================
// REQUEST INTERFACES
// =============================================================================

/** Input một tiêu chí khi tự đánh giá - DÙNG ma_tieu_chi */
export interface ITieuChiChungInput {
  ma_tieu_chi: string;           // ⚠️ Backend dùng ma_tieu_chi, KHÔNG phải tieu_chi_id
  is_achieved_cc: boolean;
  ghi_chu_cc?: string | null;
}

/** Request tự đánh giá */
export interface ITuDanhGiaRequest {
  thang: number;
  nam: number;
  tieu_chi: ITieuChiChungInput[];
  gui_phe_duyet: boolean;
  nguoi_phe_duyet_id?: string;
}

// =============================================================================
// FORM STATE TYPES
// =============================================================================

/** Form state: key = ma_tieu_chi, value = boolean */
export type ITieuChiFormState = Record<string, boolean>;

/** Ghi chú: key = ma_tieu_chi, value = string */
export type ITieuChiGhiChu = Record<string, string>;

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

export function getTrangThaiLabel(trangThai: TrangThaiTieuChiChung): string {
  const labels: Record<TrangThaiTieuChiChung, string> = {
    [TrangThaiTieuChiChung.CHUA_DANH_GIA]: 'Chưa đánh giá',
    [TrangThaiTieuChiChung.NHAP]: 'Nháp',
    [TrangThaiTieuChiChung.CHO_PHE_DUYET]: 'Chờ phê duyệt',
    [TrangThaiTieuChiChung.DA_PHE_DUYET]: 'Đã phê duyệt',
  };
  return labels[trangThai] || trangThai;
}

export function getTrangThaiBadgeClass(trangThai: TrangThaiTieuChiChung): string {
  const classes: Record<TrangThaiTieuChiChung, string> = {
    [TrangThaiTieuChiChung.CHUA_DANH_GIA]: 'bg-gray-100 text-gray-600 border-gray-300',
    [TrangThaiTieuChiChung.NHAP]: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    [TrangThaiTieuChiChung.CHO_PHE_DUYET]: 'bg-blue-100 text-blue-700 border-blue-300',
    [TrangThaiTieuChiChung.DA_PHE_DUYET]: 'bg-green-100 text-green-700 border-green-300',
  };
  return classes[trangThai] || '';
}

/**
 * Tính điểm preview từ form state.
 * Nhóm 1 & 2: mặc định đạt = full điểm
 * Nhóm 3: mặc định không đạt = 0 điểm
 */
export function tinhDiemTuFormState(
  masterData: ITieuChiChungMaster[],
  formState: ITieuChiFormState
): ITieuChiChungTongHop {
  let nhom1 = 0, nhom2 = 0, nhom3 = 0;
  
  for (const tc of masterData) {
    // Sử dụng ma_tieu_chi làm key
    const isAchieved = formState[tc.ma_tieu_chi] ?? tc.gia_tri_mac_dinh;
    const diem = isAchieved ? tc.diem_toi_da : 0;
    
    if (tc.nhom_tieu_chi === 1) nhom1 += diem;
    else if (tc.nhom_tieu_chi === 2) nhom2 += diem;
    else if (tc.nhom_tieu_chi === 3) nhom3 += diem;
  }
  
  return {
    nhom_1_diem: nhom1,
    nhom_2_diem: nhom2,
    nhom_3_diem: nhom3,
    tong_diem: nhom1 + nhom2 + nhom3,
  };
}

/**
 * Init form state từ response (nếu có) hoặc default.
 * Key = ma_tieu_chi
 */
export function initFormStateFromResponse(
  response: IKetQuaTieuChiChungResponse | null,
  masterData: ITieuChiChungMaster[]
): ITieuChiFormState {
  const state: ITieuChiFormState = {};
  
  if (response && response.tieu_chi && response.tieu_chi.length > 0) {
    // Từ response
    for (const tc of response.tieu_chi) {
      state[tc.ma_tieu_chi] = tc.is_achieved_cc;
    }
  } else {
    // Default từ master data
    for (const tc of masterData) {
      state[tc.ma_tieu_chi] = tc.gia_tri_mac_dinh;
    }
  }
  
  return state;
}

/**
 * Init ghi chú từ response.
 * Key = ma_tieu_chi
 */
export function initGhiChuFromResponse(
  response: IKetQuaTieuChiChungResponse | null
): ITieuChiGhiChu {
  const ghiChu: ITieuChiGhiChu = {};
  
  if (response && response.tieu_chi) {
    for (const tc of response.tieu_chi) {
      if (tc.ghi_chu_cc) {
        ghiChu[tc.ma_tieu_chi] = tc.ghi_chu_cc;
      }
    }
  }
  
  return ghiChu;
}

/**
 * Convert form state sang payload để gửi API.
 * ⚠️ Backend dùng ma_tieu_chi, KHÔNG phải tieu_chi_id
 */
export function convertFormToPayload(
  masterData: ITieuChiChungMaster[],
  formState: ITieuChiFormState,
  ghiChu: ITieuChiGhiChu
): ITieuChiChungInput[] {
  return masterData.map((tc: ITieuChiChungMaster): ITieuChiChungInput => ({
    ma_tieu_chi: tc.ma_tieu_chi,
    is_achieved_cc: formState[tc.ma_tieu_chi] ?? tc.gia_tri_mac_dinh,
    ghi_chu_cc: ghiChu[tc.ma_tieu_chi] || null,
  }));
}

/**
 * Kiểm tra có LĐ điều chỉnh không.
 */
export function hasLanhDaoAdjustment(tc: ITieuChiChungResponse): boolean {
  return tc.is_achieved_ld !== null && tc.is_achieved_ld !== tc.is_achieved_cc;
}
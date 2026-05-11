/**
 * src/types/tieu-chi-chung.ts
 * ============================
 * Types cho Module Tiêu chí chung - ĐỒNG BỘ VỚI BACKEND v2.6.0
 * 
 * ⚠️ QUAN TRỌNG v2.6:
 * - Backend dùng `ma_tieu_chi` (string) cho POST, KHÔNG phải `tieu_chi_id` (UUID)
 * - Hỗ trợ phê duyệt 2 cấp (cap1/cap2) cho CC
 * - CCT tự phê duyệt (0-tier)
 * - ĐT/Phó CCT → CCT (1-tier)
 * - Phó ĐT → ĐT (1-tier)
 * - CC → Phó ĐT (cap1) → ĐT (cap2)
 * 
 * Version: 2.6.0 (29/01/2026)
 */

// =============================================================================
// ENUMS
// =============================================================================

export enum TrangThaiTieuChiChung {
  CHUA_DANH_GIA = 'CHUA_DANH_GIA',
  NHAP = 'NHAP',
  CHO_PHE_DUYET = 'CHO_PHE_DUYET',
  CHO_CAP2 = 'CHO_CAP2',              // ⭐ v2.6: Chờ cấp 2 phê duyệt
  DA_PHE_DUYET = 'DA_PHE_DUYET',
}

export enum TrangThaiDanhGiaThang {
  CHUA_DANH_GIA = 'CHUA_DANH_GIA',
  DANG_DANH_GIA = 'DANG_DANH_GIA',
  CHO_TONG_HOP = 'CHO_TONG_HOP',
  DA_TONG_HOP = 'DA_TONG_HOP',
  CHO_PHE_DUYET = 'CHO_PHE_DUYET',
  CHO_CAP2 = 'CHO_CAP2',              // ⭐ v2.6
  HOAN_THANH = 'HOAN_THANH',
}

export enum LogicChamDiem {
  ALL_OR_NOTHING = 'ALL_OR_NOTHING',
  BONUS = 'BONUS',
}

/**
 * v2.6: Trạng thái phê duyệt cấp.
 */
export enum TrangThaiPheDuyetCap {
  CHO_DUYET = 'CHO_DUYET',
  DA_DUYET = 'DA_DUYET',
  TU_CHOI = 'TU_CHOI',
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

/**
 * Thông tin công chức rút gọn.
 */
export interface ICongChucBrief {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu?: string;
  don_vi_ten?: string;
}

/**
 * Response kết quả đánh giá tháng (có Virtual Record).
 * v2.6: Thêm fields phê duyệt 2 cấp.
 */
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
  
  // === PHÊ DUYỆT CẤP 1 (v2.6) ===
  nguoi_phe_duyet_tc_cap1_id?: string | null;
  nguoi_phe_duyet_tc_cap1?: ICongChucBrief | null;
  trang_thai_tc_cap1?: TrangThaiPheDuyetCap | null;
  ngay_phe_duyet_tc_cap1?: string | null;
  ly_do_tu_choi_tc_cap1?: string | null;
  
  // === PHÊ DUYỆT CẤP 2 (v2.6) ===
  nguoi_phe_duyet_tc_cap2_id?: string | null;
  nguoi_phe_duyet_tc_cap2?: ICongChucBrief | null;
  trang_thai_tc_cap2?: TrangThaiPheDuyetCap | null;
  ngay_phe_duyet_tc_cap2?: string | null;
  ly_do_tu_choi_tc_cap2?: string | null;

  // === LÝ DO TỪ CHỐI / TRẢ LẠI (v3.5+, dùng chung cho cả 2 cấp) ===
  ly_do_tu_choi_tc?: string | null;
  nguoi_tu_choi_tc_id?: string | null;
  ngay_tu_choi_tc?: string | null;
  
  // === LEGACY (backward compatible) ===
  nguoi_phe_duyet_id?: string | null;
  nguoi_phe_duyet_ten?: string | null;
  ngay_gui?: string | null;
  ngay_phe_duyet?: string | null;
  
  // === QUY TRÌNH (v2.6) ===
  quy_trinh?: 'TU_PHE_DUYET' | '1_CAP' | '2_CAP';
  is_khoa?: boolean;              // Data locked?
}

// =============================================================================
// REQUEST INTERFACES
// =============================================================================

/** Input một tiêu chí khi tự đánh giá - DÙNG ma_tieu_chi */
export interface ITieuChiChungInput {
  ma_tieu_chi: string;           // ⚠️ Backend dùng ma_tieu_chi, KHÔNG phải tieu_chi_id
  /**
   * v3.6 (08/05/2026): điểm CC tự chấm (bội số 0.5, từ 0 đến diem_toi_da).
   * Backend ưu tiên giá trị này. is_achieved_cc dưới đây chỉ giữ cho legacy.
   */
  diem_tu_cham?: number;
  is_achieved_cc?: boolean;
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

/**
 * Form state: key = ma_tieu_chi, value = điểm số CC tự chấm (bội số 0.5, từ
 * 0 đến diem_toi_da). v3.6 (08/05/2026) — đổi từ boolean sang number.
 */
export type ITieuChiFormState = Record<string, number>;

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
    [TrangThaiTieuChiChung.CHO_CAP2]: 'Chờ cấp 2 duyệt',
    [TrangThaiTieuChiChung.DA_PHE_DUYET]: 'Đã phê duyệt',
  };
  return labels[trangThai] || trangThai;
}

export function getTrangThaiBadgeClass(trangThai: TrangThaiTieuChiChung): string {
  const classes: Record<TrangThaiTieuChiChung, string> = {
    [TrangThaiTieuChiChung.CHUA_DANH_GIA]: 'bg-gray-100 text-gray-600 border-gray-300',
    [TrangThaiTieuChiChung.NHAP]: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    [TrangThaiTieuChiChung.CHO_PHE_DUYET]: 'bg-blue-100 text-blue-700 border-blue-300',
    [TrangThaiTieuChiChung.CHO_CAP2]: 'bg-indigo-100 text-indigo-700 border-indigo-300',
    [TrangThaiTieuChiChung.DA_PHE_DUYET]: 'bg-green-100 text-green-700 border-green-300',
  };
  return classes[trangThai] || '';
}

/**
 * v2.6: Lấy label cho trạng thái phê duyệt cấp.
 */
export function getTrangThaiCapLabel(trangThai: TrangThaiPheDuyetCap | null | undefined): string {
  if (!trangThai) return '—';
  const labels: Record<TrangThaiPheDuyetCap, string> = {
    [TrangThaiPheDuyetCap.CHO_DUYET]: 'Chờ duyệt',
    [TrangThaiPheDuyetCap.DA_DUYET]: 'Đã duyệt',
    [TrangThaiPheDuyetCap.TU_CHOI]: 'Từ chối',
  };
  return labels[trangThai] || trangThai;
}

/**
 * Mặc định điểm khi CC chưa nhập. v3.6: Nhóm I & II = full điểm, Nhóm III = 0.
 */
function defaultDiem(tc: ITieuChiChungMaster): number {
  return tc.gia_tri_mac_dinh ? tc.diem_toi_da : 0;
}

/**
 * Tính điểm preview từ form state (số điểm CC tự chấm cho từng tiêu chí).
 */
export function tinhDiemTuFormState(
  masterData: ITieuChiChungMaster[],
  formState: ITieuChiFormState
): ITieuChiChungTongHop {
  let nhom1 = 0, nhom2 = 0, nhom3 = 0;

  for (const tc of masterData) {
    const diem = formState[tc.ma_tieu_chi] ?? defaultDiem(tc);

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
 * Lấy `diem_tu_cham` từ response. Nếu chưa có response, dùng mặc định nhóm.
 */
export function initFormStateFromResponse(
  response: IKetQuaTieuChiChungResponse | null,
  masterData: ITieuChiChungMaster[]
): ITieuChiFormState {
  const state: ITieuChiFormState = {};

  if (response && response.tieu_chi && response.tieu_chi.length > 0) {
    // Từ response — ưu tiên diem_tu_cham, fallback boolean cho dữ liệu cũ.
    for (const tc of response.tieu_chi) {
      if (tc.diem_tu_cham != null) {
        state[tc.ma_tieu_chi] = Number(tc.diem_tu_cham);
      } else {
        const masterTc = masterData.find((m) => m.ma_tieu_chi === tc.ma_tieu_chi);
        const max = masterTc?.diem_toi_da ?? 0;
        state[tc.ma_tieu_chi] = tc.is_achieved_cc ? max : 0;
      }
    }
  } else {
    // Default từ master data
    for (const tc of masterData) {
      state[tc.ma_tieu_chi] = defaultDiem(tc);
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
 * v3.6 (08/05/2026): gửi `diem_tu_cham` (số) thay vì `is_achieved_cc` (boolean).
 * Backend tự suy is_achieved_cc = (diem >= diem_toi_da).
 */
export function convertFormToPayload(
  masterData: ITieuChiChungMaster[],
  formState: ITieuChiFormState,
  ghiChu: ITieuChiGhiChu
): ITieuChiChungInput[] {
  return masterData.map((tc: ITieuChiChungMaster): ITieuChiChungInput => {
    const diem = formState[tc.ma_tieu_chi] ?? defaultDiem(tc);
    return {
      ma_tieu_chi: tc.ma_tieu_chi,
      diem_tu_cham: diem,
      ghi_chu_cc: ghiChu[tc.ma_tieu_chi] || null,
    };
  });
}

/**
 * Kiểm tra có LĐ điều chỉnh không.
 */
export function hasLanhDaoAdjustment(tc: ITieuChiChungResponse): boolean {
  return tc.is_achieved_ld !== null && tc.is_achieved_ld !== tc.is_achieved_cc;
}

/**
 * v2.6: Kiểm tra đánh giá cần 2 cấp phê duyệt không.
 */
export function is2TierApproval(ketQua: IKetQuaTieuChiChungResponse): boolean {
  return ketQua.quy_trinh === '2_CAP';
}

/**
 * v2.6: Lấy progress của quy trình phê duyệt (0-100%).
 */
export function getApprovalProgress(ketQua: IKetQuaTieuChiChungResponse): number {
  const quyTrinh = ketQua.quy_trinh || '1_CAP';
  const trangThai = ketQua.trang_thai;

  if (quyTrinh === 'TU_PHE_DUYET') {
    return trangThai === TrangThaiTieuChiChung.DA_PHE_DUYET ? 100 : 0;
  }

  if (quyTrinh === '1_CAP') {
    return trangThai === TrangThaiTieuChiChung.DA_PHE_DUYET ? 100 : 0;
  }

  if (quyTrinh === '2_CAP') {
    if (trangThai === TrangThaiTieuChiChung.CHO_PHE_DUYET) return 0;
    if (trangThai === TrangThaiTieuChiChung.CHO_CAP2) return 50;
    if (trangThai === TrangThaiTieuChiChung.DA_PHE_DUYET) return 100;
  }

  return 0;
}

/**
 * v2.6: Lấy thông tin người phê duyệt hiện tại.
 */
export function getCurrentApprover(ketQua: IKetQuaTieuChiChungResponse): ICongChucBrief | null {
  if (ketQua.trang_thai === TrangThaiTieuChiChung.CHO_PHE_DUYET) {
    return ketQua.nguoi_phe_duyet_tc_cap1 || null;
  }
  if (ketQua.trang_thai === TrangThaiTieuChiChung.CHO_CAP2) {
    return ketQua.nguoi_phe_duyet_tc_cap2 || null;
  }
  return null;
}
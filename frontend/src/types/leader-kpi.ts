/**
 * src/types/leader-kpi.ts
 * =======================
 * TypeScript interfaces cho Kê khai công việc Lãnh đạo.
 * 
 * Lãnh đạo bao gồm: Phó ĐV, Trưởng ĐV, Phó CCT, CCT
 * 
 * Công thức KPI Lãnh đạo: (a + b + c + d + đ + e) / 6 × 70
 * - a, b, c: Tính từ công việc (mỗi đầu CV = 1 SP)
 * - d, đ, e: Tự đánh giá (100% hoặc 50%)
 * 
 * Version: 2.7.3 (01/02/2026)
 * - v2.7.3: Thêm so_loi_chat_luong, so_loi_tien_do vào IKeKhaiLanhDaoForm
 */

// =============================================================================
// ENUMS
// =============================================================================

/**
 * Trạng thái hoàn thành công việc của Lãnh đạo.
 */
export enum TrangThaiCongViecLD {
  DA_HOAN_THANH = 'DA_HOAN_THANH',
  CHUA_HOAN_THANH = 'CHUA_HOAN_THANH',
}

/**
 * Trạng thái kê khai của Lãnh đạo.
 */
export enum TrangThaiKeKhaiLD {
  NHAP = 'NHAP',
  CHO_PHE_DUYET = 'CHO_PHE_DUYET',
  DA_PHE_DUYET = 'DA_PHE_DUYET',
  TU_CHOI = 'TU_CHOI',
}

// =============================================================================
// KÊ KHAI CÔNG VIỆC LÃNH ĐẠO
// =============================================================================

/**
 * Form tạo/sửa kê khai công việc Lãnh đạo.
 * 
 * v2.7.3: Thêm so_loi_chat_luong, so_loi_tien_do để lưu tự đánh giá lỗi
 */
export interface IKeKhaiLanhDaoForm {
  ten_cong_viec: string;           // Tên công việc (bắt buộc)
  mo_ta?: string;                  // Mô tả chi tiết (không bắt buộc)
  ngay_thuc_hien: string;          // ISO date string (bắt buộc)
  trang_thai_hoan_thanh: TrangThaiCongViecLD; // Đã/Chưa hoàn thành (bắt buộc)
  so_luong: number;                // Số lượng, mặc định = 1 (bắt buộc)
  nguoi_phe_duyet_id: string;      // UUID người phê duyệt (bắt buộc)
  
  // v2.7.3: Số lỗi tự đánh giá (Lãnh đạo tự nhập khi kê khai)
  so_loi_chat_luong?: number;      // Số lỗi chất lượng (mặc định = 0)
  so_loi_tien_do?: number;         // Số lỗi tiến độ (mặc định = 0)

  // v2.7.4: Mô tả lỗi
  ghi_chu_loi_chat_luong?: string;
  ghi_chu_loi_tien_do?: string;
}

/**
 * Request tạo kê khai công việc Lãnh đạo.
 */
export interface IKeKhaiLanhDaoCreateRequest extends IKeKhaiLanhDaoForm {
  thang: number;                   // Tháng kê khai (1-12)
  nam: number;                     // Năm kê khai
}

/**
 * Request cập nhật kê khai công việc Lãnh đạo.
 */
export interface IKeKhaiLanhDaoUpdateRequest extends Partial<IKeKhaiLanhDaoForm> {
  id: string;                      // UUID kê khai cần sửa
}

/**
 * Response kê khai công việc Lãnh đạo.
 */
export interface IKeKhaiLanhDaoResponse {
  id: string;
  cong_chuc_id: string;
  thang: number;
  nam: number;
  
  // Thông tin công việc
  ten_cong_viec: string;
  mo_ta: string | null;
  ngay_thuc_hien: string;
  trang_thai_hoan_thanh: TrangThaiCongViecLD;
  so_luong: number;
  
  // Phê duyệt
  nguoi_phe_duyet_id: string;
  nguoi_phe_duyet?: {
    id: string;
    ma_cc: string;
    ho_ten: string;
    chuc_vu: string | null;
  };
  trang_thai: TrangThaiKeKhaiLD;
  
  // Đánh giá (sau khi phê duyệt)
  so_loi_chat_luong: number;
  so_loi_tien_do: number;
  y_kien_lanh_dao: string | null;
  
  // v2.7.4: Mô tả lỗi
  ghi_chu_loi_chat_luong: string | null;
  ghi_chu_loi_tien_do: string | null;

  // Timestamps
  created_at: string;
  updated_at: string;
}

// =============================================================================
// ĐÁNH GIÁ d, đ, e
// =============================================================================

/**
 * Form đánh giá d, đ, e của Lãnh đạo.
 * Checkbox: Checked = 100%, Unchecked = 50%
 */
export interface IDanhGiaDDEForm {
  d_ket_qua_don_vi: boolean;       // d - Kết quả hoạt động đơn vị
  d_ghi_chu?: string;              // Ghi chú nếu d = 50%
  
  dd_to_chuc_trien_khai: boolean;  // đ - Khả năng tổ chức triển khai
  dd_ghi_chu?: string;             // Ghi chú nếu đ = 50%
  
  e_doan_ket_noi_bo: boolean;      // e - Năng lực đoàn kết nội bộ
  e_ghi_chu?: string;              // Ghi chú nếu e = 50%
}

/**
 * Request lưu đánh giá d, đ, e.
 */
export interface IDanhGiaDDERequest extends IDanhGiaDDEForm {
  thang: number;
  nam: number;
}

/**
 * Response đánh giá d, đ, e.
 * Theo Backend handoff v2.5.8
 */
export interface IDanhGiaDDEResponse {
  id: string;
  cong_chuc_id: string;
  thang: number;
  nam: number;
  
  // Giá trị d, đ, e tự đánh giá (100 hoặc 50)
  d_ket_qua_don_vi: number;
  d_ghi_chu: string | null;
  
  dd_to_chuc_trien_khai: number;
  dd_ghi_chu: string | null;
  
  e_doan_ket_noi_bo: number;
  e_ghi_chu: string | null;
  
  // Trạng thái
  trang_thai: TrangThaiKeKhaiLD;
  nguoi_phe_duyet_id: string | null;
  y_kien_phe_duyet: string | null;
  ngay_phe_duyet: string | null;
  
  // Giá trị sau phê duyệt (LĐ cấp trên có thể điều chỉnh)
  d_phe_duyet: number | null;
  dd_phe_duyet: number | null;
  e_phe_duyet: number | null;
  
  // Giá trị cuối cùng (sau phê duyệt hoặc tự đánh giá)
  d_final: number;
  dd_final: number;
  e_final: number;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

// =============================================================================
// THỐNG KÊ & TÍNH ĐIỂM
// =============================================================================

/**
 * Thống kê kê khai tháng cho Lãnh đạo.
 * 
 * v2.7.3: Thêm đầy đủ các field tong_loi, tong_diem, tam_tinh_*
 * để không cần dùng `as any` workaround trong page.tsx
 */
export interface IThongKeKeKhaiLanhDao {
  thang: number;
  nam: number;
  
  // Tổng quan
  tong_cong_viec: number;          // Tổng số công việc đã kê khai (= Target)
  tong_hoan_thanh: number;         // Số CV đã hoàn thành
  tong_chua_hoan_thanh: number;    // Số CV chưa hoàn thành
  
  // Theo trạng thái phê duyệt
  tong_da_duyet: number;
  tong_cho_duyet: number;
  tong_tu_choi: number;
  tong_nhap: number;
  
  // Chất lượng & Tiến độ - CHÍNH THỨC (chỉ DA_PHE_DUYET)
  tong_dat_chat_luong: number;     // Số CV đạt chất lượng (không có lỗi)
  tong_dung_tien_do: number;       // Số CV đúng tiến độ (không có lỗi)
  
  // v2.6.4: Tổng số lỗi (để hiển thị)
  tong_loi_chat_luong: number;     // Tổng lỗi CL các CV đã duyệt
  tong_loi_tien_do: number;        // Tổng lỗi TĐ các CV đã duyệt
  
  // v2.6.5: Tổng điểm (để tính b, c chính xác)
  // Mỗi CV: điểm = max(0, 1 - số_lỗi × 0.25)
  tong_diem_chat_luong: number;    // b = tong_diem_tien_do / tong_da_duyet
  tong_diem_tien_do: number;       // c = tong_diem_chat_luong / tong_da_duyet
  
  // v2.7.0: TẠM TÍNH (NHAP + CHO_PHE_DUYET + DA_PHE_DUYET)
  tam_tinh_tong_cong_viec: number;
  tam_tinh_hoan_thanh: number;
  tam_tinh_chua_hoan_thanh: number;
  tam_tinh_dat_chat_luong: number;
  tam_tinh_dung_tien_do: number;
  
  // v2.6.4: Tổng số lỗi tạm tính
  tam_tinh_loi_chat_luong: number;
  tam_tinh_loi_tien_do: number;
  
  // v2.6.5: Tổng điểm tạm tính
  tam_tinh_diem_chat_luong: number;
  tam_tinh_diem_tien_do: number;
}

/**
 * Kết quả tính điểm KPI Lãnh đạo.
 */
export interface IDiemKPILanhDao {
  thang: number;
  nam: number;
  
  // Target = Tổng CV đã kê khai (đã duyệt)
  target_cong_viec: number;
  
  // 3 chỉ số từ công việc (%)
  a_so_luong: number;              // a = CV hoàn thành / Target
  b_chat_luong: number;            // b = CV đạt CL / Target
  c_tien_do: number;               // c = CV đúng TĐ / Target
  
  // 3 chỉ số tự đánh giá (100 hoặc 50)
  d_ket_qua_don_vi: number;
  dd_to_chuc_trien_khai: number;
  e_doan_ket_noi_bo: number;
  
  // Điểm KPI tổng hợp
  diem_kpi: number;                // (a + b + c + d/100 + đ/100 + e/100) / 6
  diem_kpi_quy_doi: number;        // diem_kpi × 70
}

// =============================================================================
// DANH SÁCH NGƯỜI PHÊ DUYỆT
// =============================================================================

/**
 * Thông tin người phê duyệt cho Lãnh đạo.
 */
export interface INguoiPheDuyetLanhDao {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu: string | null;
  vai_tro: {
    ma_vai_tro: string;
    ten_vai_tro: string;
  };
  don_vi: {
    id: string;
    ten_don_vi: string;
  } | null;
}

// =============================================================================
// HELPER TYPES
// =============================================================================

/**
 * Convert boolean sang giá trị phần trăm.
 */
export function boolToPercent(value: boolean): number {
  return value ? 100 : 50;
}

/**
 * Convert giá trị phần trăm sang boolean.
 */
export function percentToBool(value: number): boolean {
  return value === 100;
}

/**
 * Tính điểm KPI cho Lãnh đạo.
 */
export function tinhDiemKPILanhDao(
  thongKe: IThongKeKeKhaiLanhDao,
  dde: IDanhGiaDDEResponse | null
): IDiemKPILanhDao {
  const target = thongKe.tong_da_duyet;
  
  // Tính a, b, c
  const a = target > 0 ? Math.min(thongKe.tong_hoan_thanh / target, 1) : 0;
  const b = target > 0 ? Math.min(thongKe.tong_dat_chat_luong / target, 1) : 0;
  const c = target > 0 ? Math.min(thongKe.tong_dung_tien_do / target, 1) : 0;
  
  // Lấy d, đ, e — ưu tiên giá trị cuối (final = COALESCE phê duyệt > tự đánh giá).
  // 2026-05-14: trước đây chỉ đọc *_ket_qua_don_vi → khi LĐ cấp trên duyệt
  // và hạ điểm, UI vẫn hiển thị 100% (giá trị tự đánh giá). Bây giờ đọc
  // *_final đồng nhất với backend build_dde_response.
  const d = dde?.d_final ?? dde?.d_phe_duyet ?? dde?.d_ket_qua_don_vi ?? 100;
  const dd = dde?.dd_final ?? dde?.dd_phe_duyet ?? dde?.dd_to_chuc_trien_khai ?? 100;
  const e = dde?.e_final ?? dde?.e_phe_duyet ?? dde?.e_doan_ket_noi_bo ?? 100;
  
  // Tính điểm KPI = (a + b + c + d/100 + đ/100 + e/100) / 6
  const diemKPI = (a + b + c + d/100 + dd/100 + e/100) / 6;
  
  return {
    thang: thongKe.thang,
    nam: thongKe.nam,
    target_cong_viec: target,
    a_so_luong: a,
    b_chat_luong: b,
    c_tien_do: c,
    d_ket_qua_don_vi: d,
    dd_to_chuc_trien_khai: dd,
    e_doan_ket_noi_bo: e,
    diem_kpi: diemKPI,
    diem_kpi_quy_doi: diemKPI * 70,
  };
}
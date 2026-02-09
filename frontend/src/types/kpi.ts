/**
 * src/types/kpi.ts
 * ================
 * TypeScript interfaces cho KPI Submission (Kê khai công việc).
 * 
 * Version: 2.7.4 (02/02/2026)
 * UPDATE:
 * - Thêm 4 fields mô tả lỗi:
 *   + ghi_chu_tu_dg_chat_luong, ghi_chu_tu_dg_tien_do (CC tự nhập)
 *   + ghi_chu_loi_chat_luong, ghi_chu_loi_tien_do (LĐ chốt)
 * 
 * v2.7.0 (31/01/2026):
 * - Thêm fields tạm tính (tam_tinh_*) cho 2-tab UI
 * 
 * Tham chiếu từ:
 * - app/models/kpi_submission.py (KeKhaiCongViec, PheDuyetSp)
 * - app/models/task_catalog.py (DanhMucSpCongViec, CapDoPhucTap, SpCongViecChuan)
 */

// =============================================================================
// ENUMS
// =============================================================================

/**
 * Trạng thái của bản kê khai công việc.
 * Tương ứng với TrangThaiKeKhai trong Python.
 */
export enum KpiStatus {
  DRAFT = 'NHAP',           // Đang nhập, chưa gửi
  PENDING = 'CHO_PHE_DUYET', // Đã gửi, chờ phê duyệt
  APPROVED = 'DA_PHE_DUYET', // Đã phê duyệt
  REJECTED = 'TU_CHOI',      // Bị từ chối
  CANCELLED = 'HUY',         // Đã hủy
}

/**
 * Trạng thái phê duyệt.
 * Tương ứng với TrangThaiPheDuyet trong Python.
 */
export enum ApprovalStatus {
  PENDING = 'CHO_XU_LY',    // Chờ xử lý
  APPROVED = 'PHE_DUYET',   // Đã phê duyệt
  REJECTED = 'TU_CHOI',     // Từ chối
  REVISION = 'YEU_CAU_SUA', // Yêu cầu sửa lại
}

// =============================================================================
// MASTER DATA TYPES (Danh mục)
// =============================================================================

/**
 * Sản phẩm công việc chuẩn (SP1-SP4).
 * Tương ứng với SpCongViecChuan.
 */
export interface ISpChuan {
  id: string;
  ma_sp: string;           // SP1, SP2, SP3, SP4
  ten_sp: string;          // Tên đầy đủ
  mo_ta: string | null;
  thoi_gian_phut: number;  // Thời gian thực hiện (phút)
  he_so_quy_doi_sp1: number; // Hệ số quy đổi về SP gốc
  is_sp_goc: boolean;      // SP1 = true
  is_active: boolean;
}

/**
 * Cấp độ phức tạp (C1-C5).
 * Tương ứng với CapDoPhucTap.
 */
export interface ICapDo {
  id: string;
  ma_cap_do: string;       // C1, C2, C3, C4, C5
  ten_cap_do: string;      // Tên cấp độ
  mo_ta: string | null;
  he_so_sp1: number;       // Hệ số nhân cho SP1
  he_so_sp2: number;       // Hệ số nhân cho SP2/SP3/SP4
  is_theo_thuc_te: boolean; // C5 = true (hệ số do LĐ nhập)
  thu_tu: number;          // Thứ tự sắp xếp
  is_active: boolean;
}

/**
 * Danh mục sản phẩm/công việc.
 * Tương ứng với DanhMucSpCongViec.
 */
export interface IDanhMucCongViec {
  id: string;
  ma_danh_muc: string;     // Mã danh mục
  ten_cong_viec: string;   // Tên công việc
  mo_ta: string | null;
  nhom_cong_viec: string | null; // Nhóm công việc
  is_active: boolean;
  
  // Nested
  sp_chuan_id: string;
  sp_chuan?: ISpChuan;     // Loại SP (SP1-SP4)
  
  don_vi_ap_dung_id: string | null;
  don_vi_ap_dung_ten: string | null;
}

// =============================================================================
// KE KHAI CONG VIEC (Bản kê khai)
// =============================================================================

/**
 * Bản kê khai công việc đầy đủ.
 * Tương ứng với KeKhaiCongViec response từ API.
 */
export interface IKeKhaiCongViec {
  id: string;
  
  // Người kê khai
  cong_chuc_id: string;
  cong_chuc_ho_ten?: string;
  cong_chuc_ma_cc?: string;
  
  // Thời gian
  thang: number;           // 1-12
  nam: number;             // >= 2025
  ngay_thuc_hien: string | null; // ISO date
  
  // Công việc
  danh_muc_sp_id: string;
  danh_muc_sp?: IDanhMucCongViec;
  danh_muc_ten?: string;   // Tên công việc (flattened)
  danh_muc_ma?: string;    // Mã danh mục (flattened)
  
  // Cấp độ
  cap_do_id: string;
  cap_do?: ICapDo;
  cap_do_ma?: string;      // Mã cấp độ (flattened)
  cap_do_ten?: string;     // Tên cấp độ (flattened)
  
  // Số lượng & hệ số
  so_luong: number;        // Số lượng kê khai
  he_so_thuc_te: number | null; // Chỉ dùng cho C5
  
  // Người phê duyệt (CC chọn)
  nguoi_phe_duyet_id: string | null;
  nguoi_phe_duyet_ho_ten?: string;
  
  // Thông tin bổ sung
  mo_ta_cong_viec: string | null;
  is_doi_moi_sang_tao: boolean;
  ngay_deadline: string | null;
  ngay_hoan_thanh: string | null;
  
  // Tự đánh giá của CC
  tu_danh_gia_chat_luong: number;
  tu_danh_gia_tien_do: number;
  ghi_chu_tu_danh_gia: string | null;
  // v2.7.4: Mô tả lỗi tự đánh giá - tách riêng CL và TĐ
  ghi_chu_tu_dg_chat_luong: string | null;
  ghi_chu_tu_dg_tien_do: string | null;
  
  // Số lỗi chốt cuối (LĐ xác nhận)
  so_loi_chat_luong: number;
  so_loi_tien_do: number;
  y_kien_lanh_dao: string | null;
  // v2.7.4: Mô tả lỗi lãnh đạo chốt - tách riêng CL và TĐ
  ghi_chu_loi_chat_luong: string | null;
  ghi_chu_loi_tien_do: string | null;
  
  // Trạng thái
  trang_thai: KpiStatus;
  
  // Kết quả quy đổi
  so_sp_goc_quy_doi: number | null;
  so_sp_chat_luong: number | null;
  so_sp_tien_do: number | null;
  
  // Metadata
  created_at: string;
  updated_at: string | null;
}

/**
 * Response tóm tắt cho danh sách kê khai.
 */
export interface IKeKhaiBrief {
  id: string;
  thang: number;
  nam: number;
  ngay_thuc_hien: string | null;
  danh_muc_ten: string;
  danh_muc_ma: string;
  cap_do_ma: string;
  so_luong: number;
  trang_thai: KpiStatus;
  so_sp_goc_quy_doi: number | null;
  nguoi_phe_duyet_id: string | null; // ID người phê duyệt (cần để gửi duyệt)
  created_at: string;
}

// =============================================================================
// REQUEST TYPES (Gửi lên API)
// =============================================================================

/**
 * Request tạo mới kê khai công việc.
 */
export interface IKeKhaiCreateRequest {
  danh_muc_sp_id: string;  // ID công việc từ danh mục
  cap_do_id: string;       // ID cấp độ phức tạp
  thang: number;           // Tháng kê khai
  nam: number;             // Năm kê khai
  so_luong: number;        // Số lượng
  ngay_thuc_hien?: string; // Ngày thực hiện (optional)
  mo_ta_cong_viec?: string;
  is_doi_moi_sang_tao?: boolean;
  ngay_deadline?: string;
  ngay_hoan_thanh?: string;
  he_so_thuc_te?: number;  // Chỉ khi cấp độ C5
  nguoi_phe_duyet_id?: string; // CC chọn người phê duyệt
  
  // Tự đánh giá
  tu_danh_gia_chat_luong?: number;
  tu_danh_gia_tien_do?: number;
  ghi_chu_tu_danh_gia?: string;
  // v2.7.4: Mô tả lỗi tự đánh giá
  ghi_chu_tu_dg_chat_luong?: string;
  ghi_chu_tu_dg_tien_do?: string;
}

/**
 * Request cập nhật kê khai công việc.
 */
export interface IKeKhaiUpdateRequest {
  danh_muc_sp_id?: string;
  cap_do_id?: string;
  so_luong?: number;
  ngay_thuc_hien?: string;
  mo_ta_cong_viec?: string;
  is_doi_moi_sang_tao?: boolean;
  ngay_deadline?: string;
  ngay_hoan_thanh?: string;
  he_so_thuc_te?: number;
  nguoi_phe_duyet_id?: string;
  
  // Tự đánh giá
  tu_danh_gia_chat_luong?: number;
  tu_danh_gia_tien_do?: number;
  ghi_chu_tu_danh_gia?: string;
  // v2.7.4: Mô tả lỗi tự đánh giá
  ghi_chu_tu_dg_chat_luong?: string;
  ghi_chu_tu_dg_tien_do?: string;
}

/**
 * Request gửi kê khai đi phê duyệt.
 */
export interface ISubmitKpiRequest {
  thang: number;
  nam: number;
  ke_khai_ids?: string[];  // Nếu null => gửi tất cả bản nháp
}

// =============================================================================
// FILTER & RESPONSE TYPES
// =============================================================================

/**
 * Filter params cho danh sách kê khai.
 */
export interface IKeKhaiFilterParams {
  thang?: number;
  nam?: number;
  trang_thai?: KpiStatus;
  danh_muc_sp_id?: string;
  cap_do_id?: string;
}

/**
 * Tổng hợp kê khai theo tháng.
 * 
 * v2.7.0 UPDATE: Thêm fields tạm tính (tam_tinh_*) cho 2-tab UI
 */
export interface IKeKhaiMonthSummary {
  thang: number;
  nam: number;
  tong_ke_khai: number;
  tong_nhap: number;
  tong_cho_duyet: number;
  tong_da_duyet: number;
  tong_tu_choi: number;
  tong_sp_quy_doi: number;
  trang_thai_chung?: KpiStatus; // Trạng thái chung của tháng
  
  // =========================================================================
  // CHÍNH THỨC (chỉ DA_PHE_DUYET) - v2.5.6
  // =========================================================================
  so_sp_duoc_giao?: number | null;  // Target SP = Ngày làm việc × 96
  tong_sp_chat_luong?: number;      // Tổng SP đạt chất lượng
  tong_sp_tien_do?: number;         // Tổng SP đúng tiến độ
  ty_le_hoan_thanh?: number | null; // Tỷ lệ hoàn thành %
  
  // =========================================================================
  // TẠM TÍNH (NHAP + CHO_PHE_DUYET + DA_PHE_DUYET) - v2.7.0 NEW
  // =========================================================================
  tam_tinh_sp_quy_doi?: number;     // Tổng SP tạm tính
  tam_tinh_sp_chat_luong?: number;  // SP đạt CL tạm tính (dùng tu_danh_gia)
  tam_tinh_sp_tien_do?: number;     // SP đạt TĐ tạm tính (dùng tu_danh_gia)
  
  // =========================================================================
  // Thống kê lỗi
  // =========================================================================
  // Tự đánh giá của CC
  tong_loi_cl_tu_danh_gia?: number;
  tong_loi_td_tu_danh_gia?: number;
  
  // Lãnh đạo chốt
  tong_loi_cl_chot?: number;
  tong_loi_td_chot?: number;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Lấy label hiển thị cho trạng thái.
 */
export function getStatusLabel(status: KpiStatus): string {
  const labels: Record<KpiStatus, string> = {
    [KpiStatus.DRAFT]: 'Nháp',
    [KpiStatus.PENDING]: 'Chờ duyệt',
    [KpiStatus.APPROVED]: 'Đã duyệt',
    [KpiStatus.REJECTED]: 'Từ chối',
    [KpiStatus.CANCELLED]: 'Đã hủy',
  };
  return labels[status] || status;
}

/**
 * Lấy màu badge cho trạng thái.
 */
export function getStatusBadgeClass(status: KpiStatus): string {
  const classes: Record<KpiStatus, string> = {
    [KpiStatus.DRAFT]: 'badge-gray',
    [KpiStatus.PENDING]: 'badge-yellow',
    [KpiStatus.APPROVED]: 'badge-green',
    [KpiStatus.REJECTED]: 'badge-red',
    [KpiStatus.CANCELLED]: 'badge-gray',
  };
  return classes[status] || 'badge-gray';
}

/**
 * Kiểm tra có thể sửa/xóa kê khai không.
 * Chỉ cho phép khi trạng thái là NHÁP hoặc TỪ CHỐI.
 */
export function canEditKeKhai(status: KpiStatus): boolean {
  return status === KpiStatus.DRAFT || status === KpiStatus.REJECTED;
}

/**
 * Kiểm tra có thể gửi duyệt không.
 * Chỉ cho phép khi trạng thái là NHÁP.
 */
export function canSubmitKeKhai(status: KpiStatus): boolean {
  return status === KpiStatus.DRAFT;
}
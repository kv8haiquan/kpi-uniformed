/**
 * src/types/assessment.ts
 * ========================
 * Type definitions cho Module Đánh giá KPI & Tự chấm điểm.
 *
 * Tham chiếu: BUSINESS_RULES_FINAL.md, API_SPECS.md
 * Version: 2.4
 *
 * Cấu trúc điểm:
 * - Tiêu chí chung (30 điểm): Nhóm I (10đ) + Nhóm II (10đ) + Nhóm III (10đ)
 * - KPI (70 điểm): Dựa trên % hoàn thành công việc
 * - Tổng: 100 điểm → Xếp loại A/B/C/D
 */

// =============================================================================
// ENUMS
// =============================================================================

/**
 * Mức xếp loại chất lượng công chức.
 */
export enum MucXepLoai {
  A = 'A',   // Hoàn thành xuất sắc (≥90 điểm)
  B = 'B',   // Hoàn thành tốt (70-<90 điểm)
  C = 'C',   // Hoàn thành (50-<70 điểm)
  D = 'D',   // Không hoàn thành (<50 điểm)
  E = 'E',   // Không xếp loại (trường hợp đặc biệt)
}

/**
 * Trạng thái đánh giá tháng.
 */
export enum TrangThaiDanhGia {
  CHUA_DANH_GIA = 'CHUA_DANH_GIA',       // Chưa có dữ liệu đánh giá
  CHO_TU_DANH_GIA = 'CHO_TU_DANH_GIA',   // Chờ CC tự đánh giá TC chung
  CHO_PHE_DUYET_TC = 'CHO_PHE_DUYET_TC', // Chờ LĐ phê duyệt TC chung
  CHO_TONG_HOP = 'CHO_TONG_HOP',         // Chờ tổng hợp đơn vị
  CHO_XEP_LOAI = 'CHO_XEP_LOAI',         // Chờ CCT xếp loại
  DA_HOAN_THANH = 'DA_HOAN_THANH',       // Đã hoàn thành xếp loại
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Lấy label tiếng Việt cho mức xếp loại.
 */
export const getMucXepLoaiLabel = (muc: MucXepLoai): string => {
  const labels: Record<MucXepLoai, string> = {
    [MucXepLoai.A]: 'Hoàn thành xuất sắc nhiệm vụ',
    [MucXepLoai.B]: 'Hoàn thành tốt nhiệm vụ',
    [MucXepLoai.C]: 'Hoàn thành nhiệm vụ',
    [MucXepLoai.D]: 'Không hoàn thành nhiệm vụ',
    [MucXepLoai.E]: 'Không xếp loại',
  };
  return labels[muc] || muc;
};

/**
 * Lấy badge class cho mức xếp loại.
 */
export const getMucXepLoaiBadgeClass = (muc: MucXepLoai): string => {
  const classes: Record<MucXepLoai, string> = {
    [MucXepLoai.A]: 'bg-green-100 text-green-800 border-green-300',
    [MucXepLoai.B]: 'bg-blue-100 text-blue-800 border-blue-300',
    [MucXepLoai.C]: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    [MucXepLoai.D]: 'bg-red-100 text-red-800 border-red-300',
    [MucXepLoai.E]: 'bg-gray-100 text-gray-800 border-gray-300',
  };
  return classes[muc] || 'bg-gray-100 text-gray-800';
};

/**
 * Lấy label trạng thái đánh giá.
 */
export const getTrangThaiDanhGiaLabel = (trangThai: TrangThaiDanhGia): string => {
  const labels: Record<TrangThaiDanhGia, string> = {
    [TrangThaiDanhGia.CHUA_DANH_GIA]: 'Chưa đánh giá',
    [TrangThaiDanhGia.CHO_TU_DANH_GIA]: 'Chờ tự đánh giá',
    [TrangThaiDanhGia.CHO_PHE_DUYET_TC]: 'Chờ phê duyệt tiêu chí',
    [TrangThaiDanhGia.CHO_TONG_HOP]: 'Chờ tổng hợp',
    [TrangThaiDanhGia.CHO_XEP_LOAI]: 'Chờ xếp loại',
    [TrangThaiDanhGia.DA_HOAN_THANH]: 'Đã hoàn thành',
  };
  return labels[trangThai] || trangThai;
};

// =============================================================================
// TIÊU CHÍ CHUNG - CONSTANTS
// =============================================================================

/**
 * Định nghĩa tiêu chí chung (30 điểm).
 * Dùng để render form tự đánh giá.
 */
export interface ITieuChiChungDef {
  ma: string;
  ten: string;
  diemToiDa: number;
  moTa?: string;
}

export interface INhomTieuChi {
  nhom: string;
  ten: string;
  diemToiDa: number;
  tieuChi: ITieuChiChungDef[];
}

/**
 * Danh sách 3 nhóm tiêu chí chung theo BUSINESS_RULES.
 */
export const TIEU_CHI_CHUNG: INhomTieuChi[] = [
  {
    nhom: 'I',
    ten: 'Phẩm chất chính trị, đạo đức, kỷ luật',
    diemToiDa: 10,
    tieuChi: [
      {
        ma: '1.1',
        ten: 'Phẩm chất chính trị, đạo đức, văn hóa công vụ',
        diemToiDa: 5.0,
        moTa: 'Tuân thủ các tiêu chí a1-a8 theo quy định',
      },
      {
        ma: '1.2',
        ten: 'Ý thức kỷ luật, kỷ cương trong thực thi công vụ',
        diemToiDa: 5.0,
        moTa: 'Tuân thủ các tiêu chí b1-b4 theo quy định',
      },
    ],
  },
  {
    nhom: 'II',
    ten: 'Năng lực chuyên môn, nghiệp vụ',
    diemToiDa: 10,
    tieuChi: [
      {
        ma: '2.1',
        ten: 'Năng lực chuyên môn theo vị trí việc làm',
        diemToiDa: 2.5,
      },
      {
        ma: '2.2',
        ten: 'Khả năng đáp ứng nhiệm vụ thường xuyên, đột xuất',
        diemToiDa: 2.5,
      },
      {
        ma: '2.3',
        ten: 'Tinh thần trách nhiệm trong thực thi công vụ',
        diemToiDa: 2.5,
      },
      {
        ma: '2.4',
        ten: 'Thái độ phục vụ, khả năng phối hợp đồng nghiệp',
        diemToiDa: 2.5,
      },
    ],
  },
  {
    nhom: 'III',
    ten: 'Năng lực đổi mới, sáng tạo',
    diemToiDa: 10,
    tieuChi: [
      {
        ma: '3.1',
        ten: 'Sản phẩm/giải pháp đột phá, sáng tạo',
        diemToiDa: 2.5,
        moTa: 'Cần có minh chứng cụ thể nếu tự chấm điểm',
      },
      {
        ma: '3.2',
        ten: 'Sẵn sàng tham gia nhiệm vụ đặc biệt, phức tạp',
        diemToiDa: 2.5,
      },
      {
        ma: '3.3',
        ten: 'Tinh thần chịu trách nhiệm, khắc phục sai sót',
        diemToiDa: 2.5,
      },
      {
        ma: '3.4',
        ten: 'Chủ động quyết định, tiên phong nhiệm vụ mới',
        diemToiDa: 2.5,
      },
    ],
  },
];

// =============================================================================
// INTERFACES - API RESPONSE
// =============================================================================

/**
 * Thông tin công chức rút gọn trong đánh giá.
 */
export interface ICongChucDanhGia {
  id: string;
  ma_cc: string;
  ho_ten: string;
  don_vi?: string;
  chuc_vu?: string;
  is_lanh_dao: boolean;
}

/**
 * Chi tiết một tiêu chí chung đã chấm.
 */
export interface ITieuChiChungResponse {
  ma_tieu_chi: string;
  ten_tieu_chi: string;
  diem_toi_da: number;
  diem_tu_cham: number | null;
  diem_phe_duyet: number | null;
  ghi_chu: string | null;
  da_phe_duyet: boolean;
}

/**
 * Chi tiết điểm KPI (a, b, c cho CC thường; thêm d, đ, e cho Lãnh đạo).
 */
export interface IDiemChiTiet {
  a_so_luong: number;      // Tỷ lệ hoàn thành số lượng (0-1)
  b_chat_luong: number;    // Tỷ lệ đạt chất lượng (0-1)
  c_tien_do: number;       // Tỷ lệ đúng tiến độ (0-1)
  // Chỉ có với Lãnh đạo
  d_ket_qua_don_vi?: number;    // Kết quả hoạt động đơn vị (0-1)
  dd_kha_nang_to_chuc?: number; // Khả năng tổ chức triển khai (0-1)
  e_doan_ket_noi_bo?: number;   // Năng lực đoàn kết nội bộ (0-1)
}

/**
 * Chỉ số lãnh đạo (d, đ, e) - Chỉ có với role Lãnh đạo.
 */
export interface IChiSoLanhDao {
  d_ket_qua_don_vi: number;
  ghi_chu_d: string | null;
  co_cc_khong_hoan_thanh: boolean;
  dd_kha_nang_to_chuc: number;
  ghi_chu_dd: string | null;
  co_ton_tai_cham_tre: boolean;
  e_doan_ket_noi_bo: number;
  ghi_chu_e: string | null;
  co_mau_thuan_noi_bo: boolean;
}

/**
 * Response đánh giá tháng đầy đủ.
 * 
 * ĐỒNG BỘ VỚI BACKEND v2.4.2 - DanhGiaThangResponse
 */
export interface IDanhGiaThangResponse {
  id: string;
  cong_chuc: ICongChucDanhGia;
  thang: number;
  nam: number;
  
  /**
   * ✅ FLAG QUAN TRỌNG (Backend v2.4.2): Đánh dấu đây là Virtual Record.
   * - true: Chưa có bản ghi trong DB, hiển thị giá trị mặc định
   * - false: Đã có bản ghi thực trong DB
   * 
   * Backend luôn trả về trường này (không optional).
   */
  is_new_record: boolean;
  
  // Thông tin ngày làm việc
  so_ngay_lam_viec: number;       // Số ngày làm việc thực tế (đã trừ nghỉ)
  so_ngay_nghi_phep: number;      // Tổng ngày nghỉ đã duyệt
  so_ngay_trong_thang: number;    // Số ngày trong tháng (dương lịch)
  
  // Sản phẩm được giao
  so_sp_goc_duoc_giao: number;    // SP được giao (đã quy đổi)
  
  // Kết quả kê khai
  tong_sp_hoan_thanh: number;     // Tổng SP hoàn thành
  tong_sp_chat_luong: number;     // SP đạt chất lượng
  tong_sp_tien_do: number;        // SP đúng tiến độ
  
  // Điểm số
  diem_tieu_chi_chung: number;    // Điểm TC chung (0-30)
  diem_kpi: number;               // Tỷ lệ KPI (0-1, ví dụ 0.92 = 92%)
  diem_kpi_quy_doi: number;       // Điểm KPI quy đổi (0-70)
  diem_chi_tiet: IDiemChiTiet;    // Chi tiết a, b, c (và d, đ, e nếu LĐ)
  diem_tong: number;              // Điểm tổng (0-100)
  
  // Xếp loại
  muc_xep_loai_tu_dong: MucXepLoai | null;    // Hệ thống tự tính
  muc_xep_loai_de_xuat: MucXepLoai | null;    // Trưởng ĐV đề xuất
  muc_xep_loai_chinh_thuc: MucXepLoai | null; // CCT quyết định
  
  // Trạng thái
  trang_thai: TrangThaiDanhGia;
  
  // Tiêu chí chung đã chấm
  tieu_chi_chung: ITieuChiChungResponse[];
  
  // Chỉ số lãnh đạo (optional)
  chi_so_lanh_dao?: IChiSoLanhDao;
  is_lanh_dao: boolean;
  
  // Timestamps
  created_at: string;
  updated_at: string | null;
}

// =============================================================================
// INTERFACES - API REQUEST
// =============================================================================

/**
 * Item tiêu chí trong request tự đánh giá.
 */
export interface ITieuChiTuCham {
  ma_tieu_chi: string;
  diem_tu_cham: number;
  ghi_chu?: string;
}

/**
 * Request tự đánh giá tiêu chí chung.
 */
export interface ITuDanhGiaRequest {
  thang: number;
  nam: number;
  tieu_chi: ITieuChiTuCham[];
}

/**
 * Request phê duyệt tiêu chí chung (dành cho Lãnh đạo).
 */
export interface IPheDuyetTieuChiRequest {
  danh_gia_id: string;
  tieu_chi: Array<{
    ma_tieu_chi: string;
    diem_phe_duyet: number;
    ghi_chu?: string;
  }>;
}

// =============================================================================
// TYPE GUARDS
// =============================================================================

/**
 * Kiểm tra có thể tự đánh giá không.
 */
export const canTuDanhGia = (trangThai: TrangThaiDanhGia): boolean => {
  return trangThai === TrangThaiDanhGia.CHUA_DANH_GIA || 
         trangThai === TrangThaiDanhGia.CHO_TU_DANH_GIA;
};

/**
 * Kiểm tra có thể sửa tự đánh giá không (trước khi được phê duyệt).
 */
export const canEditTuDanhGia = (trangThai: TrangThaiDanhGia): boolean => {
  return trangThai === TrangThaiDanhGia.CHO_TU_DANH_GIA || 
         trangThai === TrangThaiDanhGia.CHO_PHE_DUYET_TC;
};

/**
 * Tính điểm tổng tiêu chí chung từ các tiêu chí đã chấm.
 */
export const tinhDiemTieuChiChung = (
  tieuChiList: Array<{ ma_tieu_chi: string; diem_tu_cham: number | null }>
): number => {
  return tieuChiList.reduce((sum, tc) => sum + (tc.diem_tu_cham || 0), 0);
};
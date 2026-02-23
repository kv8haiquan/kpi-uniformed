/**
 * src/types/legal.ts
 * ==================
 * TypeScript interfaces cho module Pháp luật (Legal).
 * Map chính xác từ response format trong docs/legal/LEGAL_API_SPECS.md
 * Base URL: /api/v1/legal | Backend Port: 8003
 */

// =============================================================================
// ĐƠN VỊ (READONLY từ public.don_vi — dùng để chọn đối tượng áp dụng)
// =============================================================================

/**
 * Công chức (READONLY từ public.cong_chuc).
 * Trả về khi gọi GET /cong-chuc (search/autocomplete).
 * Lưu ý: field là ma_cc (không phải ma_cong_chuc).
 */
export interface ICongChuc {
  id: string;       // UUID
  ho_ten: string;   // Ví dụ: "Nguyễn Văn A"
  ma_cc: string;    // Ví dụ: "20ZZ-0224" (DB column là ma_cc)
  don_vi?: { id: string; ten_don_vi: string };
}

/** Thông tin đơn vị kem so CBCC active */
export interface IDonVi {
  id: string;          // UUID
  ma_don_vi: string;   // Ví dụ: "HQCK-MC"
  ten_don_vi: string;  // Ví dụ: "HQCK quốc tế Móng Cái"
  loai_don_vi: string; // HAI_QUAN_CUA_KHAU | PHONG | DOI | LANH_DAO_CHI_CUC
  so_cbcc: number;     // Số CBCC active thuộc đơn vị
}

// =============================================================================
// LOẠI VĂN BẢN
// =============================================================================

/** Loại văn bản pháp luật (Luật, Nghị định, Thông tư, ...) */
export interface ILoaiVanBan {
  id: string;
  ma: string;        // Ví dụ: "LUAT", "NGHI_DINH", "THONG_TU"
  ten: string;       // Ví dụ: "Luật", "Nghị định", "Thông tư"
  thu_tu: number;    // Thứ tự hiển thị trong dropdown
}

// =============================================================================
// VĂN BẢN — DANH SÁCH (GET /van-ban)
// =============================================================================

/**
 * Văn bản trong danh sách.
 * Chỉ trả về VB có trang_thai_duyet = DA_XUAT_BAN.
 */
export interface IVanBanListItem {
  id: string;
  so_hieu: string;             // Ví dụ: "335/2025/NĐ-CP"
  trich_yeu: string;           // Tóm tắt ngắn nội dung
  loai_van_ban: ILoaiVanBan;   // Object loại VB (embedded)
  co_quan_ban_hanh: string;    // Ví dụ: "Chính phủ", "Bộ Tài chính"
  ngay_ban_hanh: string;       // ISO date: "2025-10-01"
  ngay_hieu_luc: string;       // ISO date: "2025-12-01"
  trang_thai_hieu_luc: string; // CON_HIEU_LUC | HET_HIEU_LUC | CHUA_HIEU_LUC
  muc_do: string;              // BINH_THUONG | QUAN_TRONG | KHAN | RAT_KHAN
  bat_buoc_doc: boolean;       // Bắt buộc CBCC xác nhận đã đọc
  han_xac_nhan: string | null; // Deadline xác nhận (ISO date), null nếu không giới hạn
  da_doc: boolean;             // CBCC hiện tại đã mở đọc chưa
  da_xac_nhan: boolean;        // CBCC hiện tại đã bấm "Xác nhận" chưa
  co_diem_moi: boolean;        // Có điểm mới quan trọng cần lưu ý
  tags?: string[];             // Tags/chuyên đề: ["xử phạt", "hành chính"] — JSONB, có thể null từ API
  ngay_xuat_ban: string;       // ISO date khi xuất bản lên hệ thống
  phien_ban?: number;          // Phiên bản nội dung (tăng khi sửa VB đã xuất bản)
  trang_thai_duyet?: string;   // NHAP | CHO_DUYET | DA_DUYET | DA_XUAT_BAN (trong /quan-ly)
}

// =============================================================================
// XÁC NHẬN ĐỌC (embedded trong VanBanDetail)
// =============================================================================

/**
 * Thông tin xác nhận đọc của CBCC đang đăng nhập.
 * Trả về null nếu CBCC chưa bao giờ mở VB.
 */
export interface IXacNhanDoc {
  da_doc: boolean;                  // Đã mở/đọc VB ít nhất 1 lần
  ngay_doc: string | null;          // ISO datetime khi mở lần đầu, null nếu chưa đọc
  da_xac_nhan: boolean;             // Đã bấm "Xác nhận đã đọc và hiểu"
  ngay_xac_nhan: string | null;     // ISO datetime khi xác nhận, null nếu chưa xác nhận
  thoi_gian_doc_giay: number;       // Tổng thời gian đọc tích lũy (giây)
}

// =============================================================================
// VĂN BẢN LIÊN KẾT
// =============================================================================

/** Văn bản có mối quan hệ với VB hiện tại */
export interface IVanBanLienKet {
  id: string;
  so_hieu: string;
  loai_lien_ket: string;   // THAY_THE | BO_SUNG | HUONG_DAN | LIEN_QUAN
  trich_yeu: string;
}

// =============================================================================
// QUIZ BRIEF (hiển thị trong chi tiết văn bản)
// =============================================================================

/** Thông tin quiz tóm tắt, embedded trong VanBanDetail */
export interface IQuizBrief {
  id: string;
  tieu_de: string;
  so_cau_hoi: number;
}

// =============================================================================
// VĂN BẢN — CHI TIẾT (GET /van-ban/{id})
// =============================================================================

/**
 * Chi tiết đầy đủ văn bản.
 * Side effect khi gọi: tạo/cập nhật xac_nhan_doc (da_doc=TRUE, ghi ngay_doc).
 */
export interface IVanBanDetail extends IVanBanListItem {
  tom_tat: string | null;            // Tóm tắt nội dung bằng ngôn ngữ đơn giản
  noi_dung_html: string | null;      // Nội dung HTML đầy đủ để hiển thị
  file_goc_url: string | null;       // URL file PDF gốc để download
  diem_moi: string | null;           // Điểm mới so với VB cũ (text)
  viec_can_lam: string | null;       // Hướng dẫn việc cần làm sau khi đọc
  chuyen_de?: string[];              // Tags/chuyên đề chi tiết — JSONB, có thể null từ API
  van_ban_lien_ket?: IVanBanLienKet[]; // Có thể null/undefined từ API
  xac_nhan?: IXacNhanDoc;            // null nếu CBCC chưa bao giờ mở VB
  quizzes?: IQuizBrief[];            // Có thể null/undefined từ API — backend trả về key "quizzes"
}

// =============================================================================
// QUIZ VĂN BẢN
// =============================================================================

/**
 * Câu hỏi khi làm bài — KHÔNG có field "correct" (ẩn đáp án đúng).
 * Server trả về danh sách lựa chọn nhưng không đánh dấu đáp án nào đúng.
 */
export interface ICauHoi {
  noi_dung: string;    // Nội dung câu hỏi
  dap_an: string[];    // Danh sách các lựa chọn (A, B, C, D...)
}

/** Câu hỏi đầy đủ dùng khi TẠO quiz (chỉ BIEN_TAP/QT_NOI_DUNG/ADMIN) */
export interface ICauHoiCreate {
  noi_dung: string;
  dap_an: string[];
  correct: number;       // Index đáp án đúng (0-based)
  giai_thich?: string;   // Giải thích tại sao đáp án đó đúng
}

/** Body tạo quiz mới cho văn bản */
export interface IQuizVanBanCreate {
  tieu_de: string;
  thoi_gian_phut: number;    // Thời gian làm bài (phút)
  diem_dat: number;          // Điểm đạt yêu cầu 0-100 (ví dụ: 70.0)
  cau_hoi: ICauHoiCreate[];
}

/** Quiz đầy đủ response (GET /van-ban/{vbId}/quiz) */
export interface IQuizVanBan {
  id: string;
  tieu_de: string;
  so_cau_hoi: number;
  thoi_gian_phut: number;
  diem_dat: number;
  cau_hoi: ICauHoi[];   // Câu hỏi không có đáp án đúng
}

// =============================================================================
// KẾT QUẢ QUIZ (POST /quiz/{id}/lam-bai)
// =============================================================================

/** Chi tiết kết quả 1 câu sau khi làm bài */
export interface IChiTietKetQuaCau {
  cau: number;          // Index câu hỏi (0-based)
  tra_loi: number;      // Index đáp án CBCC đã chọn
  dung: boolean;        // Đúng hay sai
  giai_thich: string;   // Giải thích đáp án đúng
}

/** Kết quả tổng hợp sau khi làm và nộp quiz */
export interface IKetQuaQuiz {
  diem: number;                          // Điểm số (0-100)
  so_cau_dung: number;                   // Số câu trả lời đúng
  dat_yeu_cau: boolean;                  // Đạt điểm yêu cầu
  chi_tiet: IChiTietKetQuaCau[];         // Chi tiết từng câu
}

// =============================================================================
// DASHBOARD & BÁO CÁO
// =============================================================================

/** Tóm tắt thống kê dashboard cá nhân (GET /dashboard/summary) */
export interface IDashboardSummary {
  vb_moi_tuan: number;        // VB mới xuất bản trong tuần này
  vb_chua_doc: number;        // VB bat_buoc_doc mà CBCC chưa đọc
  vb_khan: number;            // VB cấp độ KHAN hoặc RAT_KHAN
  vb_sap_het_han: number;     // VB sắp hết hạn xác nhận (trong 7 ngày tới)
  quiz_chua_lam: number;      // Số quiz chưa làm
}

/** Thống kê tổng hợp trong báo cáo đơn vị */
export interface IThongKeDonVi {
  vb_bat_buoc_trong_thang: number;   // Số VB bắt buộc đọc trong tháng
  ty_le_da_doc: number;              // Tỷ lệ CBCC đã đọc (%)
  ty_le_xac_nhan: number;            // Tỷ lệ CBCC đã xác nhận (%)
  ty_le_qua_han: number;             // Tỷ lệ quá hạn xác nhận (%)
  quiz_diem_tb: number;              // Điểm quiz trung bình của đơn vị
}

/** CBCC chưa hoàn thành đọc văn bản — trong báo cáo đơn vị */
export interface ICBCCChuaDoc {
  ho_ten: string;
  vb_chua_doc: number;    // Số VB chưa đọc
  vb_qua_han: number;     // Số VB đã quá hạn xác nhận
}

/** Báo cáo tổng hợp đơn vị (GET /bao-cao/don-vi/{don_vi_id}) */
export interface IBaoCaoDonVi {
  don_vi: { ten_don_vi: string };
  tong_cbcc: number;
  thong_ke: IThongKeDonVi;
  cbcc_chua_doc: ICBCCChuaDoc[];
}

// =============================================================================
// BÁO CÁO XÁC NHẬN ĐỌC (cho lãnh đạo — GET /van-ban/{id}/bao-cao-doc)
// =============================================================================

/** Chi tiết trạng thái đọc/xác nhận của 1 CBCC */
export interface IChiTietXacNhanDoc {
  cong_chuc: {
    ho_ten: string;
    don_vi: string;
  };
  da_doc: boolean;
  da_xac_nhan: boolean;
  ngay_doc: string | null;
}

/** Báo cáo xác nhận đọc cho lãnh đạo */
export interface IBaoCaoXacNhanDoc {
  van_ban: {
    so_hieu: string;
    han_xac_nhan: string | null;
  };
  tong_doi_tuong: number;   // Tổng số CBCC phải đọc
  da_doc: number;
  da_xac_nhan: number;
  chua_doc: number;
  qua_han: number;
  chi_tiet: IChiTietXacNhanDoc[];
}

// =============================================================================
// REQUEST BODIES
// =============================================================================

/** Body tạo văn bản mới (POST /van-ban) */
export interface IVanBanCreate {
  so_hieu: string;
  trich_yeu: string;
  loai_van_ban_id: string;
  co_quan_ban_hanh: string;
  ngay_ban_hanh: string;
  ngay_hieu_luc: string;
  trang_thai_hieu_luc: string;
  tom_tat?: string;
  noi_dung_html?: string;
  diem_moi?: string;
  viec_can_lam?: string;
  muc_do: string;
  bat_buoc_doc: boolean;
  han_xac_nhan?: string;
  doi_tuong_ap_dung?: string[];   // ["TAT_CA"] hoặc list UUID đơn vị
  chuyen_de?: string[];
  van_ban_lien_ket?: {
    van_ban_lien_quan_id: string;
    loai_lien_ket: string;
  }[];
}

/** Body cập nhật trạng thái duyệt (PATCH /van-ban/{id}/trang-thai) */
export interface ICapNhatTrangThaiBody {
  trang_thai_duyet: string;  // NHAP | CHO_DUYET | DA_DUYET | DA_XUAT_BAN
  ghi_chu?: string;
}

/** Body xác nhận đã đọc (POST /van-ban/{id}/xac-nhan) */
export interface IXacNhanDocBody {
  da_xac_nhan: boolean;
  ghi_chu?: string;
}

/** Body tracking thời gian đọc tích lũy (PATCH /van-ban/{id}/tracking) */
export interface ITrackingDocBody {
  thoi_gian_doc_giay: number;
}

/** Body nộp bài quiz (POST /quiz/{id}/lam-bai) */
export interface ILamQuizBody {
  tra_loi: { cau: number; dap_an: number }[];
}

// =============================================================================
// QUERY PARAMS
// =============================================================================

/** Query params cho GET /van-ban */
export interface IVanBanQueryParams {
  loai_van_ban_id?: string;
  trang_thai_hieu_luc?: string;   // CON_HIEU_LUC | HET_HIEU_LUC | CHUA_HIEU_LUC
  muc_do?: string;                // BINH_THUONG | QUAN_TRONG | KHAN | RAT_KHAN
  bat_buoc_doc?: boolean;
  chuyen_de?: string;
  search?: string;
  sap_xep?: 'moi_nhat' | 'quan_trong';
  page?: number;
  page_size?: number;
}

// =============================================================================
// COMMON
// =============================================================================

/** Phân trang chuẩn của hệ thống */
export interface IPagination {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

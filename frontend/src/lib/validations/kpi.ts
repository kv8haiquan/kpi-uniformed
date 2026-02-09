/**
 * src/lib/validations/kpi.ts
 * ==========================
 * Zod validation schemas cho KPI Submission (Kê khai công việc).
 * 
 * Version: 2.7.4 (02/02/2026)
 * UPDATE v2.7.4:
 * - Thêm ghi_chu_tu_dg_chat_luong, ghi_chu_tu_dg_tien_do vào keKhaiFormSchema
 */

import { z } from 'zod';

/**
 * Schema validation cho form thêm/sửa kê khai công việc.
 */
export const keKhaiFormSchema = z.object({
  // Công việc (bắt buộc)
  danh_muc_sp_id: z
    .string()
    .min(1, 'Vui lòng chọn công việc'),
  
  // Cấp độ phức tạp (bắt buộc)
  cap_do_id: z
    .string()
    .min(1, 'Vui lòng chọn cấp độ phức tạp'),
  
  // Số lượng (bắt buộc, > 0)
  // Preprocess: NaN (khi user xóa trống ô input) → undefined → Zod báo lỗi required
so_luong: z.preprocess(
  (val) => (typeof val === 'number' && isNaN(val) ? undefined : val),
  z
    .number({
      message: 'Vui lòng nhập số lượng hợp lệ',
    })
    .int('Số lượng phải là số nguyên')
    .min(0, 'Số lượng phải lớn hơn 0')
    .max(9999, 'Số lượng không được vượt quá 9999')
),

// Tháng (bắt buộc, 1-12)
thang: z
  .number({
    message: 'Vui lòng chọn tháng hợp lệ',
  })
  .int()
  .min(1, 'Tháng phải từ 1 đến 12')
  .max(12, 'Tháng phải từ 1 đến 12'),

// Năm (bắt buộc, >= 2025)
nam: z
  .number({
    message: 'Vui lòng chọn năm hợp lệ',
  })
  .int()
  .min(2025, 'Năm phải từ 2025 trở đi'),
  // Ngày thực hiện (optional)
  ngay_thuc_hien: z
    .string()
    .optional()
    .nullable(),
  
  // Mô tả công việc (optional, max 2000 ký tự)
  mo_ta_cong_viec: z
    .string()
    .max(2000, 'Mô tả không được vượt quá 2000 ký tự')
    .optional()
    .nullable(),
  
  // Đổi mới sáng tạo (optional)
  is_doi_moi_sang_tao: z
    .boolean()
    .default(false),
  
  // Ngày deadline (optional)
  ngay_deadline: z
    .string()
    .optional()
    .nullable(),
  
  // Ngày hoàn thành (optional)
  ngay_hoan_thanh: z
    .string()
    .optional()
    .nullable(),
  
  // Hệ số thực tế - chỉ dùng cho cấp độ C5 (optional)
  he_so_thuc_te: z
    .number()
    .min(0, 'Hệ số phải >= 0')
    .max(100, 'Hệ số không được vượt quá 100')
    .optional()
    .nullable(),
  
  // Người phê duyệt (optional)
  nguoi_phe_duyet_id: z
    .string()
    .optional()
    .nullable(),
  
  // Tự đánh giá: Số lỗi chất lượng (optional, >= 0)
  tu_danh_gia_chat_luong: z
    .number()
    .int()
    .min(0, 'Số lỗi không được âm')
    .default(0),
  
  // Tự đánh giá: Số lỗi tiến độ (optional, >= 0)
  tu_danh_gia_tien_do: z
    .number()
    .int()
    .min(0, 'Số lỗi không được âm')
    .default(0),
  
  // Ghi chú tự đánh giá (optional)
  ghi_chu_tu_danh_gia: z
    .string()
    .max(1000, 'Ghi chú không được vượt quá 1000 ký tự')
    .optional()
    .nullable(),

  // v2.7.4: Mô tả lỗi chất lượng - tự đánh giá (optional)
  ghi_chu_tu_dg_chat_luong: z
    .string()
    .max(1000, 'Mô tả lỗi không được vượt quá 1000 ký tự')
    .optional()
    .nullable(),

  // v2.7.4: Mô tả lỗi tiến độ - tự đánh giá (optional)
  ghi_chu_tu_dg_tien_do: z
    .string()
    .max(1000, 'Mô tả lỗi không được vượt quá 1000 ký tự')
    .optional()
    .nullable(),
});

/**
 * TypeScript type từ Zod schema.
 */
export type KeKhaiFormData = z.infer<typeof keKhaiFormSchema>;

/**
 * Schema validation cho form gửi kê khai đi duyệt.
 */
export const submitKpiSchema = z.object({
  thang: z
    .number()
    .int()
    .min(1)
    .max(12),
  
  nam: z
    .number()
    .int()
    .min(2025),
  
  // Danh sách ID kê khai cần gửi (optional - nếu null thì gửi tất cả)
  ke_khai_ids: z
    .array(z.string().uuid())
    .optional()
    .nullable(),
});

export type SubmitKpiFormData = z.infer<typeof submitKpiSchema>;

/**
 * Schema cho filter kê khai theo tháng/năm.
 */
export const keKhaiFilterSchema = z.object({
  thang: z
    .number()
    .int()
    .min(1)
    .max(12)
    .optional(),
  
  nam: z
    .number()
    .int()
    .min(2025)
    .optional(),
  
  trang_thai: z
    .string()
    .optional(),
});

export type KeKhaiFilterData = z.infer<typeof keKhaiFilterSchema>;

/**
 * Default values cho form kê khai.
 */
export const keKhaiFormDefaults: Partial<KeKhaiFormData> = {
  so_luong: 1,
  is_doi_moi_sang_tao: false,
  tu_danh_gia_chat_luong: 0,
  tu_danh_gia_tien_do: 0,
  ghi_chu_tu_dg_chat_luong: '',
  ghi_chu_tu_dg_tien_do: '',
  thang: new Date().getMonth() + 1,
  nam: new Date().getFullYear(),
};
/**
 * lib/validations/kpi-v2.ts
 * =========================
 * Zod schemas cho form V2_PL3.
 */

import { z } from 'zod';

const dateString = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Định dạng YYYY-MM-DD')
  .optional()
  .or(z.literal(''));

/**
 * Helper: NaN (input field bị xóa) → undefined → Zod required.
 */
const numberPreprocess = (val: unknown) =>
  typeof val === 'number' && Number.isNaN(val) ? undefined : val;

export const keKhaiV2Schema = z.object({
  danh_muc_sp_id: z.string().uuid('Vui lòng chọn mục công việc PL3'),
  so_luong: z.preprocess(
    numberPreprocess,
    z
      .number({ message: 'Vui lòng nhập số lượng hợp lệ' })
      .int('Số lượng phải là số nguyên')
      .positive('Số lượng phải lớn hơn 0')
      .max(9999, 'Số lượng không được vượt quá 9999')
  ),
  thang: z.number().int().min(1).max(12),
  nam: z.number().int().min(2025),
  ngay_thuc_hien: dateString,
  mo_ta_cong_viec: z.string().max(2000).optional().or(z.literal('')),
  is_doi_moi_sang_tao: z.boolean().optional().default(false),
  ngay_deadline: dateString,
  ngay_hoan_thanh: dateString,
  nguoi_phe_duyet_id: z.string().uuid('Vui lòng chọn người phê duyệt'),
  tu_danh_gia_chat_luong: z.preprocess(
    numberPreprocess,
    z.number().int().min(0).optional().default(0)
  ),
  tu_danh_gia_tien_do: z.preprocess(
    numberPreprocess,
    z.number().int().min(0).optional().default(0)
  ),
  ghi_chu_tu_danh_gia: z.string().max(2000).optional().or(z.literal('')),
  ghi_chu_tu_dg_chat_luong: z.string().max(1000).optional().or(z.literal('')),
  ghi_chu_tu_dg_tien_do: z.string().max(1000).optional().or(z.literal('')),
});

// Input type (form values trước khi resolver chạy preprocess)
export type KeKhaiV2FormInput = z.input<typeof keKhaiV2Schema>;
// Output type (sau khi resolver parse — submit handler nhận type này)
export type KeKhaiV2FormData = z.output<typeof keKhaiV2Schema>;

export const keKhaiV2MultiDaySchema = z.object({
  danh_muc_sp_id: z.string().uuid(),
  so_luong: z.preprocess(
    numberPreprocess,
    z.number().int().positive()
  ),
  ngay_thuc_hien_list: z.array(z.string().regex(/^\d{4}-\d{2}-\d{2}$/)).min(1).max(31),
  nguoi_phe_duyet_id: z.string().uuid(),
  mo_ta_cong_viec: z.string().max(2000).optional().or(z.literal('')),
  is_doi_moi_sang_tao: z.boolean().default(false),
  tu_danh_gia_chat_luong: z.preprocess(
    numberPreprocess,
    z.number().int().min(0).default(0)
  ),
  tu_danh_gia_tien_do: z.preprocess(
    numberPreprocess,
    z.number().int().min(0).default(0)
  ),
  ghi_chu_tu_danh_gia: z.string().max(2000).optional().or(z.literal('')),
  ghi_chu_tu_dg_chat_luong: z.string().max(1000).optional().or(z.literal('')),
  ghi_chu_tu_dg_tien_do: z.string().max(1000).optional().or(z.literal('')),
});

export type KeKhaiV2MultiDayFormData = z.infer<typeof keKhaiV2MultiDaySchema>;

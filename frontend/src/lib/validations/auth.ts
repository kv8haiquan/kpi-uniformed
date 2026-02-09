/**
 * src/lib/validations/auth.ts
 * ===========================
 * Zod validation schemas cho Authentication.
 */

import { z } from 'zod';

/**
 * Schema validation cho form đăng nhập.
 */
export const loginSchema = z.object({
  username: z
    .string()
    .min(1, 'Vui lòng nhập mã định danh')
    .max(50, 'Mã định danh không được quá 50 ký tự')
    .trim(),
  
  password: z
    .string()
    .min(1, 'Vui lòng nhập mật khẩu')
    .max(100, 'Mật khẩu không được quá 100 ký tự'),
});

/**
 * TypeScript type từ Zod schema.
 */
export type LoginFormData = z.infer<typeof loginSchema>;

/**
 * Schema validation cho form đổi mật khẩu (dùng sau).
 */
export const changePasswordSchema = z
  .object({
    currentPassword: z
      .string()
      .min(1, 'Vui lòng nhập mật khẩu hiện tại'),
    
    newPassword: z
      .string()
      .min(6, 'Mật khẩu mới phải có ít nhất 6 ký tự')
      .max(100, 'Mật khẩu không được quá 100 ký tự')
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        'Mật khẩu phải chứa ít nhất 1 chữ hoa, 1 chữ thường và 1 số'
      ),
    
    confirmPassword: z
      .string()
      .min(1, 'Vui lòng xác nhận mật khẩu mới'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Mật khẩu xác nhận không khớp',
    path: ['confirmPassword'],
  });

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

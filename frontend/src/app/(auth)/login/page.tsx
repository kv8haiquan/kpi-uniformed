/**
 * src/app/(auth)/login/page.tsx
 * =============================
 * Trang đăng nhập hệ thống KPI Hải quan.
 * Design: Glassmorphism + Split Layout với background sân bay Vân Đồn
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Image from 'next/image';

import { loginSchema, LoginFormData } from '@/lib/validations/auth';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/stores/useAuthStore';
import { isApiError } from '@/lib/axios';

// =============================================================================
// COMPONENT
// =============================================================================

export default function LoginPage() {
  const router = useRouter();
  const { loginSuccess, isAuthenticated } = useAuthStore();
  
  // State cho loading và error
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  // React Hook Form với Zod validation
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  // Redirect nếu đã đăng nhập
  useEffect(() => {
    if (isAuthenticated) {
      const redirectUrl = authService.getRedirectUrl();
      router.replace(redirectUrl);
    }
  }, [isAuthenticated, router]);

  // Xử lý submit form
  const onSubmit = async (data: LoginFormData) => {
    setIsSubmitting(true);
    setLoginError(null);

    try {
      // Bước 1: Gọi API login để lấy token
      const tokenResponse = await authService.login(data);

      // Bước 2: Gọi API /me để lấy thông tin user
      const user = await authService.getMe();

      // Bước 3: Cập nhật store
      loginSuccess(user, tokenResponse.access_token);

      // Bước 4: Redirect về dashboard hoặc URL đã lưu
      const redirectUrl = authService.getRedirectUrl();
      router.push(redirectUrl);
      
    } catch (error) {
      // Xử lý lỗi - hiển thị message từ backend
      if (isApiError(error)) {
        // Error đã được map message từ auth.service.ts
        setLoginError(error.message);
      } else if (error instanceof Error) {
        setLoginError(error.message);
      } else {
        setLoginError('Đã có lỗi xảy ra. Vui lòng thử lại.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      {/* Google Font - Be Vietnam Pro: hỗ trợ dấu tiếng Việt tốt */}
      {/* eslint-disable-next-line @next/next/no-page-custom-font */}
      <link
        href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800;900&display=swap"
        rel="stylesheet"
      />

      {/* Background Image - Sân bay Vân Đồn */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: "url('/images/cua-khau-mong-cai.jpg')",
        }}
      >
        {/* Overlay gradient để tăng độ tương phản */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/60 via-blue-800/40 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-blue-900/50 via-transparent to-orange-500/20" />
      </div>

      {/* Main Content - Split Layout */}
      <div className="relative z-10 flex min-h-screen">
        
        {/* Left Side - Branding & Info */}
        <div className="hidden lg:flex lg:w-1/2 flex-col justify-center px-12 xl:px-20">
          {/* Logo và tên đơn vị */}
          <div className="flex items-center gap-4 mb-8 animate-fade-in-up">
            <div className="relative w-24 h-24 xl:w-28 xl:h-28 drop-shadow-2xl">
              <Image
                src="/images/logo-hai-quan.png"
                alt="Logo Hải quan Việt Nam"
                fill
                className="object-contain"
                priority
              />
            </div>
            <div style={{ fontFamily: "'Be Vietnam Pro', sans-serif" }}>
              <p className="text-white/90 text-sm xl:text-base font-medium tracking-wider uppercase">
                Chi cục Hải quan
              </p>
              <p className="text-white text-lg xl:text-xl font-bold tracking-wide">
                KHU VỰC VIII
              </p>
            </div>
          </div>

          {/* Tên phần mềm - dùng Be Vietnam Pro để hiển thị dấu tiếng Việt đầy đủ */}
          <div className="animate-fade-in-up animation-delay-200 pt-2">
            <h1
              className="text-4xl xl:text-5xl 2xl:text-6xl font-extrabold text-white tracking-tight"
              style={{
                fontFamily: "'Be Vietnam Pro', sans-serif",
                lineHeight: '1.35',
              }}
            >
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-yellow-400 to-orange-400 drop-shadow-lg pb-1">
                PHẦN MỀM THEO DÕI,
              </span>
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-yellow-400 to-orange-400 drop-shadow-lg mt-1">
                ĐÁNH GIÁ CÔNG CHỨC
              </span>
            </h1>
          </div>

          {/* Slogan */}
          <div className="mt-8 animate-fade-in-up animation-delay-400">
            <div className="flex items-center gap-3">
              <div className="h-px w-12 bg-gradient-to-r from-transparent to-yellow-400/70" />
              <p className="text-white/80 text-sm xl:text-base font-medium tracking-widest uppercase">
                Đoàn kết • Kỷ cương • Chuyên nghiệp • Sáng tạo
              </p>
            </div>
          </div>

          {/* Decorative elements */}
          <div className="absolute bottom-12 left-12 xl:left-20 animate-fade-in-up animation-delay-600">
            <p className="text-white/50 text-xs tracking-wider">
              © 2026 Cục Hải quan - Bộ Tài chính
            </p>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center px-6 py-12">
          <div className="w-full max-w-md animate-fade-in-up animation-delay-300">
            
            {/* Glassmorphism Card - với nền đậm hơn để dễ đọc */}
            <div className="relative backdrop-blur-2xl bg-slate-900/70 rounded-3xl border border-white/20 shadow-2xl overflow-hidden">
              {/* Decorative glow effects */}
              <div className="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl" />
              <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-blue-600/20 rounded-full blur-3xl" />
              
              {/* Card Content */}
              <div className="relative z-10 p-8 xl:p-10">
                
                {/* Mobile Logo - chỉ hiển thị trên mobile */}
                <div className="flex lg:hidden flex-col items-center mb-8">
                  <div className="relative w-20 h-20 mb-3">
                    <Image
                      src="/images/logo-hai-quan.png"
                      alt="Logo Hải quan Việt Nam"
                      fill
                      className="object-contain"
                      priority
                    />
                  </div>
                  <p className="text-white/90 text-xs font-medium tracking-wider uppercase">
                    Chi cục Hải quan Khu vực VIII
                  </p>
                </div>

                {/* Form Title */}
                <div className="text-center mb-8">
                  <h2
                    className="text-2xl xl:text-3xl font-bold text-white tracking-wide drop-shadow-lg"
                    style={{ fontFamily: "'Be Vietnam Pro', sans-serif", lineHeight: '1.4' }}
                  >
                    ĐĂNG NHẬP
                  </h2>
                  <p className="text-white/80 text-sm mt-2 font-medium">
                    Vui lòng nhập thông tin tài khoản
                  </p>
                </div>

                {/* Error Message */}
                {loginError && (
                  <div className="mb-6 p-4 rounded-xl bg-red-500/20 border border-red-500/30 backdrop-blur-sm animate-shake">
                    <div className="flex items-center gap-3">
                      <div className="flex-shrink-0 w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </div>
                      <p className="text-red-200 text-sm font-medium">{loginError}</p>
                    </div>
                  </div>
                )}

                {/* Login Form */}
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                  
                  {/* Username Field */}
                  <div className="space-y-2">
                    <label className="block text-white text-sm font-semibold pl-1">
                      Tên đăng nhập
                    </label>
                    <div className="relative group">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <svg 
                          className="w-5 h-5 text-blue-300 group-focus-within:text-yellow-400 transition-colors" 
                          fill="none" 
                          viewBox="0 0 24 24" 
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      </div>
                      <input
                        id="username"
                        type="text"
                        autoComplete="username"
                        placeholder="VD: 20ZZ-0224"
                        className={`
                          w-full pl-12 pr-4 py-3.5 
                          bg-white/10 backdrop-blur-sm
                          border-2 rounded-xl
                          text-white placeholder-white/50
                          transition-all duration-300
                          focus:outline-none focus:bg-white/15
                          ${errors.username 
                            ? 'border-red-500/50 focus:border-red-500' 
                            : 'border-white/20 focus:border-yellow-400/70 hover:border-white/30'
                          }
                        `}
                        {...register('username')}
                      />
                      {/* Animated underline */}
                      <div className="absolute bottom-0 left-1/2 w-0 h-0.5 bg-gradient-to-r from-yellow-400 to-orange-400 group-focus-within:w-full group-focus-within:left-0 transition-all duration-300 rounded-full" />
                    </div>
                    {errors.username && (
                      <p className="text-red-400 text-xs pl-1 animate-fade-in">{errors.username.message}</p>
                    )}
                  </div>

                  {/* Password Field */}
                  <div className="space-y-2">
                    <label className="block text-white text-sm font-semibold pl-1">
                      Mật khẩu
                    </label>
                    <div className="relative group">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <svg 
                          className="w-5 h-5 text-blue-300 group-focus-within:text-yellow-400 transition-colors" 
                          fill="none" 
                          viewBox="0 0 24 24" 
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                      </div>
                      <input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        autoComplete="current-password"
                        placeholder="Nhập mật khẩu"
                        className={`
                          w-full pl-12 pr-12 py-3.5 
                          bg-white/10 backdrop-blur-sm
                          border-2 rounded-xl
                          text-white placeholder-white/50
                          transition-all duration-300
                          focus:outline-none focus:bg-white/15
                          ${errors.password 
                            ? 'border-red-500/50 focus:border-red-500' 
                            : 'border-white/20 focus:border-yellow-400/70 hover:border-white/30'
                          }
                        `}
                        {...register('password')}
                      />
                      {/* Toggle Password Visibility */}
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute inset-y-0 right-0 pr-4 flex items-center text-blue-300 hover:text-white transition-colors"
                      >
                        {showPassword ? (
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        )}
                      </button>
                      {/* Animated underline */}
                      <div className="absolute bottom-0 left-1/2 w-0 h-0.5 bg-gradient-to-r from-yellow-400 to-orange-400 group-focus-within:w-full group-focus-within:left-0 transition-all duration-300 rounded-full" />
                    </div>
                    {errors.password && (
                      <p className="text-red-400 text-xs pl-1 animate-fade-in">{errors.password.message}</p>
                    )}
                  </div>

                  {/* Remember Me & Forgot Password */}
                  <div className="flex items-center justify-between text-sm">
                    <label className="flex items-center gap-2 cursor-pointer group">
                      <div className="relative">
                        <input type="checkbox" className="sr-only peer" />
                        <div className="w-5 h-5 rounded-md border-2 border-white/30 bg-white/10 peer-checked:bg-yellow-400 peer-checked:border-yellow-400 transition-all duration-200" />
                        <svg 
                          className="absolute top-0.5 left-0.5 w-4 h-4 text-blue-900 opacity-0 peer-checked:opacity-100 transition-opacity" 
                          fill="none" 
                          viewBox="0 0 24 24" 
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <span className="text-white/90 group-hover:text-white transition-colors font-medium">
                        Ghi nhớ
                      </span>
                    </label>
                    <button 
                      type="button" 
                      className="text-yellow-400 hover:text-yellow-300 transition-colors font-semibold"
                    >
                      Quên mật khẩu?
                    </button>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className={`
                      relative w-full py-4 rounded-xl font-bold text-base tracking-wide
                      transition-all duration-300 transform
                      ${isSubmitting 
                        ? 'bg-gray-500 cursor-not-allowed' 
                        : 'bg-gradient-to-r from-red-600 via-red-500 to-red-600 hover:from-red-500 hover:via-red-400 hover:to-red-500 hover:scale-[1.02] hover:shadow-lg hover:shadow-red-500/30 active:scale-[0.98]'
                      }
                      text-white shadow-xl
                      overflow-hidden
                    `}
                  >
                    {/* Button glow effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full hover:translate-x-full transition-transform duration-700" />
                    
                    <span className="relative flex items-center justify-center gap-2">
                      {isSubmitting ? (
                        <>
                          <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Đang đăng nhập...
                        </>
                      ) : (
                        'ĐĂNG NHẬP'
                      )}
                    </span>
                  </button>
                </form>

                {/* Footer Note */}
                <p className="mt-6 text-center text-white/70 text-xs font-medium">
                  Liên hệ quản trị viên nếu cần hỗ trợ
                </p>
              </div>
            </div>

            {/* Mobile Footer */}
            <div className="lg:hidden mt-8 text-center">
              <p className="text-white/70 text-xs font-medium">
                © 2026 Cục Hải quan - Bộ Tài chính
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Custom Styles */}
      <style jsx>{`
        @keyframes fade-in-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
          20%, 40%, 60%, 80% { transform: translateX(4px); }
        }
        
        .animate-fade-in-up {
          animation: fade-in-up 0.6s ease-out forwards;
        }
        
        .animate-fade-in {
          animation: fade-in 0.3s ease-out forwards;
        }
        
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
        
        .animation-delay-200 {
          animation-delay: 0.2s;
          opacity: 0;
        }
        
        .animation-delay-300 {
          animation-delay: 0.3s;
          opacity: 0;
        }
        
        .animation-delay-400 {
          animation-delay: 0.4s;
          opacity: 0;
        }
        
        .animation-delay-600 {
          animation-delay: 0.6s;
          opacity: 0;
        }
      `}</style>
    </div>
  );
}
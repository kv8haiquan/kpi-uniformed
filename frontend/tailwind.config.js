/**
 * tailwind.config.js
 * ==================
 * Cấu hình Tailwind CSS cho dự án KPI Hải quan.
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // Custom fonts
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
      },
      
      // Custom colors cho Hải quan theme
      colors: {
        // Primary blue (màu chủ đạo Hải quan)
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb', // Main
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        
        // Xếp loại colors
        'xep-loai': {
          A: '#16a34a', // Green - Xuất sắc
          B: '#2563eb', // Blue - Tốt  
          C: '#ca8a04', // Yellow - Hoàn thành
          D: '#dc2626', // Red - Không hoàn thành
        },
      },
      
      // Custom animations
      animation: {
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      
      // Custom spacing
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      
      // Custom border radius
      borderRadius: {
        '4xl': '2rem',
      },
    },
  },
  plugins: [
    // Plugin cho forms (optional)
    // require('@tailwindcss/forms'),
  ],
};

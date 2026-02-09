/**
 * src/app/layout.tsx
 * ==================
 * Root layout cho toàn bộ ứng dụng.
 * Wrap AuthProvider và các global providers.
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

import { AuthProvider } from '@/providers/AuthProvider';

// =============================================================================
// FONTS
// =============================================================================

const inter = Inter({ 
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
  variable: '--font-inter',
});

// =============================================================================
// METADATA
// =============================================================================

export const metadata: Metadata = {
  title: {
    default: 'Hệ thống KPI - Chi cục Hải quan Khu vực VIII',
    template: '%s | KPI Hải quan',
  },
  description: 'Hệ thống Đánh giá và Xếp loại Công chức theo KPI - Chi cục Hải quan Khu vực VIII',
  keywords: ['KPI', 'Hải quan', 'Đánh giá', 'Công chức', 'Chi cục'],
  authors: [{ name: 'Chi cục Hải quan Khu vực VIII' }],
  robots: 'noindex, nofollow', // Hệ thống nội bộ
};

// =============================================================================
// LAYOUT COMPONENT
// =============================================================================

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="vi" className={inter.variable}>
      <body className="font-sans antialiased">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}

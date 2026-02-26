import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /**
   * Rewrites — proxy API calls từ frontend đến các backend service.
   *
   * Mỗi module có prefix khác nhau tùy backend:
   *   LMS:    /api/v1/lms/     → http://localhost:8001/api/v1/lms/
   *   Legal:  /api/legal/v1/   → http://localhost:8003/api/legal/v1/
   *   Portal: /api/portal/v1/  → http://localhost:8004/api/v1/
   *   Common: /api/common/v1/  → http://localhost:8005/api/common/v1/
   */
  async rewrites() {
    return [
      // Legal module — port 8003
      // Frontend gọi: /api/legal/v1/van-ban
      // Backend nhận: http://localhost:8003/api/legal/v1/van-ban
      {
        source: '/api/legal/v1/:path*',
        destination: 'http://localhost:8003/api/legal/v1/:path*',
      },
      // Legal static files (PDF/DOCX uploads) — dev proxy, production dùng nginx
      // Frontend gọi: /uploads/legal/van-ban/filename.pdf
      // Backend phục vụ qua FastAPI StaticFiles mount tại /uploads/legal/
      {
        source: '/uploads/legal/:path*',
        destination: 'http://localhost:8003/uploads/legal/:path*',
      },
      // Portal module — port 8004
      // Frontend gọi: /api/portal/v1/dashboard/summary
      // Backend nhận: http://localhost:8004/api/v1/dashboard/summary
      {
        source: '/api/portal/v1/:path*',
        destination: 'http://localhost:8004/api/v1/:path*',
      },
      // LMS module — port 8001
      // Frontend gọi: /api/v1/lms/dashboard/summary
      // Backend nhận: http://localhost:8001/api/v1/lms/dashboard/summary
      {
        source: '/api/v1/lms/:path*',
        destination: 'http://localhost:8001/api/v1/lms/:path*',
      },
      // LMS uploads — dev proxy, production dùng nginx
      {
        source: '/uploads/lms/:path*',
        destination: 'http://localhost:8001/uploads/lms/:path*',
      },
      // Common module — port 8005
      // Frontend gọi: /api/common/v1/thong-bao
      // Backend nhận: http://localhost:8005/api/common/v1/thong-bao
      {
        source: '/api/common/v1/:path*',
        destination: 'http://localhost:8005/api/common/v1/:path*',
      },
    ];
  },
};

export default nextConfig;

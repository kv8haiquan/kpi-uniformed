import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /**
   * Rewrites — proxy API calls từ frontend đến các backend service.
   *
   * Pattern chuẩn (SHARED_CODING_STANDARDS §5.1):
   *   Frontend  →  /api/{module}/v1/:path*
   *   Rewrite   →  http://localhost:{port}/api/v1/{module}/:path*
   *
   * ⚠️ Lưu ý: Backend Legal đang dùng prefix /api/v1/legal (chưa đổi sang /api/legal/v1).
   * Rewrite bên dưới translate để frontend luôn đúng chuẩn.
   * Khi backend sửa prefix → chỉ cần cập nhật destination ở đây.
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
      // Frontend gọi: /api/lms/v1/dashboard/summary
      // Backend nhận: http://localhost:8001/api/v1/dashboard/summary
      {
        source: '/api/lms/v1/:path*',
        destination: 'http://localhost:8001/api/v1/:path*',
      },
    ];
  },
};

export default nextConfig;

import type { NextConfig } from "next";

/**
 * Cổng backend cho các quy tắc `rewrites` bên dưới.
 *
 * Prod dùng 8001–8007, dev dùng 9001–9007. Trước đây số cổng viết cứng là
 * 800x, nên frontend dev (cổng 3001) proxy thẳng vào backend PRODUCTION —
 * giao diện đang làm dở thao tác trên dữ liệu thật.
 *
 * Đặt `BACKEND_PORT_PREFIX=90` trong `frontend/.env.local` (file này bị
 * gitignore nên không lẫn sang prod) để trỏ về dãy cổng dev.
 */
const P = process.env.BACKEND_PORT_PREFIX ?? "80";
const be = (n: number) => `http://localhost:${P}0${n}`;

const nextConfig: NextConfig = {
  /**
   * Tên miền được phép truy cập tài nguyên chế độ dev (`/_next/*`, nạp lại nóng).
   *
   * Next.js 16 mặc định CHẶN mọi Origin lạ khi chạy `next dev`. Vào
   * dev.kpihaiquan.vn thì trang HTML về được nhưng các gói mã JS bị chặn, nên
   * React không khởi động và màn hình đứng ở "Đang tải hệ thống".
   *
   * Chỉ có tác dụng ở chế độ dev. Prod chạy `next start` nên không đọc mục này.
   */
  allowedDevOrigins: ['dev.kpihaiquan.vn'],

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
        destination: `${be(3)}/api/legal/v1/:path*`,
      },
      // Legal static files (PDF/DOCX uploads) — dev proxy, production dùng nginx
      // Frontend gọi: /uploads/legal/van-ban/filename.pdf
      // Backend phục vụ qua FastAPI StaticFiles mount tại /uploads/legal/
      {
        source: '/uploads/legal/:path*',
        destination: `${be(3)}/uploads/legal/:path*`,
      },
      // Portal module — port 8004
      // Frontend gọi: /api/portal/v1/dashboard/summary
      // Backend nhận: http://localhost:8004/api/v1/dashboard/summary
      {
        source: '/api/portal/v1/:path*',
        destination: `${be(4)}/api/v1/:path*`,
      },
      // Portal static files (ảnh vinh danh, ảnh tin tức) — dev proxy, production dùng nginx
      // Frontend gọi: /uploads/portal/vinh-danh/filename.jpg
      // Backend phục vụ qua FastAPI StaticFiles mount tại /uploads/portal/
      {
        source: '/uploads/portal/:path*',
        destination: `${be(4)}/uploads/portal/:path*`,
      },
      // LMS module — port 8001
      // Frontend gọi: /api/v1/lms/dashboard/summary
      // Backend nhận: http://localhost:8001/api/v1/lms/dashboard/summary
      {
        source: '/api/v1/lms/:path*',
        destination: `${be(1)}/api/v1/lms/:path*`,
      },
      // LMS uploads — dev proxy, production dùng nginx
      {
        source: '/uploads/lms/:path*',
        destination: `${be(1)}/uploads/lms/:path*`,
      },
      // Chỉ tiêu đơn vị module — port 8007
      // Frontend gọi: /api/v1/chi-tieu/linh-vuc
      // Backend nhận: http://localhost:8007/api/v1/chi-tieu/linh-vuc
      {
        source: '/api/v1/chi-tieu/:path*',
        destination: `${be(7)}/api/v1/chi-tieu/:path*`,
      },
      // Forum module — port 8002
      // Frontend goi: /api/forum/v1/chu-de
      // Backend nhan: http://localhost:8002/api/forum/v1/chu-de
      {
        source: '/api/forum/v1/:path*',
        destination: `${be(2)}/api/forum/v1/:path*`,
      },
      // Common module — port 8005
      // Frontend gọi: /api/common/v1/thong-bao
      // Backend nhận: http://localhost:8005/api/common/v1/thong-bao
      {
        source: '/api/common/v1/:path*',
        destination: `${be(5)}/api/common/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;

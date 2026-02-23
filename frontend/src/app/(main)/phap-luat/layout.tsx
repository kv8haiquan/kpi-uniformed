/**
 * src/app/(main)/phap-luat/layout.tsx
 * =====================================
 * Layout chung cho tất cả pages trong module Pháp luật.
 * Wrapper đơn giản — navigation chính đã nằm trong (main)/layout.tsx.
 *
 * Cấu trúc pages:
 *   /phap-luat              → Dashboard (VB mới, thống kê cá nhân)
 *   /phap-luat/van-ban      → Danh sách văn bản
 *   /phap-luat/van-ban/[id] → Chi tiết văn bản + xác nhận đọc
 *   /phap-luat/can-xac-nhan → VB chưa đọc / cần xác nhận
 *   /phap-luat/quan-ly      → Quản lý VB (BIEN_TAP, QT_NOI_DUNG, ADMIN)
 */

export default function PhapLuatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

'use client';

/**
 * PresentationViewerLazy — entry point để dùng PresentationViewer từ ngoài.
 *
 * BẮT BUỘC dùng dynamic({ ssr: false }) vì:
 *  1. pdfjs-dist gọi `window`/`DOMMatrix` ở module-load time → crash trên server.
 *  2. Worker file `/pdf.worker.min.mjs` chỉ tồn tại ở browser.
 *  3. Loại pdfjs (~1.4MB) khỏi server bundle → giảm cold start Next.js.
 */

import dynamic from 'next/dynamic';

const PresentationViewerLazy = dynamic(
  () => import('./PresentationViewer').then((m) => m.PresentationViewer),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-64 bg-gray-100 rounded text-gray-500 text-sm">
        Đang tải trình xem tài liệu...
      </div>
    ),
  },
);

export default PresentationViewerLazy;

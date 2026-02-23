'use client';

/**
 * src/components/legal/PdfViewer.tsx
 * =====================================
 * Hiển thị PDF inline bằng <iframe>.
 *
 * - URL /uploads/legal/van-ban/filename.pdf được proxy qua:
 *   • Dev : Next.js rewrite → http://localhost:8003/uploads/legal/...
 *   • Prod: nginx location /uploads/legal/ → legal_backend:8003
 * - FastAPI StaticFiles phục vụ PDF với Content-Type: application/pdf
 *   → browser tự render inline (Chrome, Firefox, Edge đều hỗ trợ).
 * - Nếu iframe thất bại (CORS, format lạ) → hiển thị fallback download.
 */

import { useState } from 'react';

interface PdfViewerProps {
  /** URL file, ví dụ: /uploads/legal/van-ban/abc123_file.pdf */
  url: string;
  /** Tên file hiển thị trong header */
  filename?: string;
}

export function PdfViewer({ url, filename }: PdfViewerProps) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  const displayName = filename ?? url.split('/').pop() ?? 'File đính kèm';

  return (
    <div className="w-full border border-gray-200 rounded-xl overflow-hidden bg-gray-50">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-gray-100 border-b border-gray-200">
        <span className="text-sm font-medium text-gray-700 truncate max-w-[60%]">
          📄 {displayName}
        </span>
        <div className="flex gap-2 shrink-0">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs px-3 py-1 border border-gray-300 bg-white rounded-lg hover:bg-gray-50 text-gray-600 transition-colors"
          >
            ↗ Mở tab mới
          </a>
          <a
            href={url}
            download={displayName}
            className="text-xs px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            ⬇ Tải xuống
          </a>
        </div>
      </div>

      {/* Loading indicator */}
      {!loaded && !error && (
        <div className="flex items-center justify-center h-16 text-gray-400 text-sm border-b border-gray-100">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600 mr-2" />
          Đang tải file...
        </div>
      )}

      {/* Fallback khi iframe lỗi */}
      {error && (
        <div className="flex flex-col items-center justify-center h-48 gap-3 text-gray-500">
          <span className="text-3xl">📄</span>
          <p className="text-sm">Không thể hiển thị file trực tiếp.</p>
          <div className="flex gap-2">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-600"
            >
              ↗ Mở tab mới
            </a>
            <a
              href={url}
              download={displayName}
              className="text-xs px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              ⬇ Tải xuống
            </a>
          </div>
        </div>
      )}

      {/* PDF iframe */}
      {!error && (
        <iframe
          src={url}
          title={displayName}
          className={`w-full transition-opacity duration-300 ${loaded ? 'opacity-100' : 'opacity-0 h-0'}`}
          style={{ minHeight: loaded ? '75vh' : 0, height: loaded ? '75vh' : 0 }}
          onLoad={() => setLoaded(true)}
          onError={() => { setLoaded(false); setError(true); }}
        />
      )}
    </div>
  );
}

export default PdfViewer;

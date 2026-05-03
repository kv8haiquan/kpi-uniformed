/**
 * Trang preview tài liệu — render file qua <iframe> để bypass
 * Chrome "Download PDFs" setting (browser renders PDF inline trong iframe).
 *
 * Query params:
 * - url: URL của file (đã kèm short-lived token)
 * - ten: Tên file để hiển thị title
 */

'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { Download, ArrowLeft } from 'lucide-react';

function ViewerInner() {
  const sp = useSearchParams();
  const url = sp.get('url') || '';
  const ten = sp.get('ten') || 'Tài liệu';

  if (!url) {
    return (
      <div className="p-8 text-red-600">Thiếu tham số <code>url</code>.</div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-900 flex flex-col">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 text-white">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => window.close()}
            className="p-1 hover:bg-gray-700 rounded"
            title="Đóng tab"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <span className="font-medium truncate">{ten}</span>
        </div>
        <a
          href={url}
          download
          className="inline-flex items-center gap-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
        >
          <Download className="w-4 h-4" /> Tải về
        </a>
      </div>
      <iframe
        src={url}
        className="flex-1 w-full bg-white"
        title={ten}
      />
    </div>
  );
}

export default function XemTaiLieuPage() {
  return (
    <Suspense fallback={<div className="p-8">Đang tải...</div>}>
      <ViewerInner />
    </Suspense>
  );
}

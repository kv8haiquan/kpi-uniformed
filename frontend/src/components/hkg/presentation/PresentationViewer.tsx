'use client';

/**
 * PresentationViewer — render PDF bằng pdfjs-dist v4 trên <canvas>.
 *
 * Phase 4.1 FE_P1 scope:
 *  - Render PDF từ URL (props.url)
 *  - Hiển thị 1 trang tại 1 thời điểm theo props.currentPage (controlled)
 *  - Host (isHost=true) thấy nút Prev/Next gọi onPageChange
 *  - Chưa có WS sync (FE_P2 hook usePresentationSync mới làm)
 *
 * BẮT BUỘC import bằng dynamic({ ssr: false }) — pdfjs-dist không chạy server-side.
 */

import { useEffect, useRef, useState } from 'react';

// pdfjs-dist v4 dùng .mjs worker
import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy } from 'pdfjs-dist';

if (typeof window !== 'undefined') {
  pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';
}

interface PresentationViewerProps {
  /** URL của file PDF (đã kèm short-lived token nếu cần) */
  url: string;
  /** Trang hiện tại (1-based) — controlled bởi parent (host hoặc WS sync) */
  currentPage: number;
  /** Callback khi host bấm Prev/Next */
  onPageChange?: (page: number) => void;
  /** Host: hiển thị nút điều khiển. Đại biểu: read-only, bấm nút không ảnh hưởng. */
  isHost?: boolean;
  /** Optional zoom scale (default 1.5 — vừa đẹp cho A4 trên desktop) */
  scale?: number;
}

export function PresentationViewer({
  url,
  currentPage,
  onPageChange,
  isHost = false,
  scale = 1.5,
}: PresentationViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pdfRef = useRef<PDFDocumentProxy | null>(null);
  const renderTaskRef = useRef<{ cancel: () => void } | null>(null);

  const [totalPages, setTotalPages] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 1) Load PDF document khi url thay đổi
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const loadingTask = pdfjsLib.getDocument({ url });
    loadingTask.promise
      .then((pdf) => {
        if (cancelled) return;
        pdfRef.current = pdf;
        setTotalPages(pdf.numPages);
        setLoading(false);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Không tải được file PDF');
        setLoading(false);
      });

    return () => {
      cancelled = true;
      // pdfjs document có .destroy() để giải phóng worker
      pdfRef.current?.destroy();
      pdfRef.current = null;
    };
  }, [url]);

  // 2) Render trang khi currentPage / totalPages / scale thay đổi
  useEffect(() => {
    const pdf = pdfRef.current;
    const canvas = canvasRef.current;
    if (!pdf || !canvas || totalPages === 0) return;

    const safePage = Math.min(Math.max(1, currentPage), totalPages);
    let cancelled = false;

    pdf.getPage(safePage).then((page) => {
      if (cancelled) return;
      const viewport = page.getViewport({ scale });
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      canvas.width = viewport.width;
      canvas.height = viewport.height;

      // Cancel render task cũ nếu user nhảy trang nhanh
      renderTaskRef.current?.cancel();
      const renderTask = page.render({ canvasContext: ctx, viewport });
      renderTaskRef.current = renderTask;

      renderTask.promise.catch((e: unknown) => {
        // RenderingCancelledException khi cancel — ignore
        if (e && typeof e === 'object' && 'name' in e && (e as { name: string }).name === 'RenderingCancelledException') {
          return;
        }
        if (!cancelled) setError(e instanceof Error ? e.message : 'Lỗi render trang');
      });
    });

    return () => {
      cancelled = true;
      renderTaskRef.current?.cancel();
    };
  }, [currentPage, totalPages, scale]);

  const goPrev = () => {
    if (!isHost || !onPageChange) return;
    if (currentPage > 1) onPageChange(currentPage - 1);
  };
  const goNext = () => {
    if (!isHost || !onPageChange) return;
    if (currentPage < totalPages) onPageChange(currentPage + 1);
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-red-600 bg-red-50 border border-red-200 rounded">
        <p className="text-sm font-medium">Không hiển thị được tài liệu</p>
        <p className="text-xs mt-1 text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center bg-gray-100 rounded">
      {/* Toolbar */}
      <div className="w-full flex items-center justify-between px-4 py-2 bg-gray-800 text-white text-sm rounded-t">
        <div className="flex items-center gap-2">
          {isHost && (
            <>
              <button
                onClick={goPrev}
                disabled={currentPage <= 1 || loading}
                className="px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 rounded"
              >
                ← Trang trước
              </button>
              <button
                onClick={goNext}
                disabled={currentPage >= totalPages || loading}
                className="px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 rounded"
              >
                Trang sau →
              </button>
            </>
          )}
        </div>
        <div className="text-xs">
          {loading
            ? 'Đang tải...'
            : `Trang ${Math.min(currentPage, totalPages)} / ${totalPages}`}
        </div>
      </div>

      {/* Canvas area */}
      <div className="w-full overflow-auto p-4 bg-gray-200" style={{ maxHeight: '75vh' }}>
        <div className="flex justify-center">
          <canvas ref={canvasRef} className="shadow-lg bg-white" />
        </div>
      </div>
    </div>
  );
}

export default PresentationViewer;

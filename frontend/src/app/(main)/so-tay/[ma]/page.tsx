/**
 * src/app/(main)/so-tay/[ma]/page.tsx
 * =====================================
 * Xem một Sổ tay số trong iframe.
 *
 * Vì sao blob URL: tệp chỉ dùng nội bộ, phải đăng nhập mới lấy được; JWT nằm ở
 * localStorage nên không thể cho iframe trỏ thẳng vào API. Lấy bằng axios
 * (kèm Bearer) → blob URL. Blob URL cùng origin với trang này, nên
 * localStorage/IndexedDB của sổ (đánh dấu, ghi chú, Sổ nhật ký Đoàn) chạy bình
 * thường và giữ qua các lần mở.
 *
 * KHÔNG gắn `sandbox`: Sổ nhật ký Đoàn dùng showDirectoryPicker, Chrome cấm hộp
 * chọn tệp trong iframe sandbox. Việc chặn tải nguyên tệp do lib/so-tay-nhung.ts lo.
 *
 * Giao kèo postMessage với Sổ tay KTNB: khi chạy trong iframe, sổ KHÔNG tự mở
 * PDF (trình duyệt chặn PDF lồng iframe) mà gửi lên trang cha:
 *   FORM_SHOW_PDF  {num, code, name, pdfBlobUrl, docxBlobUrl, docxName} — biểu mẫu
 *   QD459_SHOW_PDF {blobUrl}                                          — toàn văn QĐ 459
 * Blob URL do sổ tạo, dùng được ở đây vì cùng origin.
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Download, ExternalLink, Maximize2, X } from 'lucide-react';
import { isAxiosError } from 'axios';
import { soTayApi } from '@/services/common';
import { chuanBiHtmlSoTay } from '@/lib/so-tay-nhung';

const TEN_SO: Record<string, string> = {
  'kiem-tra-noi-bo': 'Sổ tay kiểm tra nội bộ',
  'tra-cuu-loi': 'Sổ tra cứu lỗi hải quan',
};

interface IXemPdf {
  tieuDe: string;
  pdfUrl: string;
  docxUrl?: string;
  docxTen?: string;
}

export default function XemSoTayPage() {
  const { ma } = useParams<{ ma: string }>();
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [xemPdf, setXemPdf] = useState<IXemPdf | null>(null);
  const [thongBao, setThongBao] = useState<string | null>(null);

  // Tải nội dung sổ → blob URL; thu hồi khi rời trang
  useEffect(() => {
    let url: string | null = null;
    let huy = false;
    soTayApi
      .noiDung(ma)
      .then((res) => {
        if (huy) return;
        const html = chuanBiHtmlSoTay(res.data);
        url = URL.createObjectURL(new Blob([html], { type: 'text/html;charset=utf-8' }));
        setBlobUrl(url);
      })
      .catch((err: unknown) => {
        if (huy) return;
        setError(
          isAxiosError(err) && err.response?.status === 404
            ? 'Sổ tay này chưa được đăng tải'
            : 'Không tải được sổ tay, vui lòng thử lại'
        );
      });
    return () => {
      huy = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [ma]);

  // Chỉ nhận blob URL cùng origin — không để sổ (hay ai khác) đẩy URL lạ vào trang
  const laBlobNoiBo = (u: unknown): u is string =>
    typeof u === 'string' && u.startsWith(`blob:${window.location.origin}/`);

  const nhanThongDiep = useCallback((e: MessageEvent) => {
    if (e.origin !== window.location.origin) return;
    if (!iframeRef.current || e.source !== iframeRef.current.contentWindow) return;
    const d = e.data || {};
    if (d.type === 'FORM_SHOW_PDF' && laBlobNoiBo(d.pdfBlobUrl)) {
      setXemPdf({
        tieuDe: `Mẫu ${d.num}${d.code ? '/' + d.code : ''} — ${d.name || ''}`,
        pdfUrl: d.pdfBlobUrl,
        docxUrl: laBlobNoiBo(d.docxBlobUrl) ? d.docxBlobUrl : undefined,
        docxTen: typeof d.docxName === 'string' ? d.docxName : undefined,
      });
    } else if (d.type === 'QD459_SHOW_PDF' && laBlobNoiBo(d.blobUrl)) {
      setXemPdf({ tieuDe: 'Quyết định 459/QĐ-CHQ — Quy chế kiểm tra nội bộ', pdfUrl: d.blobUrl });
    } else if (d.type === 'KPI_SO_TAY_CHAN_TAI') {
      setThongBao('Sổ tay chỉ sử dụng trực tuyến trên nền tảng, không tải về máy.');
    }
  }, []);

  useEffect(() => {
    window.addEventListener('message', nhanThongDiep);
    return () => window.removeEventListener('message', nhanThongDiep);
  }, [nhanThongDiep]);

  useEffect(() => {
    if (!thongBao) return;
    const t = setTimeout(() => setThongBao(null), 4000);
    return () => clearTimeout(t);
  }, [thongBao]);

  useEffect(() => {
    if (!xemPdf) return;
    const dong = (e: KeyboardEvent) => e.key === 'Escape' && setXemPdf(null);
    window.addEventListener('keydown', dong);
    return () => window.removeEventListener('keydown', dong);
  }, [xemPdf]);

  const toanManHinh = () => iframeRef.current?.requestFullscreen?.().catch(() => {});

  // Giữ #loi-15 để mở thẳng một lỗi (Sổ tra cứu lỗi đọc location.hash)
  const src = blobUrl ? blobUrl + (typeof window !== 'undefined' ? window.location.hash : '') : '';

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <div className="flex items-center gap-3 px-4 py-2 bg-white border-b border-gray-200">
        <Link
          href="/so-tay"
          className="flex items-center gap-1 text-sm text-gray-600 hover:text-blue-600"
        >
          <ArrowLeft className="w-4 h-4" /> Sổ tay số
        </Link>
        <span className="text-gray-300">/</span>
        <h1 className="text-sm font-semibold text-gray-900 truncate flex-1">
          {TEN_SO[ma] || 'Sổ tay'}
        </h1>
        {blobUrl && (
          <button
            onClick={toanManHinh}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-blue-600"
            title="Toàn màn hình"
          >
            <Maximize2 className="w-4 h-4" />
            <span className="hidden sm:inline">Toàn màn hình</span>
          </button>
        )}
      </div>

      <div className="flex-1 relative">
        {error ? (
          <div className="flex items-center justify-center h-full text-red-700">{error}</div>
        ) : !blobUrl ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-sm text-gray-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            Đang tải sổ tay…
          </div>
        ) : (
          <iframe
            ref={iframeRef}
            src={src}
            title={TEN_SO[ma] || 'Sổ tay'}
            className="absolute inset-0 w-full h-full border-0 bg-white"
            allow="fullscreen; clipboard-read; clipboard-write; microphone"
          />
        )}
      </div>

      {thongBao && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg">
          {thongBao}
        </div>
      )}

      {xemPdf && (
        <div
          className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-2 sm:p-6"
          onClick={() => setXemPdf(null)}
        >
          <div
            className="bg-white rounded-xl shadow-xl w-full max-w-5xl h-full flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200">
              <h2 className="font-semibold text-gray-900 truncate flex-1">{xemPdf.tieuDe}</h2>
              {xemPdf.docxUrl && (
                <a
                  href={xemPdf.docxUrl}
                  download={xemPdf.docxTen || 'bieu-mau.docx'}
                  className="flex items-center gap-1 text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700"
                >
                  <Download className="w-4 h-4" /> Tải .docx (để điền)
                </a>
              )}
              {/* Trình duyệt điện thoại không hiện PDF trong khung → mở tab riêng */}
              <a
                href={xemPdf.pdfUrl}
                target="_blank"
                rel="noopener"
                className="flex items-center gap-1 text-sm text-gray-600 hover:text-blue-600 px-2"
                title="Mở PDF trong tab mới"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
              <button
                onClick={() => setXemPdf(null)}
                className="text-gray-500 hover:text-gray-900 p-1"
                title="Đóng (Esc)"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <iframe src={`${xemPdf.pdfUrl}#toolbar=1&view=FitH`} title={xemPdf.tieuDe} className="flex-1 w-full border-0" />
          </div>
        </div>
      )}
    </div>
  );
}

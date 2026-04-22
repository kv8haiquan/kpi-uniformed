/**
 * src/app/(main)/dao-tao/khoa-hoc/[id]/bai-hoc/[baiHocId]/page.tsx
 * ==================================================================
 * Xem bai hoc — sidebar danh sach + content viewer + tien do tracking.
 */

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { baiHocApi } from '@/services/lms';
import type { IBaiHoc } from '@/types/lms';

// =============================================================================
// CONTENT VIEWER — render đúng loại nội dung
// =============================================================================

/**
 * Resolve URL cho file LMS.
 * File_url dạng /uploads/lms/... — nginx proxy về LMS backend (port 8001).
 * Trả về relative URL (cùng origin, qua nginx proxy).
 */
function resolveLmsUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  return url;
}

/** Lấy YouTube embed URL nếu file_url là YouTube link */
function ytEmbedUrl(url: string): string | null {
  try {
    const u = new URL(url);
    // https://www.youtube.com/watch?v=XXXXX
    const v = u.searchParams.get('v');
    if (v) return `https://www.youtube.com/embed/${v}`;
    // https://youtu.be/XXXXX
    if (u.hostname === 'youtu.be') return `https://www.youtube.com/embed${u.pathname}`;
    // https://www.youtube.com/embed/XXXXX
    if (u.pathname.startsWith('/embed/')) return url;
  } catch {
    // URL không hợp lệ
  }
  return null;
}

function ContentViewer({ baiHoc }: { baiHoc: IBaiHoc }) {
  const { loai_noi_dung, file_url: rawFileUrl, pdf_url: rawPdfUrl, noi_dung } = baiHoc;
  // Chuyển relative /uploads/... → absolute URL của LMS backend (port 8001)
  const file_url = resolveLmsUrl(rawFileUrl);
  const pdf_url = resolveLmsUrl(rawPdfUrl);

  // ── HTML ──────────────────────────────────────────────────────────────────
  if (loai_noi_dung === 'HTML' && noi_dung) {
    return (
      <div className="p-6 prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: noi_dung }} />
    );
  }

  // ── VIDEO ─────────────────────────────────────────────────────────────────
  if (loai_noi_dung === 'VIDEO' && file_url) {
    const ytUrl = ytEmbedUrl(file_url);
    if (ytUrl) {
      return (
        <div className="aspect-video">
          <iframe
            src={ytUrl}
            className="w-full h-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      );
    }
    // File video nội bộ
    return (
      <div className="bg-black aspect-video flex items-center justify-center">
        <video
          src={file_url}
          controls
          className="w-full h-full max-h-[70vh]"
          preload="metadata"
        >
          Trình duyệt không hỗ trợ phát video.
        </video>
      </div>
    );
  }

  // ── PDF ───────────────────────────────────────────────────────────────────
  if (loai_noi_dung === 'PDF' && file_url) {
    return (
      <div className="flex flex-col" style={{ minHeight: '70vh' }}>
        <iframe
          src={file_url}
          className="w-full flex-1 border-0"
          style={{ minHeight: '70vh' }}
          title="PDF Viewer"
        />
        <div className="border-t border-gray-100 px-4 py-2 flex justify-end">
          <a
            href={file_url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-blue-600 hover:underline"
          >
            Mở trong tab mới ↗
          </a>
        </div>
      </div>
    );
  }

  // ── SLIDE ─────────────────────────────────────────────────────────────────
  if (loai_noi_dung === 'SLIDE' && file_url) {
    // Ưu tiên bản PDF convert; fallback: file_url nếu chính là PDF
    const viewUrl = pdf_url || (file_url.toLowerCase().endsWith('.pdf') ? file_url : null);
    const origExt = rawFileUrl?.split('.').pop()?.toUpperCase() ?? 'PPTX';

    if (viewUrl) {
      return (
        <div className="flex flex-col" style={{ minHeight: '70vh' }}>
          <iframe
            src={viewUrl}
            className="w-full flex-1 border-0"
            style={{ minHeight: '70vh' }}
            title="Slide Viewer"
          />
          <div className="border-t border-gray-100 px-4 py-2 flex items-center justify-between">
            <a href={viewUrl} target="_blank" rel="noreferrer" className="text-sm text-blue-600 hover:underline">
              Mở trong tab mới ↗
            </a>
            {/* Nút download bản gốc (PPTX/PPT) nếu file gốc khác PDF */}
            {file_url !== viewUrl && (
              <a
                href={file_url}
                download
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 rounded text-sm hover:bg-blue-100"
              >
                ↓ Tải slide gốc ({origExt})
              </a>
            )}
          </div>
        </div>
      );
    }

    // LibreOffice chưa cài → fallback chỉ hiện nút tải về
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[200px]">
        <span className="text-5xl mb-4">📊</span>
        <p className="text-gray-700 font-medium mb-1">Tài liệu trình chiếu</p>
        <p className="text-sm text-gray-500 mb-4">Tải slide về để xem bằng PowerPoint hoặc LibreOffice</p>
        <a
          href={file_url}
          download
          className="px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Tải xuống Slide ({origExt})
        </a>
      </div>
    );
  }

  // ── Fallback: nội dung văn bản ─────────────────────────────────────────────
  if (noi_dung) {
    return (
      <div className="p-6 whitespace-pre-wrap text-gray-700 text-sm leading-relaxed">{noi_dung}</div>
    );
  }

  return (
    <div className="p-12 text-center text-gray-400">
      <span className="text-4xl block mb-2">📝</span>
      Nội dung đang được cập nhật
    </div>
  );
}

// =============================================================================
// CONSTANTS
// =============================================================================

const TIEN_DO_ICON: Record<string, string> = {
  CHUA_XEM: '○',
  DANG_XEM: '●',
  DA_HOAN_THANH: '✓',
};
const TIEN_DO_COLOR: Record<string, string> = {
  CHUA_XEM: 'text-gray-400',
  DANG_XEM: 'text-blue-500',
  DA_HOAN_THANH: 'text-green-600',
};
const LOAI_BADGE: Record<string, { label: string; bg: string }> = {
  VIDEO: { label: 'Video', bg: 'bg-red-100 text-red-700' },
  PDF: { label: 'PDF', bg: 'bg-orange-100 text-orange-700' },
  HTML: { label: 'Bài viết', bg: 'bg-blue-100 text-blue-700' },
  SLIDE: { label: 'Slide', bg: 'bg-purple-100 text-purple-700' },
  SCORM: { label: 'SCORM', bg: 'bg-gray-100 text-gray-700' },
  QUIZ: { label: 'Quiz', bg: 'bg-green-100 text-green-700' },
};

export default function BaiHocViewPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const khoaHocId = params.id as string;
  const baiHocId = params.baiHocId as string;
  const isPreview = searchParams.get('preview') === '1' || searchParams.get('preview') === 'true';

  const [baiHoc, setBaiHoc] = useState<IBaiHoc | null>(null);
  const [allBaiHocs, setAllBaiHocs] = useState<IBaiHoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completing, setCompleting] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const timeRef = useRef(0);

  // Load data
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [bhRes, listRes] = await Promise.all([
          baiHocApi.chiTiet(baiHocId),
          baiHocApi.danhSach(khoaHocId),
        ]);
        setBaiHoc(bhRes.data.data);
        setAllBaiHocs(listRes.data.data || []);
      } catch (err: any) {
        setError(err?.response?.data?.detail?.error?.message || 'Không thể tải bài học');
      } finally {
        setLoading(false);
      }
    };
    if (baiHocId && khoaHocId) load();
  }, [baiHocId, khoaHocId]);

  // Timer: track thoi gian xem
  useEffect(() => {
    timeRef.current = 0;
    const interval = setInterval(() => { timeRef.current += 1; }, 1);
    return () => clearInterval(interval);
  }, [baiHocId]);

  // Hoan thanh bai hoc
  const handleComplete = useCallback(async () => {
    if (!baiHoc) return;
    if (isPreview) {
      alert('Chế độ xem thử: không ghi tiến độ. Chuyển sang tài khoản học viên để hoàn thành bài.');
      return;
    }
    setCompleting(true);
    try {
      await baiHocApi.capNhatTienDo(baiHocId, {
        thoi_gian_xem_giay: Math.max(timeRef.current, 1),
        hoan_thanh: true,
      });
      // Refresh data
      const [bhRes, listRes] = await Promise.all([
        baiHocApi.chiTiet(baiHocId),
        baiHocApi.danhSach(khoaHocId),
      ]);
      setBaiHoc(bhRes.data.data);
      setAllBaiHocs(listRes.data.data || []);
    } catch (err: any) {
      alert(err?.response?.data?.detail?.error?.message || 'Lỗi cập nhật tiến độ');
    } finally {
      setCompleting(false);
    }
  }, [baiHoc, baiHocId, khoaHocId, isPreview]);

  // Navigation
  const currentIdx = allBaiHocs.findIndex((bh) => bh.id === baiHocId);
  const prevBh = currentIdx > 0 ? allBaiHocs[currentIdx - 1] : null;
  const nextBh = currentIdx < allBaiHocs.length - 1 ? allBaiHocs[currentIdx + 1] : null;
  const completedCount = allBaiHocs.filter((bh) => bh.tien_do_ca_nhan?.trang_thai === 'DA_HOAN_THANH').length;
  const isCompleted = baiHoc?.tien_do_ca_nhan?.trang_thai === 'DA_HOAN_THANH';

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error || !baiHoc) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-700">{error || 'Không tìm thấy bài học'}</p>
          <Link href={`/dao-tao/khoa-hoc/${khoaHocId}`} className="text-blue-600 hover:underline mt-2 inline-block">Quay lại</Link>
        </div>
      </div>
    );
  }

  const loaiBadge = LOAI_BADGE[baiHoc.loai_noi_dung] || LOAI_BADGE.HTML;

  return (
    <div className="min-h-screen bg-gray-50">
      {isPreview && (
        <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2.5 text-sm text-yellow-800 flex items-center gap-2">
          <span>👁</span>
          <span className="font-medium">Chế độ xem thử (giảng viên)</span>
          <span className="text-yellow-700">— Không ghi tiến độ, không tính phần trăm hoàn thành.</span>
        </div>
      )}
      {/* Breadcrumb */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center gap-2 text-sm text-gray-500">
          <Link href="/dao-tao" className="hover:text-blue-600">Đào tạo</Link>
          <span>/</span>
          <Link href={`/dao-tao/khoa-hoc/${khoaHocId}`} className="hover:text-blue-600">Khóa học</Link>
          <span>/</span>
          <span className="text-gray-900 truncate max-w-xs">{baiHoc.tieu_de}</span>
          <button onClick={() => setShowSidebar(!showSidebar)} className="ml-auto text-gray-400 hover:text-gray-600 sm:hidden">
            {showSidebar ? '✕' : '☰'}
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto flex">
        {/* Sidebar */}
        <aside className={`${showSidebar ? 'block' : 'hidden'} sm:block w-72 shrink-0 bg-white border-r border-gray-200 min-h-[calc(100vh-57px)] overflow-y-auto`}>
          <div className="p-4">
            <div className="text-xs text-gray-500 mb-3">Bài {currentIdx + 1}/{allBaiHocs.length} — {completedCount}/{allBaiHocs.length} hoàn thành</div>
            <div className="space-y-1">
              {allBaiHocs.map((bh) => {
                const td = bh.tien_do_ca_nhan?.trang_thai || 'CHUA_XEM';
                const isActive = bh.id === baiHocId;
                return (
                  <Link key={bh.id} href={`/dao-tao/khoa-hoc/${khoaHocId}/bai-hoc/${bh.id}`}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                      isActive ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700 hover:bg-gray-50'
                    }`}>
                    <span className={`text-sm ${TIEN_DO_COLOR[td]}`}>{TIEN_DO_ICON[td]}</span>
                    <span className="truncate">{bh.thu_tu}. {bh.tieu_de}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        </aside>

        {/* Content */}
        <main className="flex-1 p-6">
          {/* Title */}
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${loaiBadge.bg}`}>{loaiBadge.label}</span>
              {isCompleted && <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">Hoàn thành</span>}
            </div>
            <h1 className="text-xl font-bold text-gray-900">{baiHoc.tieu_de}</h1>
            {baiHoc.thoi_luong_phut && <p className="text-sm text-gray-500 mt-1">Thời lượng: {baiHoc.thoi_luong_phut} phút</p>}
          </div>

          {/* Content Viewer */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6 overflow-hidden">
            <ContentViewer baiHoc={baiHoc} />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              {prevBh && (
                <Link href={`/dao-tao/khoa-hoc/${khoaHocId}/bai-hoc/${prevBh.id}`}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 flex items-center gap-1">
                  ← Bài trước
                </Link>
              )}
              {nextBh && (
                <Link href={`/dao-tao/khoa-hoc/${khoaHocId}/bai-hoc/${nextBh.id}`}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 flex items-center gap-1">
                  Bài tiếp →
                </Link>
              )}
            </div>

            {!isCompleted ? (
              <button onClick={handleComplete} disabled={completing}
                className="px-6 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50">
                {completing ? 'Đang xử lý...' : '✓ Hoàn thành bài học'}
              </button>
            ) : (
              <span className="px-4 py-2 bg-green-50 text-green-700 rounded-lg text-sm font-medium">
                ✓ Đã hoàn thành
              </span>
            )}
          </div>

          {/* All complete notification */}
          {completedCount === allBaiHocs.length && allBaiHocs.length > 0 && (
            <div className="mt-6 bg-green-50 border border-green-200 rounded-xl p-4 text-center">
              <span className="text-3xl">🎉</span>
              <p className="font-medium text-green-800 mt-1">Bạn đã hoàn thành tất cả bài học!</p>
              <Link href={`/dao-tao/khoa-hoc/${khoaHocId}`}
                className="text-sm text-green-600 hover:underline mt-1 inline-block">
                Quay lại khóa học
              </Link>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

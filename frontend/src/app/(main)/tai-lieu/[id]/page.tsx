/**
 * app/(main)/tai-lieu/[id]/page.tsx
 * ====================================
 * Chi tiết tài liệu — thông tin + lịch sử phiên bản.
 */

'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { taiLieuApi } from '@/services/portal';
import type { ITaiLieuItem, ITaiLieuVersionItem } from '@/types/tai-lieu';
import { getFileIcon, formatFileSize } from '@/types/tai-lieu';

// =============================================================================
// HELPERS
// =============================================================================

function formatDate(s?: string | null): string {
  if (!s) return '—';
  return new Date(s).toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

// =============================================================================
// SKELETON
// =============================================================================

function DetailSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-6 bg-gray-200 rounded w-3/5" />
      <div className="grid grid-cols-2 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-14 bg-gray-100 rounded-xl" />
        ))}
      </div>
      <div className="h-24 bg-gray-100 rounded-xl" />
    </div>
  );
}

// =============================================================================
// PAGE
// =============================================================================

export default function TaiLieuDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [taiLieu, setTaiLieu] = useState<ITaiLieuItem | null>(null);
  const [lichSu, setLichSu] = useState<ITaiLieuVersionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [uploadVersionOpen, setUploadVersionOpen] = useState(false);
  const [newVersion, setNewVersion] = useState({ file_url: '', file_name: '', mo_ta: '' });
  const [submittingVersion, setSubmittingVersion] = useState(false);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const [detailRes, lichSuRes] = await Promise.allSettled([
          taiLieuApi.chiTiet(id),
          taiLieuApi.lichSu(id),
        ]);
        if (detailRes.status === 'fulfilled') {
          const data = detailRes.value.data?.data ?? detailRes.value.data;
          setTaiLieu(data);
        } else {
          setNotFound(true);
        }
        if (lichSuRes.status === 'fulfilled') {
          const data = lichSuRes.value.data?.data ?? lichSuRes.value.data;
          setLichSu(Array.isArray(data) ? data : []);
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const handleUploadVersion = async () => {
    if (!newVersion.file_url.trim() || !newVersion.file_name.trim()) {
      alert('Vui lòng nhập URL và tên file.');
      return;
    }
    setSubmittingVersion(true);
    try {
      await taiLieuApi.taiPhienBanMoi(id, {
        file_url: newVersion.file_url.trim(),
        file_name: newVersion.file_name.trim(),
        file_size_bytes: 0,
        file_type: taiLieu?.file_type ?? 'application/pdf',
        mo_ta: newVersion.mo_ta.trim() || undefined,
      });
      router.refresh();
      setUploadVersionOpen(false);
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(e?.message ?? 'Có lỗi xảy ra.');
    } finally {
      setSubmittingVersion(false);
    }
  };

  // -------------------------------------------------------------------------

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4 sm:px-6">
          <DetailSkeleton />
        </div>
      </div>
    );
  }

  if (notFound || !taiLieu) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <span className="text-5xl">🔍</span>
          <h2 className="text-lg font-semibold text-gray-900 mt-4">Không tìm thấy tài liệu</h2>
          <button onClick={() => router.back()} className="mt-4 text-sm text-blue-600 hover:underline">
            ← Quay lại
          </button>
        </div>
      </div>
    );
  }

  const icon = getFileIcon(taiLieu.file_type);
  const size = formatFileSize(taiLieu.file_size_bytes);
  const downloadUrl = taiLieuApi.downloadUrl(taiLieu.id);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8 sm:px-6">

        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-xs text-gray-400 mb-6">
          <Link href="/tong-quan" className="hover:text-blue-600 transition-colors">Trang chủ</Link>
          <span>/</span>
          <Link href="/tai-lieu" className="hover:text-blue-600 transition-colors">Tài liệu</Link>
          <span>/</span>
          <span className="text-blue-600">{taiLieu.thu_muc.ten}</span>
        </nav>

        {/* Main card */}
        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">

          {/* Header */}
          <div className="flex items-start gap-4 p-6 border-b border-gray-100">
            <div className="w-16 h-16 bg-gray-50 rounded-xl flex items-center justify-center text-3xl flex-shrink-0">
              {icon}
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-bold text-gray-900 leading-tight">{taiLieu.ten_tai_lieu}</h1>
              <p className="text-sm text-gray-500 mt-1">
                {taiLieu.thu_muc.ten}
              </p>
            </div>
          </div>

          {/* Meta grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-gray-50 border-b border-gray-100">
            <div className="text-center">
              <div className="text-xs text-gray-400 mb-0.5">Phiên bản</div>
              <div className="text-sm font-semibold text-gray-800">v{taiLieu.phien_ban}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400 mb-0.5">Loại file</div>
              <div className="text-sm font-semibold text-gray-800 uppercase">
                {taiLieu.file_name.split('.').pop() ?? '—'}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400 mb-0.5">Kích thước</div>
              <div className="text-sm font-semibold text-gray-800">{size}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400 mb-0.5">Ngày tải</div>
              <div className="text-sm font-semibold text-gray-800">{formatDate(taiLieu.created_at)}</div>
            </div>
          </div>

          {/* Detail */}
          <div className="p-6 space-y-4">
            {/* Người tải */}
            <div>
              <span className="text-xs text-gray-400 block mb-0.5">Người tải lên</span>
              <span className="text-sm font-medium text-gray-800">{taiLieu.nguoi_tai_len.ho_ten}</span>
              <span className="text-xs text-gray-400 ml-1">({taiLieu.nguoi_tai_len.ma_cc})</span>
            </div>

            {/* Tags */}
            {taiLieu.tags && taiLieu.tags.length > 0 && (
              <div>
                <span className="text-xs text-gray-400 block mb-1.5">Tags</span>
                <div className="flex flex-wrap gap-1.5">
                  {taiLieu.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full border border-blue-100"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Mô tả */}
            {taiLieu.mo_ta && (
              <div>
                <span className="text-xs text-gray-400 block mb-0.5">Mô tả</span>
                <p className="text-sm text-gray-700 leading-relaxed">{taiLieu.mo_ta}</p>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex flex-wrap gap-3 pt-2">
              <a
                href={downloadUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                ↓ Tải xuống
              </a>
              <button
                onClick={() => setUploadVersionOpen(true)}
                className="inline-flex items-center gap-2 border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                ↑ Upload phiên bản mới
              </button>
            </div>
          </div>
        </div>

        {/* Lịch sử phiên bản */}
        {lichSu.length > 0 && (
          <div className="mt-6 bg-white rounded-2xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-800">Lịch sử phiên bản</h2>
            </div>
            <div className="divide-y divide-gray-100">
              {lichSu.map((v) => (
                <div key={v.id} className="flex items-center gap-4 px-6 py-3">
                  <span className="text-sm font-semibold text-blue-700 w-8 flex-shrink-0">v{v.phien_ban}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700 truncate">{v.file_name}</p>
                    <p className="text-xs text-gray-400">{v.nguoi_tai_len.ho_ten} · {formatDate(v.created_at)}</p>
                  </div>
                  <span className="text-xs text-gray-400 flex-shrink-0">{formatFileSize(v.file_size_bytes)}</span>
                  <a
                    href={taiLieuApi.downloadUrl(v.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline flex-shrink-0"
                  >
                    TL
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Back */}
        <div className="mt-6 text-center">
          <button onClick={() => router.back()} className="text-sm text-gray-400 hover:text-blue-600 transition-colors">
            ← Quay lại thư viện
          </button>
        </div>

      </div>

      {/* Upload version modal */}
      {uploadVersionOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-base font-semibold text-gray-900 mb-4">Upload phiên bản mới</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  URL file mới <span className="text-red-500">*</span>
                </label>
                <input
                  type="url"
                  value={newVersion.file_url}
                  onChange={(e) => setNewVersion((p) => ({ ...p, file_url: e.target.value }))}
                  placeholder="https://..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tên file <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newVersion.file_name}
                  onChange={(e) => setNewVersion((p) => ({ ...p, file_name: e.target.value }))}
                  placeholder="ten-file-v2.pdf"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ghi chú thay đổi</label>
                <textarea
                  value={newVersion.mo_ta}
                  onChange={(e) => setNewVersion((p) => ({ ...p, mo_ta: e.target.value }))}
                  rows={2}
                  placeholder="Mô tả những thay đổi trong phiên bản này..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => setUploadVersionOpen(false)}
                className="flex-1 border border-gray-300 text-gray-700 rounded-lg py-2 text-sm hover:bg-gray-50"
              >
                Hủy
              </button>
              <button
                onClick={handleUploadVersion}
                disabled={submittingVersion}
                className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {submittingVersion ? 'Đang xử lý...' : 'Upload'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * app/(main)/tin-tuc/[id]/page.tsx
 * ==================================
 * Chi tiết bài viết — render nội dung HTML từ CMS.
 */

'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { baiVietApi } from '@/services/portal';
import type { IBaiVietDetail } from '@/types/tin-tuc';

// =============================================================================
// HELPERS
// =============================================================================

function formatDate(s?: string | null): string {
  if (!s) return '';
  return new Date(s).toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

// =============================================================================
// SKELETON
// =============================================================================

function ArticleSkeleton() {
  return (
    <div className="animate-pulse max-w-3xl mx-auto">
      <div className="aspect-video bg-gray-200 rounded-xl mb-6" />
      <div className="space-y-3 mb-6">
        <div className="h-8 bg-gray-200 rounded w-4/5" />
        <div className="h-8 bg-gray-200 rounded w-3/5" />
      </div>
      <div className="flex gap-4 mb-6">
        <div className="h-4 bg-gray-100 rounded w-24" />
        <div className="h-4 bg-gray-100 rounded w-24" />
        <div className="h-4 bg-gray-100 rounded w-16" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-3 bg-gray-100 rounded" style={{ width: `${85 + Math.random() * 15}%` }} />
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// PAGE
// =============================================================================

export default function TinTucDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [article, setArticle] = useState<IBaiVietDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const res = await baiVietApi.chiTiet(id);
        const data = res.data?.data ?? res.data;
        setArticle(data);
      } catch (err: unknown) {
        const e = err as { code?: string };
        if (e?.code === 'BIZ_001') {
          setNotFound(true);
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  // -------------------------------------------------------------------------

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <ArticleSkeleton />
        </div>
      </div>
    );
  }

  if (notFound || !article) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <span className="text-5xl">🔍</span>
          <h2 className="text-lg font-semibold text-gray-900 mt-4">Không tìm thấy bài viết</h2>
          <p className="text-sm text-gray-500 mt-1">Bài viết không tồn tại hoặc đã bị gỡ xuống.</p>
          <button
            onClick={() => router.back()}
            className="mt-4 text-sm text-blue-600 hover:underline"
          >
            ← Quay lại
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <article className="max-w-3xl mx-auto px-4 py-8 sm:px-6">

        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-xs text-gray-400 mb-6">
          <Link href="/tong-quan" className="hover:text-blue-600 transition-colors">Trang chủ</Link>
          <span>/</span>
          <Link href="/tin-tuc" className="hover:text-blue-600 transition-colors">Tin tức</Link>
          <span>/</span>
          <span className="text-blue-600">{article.chuyen_muc.ten}</span>
        </nav>

        {/* Chuyên mục badge */}
        <div className="mb-4">
          <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full uppercase tracking-wide">
            {article.chuyen_muc.ten}
          </span>
          {article.is_ghim && (
            <span className="ml-2 text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded-full">
              📌 Ghim
            </span>
          )}
        </div>

        {/* Tiêu đề */}
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight mb-4">
          {article.tieu_de}
        </h1>

        {/* Meta */}
        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 mb-6 pb-6 border-b border-gray-200">
          <span>👤 {article.nguoi_soan.ho_ten}</span>
          {article.ngay_xuat_ban && (
            <span>📅 {formatDate(article.ngay_xuat_ban)}</span>
          )}
          <span>👁 {article.so_luot_xem} lượt xem</span>
        </div>

        {/* Tóm tắt */}
        {article.tom_tat && (
          <p className="text-base text-gray-600 leading-relaxed mb-6 bg-blue-50 border-l-4 border-blue-400 pl-4 py-2 rounded-r-lg italic">
            {article.tom_tat}
          </p>
        )}

        {/* Ảnh đại diện */}
        {article.anh_dai_dien && (
          <div className="mb-6 rounded-xl overflow-hidden">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={article.anh_dai_dien}
              alt={article.tieu_de}
              className="w-full max-h-96 object-cover"
            />
          </div>
        )}

        {/* Nội dung HTML */}
        {article.noi_dung ? (
          <div
            className="prose prose-sm sm:prose max-w-none text-gray-800 leading-relaxed
              prose-headings:font-semibold prose-headings:text-gray-900
              prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
              prose-img:rounded-lg prose-img:mx-auto
              prose-table:border prose-td:border prose-td:px-3 prose-td:py-2
              prose-th:border prose-th:px-3 prose-th:py-2 prose-th:bg-gray-50"
            /* Nội dung từ CMS nội bộ — không cần DOMPurify */
            dangerouslySetInnerHTML={{ __html: article.noi_dung }}
          />
        ) : (
          <p className="text-gray-400 text-center py-8">Bài viết chưa có nội dung.</p>
        )}

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-gray-200 flex items-center justify-between">
          <button
            onClick={() => router.back()}
            className="text-sm text-gray-500 hover:text-blue-600 transition-colors"
          >
            ← Quay lại
          </button>
          {article.nguoi_duyet && (
            <p className="text-xs text-gray-400">
              Duyệt bởi: {article.nguoi_duyet.ho_ten}
            </p>
          )}
        </div>

      </article>
    </div>
  );
}

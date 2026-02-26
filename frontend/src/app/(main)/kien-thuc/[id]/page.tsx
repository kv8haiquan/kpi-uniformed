/**
 * src/app/(main)/kien-thuc/[id]/page.tsx
 * ========================================
 * Chi tiet Knowledge Base — noi dung, tags, lien ket cross-module.
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { knowledgeBaseApi } from '@/services/common';
import type { IKnowledgeBase } from '@/types/common';
import { TRANG_THAI_KB_CONFIG } from '@/types/common';

// =============================================================================
// MAIN
// =============================================================================

export default function KienThucDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [item, setItem] = useState<IKnowledgeBase | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await knowledgeBaseApi.chiTiet(id);
        setItem(res.data.data);
      } catch (err: any) {
        setError(err?.response?.data?.error?.message || 'Khong tim thay bai viet');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-3xl mx-auto bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <span className="text-3xl">⚠️</span>
          <p className="mt-2 text-red-700">{error || 'Khong tim thay'}</p>
          <button
            onClick={() => router.push('/kien-thuc')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            Quay lai
          </button>
        </div>
      </div>
    );
  }

  const ttConfig = TRANG_THAI_KB_CONFIG[item.trang_thai] || { label: item.trang_thai, cls: 'bg-gray-100 text-gray-600' };
  const loaiIcon = item.loai === 'SOP' ? '📑' : '❓';

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6">
          <Link href="/kien-thuc" className="hover:text-blue-600">Kho tri thuc</Link>
          <span>/</span>
          <span className="text-gray-900 truncate">{item.tieu_de}</span>
        </nav>

        {/* Header card */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
          <div className="p-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-50 shrink-0">
                <span className="text-2xl">{loaiIcon}</span>
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-xl font-bold text-gray-900 mb-2">{item.tieu_de}</h1>
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`px-2 py-0.5 text-xs rounded-full ${ttConfig.cls}`}>
                    {ttConfig.label}
                  </span>
                  <span className="text-xs text-gray-400">{item.loai}</span>
                  <span className="text-xs text-gray-400">Phien ban {item.phien_ban}</span>
                  {item.chu_so_huu && (
                    <span className="text-xs text-gray-400">
                      boi {item.chu_so_huu.ho_ten}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Tags */}
            {item.tags && item.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-4">
                {item.tags.map((tag) => (
                  <Link
                    key={tag}
                    href={`/kien-thuc?tags=${encodeURIComponent(tag)}`}
                    className="px-2.5 py-1 text-xs bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 transition-colors"
                  >
                    {tag}
                  </Link>
                ))}
              </div>
            )}

            {/* Chuyen de */}
            {item.chuyen_de && item.chuyen_de.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {item.chuyen_de.map((cd) => (
                  <span key={cd} className="px-2.5 py-1 text-xs bg-purple-50 text-purple-600 rounded-full">
                    {cd}
                  </span>
                ))}
              </div>
            )}

            {/* Meta */}
            <div className="flex flex-wrap gap-4 mt-4 text-xs text-gray-400">
              <span>Tao: {new Date(item.created_at).toLocaleDateString('vi-VN')}</span>
              <span>Cap nhat: {new Date(item.updated_at).toLocaleDateString('vi-VN')}</span>
              {item.ngay_cap_nhat_cuoi && (
                <span>Cap nhat cuoi: {new Date(item.ngay_cap_nhat_cuoi).toLocaleDateString('vi-VN')}</span>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
          <div className="p-6">
            <div
              className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-a:text-blue-600"
              dangerouslySetInnerHTML={{ __html: item.noi_dung }}
            />
          </div>
        </div>

        {/* Cross-module links */}
        {(item.van_ban_lien_quan?.length || item.chu_de_forum_lien_quan?.length) && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">Lien ket</h2>
            </div>
            <div className="p-6 space-y-4">
              {/* Van ban lien quan */}
              {item.van_ban_lien_quan && item.van_ban_lien_quan.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1.5">
                    <span>⚖️</span> Van ban phap luat lien quan
                  </h3>
                  <div className="space-y-1.5">
                    {item.van_ban_lien_quan.map((vbId) => (
                      <Link
                        key={vbId}
                        href={`/phap-luat/van-ban/${vbId}`}
                        className="block px-3 py-2 text-sm bg-gray-50 rounded-lg hover:bg-blue-50 hover:text-blue-600 transition-colors"
                      >
                        Van ban #{vbId.slice(0, 8)}...
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Chu de forum lien quan */}
              {item.chu_de_forum_lien_quan && item.chu_de_forum_lien_quan.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1.5">
                    <span>💬</span> Chu de dien dan lien quan
                  </h3>
                  <div className="space-y-1.5">
                    {item.chu_de_forum_lien_quan.map((cdId) => (
                      <Link
                        key={cdId}
                        href={`/dien-dan/chu-de/${cdId}`}
                        className="block px-3 py-2 text-sm bg-gray-50 rounded-lg hover:bg-blue-50 hover:text-blue-600 transition-colors"
                      >
                        Chu de #{cdId.slice(0, 8)}...
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Back */}
        <div className="text-center">
          <Link
            href="/kien-thuc"
            className="inline-flex items-center gap-2 text-sm text-blue-600 hover:underline"
          >
            ← Quay lai kho tri thuc
          </Link>
        </div>
      </div>
    </div>
  );
}

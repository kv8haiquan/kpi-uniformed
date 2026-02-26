/**
 * src/app/(main)/dien-dan/cua-toi/page.tsx
 * Trang quan ly chu de cua toi va chu de dang theo doi.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronRight, Eye, MessageSquare, ThumbsUp, Clock, Loader2 } from 'lucide-react';
import { useAuthStore } from '@/stores/useAuthStore';
import { chuDeApi, theoDoiApi } from '@/services/forum';
import type { IChuDeListItem } from '@/types/forum';
import { TRANG_THAI_LABEL, TRANG_THAI_COLOR } from '@/types/forum';

type Tab = 'cua-toi' | 'theo-doi';

export default function CuaToiPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);

  const [activeTab, setActiveTab] = useState<Tab>('cua-toi');

  // Tab 1: Chu de cua toi
  const [chuDeCuaToi, setChuDeCuaToi] = useState<IChuDeListItem[]>([]);
  const [isLoadingCuaToi, setIsLoadingCuaToi] = useState(true);

  // Tab 2: Dang theo doi
  const [chuDeTheoDoi, setChuDeTheoDoi] = useState<IChuDeListItem[]>([]);
  const [isLoadingTheoDoi, setIsLoadingTheoDoi] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Load chu de cua toi (tab 1)
  useEffect(() => {
    if (activeTab === 'cua-toi') {
      const loadCuaToi = async () => {
        setIsLoadingCuaToi(true);
        try {
          const result = await chuDeApi.danhSach({ page: 1, page_size: 100 });
          // Filter client-side (backend khong co tac_gia filter)
          const filtered = result.items.filter((item) => item.tac_gia?.id === user?.id);
          setChuDeCuaToi(filtered);
        } catch (err) {
          console.error('Failed to load chu de cua toi:', err);
        } finally {
          setIsLoadingCuaToi(false);
        }
      };
      loadCuaToi();
    }
  }, [activeTab, user?.id]);

  // Load chu de theo doi (tab 2)
  useEffect(() => {
    if (activeTab === 'theo-doi') {
      const loadTheoDoi = async () => {
        setIsLoadingTheoDoi(true);
        try {
          const result = await theoDoiApi.cuaToi({ page, page_size: 20 });
          setChuDeTheoDoi(result.items);
          if (result.pagination) {
            setTotalPages(result.pagination.total_pages || 1);
          }
        } catch (err) {
          console.error('Failed to load chu de theo doi:', err);
        } finally {
          setIsLoadingTheoDoi(false);
        }
      };
      loadTheoDoi();
    }
  }, [activeTab, page]);

  const handleClickChuDe = (id: string) => {
    router.push(`/dien-dan/chu-de/${id}`);
  };

  const renderChuDeList = (items: IChuDeListItem[], isLoading: boolean) => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      );
    }

    if (items.length === 0) {
      return (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MessageSquare className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-500 font-medium">Chua co chu de nao</p>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {items.map((item) => (
          <div
            key={item.id}
            onClick={() => handleClickChuDe(item.id)}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-3 mb-2">
              <h3 className="font-medium text-gray-900 flex-1 line-clamp-2">{item.tieu_de}</h3>
              <span className={`px-2 py-1 rounded text-xs font-medium flex-shrink-0 ${TRANG_THAI_COLOR[item.trang_thai]}`}>
                {TRANG_THAI_LABEL[item.trang_thai]}
              </span>
            </div>

            {/* Summary */}
            {item.noi_dung_tom_tat && (
              <p className="text-sm text-gray-600 mb-3 line-clamp-2">{item.noi_dung_tom_tat}</p>
            )}

            {/* Tags */}
            {item.tags && item.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {item.tags.map((tag) => (
                  <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Stats row */}
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <Eye className="w-4 h-4" />
                <span>{item.so_luot_xem}</span>
              </div>
              <div className="flex items-center gap-1">
                <MessageSquare className="w-4 h-4" />
                <span>{item.so_tra_loi}</span>
              </div>
              <div className="flex items-center gap-1">
                <ThumbsUp className="w-4 h-4" />
                <span>{item.so_upvote}</span>
              </div>
              <div className="flex items-center gap-1 ml-auto">
                <Clock className="w-4 h-4" />
                <span>{new Date(item.created_at).toLocaleDateString('vi-VN')}</span>
              </div>
            </div>

            {/* Badges */}
            <div className="flex gap-2 mt-2">
              {item.is_ghim && (
                <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded font-medium">
                  Ghim
                </span>
              )}
              {item.is_khoa && (
                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-medium">
                  Khoa
                </span>
              )}
              {item.co_dap_an_chuan && (
                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded font-medium">
                  Co dap an chuan
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-6">
          <button onClick={() => router.push('/dien-dan')} className="hover:text-blue-600">
            Dien dan
          </button>
          <ChevronRight className="w-4 h-4" />
          <span className="text-gray-900 font-medium">Cua toi</span>
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Chu de cua toi</h1>

        {/* Tabs */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => {
                setActiveTab('cua-toi');
                setPage(1);
              }}
              className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'cua-toi'
                  ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Chu de cua toi
            </button>
            <button
              onClick={() => {
                setActiveTab('theo-doi');
                setPage(1);
              }}
              className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'theo-doi'
                  ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Dang theo doi
            </button>
          </div>

          {/* Tab content */}
          <div className="p-6">
            {activeTab === 'cua-toi' && renderChuDeList(chuDeCuaToi, isLoadingCuaToi)}
            {activeTab === 'theo-doi' && (
              <>
                {renderChuDeList(chuDeTheoDoi, isLoadingTheoDoi)}

                {/* Pagination for "Dang theo doi" tab */}
                {!isLoadingTheoDoi && chuDeTheoDoi.length > 0 && totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-6">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Trang truoc
                    </button>
                    <span className="text-sm text-gray-600">
                      Trang {page} / {totalPages}
                    </span>
                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Trang sau
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

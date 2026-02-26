/**
 * src/app/(main)/dien-dan/chuyen-muc/[id]/page.tsx
 * Trang danh sách chủ đề trong một chuyên mục.
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Search,
  Filter,
  Pin,
  MessageSquare,
  TrendingUp,
  Eye,
  CheckCircle,
  Home,
  ChevronRight,
} from 'lucide-react';
import { chuDeApi, chuyenMucApi } from '@/services/forum';
import type { IChuDeListItem, IChuyenMuc, IChuDeQueryParams } from '@/types/forum';
import { TRANG_THAI_COLOR, TRANG_THAI_LABEL } from '@/types/forum';

export default function ChuyenMucPage() {
  const params = useParams();
  const router = useRouter();
  const chuyenMucId = params.id as string;

  const [chuyenMuc, setChuyenMuc] = useState<IChuyenMuc | null>(null);
  const [topics, setTopics] = useState<IChuDeListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'moi_nhat' | 'nhieu_upvote' | 'nhieu_tra_loi'>('moi_nhat');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState<any>(null);

  useEffect(() => {
    const fetchChuyenMuc = async () => {
      try {
        const allChuyenMuc = await chuyenMucApi.danhSach(true);
        // Tim chuyen muc trong list (co the la parent hoac child)
        const found = allChuyenMuc.find((cm) => cm.id === chuyenMucId);
        if (!found) {
          // Tim trong children
          for (const parent of allChuyenMuc) {
            if (parent.children) {
              const child = parent.children.find((c) => c.id === chuyenMucId);
              if (child) {
                setChuyenMuc(child);
                return;
              }
            }
          }
        } else {
          setChuyenMuc(found);
        }
      } catch (err) {
        console.error('Error fetching chuyen muc:', err);
      }
    };

    fetchChuyenMuc();
  }, [chuyenMucId]);

  useEffect(() => {
    const fetchTopics = async () => {
      try {
        setIsLoading(true);
        const queryParams: IChuDeQueryParams = {
          chuyen_muc_id: chuyenMucId,
          page,
          page_size: 20,
          sap_xep: sortBy,
        };

        if (searchQuery) {
          queryParams.search = searchQuery;
        }
        if (selectedTags.length > 0) {
          queryParams.tags = selectedTags.join(',');
        }

        const result = await chuDeApi.danhSach(queryParams);
        setTopics(result.items);
        setPagination(result.pagination);
      } catch (err) {
        console.error('Error fetching topics:', err);
        setError('Không thể tải danh sách chủ đề');
      } finally {
        setIsLoading(false);
      }
    };

    fetchTopics();
  }, [chuyenMucId, page, sortBy, searchQuery, selectedTags]);

  // Format time
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 30) return `${diffDays} ngày trước`;
    return date.toLocaleDateString('vi-VN');
  };

  // Separate pinned and regular topics
  const pinnedTopics = topics.filter((t) => t.is_ghim);
  const regularTopics = topics.filter((t) => !t.is_ghim);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-5xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
          <Link href="/dien-dan" className="hover:text-blue-600 flex items-center gap-1">
            <Home className="w-4 h-4" />
            Diễn đàn
          </Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-gray-900 font-medium">
            {chuyenMuc?.ten_chuyen_muc || 'Đang tải...'}
          </span>
        </div>

        {/* Header */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center text-3xl">
              {chuyenMuc?.icon || '📁'}
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {chuyenMuc?.ten_chuyen_muc || 'Chuyên mục'}
              </h1>
              {chuyenMuc?.mo_ta && (
                <p className="text-gray-600 mb-3">{chuyenMuc.mo_ta}</p>
              )}
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>{chuyenMuc?.so_chu_de || 0} chủ đề</span>
                <span>•</span>
                <span>{chuyenMuc?.so_tra_loi || 0} trả lời</span>
              </div>
            </div>
          </div>
        </div>

        {/* Filter bar */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm kiếm chủ đề..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Sort */}
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="moi_nhat">Mới nhất</option>
                <option value="nhieu_upvote">Nhiều upvote</option>
                <option value="nhieu_tra_loi">Nhiều trả lời</option>
              </select>
            </div>
          </div>
        </div>

        {/* Topic list */}
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-lg p-6 h-32 animate-pulse"></div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Pinned topics */}
            {pinnedTopics.map((topic) => (
              <Link
                key={topic.id}
                href={`/dien-dan/chu-de/${topic.id}`}
                className="block bg-yellow-50 border-2 border-yellow-300 rounded-lg p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start gap-4">
                  {/* Pin icon */}
                  <Pin className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-1" />

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                      {topic.tieu_de}
                      {topic.co_dap_an_chuan && (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      )}
                    </h3>
                    {topic.noi_dung_tom_tat && (
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {topic.noi_dung_tom_tat}
                      </p>
                    )}
                    <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
                      <span className="font-medium text-gray-700">
                        {topic.tac_gia?.ho_ten || 'Ẩn danh'}
                      </span>
                      <span className="flex items-center gap-1">
                        <TrendingUp className="w-4 h-4" />
                        {topic.so_upvote}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageSquare className="w-4 h-4" />
                        {topic.so_tra_loi}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="w-4 h-4" />
                        {topic.so_luot_xem}
                      </span>
                      <span>{formatTimeAgo(topic.created_at)}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs ${TRANG_THAI_COLOR[topic.trang_thai]}`}>
                        {TRANG_THAI_LABEL[topic.trang_thai]}
                      </span>
                    </div>
                    {topic.tags && topic.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {topic.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}

            {/* Regular topics */}
            {regularTopics.map((topic) => (
              <Link
                key={topic.id}
                href={`/dien-dan/chu-de/${topic.id}`}
                className="block bg-white border border-gray-200 rounded-lg p-5 hover:border-blue-400 hover:shadow-md transition-all"
              >
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                      {topic.tieu_de}
                      {topic.co_dap_an_chuan && (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      )}
                    </h3>
                    {topic.noi_dung_tom_tat && (
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {topic.noi_dung_tom_tat}
                      </p>
                    )}
                    <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
                      <span className="font-medium text-gray-700">
                        {topic.tac_gia?.ho_ten || 'Ẩn danh'}
                      </span>
                      <span className="flex items-center gap-1">
                        <TrendingUp className="w-4 h-4" />
                        {topic.so_upvote}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageSquare className="w-4 h-4" />
                        {topic.so_tra_loi}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="w-4 h-4" />
                        {topic.so_luot_xem}
                      </span>
                      <span>{formatTimeAgo(topic.created_at)}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs ${TRANG_THAI_COLOR[topic.trang_thai]}`}>
                        {TRANG_THAI_LABEL[topic.trang_thai]}
                      </span>
                    </div>
                    {topic.tags && topic.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {topic.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}

            {topics.length === 0 && !isLoading && (
              <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">Chưa có chủ đề nào trong chuyên mục này</p>
                <Link
                  href="/dien-dan/tao-moi"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Tạo chủ đề đầu tiên
                </Link>
              </div>
            )}
          </div>
        )}

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div className="mt-6 flex justify-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Trước
            </button>
            <span className="px-4 py-2 text-gray-700">
              Trang {page} / {pagination.total_pages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
              disabled={page === pagination.total_pages}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Sau
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

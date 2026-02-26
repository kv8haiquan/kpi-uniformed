/**
 * src/app/(main)/dien-dan/page.tsx
 * Trang chính Module Diễn đàn - Danh sách chuyên mục và chủ đề hot.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { MessageSquare, TrendingUp, Plus, ArrowRight, Clock } from 'lucide-react';
import { chuyenMucApi, chuDeApi } from '@/services/forum';
import type { IChuyenMuc, IChuDeListItem } from '@/types/forum';

export default function DienDanPage() {
  const [chuyenMucList, setChuyenMucList] = useState<IChuyenMuc[]>([]);
  const [hotTopics, setHotTopics] = useState<IChuDeListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const [chuyenMucData, hotData] = await Promise.all([
          chuyenMucApi.danhSach(true),
          chuDeApi.danhSach({ sap_xep: 'nhieu_upvote', page_size: 10 }),
        ]);
        setChuyenMucList(chuyenMucData);
        setHotTopics(hotData.items);
      } catch (err) {
        console.error('Error fetching forum data:', err);
        setError('Không thể tải dữ liệu diễn đàn');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Flatten chuyen muc tree: show parent with children count
  const flattenChuyenMuc = (list: IChuyenMuc[]): IChuyenMuc[] => {
    const result: IChuyenMuc[] = [];
    list.forEach((cm) => {
      result.push(cm);
      if (cm.children && cm.children.length > 0) {
        result.push(...cm.children);
      }
    });
    return result;
  };

  const flatList = flattenChuyenMuc(chuyenMucList);

  // Format thoi gian
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header skeleton */}
          <div className="mb-8 animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-48 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-96"></div>
          </div>
          {/* Content skeleton */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-lg p-6 h-32"></div>
              ))}
            </div>
            <div className="bg-white rounded-lg p-6 h-96"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-700">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Thử lại
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
              <MessageSquare className="w-8 h-8 text-blue-600" />
              Diễn đàn
            </h1>
            <p className="text-gray-600">
              Thảo luận, trao đổi kinh nghiệm nghiệp vụ và giải đáp thắc mắc
            </p>
          </div>
          <Link
            href="/dien-dan/tao-moi"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Tạo chủ đề mới
          </Link>
        </div>

        {/* Main layout: 2 columns */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left/Top: Chuyen muc grid */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Chuyên mục
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {flatList.map((cm) => (
                <Link
                  key={cm.id}
                  href={`/dien-dan/chuyen-muc/${cm.id}`}
                  className="bg-white rounded-lg p-5 border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all"
                >
                  <div className="flex items-start gap-3">
                    {/* Icon */}
                    <div className="flex-shrink-0 w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
                      {cm.icon || '📁'}
                    </div>
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 mb-1 truncate">
                        {cm.ten_chuyen_muc}
                      </h3>
                      {cm.mo_ta && (
                        <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                          {cm.mo_ta}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>{cm.so_chu_de} chủ đề</span>
                        <span>•</span>
                        <span>{cm.so_tra_loi} trả lời</span>
                      </div>
                      {cm.chu_de_moi_nhat && (
                        <div className="mt-2 text-xs text-blue-600 hover:underline flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {cm.chu_de_moi_nhat.tieu_de.substring(0, 40)}...
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Right/Bottom: Hot topics */}
          <div>
            <div className="bg-white rounded-lg border border-gray-200 p-5 sticky top-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-orange-500" />
                Chủ đề nổi bật tuần này
              </h2>
              {hotTopics.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">
                  Chưa có chủ đề nào
                </p>
              ) : (
                <div className="space-y-3">
                  {hotTopics.map((topic) => (
                    <Link
                      key={topic.id}
                      href={`/dien-dan/chu-de/${topic.id}`}
                      className="block p-3 rounded-md hover:bg-gray-50 transition-colors border border-gray-100"
                    >
                      <h3 className="font-medium text-gray-900 text-sm mb-1 line-clamp-2">
                        {topic.tieu_de}
                      </h3>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <TrendingUp className="w-3 h-3" />
                          {topic.so_upvote}
                        </span>
                        <span className="flex items-center gap-1">
                          <MessageSquare className="w-3 h-3" />
                          {topic.so_tra_loi}
                        </span>
                      </div>
                      {topic.tags && topic.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {topic.tags.slice(0, 2).map((tag, idx) => (
                            <span
                              key={idx}
                              className="inline-block px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="mt-2 text-xs text-gray-400">
                        {formatTimeAgo(topic.created_at)}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

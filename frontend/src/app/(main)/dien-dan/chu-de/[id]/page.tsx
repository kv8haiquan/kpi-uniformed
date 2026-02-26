/**
 * src/app/(main)/dien-dan/chu-de/[id]/page.tsx
 * Trang chi tiết chủ đề - MOST IMPORTANT PAGE.
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  Home,
  ChevronRight,
  Eye,
  MessageSquare,
  Lock,
  Bell,
  BellOff,
  FileText,
  BookOpen,
} from 'lucide-react';
import { chuDeApi, traLoiApi, theoDoiApi } from '@/services/forum';
import type { IChuDeDetail, ITraLoiInChuDe } from '@/types/forum';
import { TRANG_THAI_COLOR, TRANG_THAI_LABEL } from '@/types/forum';
import VoteButton from '@/components/forum/VoteButton';
import NestedReply from '@/components/forum/NestedReply';
import { useAuthStore } from '@/stores/useAuthStore';

export default function ChuDePage() {
  const params = useParams();
  const chuDeId = params.id as string;
  const { user } = useAuthStore();

  const [chuDe, setChuDe] = useState<IChuDeDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Reply form state
  const [replyContent, setReplyContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Theo doi state
  const [isFollowing, setIsFollowing] = useState(false);
  const [isFollowLoading, setIsFollowLoading] = useState(false);

  useEffect(() => {
    fetchChuDe();
  }, [chuDeId]);

  const fetchChuDe = async () => {
    try {
      setIsLoading(true);
      const data = await chuDeApi.chiTiet(chuDeId);
      setChuDe(data);
      setIsFollowing(data.da_theo_doi || false);
    } catch (err) {
      console.error('Error fetching chu de:', err);
      setError('Không thể tải chủ đề');
    } finally {
      setIsLoading(false);
    }
  };

  // Submit reply
  const handleSubmitReply = async () => {
    if (!replyContent.trim() || isSubmitting || !chuDe) return;

    setIsSubmitting(true);
    try {
      await traLoiApi.taoMoi(chuDeId, {
        noi_dung: replyContent.trim(),
      });
      setReplyContent('');
      // Refresh chu de to get new reply
      await fetchChuDe();
    } catch (err) {
      console.error('Error submitting reply:', err);
      alert('Có lỗi xảy ra khi gửi trả lời');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Toggle follow
  const handleToggleFollow = async () => {
    if (isFollowLoading || !chuDe) return;

    setIsFollowLoading(true);
    try {
      if (isFollowing) {
        await theoDoiApi.boTheoDoi(chuDeId);
        setIsFollowing(false);
      } else {
        await theoDoiApi.theoDoi(chuDeId);
        setIsFollowing(true);
      }
    } catch (err) {
      console.error('Error toggling follow:', err);
      alert('Có lỗi xảy ra');
    } finally {
      setIsFollowLoading(false);
    }
  };

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

  // Get dap an chuan (if any)
  const dapAnChuan = chuDe?.tra_loi.find((t) => t.is_dap_an_chuan);
  const otherReplies = chuDe?.tra_loi.filter((t) => !t.is_dap_an_chuan) || [];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-5xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-2/3 mb-4"></div>
            <div className="bg-white rounded-lg p-6 h-96"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !chuDe) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-5xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-700">{error || 'Không tìm thấy chủ đề'}</p>
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
          <Link
            href={`/dien-dan/chuyen-muc/${chuDe.chuyen_muc_id}`}
            className="hover:text-blue-600"
          >
            Chuyên mục
          </Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-gray-900">Chi tiết</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header card */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              {/* Title */}
              <div className="flex items-start gap-4 mb-4">
                <div className="flex-shrink-0">
                  <VoteButton
                    doi_tuong_type="CHU_DE"
                    doi_tuong_id={chuDe.id}
                    so_upvote={chuDe.so_upvote}
                    da_upvote={chuDe.da_upvote}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <h1 className="text-2xl font-bold text-gray-900 mb-3">
                    {chuDe.tieu_de}
                  </h1>
                  {/* Meta */}
                  <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600 mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-semibold text-xs">
                        {chuDe.tac_gia?.ho_ten?.[0] || '?'}
                      </div>
                      <span className="font-medium">
                        {chuDe.tac_gia?.ho_ten || 'Ẩn danh'}
                      </span>
                    </div>
                    {chuDe.tac_gia?.chuc_vu && (
                      <>
                        <span>•</span>
                        <span>{chuDe.tac_gia.chuc_vu}</span>
                      </>
                    )}
                    <span>•</span>
                    <span>{formatTimeAgo(chuDe.created_at)}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs ${TRANG_THAI_COLOR[chuDe.trang_thai]}`}>
                      {TRANG_THAI_LABEL[chuDe.trang_thai]}
                    </span>
                  </div>
                  {/* Tags */}
                  {chuDe.tags && chuDe.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {chuDe.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Action bar */}
              <div className="flex items-center gap-4 py-3 border-t border-gray-200">
                <button
                  onClick={handleToggleFollow}
                  disabled={isFollowLoading}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                    isFollowing
                      ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {isFollowing ? (
                    <>
                      <BellOff className="w-4 h-4" />
                      Bỏ theo dõi
                    </>
                  ) : (
                    <>
                      <Bell className="w-4 h-4" />
                      Theo dõi
                    </>
                  )}
                </button>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    {chuDe.so_luot_xem} lượt xem
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageSquare className="w-4 h-4" />
                    {chuDe.so_tra_loi} trả lời
                  </span>
                </div>
                {chuDe.is_khoa && (
                  <span className="flex items-center gap-1 text-sm text-red-600">
                    <Lock className="w-4 h-4" />
                    Đã khóa
                  </span>
                )}
              </div>
            </div>

            {/* Content */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div
                className="prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: chuDe.noi_dung }}
              />
            </div>

            {/* Dap an chuan (if exists) */}
            {dapAnChuan && (
              <div className="bg-green-50 border-2 border-green-500 rounded-lg p-6">
                <div className="flex items-center gap-2 mb-4 text-green-700 font-semibold">
                  <span className="text-lg">✓</span>
                  Đáp án chuẩn
                </div>
                <NestedReply
                  traLoi={dapAnChuan}
                  chuDeId={chuDe.id}
                  onReplySubmit={fetchChuDe}
                  isLocked={chuDe.is_khoa}
                />
              </div>
            )}

            {/* Other replies */}
            {otherReplies.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  {otherReplies.length} Trả lời khác
                </h2>
                <div className="divide-y divide-gray-200">
                  {otherReplies.map((reply) => (
                    <NestedReply
                      key={reply.id}
                      traLoi={reply}
                      chuDeId={chuDe.id}
                      onReplySubmit={fetchChuDe}
                      isLocked={chuDe.is_khoa}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Reply form */}
            {chuDe.is_khoa ? (
              <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-6 text-center">
                <Lock className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
                <p className="text-yellow-700 font-medium">
                  Chủ đề đã bị khóa, không thể trả lời
                </p>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Viết trả lời của bạn
                </h3>
                <textarea
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  placeholder="Nhập nội dung trả lời..."
                  rows={5}
                  className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  disabled={isSubmitting}
                />
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-gray-500">
                    Hãy trả lời một cách chuyên nghiệp và có căn cứ
                  </p>
                  <button
                    onClick={handleSubmitReply}
                    disabled={!replyContent.trim() || isSubmitting}
                    className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isSubmitting ? 'Đang gửi...' : 'Gửi trả lời'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Van ban lien quan */}
            {chuDe.van_ban_lien_quan && Array.isArray(chuDe.van_ban_lien_quan) && chuDe.van_ban_lien_quan.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  Văn bản liên quan
                </h3>
                <ul className="space-y-2">
                  {chuDe.van_ban_lien_quan.map((vb: any, idx: number) => (
                    <li key={idx} className="text-sm text-blue-600 hover:underline">
                      <a href={vb.url || '#'} target="_blank" rel="noopener noreferrer">
                        {vb.ten || vb.trich_dan || 'Văn bản'}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* SOP lien quan */}
            {chuDe.sop_lien_quan && Array.isArray(chuDe.sop_lien_quan) && chuDe.sop_lien_quan.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-green-600" />
                  SOP liên quan
                </h3>
                <ul className="space-y-2">
                  {chuDe.sop_lien_quan.map((sop: any, idx: number) => (
                    <li key={idx} className="text-sm text-green-600 hover:underline">
                      <a href={sop.url || '#'} target="_blank" rel="noopener noreferrer">
                        {sop.ten || sop.trich_dan || 'SOP'}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

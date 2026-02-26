'use client';

/**
 * NestedReply.tsx
 * ===============
 * Component hien thi tra loi (co the nested 2 level).
 * Hien thi VoteButton, thong tin tac gia, nut tra loi, va form inline.
 */

import { useState } from 'react';
import { Check, MessageSquare } from 'lucide-react';
import { traLoiApi } from '@/services/forum';
import type { ITraLoiInChuDe, ICanCuPhapLy } from '@/types/forum';
import VoteButton from './VoteButton';

interface NestedReplyProps {
  traLoi: ITraLoiInChuDe;
  chuDeId: string;
  depth?: number;
  onReplySubmit?: () => void;
  isLocked?: boolean;
}

export default function NestedReply({
  traLoi,
  chuDeId,
  depth = 0,
  onReplySubmit,
  isLocked = false,
}: NestedReplyProps) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Format thoi gian tuong doi
  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Vua xong';
    if (diffMins < 60) return `${diffMins} phut truoc`;
    if (diffHours < 24) return `${diffHours} gio truoc`;
    if (diffDays < 30) return `${diffDays} ngay truoc`;
    return date.toLocaleDateString('vi-VN');
  };

  // Lay chu cai dau ten de lam avatar
  const getInitials = (name: string | null | undefined) => {
    if (!name) return '?';
    const parts = name.trim().split(' ');
    return parts[parts.length - 1][0].toUpperCase();
  };

  // Xu ly submit tra loi
  const handleSubmitReply = async () => {
    if (!replyContent.trim() || isSubmitting) return;

    setIsSubmitting(true);

    try {
      await traLoiApi.taoMoi(chuDeId, {
        noi_dung: replyContent.trim(),
        parent_id: traLoi.id,
      });

      setReplyContent('');
      setShowReplyForm(false);

      if (onReplySubmit) {
        onReplySubmit();
      }
    } catch (error) {
      console.error('Reply submit error:', error);
      alert('Co loi xay ra khi gui tra loi');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`flex gap-3 ${depth > 0 ? 'ml-8' : ''} py-3`}>
      {/* VoteButton ben trai */}
      <div className="flex-shrink-0">
        <VoteButton
          doi_tuong_type="TRA_LOI"
          doi_tuong_id={traLoi.id}
          so_upvote={traLoi.so_upvote}
          da_upvote={traLoi.da_upvote}
        />
      </div>

      {/* Noi dung chinh */}
      <div className="flex-1">
        {/* Header: avatar + thong tin tac gia */}
        <div className="flex items-start gap-3 mb-2">
          {/* Avatar */}
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold">
            {getInitials(traLoi.tac_gia?.ho_ten)}
          </div>

          {/* Thong tin tac gia */}
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-gray-900">
                {traLoi.tac_gia?.ho_ten || 'Nguoi dung an danh'}
              </span>
              {traLoi.tac_gia?.chuc_vu && (
                <span className="text-sm text-gray-600">
                  • {traLoi.tac_gia.chuc_vu}
                </span>
              )}
              {traLoi.is_dap_an_chuan && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                  <Check className="w-3 h-3" />
                  Dap an chuan
                </span>
              )}
            </div>
            <div className="text-sm text-gray-500">
              {formatRelativeTime(traLoi.created_at)}
            </div>
          </div>
        </div>

        {/* Noi dung tra loi */}
        <div
          className="prose prose-sm max-w-none mb-3"
          dangerouslySetInnerHTML={{ __html: traLoi.noi_dung }}
        />

        {/* Can cu phap ly */}
        {traLoi.can_cu_phap_ly && traLoi.can_cu_phap_ly.length > 0 && (
          <div className="mb-3 p-3 bg-blue-50 rounded-md border border-blue-200">
            <div className="text-sm font-semibold text-blue-900 mb-2">
              Can cu phap ly:
            </div>
            <ul className="space-y-1">
              {traLoi.can_cu_phap_ly.map((item, idx) => (
                <li key={idx} className="text-sm text-blue-800">
                  <span className="inline-block w-20 font-medium">
                    [{item.loai === 'VAN_BAN' ? 'Van ban' : 'SOP'}]
                  </span>
                  {item.trich_dan}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Nut tra loi (chi hien thi neu depth < 1 va chua khoa) */}
        {depth < 1 && !isLocked && (
          <button
            onClick={() => setShowReplyForm(!showReplyForm)}
            className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            <MessageSquare className="w-4 h-4" />
            Tra loi
          </button>
        )}

        {/* Form tra loi inline */}
        {showReplyForm && (
          <div className="mt-3 p-3 bg-gray-50 rounded-md border border-gray-200">
            <textarea
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              placeholder="Nhap tra loi cua ban..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              disabled={isSubmitting}
            />
            <div className="flex gap-2 mt-2">
              <button
                onClick={handleSubmitReply}
                disabled={!replyContent.trim() || isSubmitting}
                className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Dang gui...' : 'Gui'}
              </button>
              <button
                onClick={() => {
                  setShowReplyForm(false);
                  setReplyContent('');
                }}
                disabled={isSubmitting}
                className="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-md hover:bg-gray-300 disabled:opacity-50"
              >
                Huy
              </button>
            </div>
          </div>
        )}

        {/* Render tra loi con (depth + 1) */}
        {traLoi.children && traLoi.children.length > 0 && (
          <div className="mt-3 space-y-3 border-l-2 border-gray-200 pl-3">
            {traLoi.children.map((child) => (
              <NestedReply
                key={child.id}
                traLoi={child}
                chuDeId={chuDeId}
                depth={depth + 1}
                onReplySubmit={onReplySubmit}
                isLocked={isLocked}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

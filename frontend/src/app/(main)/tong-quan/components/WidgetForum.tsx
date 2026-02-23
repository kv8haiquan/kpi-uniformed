/**
 * WidgetForum.tsx
 * ================
 * Widget hiển thị tóm tắt diễn đàn (chủ đề mới, trả lời mới).
 * Fallback: card điều hướng nếu service chưa có.
 */

import Link from 'next/link';
import DashboardWidget from './DashboardWidget';
import type { IForumDashboardSummary } from '@/types/portal';

// =============================================================================
// COMPONENT
// =============================================================================

interface WidgetForumProps {
  data: IForumDashboardSummary | null;
  loading: boolean;
}

export default function WidgetForum({ data, loading }: WidgetForumProps) {
  return (
    <DashboardWidget
      title="Diễn đàn"
      icon="💬"
      href="/dien-dan"
      hrefLabel="Vào diễn đàn"
      loading={loading}
      colorClass="bg-teal-100"
    >
      {data ? (
        <div className="space-y-3">
          {/* 2 chỉ số */}
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center bg-teal-50 rounded-lg py-3 px-2">
              <div className="text-2xl font-bold text-teal-700">
                {data.chu_de_moi ?? 0}
              </div>
              <div className="text-xs text-gray-500 mt-1">Chủ đề mới</div>
            </div>
            <div className="text-center bg-cyan-50 rounded-lg py-3 px-2">
              <div className="text-2xl font-bold text-cyan-700">
                {data.tra_loi_moi ?? 0}
              </div>
              <div className="text-xs text-gray-500 mt-1">Trả lời mới</div>
            </div>
          </div>

          <Link
            href="/dien-dan"
            className="block text-center text-xs text-teal-600 hover:underline"
          >
            Tham gia thảo luận →
          </Link>
        </div>
      ) : (
        /* Fallback */
        <div className="space-y-3">
          <p className="text-xs text-gray-500 text-center">Diễn đàn trao đổi nghiệp vụ</p>
          <div className="grid grid-cols-2 gap-2">
            <Link
              href="/dien-dan"
              className="block text-center rounded-lg bg-teal-50 hover:bg-teal-100 border border-teal-200 p-2 transition-colors"
            >
              <div className="text-lg">🗣️</div>
              <div className="text-xs text-teal-700 font-medium mt-1">Thảo luận</div>
            </Link>
            <Link
              href="/dien-dan/tao-chu-de"
              className="block text-center rounded-lg bg-cyan-50 hover:bg-cyan-100 border border-cyan-200 p-2 transition-colors"
            >
              <div className="text-lg">✏️</div>
              <div className="text-xs text-cyan-700 font-medium mt-1">Tạo chủ đề</div>
            </Link>
          </div>
        </div>
      )}
    </DashboardWidget>
  );
}

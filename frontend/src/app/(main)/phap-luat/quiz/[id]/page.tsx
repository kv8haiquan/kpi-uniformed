/**
 * src/app/(main)/phap-luat/quiz/[id]/page.tsx
 * ==============================================
 * Trang làm quiz kiểm tra hiểu biết pháp luật.
 *
 * URL params:
 *   [id] = quizId (UUID quiz cụ thể)
 *
 * Query params:
 *   ?vbId={vanBanId} — để fetch danh sách quiz của VB và tìm quiz này
 *
 * Flow:
 *   1. Đọc quizId từ params, vbId từ searchParams
 *   2. Gọi getQuiz(vbId) → lấy danh sách quiz → tìm quiz với id = quizId
 *   3. Render QuizForm
 */

'use client';

import { useEffect, useState, Suspense } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { legalService } from '@/services/legal';
import { QuizForm } from '@/components/legal/QuizForm';
import type { IQuizVanBan } from '@/types/legal';

// =============================================================================
// INNER (cần Suspense vì dùng useSearchParams)
// =============================================================================
function QuizPageInner() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const quizId = params?.id as string;
  const vbId = searchParams?.get('vbId') ?? '';

  const [quiz, setQuiz] = useState<IQuizVanBan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!quizId || !vbId) {
      setError('Thiếu thông tin quiz. Vui lòng truy cập từ trang chi tiết văn bản.');
      setLoading(false);
      return;
    }
    const load = async () => {
      try {
        const res = await legalService.getQuiz(vbId);
        // Kiểm tra success field theo SHARED_CODING_STANDARDS §5.1
        if (res.data?.success) {
          const quizzes: IQuizVanBan[] = res.data.data ?? [];
          const found = quizzes.find(q => q.id === quizId);
          if (!found) {
            setError('Không tìm thấy quiz này.');
          } else {
            setQuiz(found);
          }
        } else {
          const msg = res.data?.error?.message || 'Không thể tải quiz.';
          console.warn('[Legal] getQuiz:', res.data?.error?.code, msg);
          setError(msg);
        }
      } catch {
        setError('Không thể tải quiz. Vui lòng thử lại.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [quizId, vbId]);

  // Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Đang tải quiz...</p>
        </div>
      </div>
    );
  }

  // Error
  if (error || !quiz) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white rounded-xl border border-red-200 p-8 text-center max-w-md">
          <span className="text-4xl block mb-3">⚠️</span>
          <p className="text-red-700 font-medium mb-4">{error || 'Không tìm thấy quiz'}</p>
          {vbId ? (
            <Link
              href={`/phap-luat/${vbId}`}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition-colors"
            >
              ← Quay lại văn bản
            </Link>
          ) : (
            <button
              onClick={() => router.push('/phap-luat')}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition-colors"
            >
              ← Về trang chính
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6">

        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-gray-400 mb-6">
          <Link href="/phap-luat" className="hover:text-purple-600 transition-colors">⚖️ Pháp luật</Link>
          {vbId && (
            <>
              <span>›</span>
              <Link href={`/phap-luat/${vbId}`} className="hover:text-purple-600 transition-colors">
                Văn bản
              </Link>
            </>
          )}
          <span>›</span>
          <span className="text-gray-700 font-medium">Quiz</span>
        </nav>

        {/* Quiz form */}
        <QuizForm
          quiz={quiz}
          onClose={vbId ? () => router.push(`/phap-luat/${vbId}`) : undefined}
        />

        {/* Note */}
        <p className="text-center text-xs text-gray-400 mt-4">
          💡 Có thể làm lại quiz nhiều lần. Kết quả tốt nhất sẽ được ghi nhận.
        </p>

      </div>
    </div>
  );
}

// =============================================================================
// PAGE (bọc Suspense cho useSearchParams)
// =============================================================================
export default function QuizPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
        </div>
      }
    >
      <QuizPageInner />
    </Suspense>
  );
}

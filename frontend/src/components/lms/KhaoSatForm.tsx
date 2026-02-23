/**
 * src/components/lms/KhaoSatForm.tsx
 * ====================================
 * Form khảo sát sau khi hoàn thành khóa học.
 * 5 sao tổng thể + 4 câu hỏi chi tiết (1–5) + textarea góp ý.
 * POST /khoa-hoc/{id}/khao-sat
 */

'use client';

import { useState } from 'react';
import { khaoSatApi } from '@/services/lms';

const QUESTIONS = [
  { key: 'noi_dung', label: 'Nội dung khóa học phù hợp và bổ ích' },
  { key: 'giang_vien', label: 'Giảng viên truyền đạt rõ ràng, dễ hiểu' },
  { key: 'tai_lieu', label: 'Tài liệu học tập đầy đủ, chất lượng' },
  { key: 'ung_dung', label: 'Kiến thức có thể ứng dụng vào công việc thực tế' },
];

const RATING_LABELS = ['', 'Rất không hài lòng', 'Không hài lòng', 'Bình thường', 'Hài lòng', 'Rất hài lòng'];

interface Props {
  khoaHocId: string;
  onSuccess?: () => void;
}

export default function KhaoSatForm({ khoaHocId, onSuccess }: Props) {
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [scores, setScores] = useState<Record<string, number>>({});
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async () => {
    if (!rating) {
      alert('Vui lòng chọn đánh giá tổng thể (số sao)');
      return;
    }
    setSubmitting(true);
    try {
      await khaoSatApi.guiKhaoSat(khoaHocId, {
        noi_dung: {
          rating,
          feedback: feedback.trim() || null,
          questions: QUESTIONS.map((q) => ({ q: q.key, score: scores[q.key] ?? 0 })),
        },
      });
      setDone(true);
      onSuccess?.();
    } catch (err: any) {
      const msg = err?.response?.data?.detail?.error?.message || 'Gửi khảo sát thất bại. Vui lòng thử lại.';
      alert(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="text-center py-14">
        <div className="text-6xl mb-4">🎉</div>
        <h3 className="text-xl font-semibold text-gray-900">Cảm ơn bạn đã phản hồi!</h3>
        <p className="text-gray-500 mt-2 text-sm">
          Ý kiến của bạn giúp chúng tôi cải thiện chất lượng đào tạo.
        </p>
      </div>
    );
  }

  const displayRating = hoverRating || rating;

  return (
    <div className="max-w-xl mx-auto py-6 space-y-7">
      {/* Đánh giá tổng thể — 5 sao */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-1">Đánh giá tổng thể <span className="text-red-500">*</span></h3>
        <p className="text-xs text-gray-500 mb-3">Bạn hài lòng với khóa học này như thế nào?</p>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map((s) => (
            <button
              key={s}
              onClick={() => setRating(s)}
              onMouseEnter={() => setHoverRating(s)}
              onMouseLeave={() => setHoverRating(0)}
              className="text-4xl transition-transform hover:scale-110 focus:outline-none"
              aria-label={`${s} sao`}
            >
              {s <= displayRating ? '⭐' : '☆'}
            </button>
          ))}
        </div>
        {rating > 0 && (
          <p className="text-sm text-yellow-700 font-medium mt-2">{RATING_LABELS[rating]}</p>
        )}
      </div>

      {/* 4 câu hỏi chi tiết — nút 1–5 */}
      <div className="space-y-5">
        <h3 className="font-semibold text-gray-900">Đánh giá chi tiết</h3>
        {QUESTIONS.map((q) => (
          <div key={q.key}>
            <p className="text-sm text-gray-700 mb-2">{q.label}</p>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((s) => (
                <button
                  key={s}
                  onClick={() => setScores((prev) => ({ ...prev, [q.key]: s }))}
                  className={`w-10 h-10 rounded-lg border text-sm font-semibold transition-colors ${
                    scores[q.key] === s
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'border-gray-300 text-gray-600 hover:border-blue-400 hover:text-blue-600'
                  }`}
                >
                  {s}
                </button>
              ))}
              <span className="self-center text-xs text-gray-400 ml-1">
                {scores[q.key] ? RATING_LABELS[scores[q.key]] : 'Chưa đánh giá'}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Góp ý */}
      <div>
        <label className="block text-sm font-semibold text-gray-900 mb-2">
          Góp ý thêm <span className="font-normal text-gray-400">(tuỳ chọn)</span>
        </label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          rows={4}
          placeholder="Nhận xét, góp ý để cải thiện khóa học..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        />
      </div>

      <button
        onClick={handleSubmit}
        disabled={submitting || !rating}
        className="w-full px-4 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {submitting ? 'Đang gửi...' : '⭐ Gửi khảo sát'}
      </button>
    </div>
  );
}

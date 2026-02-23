/**
 * src/components/legal/QuizForm.tsx
 * ====================================
 * Form làm quiz kiểm tra hiểu biết pháp luật.
 *
 * 3 states:
 *   CHUA_BAT_DAU → Màn hình thông tin quiz, nút "Bắt đầu"
 *   DANG_LAM     → Danh sách câu hỏi + timer đếm ngược + nút "Nộp bài"
 *   DA_NOP       → Kết quả: điểm, đạt/không đạt, chi tiết từng câu
 *
 * Timer tự động nộp bài khi hết giờ.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import type { IQuizVanBan, IKetQuaQuiz } from '@/types/legal';
import { legalService } from '@/services/legal';

type QuizState = 'CHUA_BAT_DAU' | 'DANG_LAM' | 'DA_NOP';

interface QuizFormProps {
  quiz: IQuizVanBan;
  onClose?: () => void;
}

// =============================================================================
// FORMAT THỜI GIAN
// =============================================================================
function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================
export function QuizForm({ quiz, onClose }: QuizFormProps) {
  const [quizState, setQuizState] = useState<QuizState>('CHUA_BAT_DAU');
  // answers: { câuIndex: indexĐápÁn }
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [ketQua, setKetQua] = useState<IKetQuaQuiz | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Timer (giây)
  const totalSeconds = quiz.thoi_gian_phut ? quiz.thoi_gian_phut * 60 : null;
  const [timeLeft, setTimeLeft] = useState<number | null>(totalSeconds);

  // Số câu đã trả lời
  const soCauDaTraLoi = Object.keys(answers).length;

  // Nộp bài
  const handleNopBai = useCallback(async () => {
    if (loading) return;
    setLoading(true);
    setError('');
    try {
      const tra_loi = Object.entries(answers).map(([cau, dap_an]) => ({
        cau: parseInt(cau),
        dap_an,
      }));
      const res = await legalService.lamQuiz(quiz.id, { tra_loi });
      setKetQua(res.data.data);
      setQuizState('DA_NOP');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: { error?: { message?: string } } } } };
      setError(e?.response?.data?.detail?.error?.message || 'Không thể nộp bài. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }, [answers, quiz.id, loading]);

  // Countdown timer
  useEffect(() => {
    if (quizState !== 'DANG_LAM' || timeLeft === null) return;
    if (timeLeft <= 0) {
      handleNopBai();
      return;
    }
    const t = setTimeout(() => setTimeLeft(prev => (prev !== null ? prev - 1 : prev)), 1000);
    return () => clearTimeout(t);
  }, [quizState, timeLeft, handleNopBai]);

  const batDau = () => {
    setAnswers({});
    setKetQua(null);
    setError('');
    setTimeLeft(totalSeconds);
    setQuizState('DANG_LAM');
  };

  const handleAnswer = (cauIdx: number, dapAnIdx: number) => {
    setAnswers(prev => ({ ...prev, [cauIdx]: dapAnIdx }));
  };

  // =============================================================================
  // STATE: CHƯA BẮT ĐẦU
  // =============================================================================
  if (quizState === 'CHUA_BAT_DAU') {
    return (
      <div className="bg-white rounded-xl border border-purple-200 p-8 text-center">
        <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">📝</span>
        </div>
        <h3 className="text-lg font-bold text-gray-900 mb-2">{quiz.tieu_de}</h3>
        <div className="flex justify-center gap-6 text-sm text-gray-500 mb-6">
          <span>📋 {quiz.so_cau_hoi} câu</span>
          {quiz.thoi_gian_phut && <span>⏱ {quiz.thoi_gian_phut} phút</span>}
          <span>🎯 Đạt: {quiz.diem_dat}%</span>
        </div>
        <button
          onClick={batDau}
          className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
        >
          Bắt đầu làm bài
        </button>
      </div>
    );
  }

  // =============================================================================
  // STATE: ĐANG LÀM
  // =============================================================================
  if (quizState === 'DANG_LAM') {
    const sapHetGio = timeLeft !== null && timeLeft < 300;

    return (
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {/* Header sticky: tên quiz + progress + timer */}
        <div className={`sticky top-0 z-10 px-4 py-3 border-b flex items-center justify-between ${
          sapHetGio ? 'bg-red-50 border-red-200' : 'bg-purple-50 border-purple-100'
        }`}>
          <div>
            <h3 className="font-semibold text-gray-900 text-sm">{quiz.tieu_de}</h3>
            <p className="text-xs text-gray-500">
              Đã trả lời <strong className="text-purple-700">{soCauDaTraLoi}</strong>/{quiz.so_cau_hoi} câu
            </p>
          </div>
          {timeLeft !== null && (
            <span className={`font-mono font-bold text-lg ${sapHetGio ? 'text-red-600 animate-pulse' : 'text-purple-700'}`}>
              ⏱ {formatTime(timeLeft)}
            </span>
          )}
        </div>

        {/* Danh sách câu hỏi */}
        <div className="p-4 space-y-5">
          {quiz.cau_hoi.map((ch, cIdx) => (
            <div key={cIdx} className="border border-gray-100 rounded-xl p-4">
              <p className="text-sm font-medium text-gray-900 mb-3">
                <span className="inline-block bg-purple-100 text-purple-700 font-bold px-2 py-0.5 rounded mr-2 text-xs">
                  Câu {cIdx + 1}
                </span>
                {ch.noi_dung}
              </p>
              <div className="space-y-2">
                {ch.dap_an.map((da, dIdx) => (
                  <label
                    key={dIdx}
                    className={`flex items-center gap-3 p-2.5 rounded-lg cursor-pointer border transition-colors ${
                      answers[cIdx] === dIdx
                        ? 'bg-purple-50 border-purple-300'
                        : 'border-transparent hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name={`cau-${cIdx}`}
                      checked={answers[cIdx] === dIdx}
                      onChange={() => handleAnswer(cIdx, dIdx)}
                      className="accent-purple-600 shrink-0"
                    />
                    <span className="text-sm text-gray-800">
                      <span className="font-medium text-purple-600 mr-1">
                        {String.fromCharCode(65 + dIdx)}.
                      </span>
                      {da}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer nộp bài */}
        {error && (
          <div className="mx-4 mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}
        <div className="px-4 pb-4 flex items-center justify-between border-t border-gray-100 pt-3">
          <span className="text-sm text-gray-500">
            Đã trả lời{' '}
            <strong className="text-purple-700">{soCauDaTraLoi}</strong>/{quiz.so_cau_hoi} câu
          </span>
          <button
            onClick={handleNopBai}
            disabled={loading || soCauDaTraLoi === 0}
            className="px-5 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium text-sm transition-colors"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Đang nộp...
              </span>
            ) : 'Nộp bài'}
          </button>
        </div>
      </div>
    );
  }

  // =============================================================================
  // STATE: ĐÃ NỘP — Kết quả
  // =============================================================================
  const kq = ketQua!;
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Header kết quả */}
      <div className={`p-6 text-center ${kq.dat_yeu_cau ? 'bg-green-50' : 'bg-red-50'}`}>
        <div className="text-5xl mb-3">{kq.dat_yeu_cau ? '🎉' : '😔'}</div>
        <div className={`text-4xl font-bold mb-1 ${kq.dat_yeu_cau ? 'text-green-700' : 'text-red-700'}`}>
          {kq.diem.toFixed(1)} điểm
        </div>
        <div className={`text-sm font-semibold mb-3 ${kq.dat_yeu_cau ? 'text-green-600' : 'text-red-600'}`}>
          {kq.dat_yeu_cau ? '✅ Đạt yêu cầu' : '❌ Chưa đạt yêu cầu'}
        </div>
        <div className="flex justify-center gap-8 text-sm">
          <div className="text-center">
            <div className="font-bold text-green-700 text-xl">{kq.so_cau_dung}</div>
            <div className="text-gray-500 text-xs">Câu đúng</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-red-600 text-xl">{quiz.so_cau_hoi - kq.so_cau_dung}</div>
            <div className="text-gray-500 text-xs">Câu sai</div>
          </div>
        </div>
      </div>

      {/* Chi tiết từng câu */}
      {kq.chi_tiet && kq.chi_tiet.length > 0 && (
        <div className="p-4">
          <h4 className="font-semibold text-gray-800 text-sm mb-3">📋 Chi tiết từng câu:</h4>
          <div className="space-y-3">
            {kq.chi_tiet.map((ct, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg border text-sm ${
                  ct.dung ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                }`}
              >
                <div className="flex items-start gap-2">
                  <span className="shrink-0 text-base">{ct.dung ? '✅' : '❌'}</span>
                  <div>
                    <p className="font-medium text-gray-900">
                      Câu {ct.cau + 1}:{' '}
                      <span className="font-normal">
                        Bạn chọn{' '}
                        <em>&ldquo;{quiz.cau_hoi[ct.cau]?.dap_an[ct.tra_loi] ?? '?'}&rdquo;</em>
                      </span>
                    </p>
                    {!ct.dung && ct.giai_thich && (
                      <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                        💡 <strong>Giải thích:</strong> {ct.giai_thich}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="p-4 flex gap-3 border-t border-gray-100">
        <button
          onClick={batDau}
          className="flex-1 py-2.5 border border-purple-300 text-purple-700 rounded-lg text-sm font-medium hover:bg-purple-50 transition-colors"
        >
          🔄 Làm lại
        </button>
        {onClose && (
          <button
            onClick={onClose}
            className="flex-1 py-2.5 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors"
          >
            Đóng
          </button>
        )}
      </div>
    </div>
  );
}

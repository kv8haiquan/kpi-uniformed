/**
 * src/app/(main)/dao-tao/ky-thi/[id]/thi/page.tsx
 * =================================================
 * Trang lam bai thi DGNL — 3 states: CHUA_BAT_DAU → DANG_LAM → DA_NOP.
 */

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { kyThiApi } from '@/services/lms';
import type { IKyThi, IDgnlCauHoi } from '@/types/lms';

type ExamState = 'CHUA_BAT_DAU' | 'DANG_LAM' | 'DA_NOP';

function formatTime(secs: number): string {
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

export default function ThiDgnlPage() {
  const params = useParams();
  const router = useRouter();
  const kyThiId = params.id as string;

  const [state, setState] = useState<ExamState>('CHUA_BAT_DAU');
  const [kyThi, setKyThi] = useState<IKyThi | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dang lam
  const [cauHoi, setCauHoi] = useState<IDgnlCauHoi[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [traLoi, setTraLoi] = useState<Record<string, any>>({});
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const handleNopBaiRef = useRef<() => void>(() => {});

  // Load ky thi info
  useEffect(() => {
    const load = async () => {
      try {
        const res = await kyThiApi.chiTiet(kyThiId);
        setKyThi(res.data.data);
      } catch {
        setError('Không tìm thấy kỳ thi');
      } finally {
        setLoading(false);
      }
    };
    if (kyThiId) load();
  }, [kyThiId]);

  // Timer
  useEffect(() => {
    if (state !== 'DANG_LAM' || timeLeft === null) return;
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev === null || prev <= 0) {
          if (timerRef.current) clearInterval(timerRef.current);
          handleNopBaiRef.current();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [state]);

  // Bat dau thi
  const handleBatDau = async () => {
    try {
      setLoading(true);
      const res = await kyThiApi.batDau(kyThiId);
      const data = res.data.data;
      setCauHoi(data.cau_hoi || []);
      setTimeLeft(data.thoi_gian_con_lai_giay);
      setState('DANG_LAM');
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Không thể bắt đầu thi');
    } finally {
      setLoading(false);
    }
  };

  // Nop bai
  const handleNopBai = useCallback(async () => {
    if (submitting) return;
    setSubmitting(true);
    if (timerRef.current) clearInterval(timerRef.current);

    try {
      const cauTraLoi = cauHoi.map(ch => ({
        cau_hoi_id: ch.id,
        tra_loi: traLoi[ch.id] || null,
      }));
      await kyThiApi.nopBai(kyThiId, { cau_tra_loi: cauTraLoi });
      setState('DA_NOP');
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi nộp bài');
    } finally {
      setSubmitting(false);
    }
  }, [submitting, cauHoi, traLoi, kyThiId]);

  handleNopBaiRef.current = handleNopBai;

  // Chon dap an
  const handleChonDapAn = (cauHoiId: string, loai: string, value: any) => {
    setTraLoi(prev => ({
      ...prev,
      [cauHoiId]: { dap_an: value },
    }));
  };

  // Nhom cau hoi theo linh vuc
  const linhVucGroups = cauHoi.reduce<Record<string, IDgnlCauHoi[]>>((acc, ch) => {
    const key = ch.linh_vuc || 'Khác';
    if (!acc[key]) acc[key] = [];
    acc[key].push(ch);
    return acc;
  }, {});

  const currentCauHoi = cauHoi[currentIdx];
  const soTraLoi = Object.keys(traLoi).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  // ===== DA_NOP =====
  if (state === 'DA_NOP') {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md text-center">
          <div className="text-5xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Đã nộp bài thành công!</h2>
          <p className="text-gray-500 mb-6">Bài thi của bạn đã được chấm điểm tự động.</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => router.push(`/dao-tao/ky-thi/${kyThiId}/ket-qua`)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Xem kết quả
            </button>
            <button
              onClick={() => router.push('/dao-tao/ky-thi')}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Quay lại
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ===== CHUA_BAT_DAU =====
  if (state === 'CHUA_BAT_DAU') {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-lg">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">{kyThi?.ten_ky_thi}</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-3 mb-6 text-sm">
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">Thời gian làm bài</span>
              <span className="font-semibold">{kyThi?.thoi_gian_lam_bai_phut} phút</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">Điểm đạt</span>
              <span className="font-semibold">{kyThi?.diem_dat}%</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">Số lượt thi tối đa</span>
              <span className="font-semibold">{kyThi?.so_lan_thi_toi_da}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">Trộn câu hỏi</span>
              <span>{kyThi?.tron_cau_hoi ? 'Có' : 'Không'}</span>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-6 text-sm text-yellow-800">
            <strong>Lưu ý:</strong> Sau khi bấm "Bắt đầu thi", đồng hồ sẽ bắt đầu đếm ngược.
            Bài thi sẽ tự động nộp khi hết giờ.
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleBatDau}
              className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold"
            >
              Bắt đầu thi
            </button>
            <button
              onClick={() => router.push('/dao-tao/ky-thi')}
              className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Quay lại
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ===== DANG_LAM =====
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="font-semibold text-gray-900">{kyThi?.ten_ky_thi}</h1>
            <p className="text-xs text-gray-500">
              Câu {currentIdx + 1}/{cauHoi.length} | Đã trả lời: {soTraLoi}/{cauHoi.length}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className={`text-lg font-mono font-bold ${(timeLeft || 0) < 300 ? 'text-red-600' : 'text-gray-900'}`}>
              {timeLeft !== null ? formatTime(timeLeft) : '--:--'}
            </div>
            <button
              onClick={() => {
                if (confirm('Bạn có chắc muốn nộp bài?')) handleNopBai();
              }}
              disabled={submitting}
              className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {submitting ? 'Đang nộp...' : 'Nộp bài'}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6 flex gap-6">
        {/* Sidebar nav */}
        <div className="hidden lg:block w-64 flex-shrink-0">
          <div className="bg-white rounded-xl border p-4 sticky top-20">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Danh sách câu hỏi</h3>
            {Object.entries(linhVucGroups).map(([lv, chs]) => (
              <div key={lv} className="mb-3">
                <div className="text-xs font-medium text-gray-500 mb-1">{lv}</div>
                <div className="flex flex-wrap gap-1">
                  {chs.map(ch => {
                    const idx = cauHoi.indexOf(ch);
                    const answered = !!traLoi[ch.id];
                    const isCurrent = idx === currentIdx;
                    return (
                      <button
                        key={ch.id}
                        onClick={() => setCurrentIdx(idx)}
                        className={`w-8 h-8 text-xs rounded-lg font-medium transition-colors
                          ${isCurrent ? 'bg-blue-600 text-white' :
                            answered ? 'bg-green-100 text-green-700 border border-green-300' :
                            'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                      >
                        {idx + 1}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main question */}
        <div className="flex-1">
          {currentCauHoi && (
            <div className="bg-white rounded-xl border p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
                  Câu {currentIdx + 1}
                </span>
                {currentCauHoi.linh_vuc && (
                  <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full text-xs">
                    {currentCauHoi.linh_vuc}
                  </span>
                )}
                <span className="text-xs text-gray-400 ml-auto">{currentCauHoi.diem} điểm</span>
              </div>

              <div
                className="prose prose-sm max-w-none mb-6"
                dangerouslySetInnerHTML={{ __html: currentCauHoi.noi_dung }}
              />

              {/* Lua chon */}
              {currentCauHoi.lua_chon && (
                <div className="space-y-2">
                  {currentCauHoi.lua_chon.map((lc) => {
                    const selected = traLoi[currentCauHoi.id]?.dap_an;
                    const isSelected = currentCauHoi.loai === 'TRAC_NGHIEM_NHIEU'
                      ? (selected || []).includes(lc.key)
                      : selected === lc.key;

                    return (
                      <button
                        key={lc.key}
                        onClick={() => {
                          if (currentCauHoi.loai === 'TRAC_NGHIEM_NHIEU') {
                            const prev = traLoi[currentCauHoi.id]?.dap_an || [];
                            const next = prev.includes(lc.key)
                              ? prev.filter((k: string) => k !== lc.key)
                              : [...prev, lc.key];
                            handleChonDapAn(currentCauHoi.id, currentCauHoi.loai, next);
                          } else {
                            handleChonDapAn(currentCauHoi.id, currentCauHoi.loai, lc.key);
                          }
                        }}
                        className={`w-full text-left p-3 rounded-lg border transition-colors flex items-start gap-3
                          ${isSelected
                            ? 'border-blue-500 bg-blue-50 text-blue-900'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}`}
                      >
                        <span className={`flex-shrink-0 w-7 h-7 rounded-full border-2 flex items-center justify-center text-xs font-bold
                          ${isSelected ? 'border-blue-500 bg-blue-500 text-white' : 'border-gray-300 text-gray-500'}`}>
                          {lc.key}
                        </span>
                        <span className="text-sm" dangerouslySetInnerHTML={{ __html: lc.noi_dung }} />
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Navigation */}
              <div className="flex justify-between mt-8 pt-4 border-t">
                <button
                  onClick={() => setCurrentIdx(Math.max(0, currentIdx - 1))}
                  disabled={currentIdx === 0}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-30"
                >
                  Câu trước
                </button>
                <button
                  onClick={() => setCurrentIdx(Math.min(cauHoi.length - 1, currentIdx + 1))}
                  disabled={currentIdx === cauHoi.length - 1}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-30"
                >
                  Câu tiếp
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

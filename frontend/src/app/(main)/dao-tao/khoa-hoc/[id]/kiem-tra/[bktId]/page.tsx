/**
 * src/app/(main)/dao-tao/khoa-hoc/[id]/kiem-tra/[bktId]/page.tsx
 * ================================================================
 * Lam bai kiem tra — 3 states: CHUA_BAT_DAU → DANG_LAM → DA_NOP.
 */

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { baiKiemTraApi } from '@/services/lms';
import type { IBaiKiemTra, ICauHoiForExam, IKetQuaResponse } from '@/types/lms';

type ExamState = 'CHUA_BAT_DAU' | 'DANG_LAM' | 'DA_NOP';

export default function KiemTraPage() {
  const params = useParams();
  const khoaHocId = params.id as string;
  const bktId = params.bktId as string;

  const [state, setState] = useState<ExamState>('CHUA_BAT_DAU');
  const [bkt, setBkt] = useState<IBaiKiemTra | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dang lam state
  const [cauHoi, setCauHoi] = useState<ICauHoiForExam[]>([]);
  const [ketQuaId, setKetQuaId] = useState('');
  const [currentIdx, setCurrentIdx] = useState(0);
  const [traLoi, setTraLoi] = useState<Record<string, any>>({});
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Ket qua state
  const [ketQua, setKetQua] = useState<IKetQuaResponse | null>(null);

  // Load BKT info
  useEffect(() => {
    const load = async () => {
      try {
        const res = await baiKiemTraApi.chiTiet(bktId);
        setBkt(res.data.data);
      } catch (err: any) {
        setError('Không tìm thấy bài kiểm tra');
      } finally {
        setLoading(false);
      }
    };
    if (bktId) load();
  }, [bktId]);

  // Timer countdown
  useEffect(() => {
    if (state !== 'DANG_LAM' || timeLeft === null) return;
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev === null || prev <= 0) {
          if (timerRef.current) clearInterval(timerRef.current);
          handleNopBai();
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
      const res = await baiKiemTraApi.batDau(bktId);
      const data = res.data.data;
      setCauHoi(data.cau_hoi);
      setKetQuaId(data.ket_qua_id);
      setCurrentIdx(0);
      setTraLoi({});
      if (data.thoi_gian_phut) {
        setTimeLeft(data.thoi_gian_phut * 60);
      }
      setState('DANG_LAM');
    } catch (err: any) {
      alert(err?.response?.data?.detail?.error?.message || 'Không thể bắt đầu thi');
    } finally {
      setLoading(false);
    }
  };

  // Nop bai
  const handleNopBai = useCallback(async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      const traLoiList = Object.entries(traLoi).map(([cau_hoi_id, dap_an]) => ({
        cau_hoi_id,
        dap_an,
      }));
      const res = await baiKiemTraApi.nopBai(bktId, {
        ket_qua_id: ketQuaId,
        tra_loi: traLoiList,
      });
      setKetQua(res.data.data);
      setState('DA_NOP');
      if (timerRef.current) clearInterval(timerRef.current);
    } catch (err: any) {
      alert(err?.response?.data?.detail?.error?.message || 'Lỗi nộp bài');
    } finally {
      setSubmitting(false);
    }
  }, [traLoi, ketQuaId, bktId, submitting]);

  // Update tra loi
  const setAnswer = (cauHoiId: string, value: any) => {
    setTraLoi((prev) => ({ ...prev, [cauHoiId]: value }));
  };

  // Format time
  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (loading && state === 'CHUA_BAT_DAU') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-700">{error}</p>
          <Link href={`/dao-tao/khoa-hoc/${khoaHocId}`} className="text-blue-600 hover:underline mt-2 inline-block">Quay lại</Link>
        </div>
      </div>
    );
  }

  // =========================================================================
  // STATE 1: CHUA BAT DAU
  // =========================================================================
  if (state === 'CHUA_BAT_DAU' && bkt) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-lg w-full bg-white rounded-2xl shadow-lg border border-gray-200 p-8 text-center">
          <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">📝</span>
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">{bkt.tieu_de}</h1>
          <div className="grid grid-cols-2 gap-3 my-6 text-sm">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-gray-500">Số câu</div>
              <div className="font-bold text-gray-900">{bkt.so_cau_hoi}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-gray-500">Thời gian</div>
              <div className="font-bold text-gray-900">{bkt.thoi_gian_lam_bai_phut ? `${bkt.thoi_gian_lam_bai_phut} phút` : 'Không giới hạn'}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-gray-500">Điểm đạt</div>
              <div className="font-bold text-gray-900">{bkt.diem_dat}%</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-gray-500">Trạng thái</div>
              <div className="font-bold text-green-600">Sẵn sàng</div>
            </div>
          </div>
          <button onClick={handleBatDau} disabled={loading}
            className="w-full px-6 py-3 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 transition-colors disabled:opacity-50">
            {loading ? 'Đang tải...' : 'Bắt đầu làm bài'}
          </button>
          <Link href={`/dao-tao/khoa-hoc/${khoaHocId}`}
            className="text-sm text-gray-500 hover:text-gray-700 mt-4 inline-block">Quay lại khóa học</Link>
        </div>
      </div>
    );
  }

  // =========================================================================
  // STATE 2: DANG LAM
  // =========================================================================
  if (state === 'DANG_LAM' && cauHoi.length > 0) {
    const current = cauHoi[currentIdx];
    const answered = Object.keys(traLoi).length;

    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
            <div className="text-sm font-medium text-gray-900">{bkt?.tieu_de}</div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">Câu {currentIdx + 1}/{cauHoi.length}</span>
              {timeLeft !== null && (
                <span className={`px-3 py-1 rounded-full text-sm font-mono font-bold ${
                  timeLeft < 300 ? 'bg-red-100 text-red-700 animate-pulse' : 'bg-blue-100 text-blue-700'
                }`}>
                  {formatTime(timeLeft)}
                </span>
              )}
            </div>
          </div>
          {/* Quick nav */}
          <div className="max-w-4xl mx-auto px-4 pb-3 flex gap-1 flex-wrap">
            {cauHoi.map((ch, i) => (
              <button key={ch.id} onClick={() => setCurrentIdx(i)}
                className={`w-8 h-8 rounded-md text-xs font-medium ${
                  i === currentIdx ? 'bg-blue-600 text-white' :
                  traLoi[ch.id] !== undefined ? 'bg-green-100 text-green-700 border border-green-300' :
                  'bg-gray-100 text-gray-500 border border-gray-200'
                }`}>
                {i + 1}
              </button>
            ))}
          </div>
        </div>

        {/* Question */}
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-medium text-gray-600">Câu {currentIdx + 1}</span>
              <span className="px-2 py-0.5 bg-blue-50 rounded text-xs text-blue-600">{current.loai}</span>
              <span className="text-xs text-gray-400">{current.diem} điểm</span>
            </div>
            <div className="text-gray-900 mb-6 whitespace-pre-wrap">{current.noi_dung}</div>

            {/* Answer input by type */}
            {(current.loai === 'TRAC_NGHIEM_1') && current.lua_chon && (
              <div className="space-y-2">
                {current.lua_chon.map((lc) => (
                  <label key={lc.key}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      traLoi[current.id] === lc.key ? 'bg-blue-50 border-blue-300' : 'border-gray-200 hover:bg-gray-50'
                    }`}>
                    <input type="radio" name={`q-${current.id}`} value={lc.key}
                      checked={traLoi[current.id] === lc.key}
                      onChange={() => setAnswer(current.id, lc.key)}
                      className="w-4 h-4 text-blue-600" />
                    <span className="font-medium text-gray-600 w-6">{lc.key}.</span>
                    <span className="text-gray-800">{lc.noi_dung}</span>
                  </label>
                ))}
              </div>
            )}

            {(current.loai === 'TRAC_NGHIEM_NHIEU') && current.lua_chon && (
              <div className="space-y-2">
                <p className="text-xs text-gray-500 mb-2">Chọn nhiều đáp án</p>
                {current.lua_chon.map((lc) => {
                  const selected = Array.isArray(traLoi[current.id]) ? traLoi[current.id] : [];
                  const isChecked = selected.includes(lc.key);
                  return (
                    <label key={lc.key}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        isChecked ? 'bg-blue-50 border-blue-300' : 'border-gray-200 hover:bg-gray-50'
                      }`}>
                      <input type="checkbox" checked={isChecked}
                        onChange={() => {
                          const newVal = isChecked ? selected.filter((k: string) => k !== lc.key) : [...selected, lc.key];
                          setAnswer(current.id, newVal);
                        }}
                        className="w-4 h-4 text-blue-600" />
                      <span className="font-medium text-gray-600 w-6">{lc.key}.</span>
                      <span className="text-gray-800">{lc.noi_dung}</span>
                    </label>
                  );
                })}
              </div>
            )}

            {current.loai === 'DUNG_SAI' && (
              <div className="flex gap-4">
                {[{ val: true, label: 'Đúng' }, { val: false, label: 'Sai' }].map(({ val, label }) => (
                  <label key={label}
                    className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border cursor-pointer transition-colors ${
                      traLoi[current.id] === val ? 'bg-blue-50 border-blue-300' : 'border-gray-200 hover:bg-gray-50'
                    }`}>
                    <input type="radio" name={`q-${current.id}`}
                      checked={traLoi[current.id] === val}
                      onChange={() => setAnswer(current.id, val)}
                      className="w-4 h-4 text-blue-600" />
                    <span className="font-medium">{label}</span>
                  </label>
                ))}
              </div>
            )}

            {current.loai === 'TU_LUAN' && (
              <textarea
                rows={6}
                value={traLoi[current.id] || ''}
                onChange={(e) => setAnswer(current.id, e.target.value)}
                placeholder="Nhập câu trả lời..."
                className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              />
            )}
          </div>

          {/* Navigation + Submit */}
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <button onClick={() => setCurrentIdx(Math.max(0, currentIdx - 1))}
                disabled={currentIdx === 0}
                className="px-4 py-2 border rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50">← Câu trước</button>
              <button onClick={() => setCurrentIdx(Math.min(cauHoi.length - 1, currentIdx + 1))}
                disabled={currentIdx === cauHoi.length - 1}
                className="px-4 py-2 border rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50">Câu tiếp →</button>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-500">{answered}/{cauHoi.length} đã trả lời</span>
              <button onClick={() => {
                if (confirm(`Bạn đã trả lời ${answered}/${cauHoi.length} câu. Nộp bài?`)) handleNopBai();
              }} disabled={submitting}
                className="px-6 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50">
                {submitting ? 'Đang nộp...' : 'Nộp bài'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // =========================================================================
  // STATE 3: DA NOP
  // =========================================================================
  if (state === 'DA_NOP' && ketQua) {
    const cheDoXem = ketQua.che_do_xem;
    const hasChiTiet = Array.isArray(ketQua.chi_tiet) && ketQua.chi_tiet.length > 0;

    return (
      <div className="min-h-screen bg-gray-50 py-6 px-4">
        <div className="max-w-2xl mx-auto space-y-5">

          {/* Score card */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 text-center">
            <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 ${
              ketQua.dat_yeu_cau ? 'bg-green-100' : 'bg-red-100'
            }`}>
              <span className="text-4xl">{ketQua.dat_yeu_cau ? '🎉' : '😔'}</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">
              {ketQua.dat_yeu_cau ? 'Chúc mừng! Bạn đã đạt!' : 'Chưa đạt yêu cầu'}
            </h1>
            <div className={`inline-block px-4 py-1 rounded-full text-sm font-bold mt-2 ${
              ketQua.dat_yeu_cau ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {ketQua.dat_yeu_cau ? 'ĐẠT' : 'CHƯA ĐẠT'}
            </div>

            <div className="grid grid-cols-3 gap-3 my-6">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-gray-900">{ketQua.diem}</div>
                <div className="text-xs text-gray-500">Điểm</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-green-600">{ketQua.so_cau_dung}</div>
                <div className="text-xs text-gray-500">Câu đúng</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-red-600">{ketQua.so_cau_sai}</div>
                <div className="text-xs text-gray-500">Câu sai</div>
              </div>
            </div>

            {/* Thông báo XEM_KHI_LAN_CUOI */}
            {ketQua.thong_bao && (
              <div className="mb-5 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-700 text-left flex gap-2">
                <span className="shrink-0">ℹ️</span>
                <span>{ketQua.thong_bao}</span>
              </div>
            )}

            <div className="flex gap-3">
              <Link href={`/dao-tao/khoa-hoc/${khoaHocId}`}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 text-center">
                Quay lại khóa học
              </Link>
              <button onClick={() => { setState('CHUA_BAT_DAU'); setKetQua(null); }}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700">
                Làm lại
              </button>
            </div>
          </div>

          {/* Chi tiết từng câu (khi có dữ liệu) */}
          {hasChiTiet && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h3 className="font-semibold text-gray-900 mb-4">
                Chi tiết từng câu
                {cheDoXem === 'CHI_XEM_CAU_SAI' && (
                  <span className="ml-2 text-xs font-normal text-gray-400">(chỉ hiện câu sai)</span>
                )}
              </h3>
              <div className="space-y-4">
                {ketQua.chi_tiet!.map((ct: any, i: number) => {
                  const isCorrect = ct.dung === true;
                  const isWrong   = ct.dung === false;

                  return (
                    <div key={i} className={`rounded-lg border p-4 ${
                      isCorrect ? 'bg-green-50 border-green-200' :
                      isWrong   ? 'bg-red-50 border-red-200' :
                                  'bg-yellow-50 border-yellow-200'
                    }`}>
                      {/* Header: số thứ tự + nội dung + điểm */}
                      <div className="flex items-start gap-2 mb-2">
                        <span className="text-lg shrink-0">
                          {isCorrect ? '✅' : isWrong ? '❌' : '⏳'}
                        </span>
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-medium text-gray-500">Câu {i + 1}</span>
                          {ct.noi_dung && (
                            <p className="text-sm text-gray-900 mt-0.5 whitespace-pre-wrap">{ct.noi_dung}</p>
                          )}
                        </div>
                        <span className={`text-sm font-bold shrink-0 ${
                          isCorrect ? 'text-green-700' : isWrong ? 'text-red-700' : 'text-yellow-700'
                        }`}>
                          {ct.diem_dat}/{ct.diem_toi_da}đ
                        </span>
                      </div>

                      {/* Đáp án người dùng đã chọn */}
                      {ct.tra_loi !== undefined && ct.tra_loi !== null && (
                        <div className={`mt-2 px-3 py-1.5 rounded text-xs ${
                          isCorrect ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          <span className="font-medium">Bạn chọn:</span>{' '}
                          {Array.isArray(ct.tra_loi)
                            ? ct.tra_loi.join(', ')
                            : typeof ct.tra_loi === 'boolean'
                            ? (ct.tra_loi ? 'Đúng' : 'Sai')
                            : String(ct.tra_loi)}
                        </div>
                      )}

                      {/* Đáp án đúng (chỉ hiện khi sai và có thông tin) */}
                      {ct.dap_an_dung !== undefined && ct.dap_an_dung !== null && isWrong && (
                        <div className="mt-1.5 px-3 py-1.5 rounded text-xs bg-green-100 text-green-800">
                          <span className="font-medium">Đáp án đúng:</span>{' '}
                          {Array.isArray(ct.dap_an_dung)
                            ? ct.dap_an_dung.join(', ')
                            : typeof ct.dap_an_dung === 'boolean'
                            ? (ct.dap_an_dung ? 'Đúng' : 'Sai')
                            : String(ct.dap_an_dung)}
                        </div>
                      )}

                      {/* Giải thích */}
                      {ct.giai_thich && (
                        <div className="mt-2 px-3 py-2 bg-blue-50 border border-blue-100 rounded text-xs text-blue-800">
                          <span className="font-medium">Giải thích:</span>{' '}{ct.giai_thich}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Thông báo khi không có chi tiết */}
          {!hasChiTiet && !ketQua.thong_bao && (cheDoXem === 'KHONG_CHO_XEM' || cheDoXem === 'CHI_XEM_DIEM') && (
            <div className="text-center py-5 text-sm text-gray-500 bg-white rounded-xl border border-gray-200 shadow-sm">
              {cheDoXem === 'KHONG_CHO_XEM'
                ? '🔒 Đề thi này không hiển thị kết quả chi tiết.'
                : '📊 Chỉ xem điểm tổng — kết quả chi tiết bị ẩn.'}
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
}

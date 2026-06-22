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
  const [violations, setViolations] = useState(0);
  const [resumeNotice, setResumeNotice] = useState<string | null>(null);
  // Anti-cheat: ép toàn màn hình + cảnh báo khi thoát
  const [fsWarning, setFsWarning] = useState(false);
  // Khóa bài khi tài khoản bị dùng để thi ở thiết bị khác (single-session)
  const [kicked, setKicked] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const handleNopBaiRef = useRef<(opts?: { retry?: number }) => Promise<void>>(async () => {});
  const traLoiRef = useRef(traLoi);
  const violationsRef = useRef(violations);
  const phienTokenRef = useRef<string | null>(null);
  const lastViolationAtRef = useRef(0);
  traLoiRef.current = traLoi;
  violationsRef.current = violations;

  // Bật ép toàn màn hình cho kỳ thi này? (mặc định bật)
  const yeuCauFullscreen = kyThi?.yeu_cau_toan_man_hinh !== false;

  // Phát hiện 409 (PHIEN_001) -> khóa bài trên thiết bị này
  const isPhienConflict = (err: any) =>
    err?.response?.status === 409 || err?.response?.data?.detail?.error?.code === 'PHIEN_001';

  const enterFullscreen = useCallback(async () => {
    try {
      const el: any = document.documentElement;
      if (!document.fullscreenElement && el.requestFullscreen) {
        await el.requestFullscreen();
      }
    } catch {
      /* trình duyệt từ chối — vẫn cho thi, chỉ ghi nhận vi phạm khi thoát */
    }
  }, []);

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

  // Timer — dem nguoc dua tren mocac dau tu server.
  useEffect(() => {
    if (state !== 'DANG_LAM' || timeLeft === null) return;
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev === null || prev <= 0) {
          if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
          handleNopBaiRef.current();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [state]);

  // Auto-save bai lam moi 30s (Bug C/D fix 27/05/2026): tranh mat bai khi treo
  // may / dong tab / mat mang. Backend bo qua silently neu khong phai DANG_THI.
  useEffect(() => {
    if (state !== 'DANG_LAM') return;
    const interval = setInterval(async () => {
      const entries = Object.entries(traLoiRef.current);
      if (entries.length === 0) return;
      try {
        await kyThiApi.luuNhap(kyThiId, {
          cau_tra_loi: entries.map(([cau_hoi_id, tra_loi]) => ({ cau_hoi_id, tra_loi })),
          so_lan_vi_pham: violationsRef.current,
        }, phienTokenRef.current || undefined);
      } catch (err: any) {
        // Tài khoản bị dùng để thi ở thiết bị khác -> khóa bài tại đây
        if (isPhienConflict(err)) setKicked(true);
        /* các lỗi autosave khác bỏ qua để không gây nhiễu cho user */
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [state, kyThiId]);

  // Canh bao khi user dong tab/F5 khi dang thi
  useEffect(() => {
    if (state !== 'DANG_LAM') return;
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = 'Bạn đang làm bài thi. Nếu thoát, có thể mất bài làm chưa lưu.';
      return e.returnValue;
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [state]);

  // Gắn cờ khi thoát toàn màn hình / chuyển tab (anti-cheat, có hiển thị cảnh báo).
  // Cooldown 2s tránh đếm trùng khi 1 hành động fire cả 2 event.
  useEffect(() => {
    if (state !== 'DANG_LAM') return;
    const COOLDOWN_MS = 2000;
    const ghiNhanViPham = () => {
      const now = Date.now();
      if (now - lastViolationAtRef.current < COOLDOWN_MS) return;
      lastViolationAtRef.current = now;
      setViolations(v => v + 1);
      setFsWarning(true);
    };
    const onFullscreenChange = () => {
      if (yeuCauFullscreen && !document.fullscreenElement) ghiNhanViPham();
    };
    const onVisibilityChange = () => {
      if (document.hidden) ghiNhanViPham();
    };
    document.addEventListener('fullscreenchange', onFullscreenChange);
    document.addEventListener('visibilitychange', onVisibilityChange);
    return () => {
      document.removeEventListener('fullscreenchange', onFullscreenChange);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, [state, yeuCauFullscreen]);

  // Bat dau thi
  const handleBatDau = async () => {
    try {
      setLoading(true);
      const res = await kyThiApi.batDau(kyThiId);
      const data = res.data.data;
      phienTokenRef.current = data.phien_token || null;
      setCauHoi(data.cau_hoi || []);
      setTimeLeft(data.thoi_gian_con_lai_giay);

      // Ép toàn màn hình (cần user-gesture — đang trong onClick nên hợp lệ)
      if (data.yeu_cau_toan_man_hinh !== false) {
        await enterFullscreen();
      }

      // Restore bai lam nhap neu dang tiep tuc (resume autosave)
      if (data.dang_tiep_tuc && Array.isArray(data.chi_tiet_nhap)) {
        const restored: Record<string, any> = {};
        for (const item of data.chi_tiet_nhap) {
          if (item?.cau_hoi_id && item.tra_loi != null) {
            restored[item.cau_hoi_id] = item.tra_loi;
          }
        }
        setTraLoi(restored);
        setViolations(data.so_lan_vi_pham || 0);
        const tongCau = data.cau_hoi?.length || 0;
        const soKhoiPhuc = Object.keys(restored).length;
        setResumeNotice(`🔄 Đã khôi phục bài làm dở: ${soKhoiPhuc}/${tongCau} câu đã trả lời.`);
        // Tu an thong bao sau 8 giay
        setTimeout(() => setResumeNotice(null), 8000);
      }

      setState('DANG_LAM');
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Không thể bắt đầu thi');
    } finally {
      setLoading(false);
    }
  };

  // Nop bai — co retry voi backoff (1s, 3s, 8s) cho 4 lan thu.
  const handleNopBai = useCallback(async (opts?: { retry?: number }) => {
    if (submitting) return;
    setSubmitting(true);
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }

    const cauTraLoi = cauHoi.map(ch => ({
      cau_hoi_id: ch.id,
      tra_loi: traLoiRef.current[ch.id] || null,
    }));

    const delays = [0, 1000, 3000, 8000];
    const maxAttempts = delays.length;
    const startAttempt = opts?.retry ?? 0;

    for (let attempt = startAttempt; attempt < maxAttempts; attempt++) {
      if (delays[attempt] > 0) {
        await new Promise(r => setTimeout(r, delays[attempt]));
      }
      try {
        await kyThiApi.nopBai(kyThiId, { cau_tra_loi: cauTraLoi }, phienTokenRef.current || undefined);
        if (document.fullscreenElement) { try { await document.exitFullscreen(); } catch { /* ignore */ } }
        setState('DA_NOP');
        setError(null);
        setSubmitting(false);
        return;
      } catch (err: any) {
        const code = err?.response?.data?.detail?.error?.code;
        // Tài khoản bị dùng để thi ở thiết bị khác -> khóa bài, dừng retry
        if (isPhienConflict(err)) {
          setKicked(true);
          setSubmitting(false);
          return;
        }
        // Bug B fix: backend tra DGNL_033 nghia la bai da nop tu lan submit
        // truoc (commit DB thanh cong, response mat). Coi nhu nop thanh cong.
        if (code === 'DGNL_033') {
          setState('DA_NOP');
          setError(null);
          setSubmitting(false);
          return;
        }
        // Loi nghiep vu khac (vd: DGNL_028 het han) — dung retry ngay
        if (code && code !== 'DGNL_033' && err?.response?.status && err.response.status < 500 && err.response.status !== 408 && err.response.status !== 429) {
          setError(err?.response?.data?.detail?.error?.message || 'Lỗi nộp bài');
          setSubmitting(false);
          return;
        }
        // Lan cuoi van fail -> hien loi, cho user thu lai thu cong
        if (attempt === maxAttempts - 1) {
          setError('Không nộp được bài sau nhiều lần thử. Vui lòng kiểm tra mạng và bấm "Nộp bài" lại.');
          setSubmitting(false);
          return;
        }
      }
    }
  }, [submitting, cauHoi, kyThiId]);

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

  // ===== BỊ KHÓA (tài khoản đang thi ở thiết bị khác) =====
  if (kicked) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md text-center">
          <div className="text-5xl mb-4">🔒</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Bài làm đã bị khóa</h2>
          <p className="text-gray-600 mb-6">
            Tài khoản của bạn đang được dùng để thi ở một thiết bị khác. Để đảm bảo
            tính minh bạch, bài làm trên thiết bị này đã bị khóa. Vui lòng tiếp tục
            trên thiết bị đang thi.
          </p>
          <button
            onClick={() => router.push('/dao-tao/ky-thi')}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Quay lại
          </button>
        </div>
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
    // Phan biet hanh vi theo trang thai thi sinh hien tai
    const ttTs = kyThi?.trang_thai_thi_sinh;
    const lanThi = kyThi?.lan_thi_hien_tai || 0;
    const soLanToiDa = kyThi?.so_lan_thi_toi_da || 1;
    const isResume = ttTs === 'DANG_THI';
    const isRetry = ttTs === 'DA_NOP' && lanThi < soLanToiDa;
    const hetLuot = ttTs === 'DA_NOP' && lanThi >= soLanToiDa;
    const isVang = ttTs === 'VANG';

    let btnLabel = 'Bắt đầu thi';
    let btnColor = 'bg-blue-600 hover:bg-blue-700';
    if (isResume) { btnLabel = '🔄 Tiếp tục làm bài'; btnColor = 'bg-amber-500 hover:bg-amber-600'; }
    else if (isRetry) { btnLabel = `Thi lại (lần ${lanThi + 1}/${soLanToiDa})`; btnColor = 'bg-indigo-600 hover:bg-indigo-700'; }

    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-lg">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">{kyThi?.ten_ky_thi}</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {isResume && (
            <div className="mb-4 p-4 bg-amber-50 border-2 border-amber-300 rounded-lg text-amber-900">
              <div className="font-semibold mb-1">🔄 Bài thi đang dở dang</div>
              <p className="text-sm">
                Bạn đã bắt đầu thi nhưng chưa nộp bài. Hệ thống sẽ khôi phục đáp án đã chọn và
                thời gian còn lại. Bấm <strong>"Tiếp tục làm bài"</strong> để vào lại.
              </p>
            </div>
          )}

          {hetLuot && (
            <div className="mb-4 p-4 bg-red-50 border-2 border-red-300 rounded-lg text-red-900">
              <div className="font-semibold mb-1">⛔ Đã hết lượt thi</div>
              <p className="text-sm">Bạn đã thi {lanThi}/{soLanToiDa} lần. Không thể thi thêm.</p>
            </div>
          )}

          {isVang && (
            <div className="mb-4 p-4 bg-red-50 border-2 border-red-300 rounded-lg text-red-900">
              <div className="font-semibold mb-1">⛔ Đã đánh dấu vắng</div>
              <p className="text-sm">Bạn không thể tham gia kỳ thi này.</p>
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
              <span className="text-gray-500">Số lượt thi</span>
              <span className="font-semibold">
                {ttTs ? `${lanThi}/${soLanToiDa}` : soLanToiDa}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">Trộn câu hỏi</span>
              <span>{kyThi?.tron_cau_hoi ? 'Có' : 'Không'}</span>
            </div>
          </div>

          {!isResume && !hetLuot && !isVang && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-6 text-sm text-yellow-800">
              <strong>Lưu ý:</strong> Sau khi bấm &ldquo;{btnLabel}&rdquo;, đồng hồ sẽ bắt đầu đếm ngược.
              Bài thi sẽ tự động nộp khi hết giờ.
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={handleBatDau}
              disabled={hetLuot || isVang}
              className={`flex-1 px-6 py-3 text-white rounded-lg font-semibold disabled:bg-gray-300 disabled:cursor-not-allowed ${btnColor}`}
            >
              {btnLabel}
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
      {/* Cảnh báo vi phạm khi thoát toàn màn hình / chuyển tab */}
      {fsWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-md text-center">
            <div className="text-4xl mb-3">⚠️</div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">Phát hiện thoát màn hình thi</h3>
            <p className="text-sm text-gray-600 mb-1">
              Bạn vừa thoát toàn màn hình hoặc chuyển sang cửa sổ khác. Hành vi này
              đã được hệ thống ghi nhận.
            </p>
            <p className="text-sm font-semibold text-red-600 mb-4">
              Số lần vi phạm: {violations}
            </p>
            <button
              onClick={async () => {
                if (yeuCauFullscreen) await enterFullscreen();
                setFsWarning(false);
              }}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold"
            >
              {yeuCauFullscreen ? 'Quay lại toàn màn hình' : 'Tiếp tục làm bài'}
            </button>
          </div>
        </div>
      )}
      {/* Resume notice — hien 8 giay sau khi khoi phuc bai lam do */}
      {resumeNotice && (
        <div className="bg-amber-50 border-b border-amber-300 px-4 py-2 text-sm text-amber-900 text-center font-medium">
          {resumeNotice}
        </div>
      )}
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
            {violations > 0 && (
              <div
                className="flex items-center gap-1 px-2.5 py-1 bg-red-50 border border-red-200 text-red-700 text-xs font-semibold rounded-full"
                title="Số lần thoát toàn màn hình / chuyển tab đã ghi nhận"
              >
                ⚠️ Vi phạm: {violations}
              </div>
            )}
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

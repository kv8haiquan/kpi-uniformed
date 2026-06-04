/**
 * src/app/(main)/dao-tao/khoa-hoc/[id]/kiem-tra/[bktId]/page.tsx
 * ================================================================
 * Lam bai kiem tra — 3 states: CHUA_BAT_DAU → DANG_LAM → DA_NOP.
 */

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { baiKiemTraApi } from '@/services/lms';
import type { IBaiKiemTra, ICauHoiForExam, IKetQuaResponse } from '@/types/lms';

type ExamState = 'CHUA_BAT_DAU' | 'DANG_LAM' | 'DA_NOP' | 'THUC_HANH_CHUA_NOP' | 'THUC_HANH_DA_NOP';

export default function KiemTraPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const khoaHocId = params.id as string;
  const bktId = params.bktId as string;
  // Preview flag: GV/QT xem thử → không lưu kết quả
  const isPreview = searchParams.get('preview') === '1' || searchParams.get('preview') === 'true';

  const [state, setState] = useState<ExamState>('CHUA_BAT_DAU');
  const [bkt, setBkt] = useState<IBaiKiemTra | null>(null);
  const [lichSu, setLichSu] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Loai BKT (detect sau khi bat-dau)
  const [loaiBKT, setLoaiBKT] = useState<'TRAC_NGHIEM' | 'THUC_HANH'>('TRAC_NGHIEM');

  // Thuc hanh state
  const [yeuCauBaiLam, setYeuCauBaiLam] = useState<string>('');
  const [thDungLuongMb, setThDungLuongMb] = useState<number>(500);
  const [thDinhDang, setThDinhDang] = useState<string>('mp4,mov,webm');
  const [thFile, setThFile] = useState<File | null>(null);
  const [thUploadPct, setThUploadPct] = useState<number | null>(null);
  const [thKetQua, setThKetQua] = useState<any>(null); // ket qua sau khi upload

  // Dang lam state
  const [cauHoi, setCauHoi] = useState<ICauHoiForExam[]>([]);
  const [ketQuaId, setKetQuaId] = useState('');
  const [currentIdx, setCurrentIdx] = useState(0);
  const [traLoi, setTraLoi] = useState<Record<string, any>>({});
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Silent audit — đếm thoát fullscreen / chuyển tab âm thầm cho TCCB tham khảo.
  // KHÔNG hiển thị cho user, KHÔNG auto-nộp, KHÔNG yêu cầu fullscreen.
  const [violations, setViolations] = useState(0);
  const lastViolationAtRef = useRef(0);
  const SILENT_COOLDOWN_MS = 2000;

  // Ket qua state
  const [ketQua, setKetQua] = useState<IKetQuaResponse | null>(null);

  // Load BKT info and lich su
  useEffect(() => {
    const load = async () => {
      try {
        const [bktRes, lsRes] = await Promise.all([
          baiKiemTraApi.chiTiet(bktId),
          baiKiemTraApi.lichSuThi(bktId).catch(() => null),
        ]);
        setBkt(bktRes.data.data);
        if (lsRes) setLichSu(lsRes.data.data);
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
          handleNopBaiRef.current();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [state]);

  // Silent audit — ghi nhận âm thầm số lần thoát fullscreen / chuyển tab.
  // Cooldown 2s chống đếm trùng khi 1 hành động fire cả 2 event.
  useEffect(() => {
    if (state !== 'DANG_LAM') return;
    if (isPreview) return;

    const tryCount = () => {
      const now = Date.now();
      if (now - lastViolationAtRef.current < SILENT_COOLDOWN_MS) return;
      lastViolationAtRef.current = now;
      setViolations(prev => prev + 1);
    };

    const onFullscreenChange = () => {
      if (!document.fullscreenElement) tryCount();
    };
    const onVisibilityChange = () => {
      if (document.hidden) tryCount();
    };

    document.addEventListener('fullscreenchange', onFullscreenChange);
    document.addEventListener('visibilitychange', onVisibilityChange);

    return () => {
      document.removeEventListener('fullscreenchange', onFullscreenChange);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, [state, isPreview]);

  // Fix Issue 3: Warn before closing tab/navigating away during exam
  useEffect(() => {
    if (state !== 'DANG_LAM') return;
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      // Modern browsers show their own message, but we set returnValue for compatibility
      e.returnValue = 'Bạn đang làm bài kiểm tra. Nếu thoát, bài làm có thể bị mất!';
      return e.returnValue;
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [state]);

  // Auto-save refs to access latest state
  const traLoiRef = useRef(traLoi);
  traLoiRef.current = traLoi;
  const violationsRef = useRef(violations);
  violationsRef.current = violations;

  // Auto-save every 30 seconds
  useEffect(() => {
    if (state !== 'DANG_LAM' || !ketQuaId) return;
    if (isPreview) return; // Preview: không auto-save
    const interval = setInterval(async () => {
      const currentTraLoi = traLoiRef.current;
      const entries = Object.entries(currentTraLoi);
      if (entries.length === 0) return;
      try {
        await baiKiemTraApi.luuNhap(bktId, {
          ket_qua_id: ketQuaId,
          tra_loi: entries.map(([cau_hoi_id, dap_an]) => ({ cau_hoi_id, dap_an })),
          so_lan_vi_pham: violationsRef.current,
        });
      } catch { /* ignore save errors */ }
    }, 30000);
    return () => clearInterval(interval);
  }, [state, ketQuaId, bktId]);

  // Bat dau thi
  const handleBatDau = async () => {
    try {
      setLoading(true);
      const res = await baiKiemTraApi.batDau(bktId, isPreview);
      const data = res.data.data;
      // Detect loai
      const loai = data.loai_bai_kiem_tra || 'TRAC_NGHIEM';
      setLoaiBKT(loai);

      if (loai === 'THUC_HANH') {
        setYeuCauBaiLam(data.yeu_cau_bai_lam || '');
        setThDungLuongMb(data.dung_luong_toi_da_mb || 500);
        setThDinhDang(data.dinh_dang_cho_phep || 'mp4,mov,webm');
        setKetQuaId(data.ket_qua_id || '');
        setState('THUC_HANH_CHUA_NOP');
        setLoading(false);
        return;
      }

      setCauHoi(data.cau_hoi);
      setKetQuaId(data.ket_qua_id || '');
      setCurrentIdx(0);

      // Restore draft answers if resuming
      if (data.dang_tiep_tuc && data.chi_tiet_nhap) {
        const restored: Record<string, any> = {};
        data.chi_tiet_nhap.forEach((item: any) => {
          restored[item.cau_hoi_id] = item.dap_an;
        });
        setTraLoi(restored);
        setViolations(data.so_lan_vi_pham || 0);
      } else {
        setTraLoi({});
      }

      // Calculate remaining time
      if (data.thoi_gian_phut) {
        if (data.dang_tiep_tuc && data.thoi_gian_da_lam_giay) {
          const remaining = data.thoi_gian_phut * 60 - data.thoi_gian_da_lam_giay;

          // Fix Issue 2: Auto-submit if time already expired while user was away
          if (remaining <= 0) {
            setTimeLeft(0);
            setState('DANG_LAM');
            // Use restored answers or empty
            const traLoiToSubmit = data.chi_tiet_nhap
              ? Object.fromEntries(data.chi_tiet_nhap.map((item: any) => [item.cau_hoi_id, item.dap_an]))
              : {};
            const traLoiList = Object.entries(traLoiToSubmit).map(([cau_hoi_id, dap_an]) => ({ cau_hoi_id, dap_an }));
            try {
              const res = await baiKiemTraApi.nopBai(bktId, { ket_qua_id: data.ket_qua_id, tra_loi: traLoiList });
              setKetQua(res.data.data);
              setState('DA_NOP');
            } catch {
              alert('Bài thi đã hết giờ. Vui lòng liên hệ quản trị viên.');
            }
            setLoading(false);
            return; // Don't continue to DANG_LAM state
          }

          setTimeLeft(Math.max(0, remaining));
        } else {
          setTimeLeft(data.thoi_gian_phut * 60);
        }
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
      if (isPreview) {
        // Chế độ xem thử — không gọi API, chỉ hiển thị mock result
        alert('Chế độ xem thử: bài không được chấm, không lưu kết quả.');
        setState('DA_NOP');
        setKetQua({
          id: 'preview',
          lan_thu: 0,
          diem: 0,
          so_cau_dung: 0,
          so_cau_sai: 0,
          dat_yeu_cau: false,
          che_do_xem: 'KHONG_CHO_XEM',
          thong_bao: 'Chế độ xem thử — không có kết quả thực',
          chi_tiet: null,
        } as any);
        if (timerRef.current) clearInterval(timerRef.current);
        return;
      }
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
  }, [traLoi, ketQuaId, bktId, submitting, isPreview]);

  // Fix Issue 1: Ref to avoid stale closure in timer auto-submit
  const handleNopBaiRef = useRef(handleNopBai);
  handleNopBaiRef.current = handleNopBai;

  // Nop video bai thuc hanh
  const handleNopVideo = useCallback(async () => {
    if (!thFile) {
      alert('Vui lòng chọn file video để nộp');
      return;
    }
    if (isPreview) {
      alert('Chế độ xem thử: không thể nộp bài thật. Dùng tài khoản học viên để upload.');
      return;
    }
    // Client-side check
    const ext = (thFile.name.split('.').pop() || '').toLowerCase();
    const allowedSet = new Set(
      thDinhDang.split(',').map((e) => e.trim().replace(/^\./, '').toLowerCase()).filter(Boolean)
    );
    if (!allowedSet.has(ext)) {
      alert(`Định dạng .${ext} không được chấp nhận. Cho phép: ${[...allowedSet].join(', ')}`);
      return;
    }
    if (thFile.size > thDungLuongMb * 1024 * 1024) {
      alert(`File vượt quá ${thDungLuongMb} MB`);
      return;
    }

    try {
      setThUploadPct(0);
      const res = await baiKiemTraApi.nopVideo(bktId, thFile, (pct) => setThUploadPct(pct));
      setThKetQua(res.data.data);
      setState('THUC_HANH_DA_NOP');
      setThUploadPct(null);
    } catch (err: any) {
      setThUploadPct(null);
      alert(err?.response?.data?.detail?.error?.message || 'Lỗi nộp video. Thử lại sau.');
    }
  }, [thFile, thDinhDang, thDungLuongMb, bktId, isPreview]);

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

  // Banner preview (hien o tat ca state khi isPreview=true)
  const PreviewBanner = () =>
    isPreview ? (
      <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2.5 text-sm text-yellow-800 flex items-center gap-2">
        <span>👁</span>
        <span className="font-medium">Chế độ xem thử (giảng viên)</span>
        <span className="text-yellow-700">— Bài không được chấm, không tính lượt, không lưu kết quả.</span>
      </div>
    ) : null;

  // =========================================================================
  // STATE 1: CHUA BAT DAU
  // =========================================================================
  if (state === 'CHUA_BAT_DAU' && bkt) {
    const laThucHanh = bkt.loai_bai_kiem_tra === 'THUC_HANH';
    return (
      <div className="min-h-screen bg-gray-50">
        <PreviewBanner />
        <div className="flex items-center justify-center p-4">
        <div className="max-w-lg w-full bg-white rounded-2xl shadow-lg border border-gray-200 p-8 text-center mt-6">
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 ${
            laThucHanh ? 'bg-orange-100' : 'bg-purple-100'
          }`}>
            <span className="text-3xl">{laThucHanh ? '🎬' : '📝'}</span>
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-1">{bkt.tieu_de}</h1>
          <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
            laThucHanh ? 'bg-orange-100 text-orange-700' : 'bg-blue-100 text-blue-700'
          }`}>
            {laThucHanh ? 'Thực hành — nộp video' : 'Trắc nghiệm'}
          </span>

          {laThucHanh ? (
            <div className="mt-5 space-y-2 text-sm text-left">
              {bkt.yeu_cau_bai_lam && (
                <div className="bg-orange-50 border border-orange-100 rounded-lg p-3">
                  <div className="text-xs font-semibold text-orange-700 mb-1 uppercase">Yêu cầu bài làm</div>
                  <div className="text-gray-800 whitespace-pre-wrap">{bkt.yeu_cau_bai_lam}</div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-gray-500 text-xs">Định dạng</div>
                  <div className="font-medium text-gray-900 text-sm">{bkt.dinh_dang_cho_phep || 'mp4,mov,webm'}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-gray-500 text-xs">Dung lượng tối đa</div>
                  <div className="font-medium text-gray-900 text-sm">{bkt.dung_luong_toi_da_mb ?? 500} MB</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-gray-500 text-xs">Điểm đạt</div>
                  <div className="font-medium text-gray-900 text-sm">{bkt.diem_dat}%</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-gray-500 text-xs">Số lần nộp</div>
                  <div className="font-medium text-gray-900 text-sm">
                    {lichSu ? `Còn ${bkt.so_lan_lam_toi_da - lichSu.so_lan_da_lam}/${bkt.so_lan_lam_toi_da}` : `${bkt.so_lan_lam_toi_da} lượt`}
                  </div>
                </div>
              </div>
            </div>
          ) : (
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
              <div className="text-gray-500">Lượt làm</div>
              <div className="font-bold text-gray-900">
                {lichSu ? `Còn ${bkt.so_lan_lam_toi_da - lichSu.so_lan_da_lam}/${bkt.so_lan_lam_toi_da}` : `${bkt.so_lan_lam_toi_da} lượt`}
              </div>
            </div>
            {bkt.gio_mo && bkt.gio_dong && (
              <div className="bg-gray-50 rounded-lg p-3 col-span-2">
                <div className="text-gray-500">Khung giờ</div>
                <div className="font-bold text-gray-900">{bkt.gio_mo} - {bkt.gio_dong}</div>
              </div>
            )}
          </div>
          )}

          <button onClick={handleBatDau} disabled={loading}
            className={`w-full px-6 py-3 text-white rounded-xl font-semibold transition-colors disabled:opacity-50 mt-5 ${
              laThucHanh ? 'bg-orange-600 hover:bg-orange-700' : 'bg-purple-600 hover:bg-purple-700'
            }`}>
            {loading ? 'Đang tải...' : laThucHanh ? 'Bắt đầu nộp video' : 'Bắt đầu làm bài'}
          </button>
          <Link href={`/dao-tao/khoa-hoc/${khoaHocId}`}
            className="text-sm text-gray-500 hover:text-gray-700 mt-4 inline-block">Quay lại khóa học</Link>
        </div>
        </div>
      </div>
    );
  }

  // =========================================================================
  // STATE: THUC_HANH_CHUA_NOP — form upload video
  // =========================================================================
  if (state === 'THUC_HANH_CHUA_NOP' && bkt) {
    return (
      <div className="min-h-screen bg-gray-50">
        <PreviewBanner />
        <div className="max-w-2xl mx-auto p-4">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mt-4">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-2xl">🎬</span>
              <div className="flex-1 min-w-0">
                <h1 className="text-lg font-bold text-gray-900 truncate">{bkt.tieu_de}</h1>
                <p className="text-xs text-gray-500">Bài thực hành — nộp video</p>
              </div>
            </div>

            {yeuCauBaiLam && (
              <div className="bg-orange-50 border border-orange-100 rounded-lg p-4 mb-4">
                <div className="text-xs font-semibold text-orange-700 mb-1 uppercase">Yêu cầu bài làm</div>
                <div className="text-sm text-gray-800 whitespace-pre-wrap">{yeuCauBaiLam}</div>
              </div>
            )}

            <div className="flex gap-4 text-xs text-gray-500 mb-4">
              <span>📦 Tối đa: <strong className="text-gray-700">{thDungLuongMb} MB</strong></span>
              <span>🎬 Định dạng: <strong className="text-gray-700">{thDinhDang}</strong></span>
            </div>

            {/* Chọn file */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              {thFile ? (
                <div className="space-y-2">
                  <div className="text-3xl">🎬</div>
                  <div className="text-sm font-medium text-gray-900 truncate">{thFile.name}</div>
                  <div className="text-xs text-gray-500">
                    {(thFile.size / (1024 * 1024)).toFixed(2)} MB · {thFile.type || 'video'}
                  </div>
                  <button
                    onClick={() => setThFile(null)}
                    disabled={thUploadPct !== null}
                    className="text-xs text-gray-500 hover:text-red-600 disabled:opacity-50"
                  >
                    Đổi file
                  </button>
                </div>
              ) : (
                <label className="cursor-pointer">
                  <input
                    type="file"
                    accept={thDinhDang.split(',').map((e) => '.' + e.trim().replace(/^\./, '')).join(',')}
                    className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) setThFile(f);
                      e.target.value = '';
                    }}
                  />
                  <div className="text-4xl mb-2">📂</div>
                  <div className="text-sm font-medium text-gray-700">Nhấn để chọn video bài làm</div>
                  <div className="text-xs text-gray-400 mt-1">{thDinhDang} · tối đa {thDungLuongMb} MB</div>
                </label>
              )}
            </div>

            {thUploadPct !== null && (
              <div className="mt-4">
                <div className="text-sm text-blue-700 mb-1">Đang tải lên... {thUploadPct}%</div>
                <div className="w-full bg-blue-100 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full transition-all" style={{ width: `${thUploadPct}%` }} />
                </div>
              </div>
            )}

            <div className="flex justify-between items-center mt-5">
              <Link href={`/dao-tao/khoa-hoc/${khoaHocId}`}
                className="text-sm text-gray-500 hover:text-gray-700">← Quay lại khóa học</Link>
              <button
                onClick={handleNopVideo}
                disabled={!thFile || thUploadPct !== null || isPreview}
                className="px-6 py-2.5 bg-orange-600 text-white rounded-lg text-sm font-semibold hover:bg-orange-700 disabled:opacity-50"
                title={isPreview ? 'Chế độ xem thử: không thể nộp bài' : ''}
              >
                {thUploadPct !== null ? `Đang tải... ${thUploadPct}%` : 'Nộp bài'}
              </button>
            </div>

            {isPreview && (
              <p className="text-xs text-yellow-700 mt-3 text-center">
                Đang ở chế độ xem thử — nút "Nộp bài" bị khóa. Dùng tài khoản học viên để nộp thật.
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // =========================================================================
  // STATE: THUC_HANH_DA_NOP — da nop, cho cham
  // =========================================================================
  if (state === 'THUC_HANH_DA_NOP' && bkt) {
    return (
      <div className="min-h-screen bg-gray-50">
        <PreviewBanner />
        <div className="max-w-2xl mx-auto p-4">
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 text-center mt-6">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">✅</span>
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">Đã nộp bài!</h1>
            <p className="text-sm text-gray-600 mb-1">
              Video bài làm của bạn đã được gửi đến giảng viên.
            </p>
            <p className="text-sm text-gray-500 mb-6">
              Trạng thái: <span className="inline-block px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 font-medium text-xs">Chờ chấm</span>
            </p>

            {thKetQua && (
              <div className="bg-gray-50 rounded-lg p-4 text-left text-sm space-y-2 mb-5">
                <div><span className="text-gray-500">Tên file:</span> <span className="font-medium text-gray-800">{thKetQua.bai_nop_ten_file}</span></div>
                {thKetQua.bai_nop_size_bytes && (
                  <div><span className="text-gray-500">Dung lượng:</span> <span className="font-medium text-gray-800">{(thKetQua.bai_nop_size_bytes / (1024 * 1024)).toFixed(2)} MB</span></div>
                )}
                <div><span className="text-gray-500">Lần nộp:</span> <span className="font-medium text-gray-800">{thKetQua.lan_thu}</span></div>
                {thKetQua.bai_nop_url && (
                  <div>
                    <span className="text-gray-500">Bài nộp:</span>{' '}
                    <a href={thKetQua.bai_nop_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                      Xem lại video đã nộp ↗
                    </a>
                  </div>
                )}
              </div>
            )}

            <Link href={`/dao-tao/khoa-hoc/${khoaHocId}`}
              className="inline-block px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
              Quay lại khóa học
            </Link>
          </div>
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
        <PreviewBanner />
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
      <div className="min-h-screen bg-gray-50">
        <PreviewBanner />
        <div className="py-6 px-4">
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
                  const formatAnswer = (v: any): string => {
                    if (v === null || v === undefined) return 'Không trả lời';
                    let raw: any = v;
                    if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
                      if ('dap_an' in raw) raw = raw.dap_an;
                      else if ('dap_an_dung' in raw) raw = raw.dap_an_dung;
                      else if ('goi_y' in raw) raw = raw.goi_y;
                    }
                    if (raw === null || raw === undefined || raw === '') return 'Không trả lời';
                    if (Array.isArray(raw)) return raw.length ? raw.join(', ') : 'Không trả lời';
                    if (typeof raw === 'boolean') return raw ? 'Đúng' : 'Sai';
                    if (typeof raw === 'object') return JSON.stringify(raw);
                    return String(raw);
                  };

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
                          {formatAnswer(ct.tra_loi)}
                        </div>
                      )}

                      {/* Đáp án đúng (chỉ hiện khi sai và có thông tin) */}
                      {ct.dap_an_dung !== undefined && ct.dap_an_dung !== null && isWrong && (
                        <div className="mt-1.5 px-3 py-1.5 rounded text-xs bg-green-100 text-green-800">
                          <span className="font-medium">Đáp án đúng:</span>{' '}
                          {formatAnswer(ct.dap_an_dung)}
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
      </div>
    );
  }

  return null;
}

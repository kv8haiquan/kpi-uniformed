/**
 * /hop-khong-giay/diem-danh-qr — landing page khi CBCC scan QR.
 *
 * G4-fix-5.b (01/05/2026):
 * Flow: chu_toa/thu_ky sinh QR ở tab Điểm danh → CBCC scan camera điện thoại
 * → mở URL này (kèm token query) → auto call /diem-danh/quet → hiện kết quả.
 *
 * Mobile-first: full-screen card với icon to, dễ đọc trên màn hình nhỏ.
 */

'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  CheckCircle2, XCircle, Loader2, Calendar, Clock, AlertTriangle,
} from 'lucide-react';
import { diemDanhApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import {
  TRANG_THAI_DIEM_DANH_COLOR as TRANG_THAI_COLOR,
  TRANG_THAI_DIEM_DANH_LABELS as TRANG_THAI_LABELS,
  type IDiemDanh,
} from '@/types/hkg';

type Status = 'pending' | 'submitting' | 'success' | 'error' | 'no_token';

export default function DiemDanhQrPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<Status>('pending');
  const [result, setResult] = useState<IDiemDanh | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (!token) {
      setStatus('no_token');
      return;
    }

    let cancelled = false;
    const submit = async () => {
      setStatus('submitting');
      try {
        const dd = await diemDanhApi.quet(token);
        if (!cancelled) {
          setResult(dd);
          setStatus('success');
        }
      } catch (e: unknown) {
        if (!cancelled) {
          const code = (e as { response?: { data?: { detail?: { error?: { code?: string } } } } })
            ?.response?.data?.detail?.error?.code;
          // Idempotent: 409 ALREADY_CHECKED_IN → vẫn là success behaviorally
          if (code === 'ALREADY_CHECKED_IN') {
            setError('Bạn đã điểm danh cuộc họp này rồi.');
          } else {
            setError(errMsg(e, 'Lỗi điểm danh'));
          }
          setStatus('error');
        }
      }
    };
    submit();
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className="min-h-[calc(100vh-200px)] flex items-center justify-center p-4">
      <div className="bg-white border-2 rounded-lg shadow-lg p-8 max-w-md w-full text-center space-y-4">
        {status === 'no_token' && (
          <>
            <AlertTriangle className="w-16 h-16 text-amber-500 mx-auto" />
            <h2 className="text-xl font-semibold text-gray-800">
              Thiếu token
            </h2>
            <p className="text-sm text-gray-600">
              URL không chứa token điểm danh. Vui lòng scan QR từ chu_toa/thu_ky cuộc họp.
            </p>
          </>
        )}

        {status === 'submitting' && (
          <>
            <Loader2 className="w-16 h-16 text-blue-600 mx-auto animate-spin" />
            <h2 className="text-xl font-semibold text-gray-800">
              Đang điểm danh...
            </h2>
            <p className="text-sm text-gray-600">Vui lòng đợi vài giây</p>
          </>
        )}

        {status === 'success' && result && (
          <>
            <CheckCircle2 className="w-20 h-20 text-green-600 mx-auto" />
            <h2 className="text-2xl font-bold text-gray-800">
              Điểm danh thành công!
            </h2>
            <div className="space-y-2 text-sm text-gray-700">
              <div className="flex items-center justify-center gap-2">
                <span className={`px-3 py-1 rounded-full font-semibold ${TRANG_THAI_COLOR[result.trang_thai]} bg-opacity-10`}>
                  {TRANG_THAI_LABELS[result.trang_thai]}
                </span>
              </div>
              {result.gio_diem_danh && (
                <div className="flex items-center justify-center gap-2 text-gray-600">
                  <Clock className="w-4 h-4" />
                  {new Date(result.gio_diem_danh).toLocaleString('vi-VN')}
                </div>
              )}
            </div>

            <div className="pt-4 border-t">
              <button
                onClick={() => router.push(`/hop-khong-giay/chi-tiet/${result.cuoc_hop_id}`)}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
              >
                Xem chi tiết cuộc họp
              </button>
            </div>
          </>
        )}

        {status === 'error' && (
          <>
            <XCircle className="w-16 h-16 text-red-600 mx-auto" />
            <h2 className="text-xl font-semibold text-gray-800">
              Không thể điểm danh
            </h2>
            <p className="text-sm text-red-700">{error}</p>
            <div className="pt-4 border-t">
              <button
                onClick={() => router.push('/hop-khong-giay')}
                className="w-full px-4 py-2 bg-gray-100 border rounded font-medium hover:bg-gray-200"
              >
                Quay về danh sách cuộc họp
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

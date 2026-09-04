/**
 * Tab Điểm danh — sinh QR + tự điểm danh + bảng chi tiết từng thành phần.
 *
 * G4-fix-7 (01/05/2026):
 * - Ẩn "Sinh QR" cho CBCC thường (canEdit only)
 * - Pre-compute window status: nếu chưa đến giờ → message "Chưa đến giờ họp"
 * - Hide "Tôi có mặt" cho CBCC ngoài thành phần (myStatus.is_invited check)
 *
 * 04/09/2026: 6 ô số tổng hợp trước đây chỉ cho biết BAO NHIÊU người có mặt
 * mà không cho biết là AI. Nay chuyển hẳn vào BangDiemDanhChiTiet — ở đó
 * chúng thành nút lọc cho bảng danh sách, kèm chấm tay và xuất Excel.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { QrCode, X, CheckCircle2, Loader2, Clock } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { diemDanhApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import {
  HINH_THUC_DIEM_DANH_LABELS,
  TRANG_THAI_DIEM_DANH_LABELS,
  type IMyStatus,
  type IQRTokenResponse,
} from '@/types/hkg';
import { useMeeting } from '@/components/hkg/MeetingContext';
import BangDiemDanhChiTiet from '@/components/hkg/BangDiemDanhChiTiet';

export default function DiemDanhTabPage() {
  const { id } = useParams<{ id: string }>();
  const { isLocked, canEdit } = useMeeting();
  const [qr, setQr] = useState<IQRTokenResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [myStatus, setMyStatus] = useState<IMyStatus | null>(null);
  const [checkinBusy, setCheckinBusy] = useState(false);
  // Đổi khoá này là buộc bảng chi tiết dựng lại và nạp số liệu mới. Bảng tự
  // tính 6 ô số từ danh sách của nó nên không cần gọi thêm endpoint tổng hợp.
  const [khoaBang, setKhoaBang] = useState(0);

  const fetchMyStatus = useCallback(async () => {
    try {
      setMyStatus(await diemDanhApi.myStatus(id));
    } catch {
      // silent — non-critical
    }
  }, [id]);

  useEffect(() => {
    fetchMyStatus();
  }, [fetchMyStatus]);

  const handleSelfCheckin = async () => {
    setCheckinBusy(true);
    setError(null);
    try {
      await diemDanhApi.tuDiemDanh(id);
      await fetchMyStatus();
      setKhoaBang((n) => n + 1);
    } catch (e: unknown) {
      setError(errMsg(e, 'Không thể điểm danh'));
    } finally {
      setCheckinBusy(false);
    }
  };

  const handleSinhQr = async () => {
    setError(null);
    try {
      const r = await diemDanhApi.qrToken(id);
      setQr(r);
    } catch (e: unknown) { setError(errMsg(e)); }
  };

  const qrFullUrl = qr
    ? `${typeof window !== 'undefined' ? window.location.origin : ''}${qr.qr_url}`
    : '';

  // Format giờ Việt Nam friendly
  const fmtVN = (iso: string) => {
    const d = new Date(iso);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')} ngày ${d.toLocaleDateString('vi-VN')}`;
  };

  return (
    <div className="bg-white border rounded p-6 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Điểm danh</h3>
        {/* G4-fix-7: ẨN "Sinh QR" cho CBCC thường */}
        {canEdit && !isLocked && (
          <button
            onClick={handleSinhQr}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            <QrCode className="w-4 h-4" />
            Sinh QR điểm danh
          </button>
        )}
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
          {error}
        </div>
      )}

      {/* Block "điểm danh của tôi" — chỉ hiện cho CBCC trong thành phần */}
      {myStatus?.is_invited && !isLocked && (
        <div className={`p-4 border rounded ${
          myStatus.da_diem_danh
            ? 'bg-green-50 border-green-300'
            : myStatus.window_status === 'NOT_YET_OPEN'
              ? 'bg-amber-50 border-amber-300'
              : myStatus.window_status === 'CLOSED'
                ? 'bg-gray-50 border-gray-300'
                : 'bg-blue-50 border-blue-300'
        }`}>
          {myStatus.da_diem_danh ? (
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-8 h-8 text-green-600" />
              <div>
                <p className="font-medium text-green-900">
                  Bạn đã điểm danh
                  {myStatus.trang_thai
                    && ` — ${TRANG_THAI_DIEM_DANH_LABELS[myStatus.trang_thai]}`}
                </p>
                <p className="text-xs text-green-700 mt-0.5">
                  {myStatus.hinh_thuc
                    ? HINH_THUC_DIEM_DANH_LABELS[myStatus.hinh_thuc]
                    : ''}
                  {myStatus.gio_diem_danh && (
                    <> · {new Date(myStatus.gio_diem_danh).toLocaleString('vi-VN')}</>
                  )}
                </p>
              </div>
            </div>
          ) : myStatus.window_status === 'NOT_YET_OPEN' ? (
            <div className="flex items-center gap-3">
              <Clock className="w-8 h-8 text-amber-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-amber-900">Chưa đến giờ điểm danh</p>
                <p className="text-xs text-amber-700 mt-0.5">
                  Mở điểm danh từ <strong>{fmtVN(myStatus.open_at)}</strong>.
                  Bạn có thể quay lại tab này sau.
                </p>
              </div>
            </div>
          ) : myStatus.window_status === 'CLOSED' ? (
            <div className="flex items-center gap-3">
              <Clock className="w-8 h-8 text-gray-500 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-700">Đã đóng điểm danh</p>
                <p className="text-xs text-gray-600 mt-0.5">
                  Cuộc họp đã kết thúc lúc <strong>{fmtVN(myStatus.close_at)}</strong>.
                  Liên hệ thư ký nếu cần điểm danh bổ sung.
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <p className="font-medium text-blue-900">Bạn chưa điểm danh</p>
                <p className="text-xs text-blue-700 mt-0.5">
                  Bấm "Tôi có mặt" để tự điểm danh, hoặc quét QR từ chu_toa/thư ký.
                </p>
              </div>
              <button
                onClick={handleSelfCheckin}
                disabled={checkinBusy}
                className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded font-medium hover:bg-green-700 disabled:opacity-50"
              >
                {checkinBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                Tôi có mặt
              </button>
            </div>
          )}
        </div>
      )}

      {qr && (
        <div className="p-6 bg-blue-50 border border-blue-200 rounded">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-base font-medium text-blue-900">QR điểm danh</p>
              <p className="text-xs text-blue-700 mt-1">
                CBCC scan QR bằng camera điện thoại để điểm danh.
                Token hết hạn sau {Math.round(qr.expires_in_seconds / 60)} phút.
              </p>
            </div>
            <button
              onClick={() => setQr(null)}
              className="p-1 hover:bg-blue-100 rounded text-blue-700"
              title="Đóng"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-col items-center gap-3">
            <div className="bg-white p-4 rounded border-2 border-blue-300">
              <QRCodeSVG
                value={qrFullUrl}
                size={256}
                level="M"
                includeMargin={false}
              />
            </div>
            <p className="text-xs text-gray-600 break-all max-w-md text-center">
              {qrFullUrl}
            </p>
          </div>
        </div>
      )}

      {/* Bảng chi tiết chỉ dành cho ban tổ chức — CBCC thường không xem được
          ai có mặt/ai vắng của cả cuộc họp (máy chủ cũng chặn 403). */}
      {canEdit && (
        <BangDiemDanhChiTiet
          key={khoaBang}
          cuocHopId={id}
          onSaved={fetchMyStatus}
        />
      )}
    </div>
  );
}

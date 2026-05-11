/**
 * Tab Tổng quan — actions: gửi giấy mời, hủy, xác nhận tham dự.
 */

'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Send, X, CheckCircle, Loader2, Users, BellRing } from 'lucide-react';
import { cuocHopApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import { useMeeting } from '@/components/hkg/MeetingContext';
import SuaThanhPhanModal from '@/components/hkg/SuaThanhPhanModal';

export default function TongQuanPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { ch, isCancelled, isLocked, canEdit, refresh } = useMeeting();
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
  const [showSuaThanhPhan, setShowSuaThanhPhan] = useState(false);

  const handleAction = async (
    action: 'gui-giay-moi' | 'huy' | 'xac-nhan',
  ) => {
    setBusy(action);
    setMsg(null);
    try {
      if (action === 'gui-giay-moi') {
        const r = await cuocHopApi.guiGiayMoi(id);
        setMsg({
          type: 'ok',
          text: `Đã gửi thông báo tới ${r.so_giay_moi_da_gui} người tham dự`,
        });
        await refresh(); // cập nhật trang_thai → DA_THONG_BAO để đổi nhãn nút
      } else if (action === 'huy') {
        const ly_do = window.prompt('Lý do hủy?') || 'Không nhập';
        await cuocHopApi.huy(id, ly_do);
        setMsg({ type: 'ok', text: 'Đã hủy cuộc họp' });
        await refresh(); // refresh context để banner đỏ + isLocked tabs
        setTimeout(() => router.push('/hop-khong-giay'), 1500);
      } else if (action === 'xac-nhan') {
        await cuocHopApi.xacNhanThamDu(id, { xac_nhan: 'THAM_DU' });
        setMsg({ type: 'ok', text: 'Đã xác nhận tham dự' });
      }
    } catch (e: unknown) {
      setMsg({ type: 'err', text: errMsg(e, 'Lỗi thao tác') });
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="bg-white border rounded p-6 space-y-4">
      <h3 className="text-lg font-medium">Hành động</h3>
      {isCancelled ? (
        <p className="text-sm text-gray-500 italic">
          Cuộc họp đã hủy — không có hành động khả dụng.
        </p>
      ) : (
        <div className="flex flex-wrap gap-3">
          {/* CBCC thường: chỉ thấy "Xác nhận tham dự" */}
          <button
            onClick={() => handleAction('xac-nhan')}
            disabled={busy !== null || isLocked}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50"
          >
            <CheckCircle className="w-4 h-4" />
            Xác nhận tham dự
          </button>

          {/* Organizer-only buttons (G4-fix-7: ẨN cho CBCC) */}
          {canEdit && (
            <>
              {ch?.trang_thai === 'DA_THONG_BAO' ? (
                <button
                  type="button"
                  disabled
                  title="Giấy mời đã được gửi tới toàn bộ thành phần"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 border border-green-300 rounded text-sm cursor-not-allowed"
                >
                  <BellRing className="w-4 h-4" />
                  Đã gửi thông báo
                </button>
              ) : (
                <button
                  onClick={() => handleAction('gui-giay-moi')}
                  disabled={busy !== null || isLocked}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {busy === 'gui-giay-moi' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  Gửi giấy mời
                </button>
              )}
              <button
                onClick={() => setShowSuaThanhPhan(true)}
                disabled={busy !== null || isLocked}
                className="inline-flex items-center gap-2 px-4 py-2 border border-blue-300 text-blue-700 rounded text-sm hover:bg-blue-50 disabled:opacity-50"
              >
                <Users className="w-4 h-4" />
                Sửa thành phần
              </button>
              <button
                onClick={() => handleAction('huy')}
                disabled={busy !== null || isLocked}
                className="inline-flex items-center gap-2 px-4 py-2 border border-red-300 text-red-700 rounded text-sm hover:bg-red-50 disabled:opacity-50"
              >
                <X className="w-4 h-4" />
                Hủy cuộc họp
              </button>
            </>
          )}
        </div>
      )}

      {showSuaThanhPhan && ch && (
        <SuaThanhPhanModal
          ch={ch}
          onClose={() => setShowSuaThanhPhan(false)}
          onSaved={() => {
            setMsg({ type: 'ok', text: 'Đã lưu thành phần' });
            refresh();
          }}
        />
      )}

      {msg && (
        <div
          className={`p-3 rounded text-sm ${
            msg.type === 'ok'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {msg.text}
        </div>
      )}
    </div>
  );
}

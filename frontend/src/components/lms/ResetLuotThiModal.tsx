/**
 * src/components/lms/ResetLuotThiModal.tsx
 * =========================================
 * Modal reset bài thi ĐGNL của 1 thí sinh — chỉ QT_DAO_TAO.
 *
 * Dùng khi có người đăng nhập nhầm tài khoản làm bài, hoặc sự cố giữa chừng.
 * Đây là thao tác xóa dữ liệu thật nên màn hình bắt buộc: chọn rõ mức reset,
 * nhập lý do, và nhìn thấy chính xác cái gì sẽ mất trước khi bấm.
 */

'use client';

import { useState } from 'react';
import { kyThiApi } from '@/services/lms';
import type { IThiSinh } from '@/types/lms';

type LoaiReset = 'XOA_SACH' | 'MO_KHOA_LUOT';

export default function ResetLuotThiModal({
  kyThiId,
  thiSinh,
  soLanThiToiDa,
  onClose,
  onDone,
}: {
  kyThiId: string;
  thiSinh: IThiSinh;
  soLanThiToiDa?: number;
  onClose: () => void;
  onDone: () => void;
}) {
  const [loaiReset, setLoaiReset] = useState<LoaiReset>('XOA_SACH');
  const [lyDo, setLyDo] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lanHienTai = thiSinh.lan_thi_hien_tai || 0;
  const toiDa = soLanThiToiDa || 1;
  const hetLuot = lanHienTai >= toiDa;
  // Mở khóa chỉ có nghĩa khi: đã nộp, đang bị khóa, và còn lượt chưa dùng
  const moKhoaDuoc = thiSinh.trang_thai === 'DA_NOP' && !!thiSinh.da_xac_nhan && !hetLuot;
  const lyDoHopLe = lyDo.trim().length >= 5;

  const handleSubmit = async () => {
    if (!lyDoHopLe) {
      setError('Vui lòng nhập lý do (ít nhất 5 ký tự) — nhật ký cần truy nguyên được');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await kyThiApi.resetLuotThi(kyThiId, thiSinh.cong_chuc_id, {
        loai_reset: loaiReset,
        ly_do: lyDo.trim(),
      });
      onDone();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Không thể reset lượt thi');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg max-h-[85vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-lg font-bold text-gray-900">♻️ Reset lượt thi</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          {thiSinh.ho_ten} <span className="font-mono text-xs">({thiSinh.ma_cc})</span>
        </p>

        {/* Hiện trạng — để người thao tác biết mình đang xóa cái gì */}
        <div className="mb-4 p-3 bg-gray-50 border rounded-lg text-sm grid grid-cols-2 gap-y-1">
          <span className="text-gray-500">Trạng thái</span>
          <span className="font-medium">{thiSinh.trang_thai}</span>
          <span className="text-gray-500">Lượt đã dùng</span>
          <span className="font-medium">{lanHienTai}/{toiDa}</span>
          <span className="text-gray-500">Điểm hiện tại</span>
          <span className="font-medium">
            {thiSinh.diem_tong !== null && thiSinh.diem_tong !== undefined ? `${thiSinh.diem_tong}%` : '—'}
          </span>
          <span className="text-gray-500">Đã chốt ca thi</span>
          <span className="font-medium">{thiSinh.da_xac_nhan ? 'Có (đang bị khóa)' : 'Chưa'}</span>
        </div>

        {/* Chon muc reset */}
        <div className="space-y-2 mb-4">
          <label
            className={`flex gap-3 p-3 border rounded-lg cursor-pointer ${
              loaiReset === 'XOA_SACH' ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
            }`}
          >
            <input
              type="radio"
              className="mt-1"
              checked={loaiReset === 'XOA_SACH'}
              onChange={() => setLoaiReset('XOA_SACH')}
            />
            <span className="text-sm">
              <span className="font-semibold block">Xóa sạch — thi lại từ đầu</span>
              <span className="text-gray-600">
                Xóa điểm, bài làm, lịch sử các lần thi và số lần vi phạm. Thí sinh về trạng thái
                chưa thi, có lại đủ {toiDa} lượt. Kết quả người làm nhầm biến mất khỏi báo cáo.
              </span>
            </span>
          </label>

          <label
            className={`flex gap-3 p-3 border rounded-lg ${
              !moKhoaDuoc
                ? 'opacity-50 cursor-not-allowed'
                : loaiReset === 'MO_KHOA_LUOT'
                  ? 'border-blue-500 bg-blue-50 cursor-pointer'
                  : 'hover:bg-gray-50 cursor-pointer'
            }`}
          >
            <input
              type="radio"
              className="mt-1"
              disabled={!moKhoaDuoc}
              checked={loaiReset === 'MO_KHOA_LUOT'}
              onChange={() => setLoaiReset('MO_KHOA_LUOT')}
            />
            <span className="text-sm">
              <span className="font-semibold block">Chỉ mở khóa lượt tiếp theo</span>
              <span className="text-gray-600">
                Giữ nguyên kết quả đã có, chỉ gỡ chốt ca thi để thí sinh vào thi lượt sau.
                Điểm cuối cùng là điểm CAO NHẤT giữa các lần.
              </span>
              {!moKhoaDuoc && (
                <span className="block mt-1 text-xs text-amber-700">
                  {thiSinh.trang_thai !== 'DA_NOP'
                    ? 'Không dùng được: thí sinh chưa nộp bài.'
                    : hetLuot
                      ? `Không dùng được: đã dùng hết ${toiDa}/${toiDa} lượt.`
                      : 'Không dùng được: thí sinh chưa bị khóa, vẫn vào thi lại được.'}
                </span>
              )}
            </span>
          </label>
        </div>

        {/* Ly do — bat buoc */}
        <label className="block mb-4">
          <span className="text-sm font-medium text-gray-700">
            Lý do <span className="text-red-500">*</span>
          </span>
          <textarea
            value={lyDo}
            onChange={(e) => setLyDo(e.target.value)}
            rows={3}
            maxLength={1000}
            placeholder="VD: Đồng chí khác đăng nhập nhầm tài khoản và làm bài ngày 26/8"
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <span className="text-xs text-gray-500">
            Được ghi vào nhật ký cùng tên người thực hiện. Bản ghi cũ được chụp lại trước khi xóa
            nên vẫn tra cứu được về sau.
          </span>
        </label>

        {error && (
          <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">{error}</div>
        )}

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            Hủy
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving || !lyDoHopLe}
            className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {saving ? 'Đang xử lý...' : loaiReset === 'XOA_SACH' ? 'Xóa sạch bài thi' : 'Mở khóa lượt'}
          </button>
        </div>
      </div>
    </div>
  );
}

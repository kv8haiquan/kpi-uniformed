/**
 * Thêm một người vào ô trực ban — G4.7.
 *
 * Một ô có thể có nhiều người (trụ sở Chi cục thường có một lãnh đạo và một
 * công chức), nên form này chỉ thêm từng người; sửa thì xoá rồi thêm lại.
 */

'use client';

import { useState } from 'react';
import { Loader2, X } from 'lucide-react';

import { trucBanApi } from '@/services/truc-ban';
import { errMsg } from '@/lib/hkg-error';

interface Props {
  ngay: string;
  truSoId: string;
  tenTruSo: string;
  onDong: () => void;
  onXong: () => void;
}

const oCss =
  'w-full rounded-lg border border-gray-300 px-3 py-1.5 focus:border-blue-500 focus:outline-none';

export default function FormNguoiTruc({
  ngay,
  truSoId,
  tenTruSo,
  onDong,
  onXong,
}: Props) {
  const [hoTen, setHoTen] = useState('');
  const [chucVu, setChucVu] = useState('');
  const [sdt, setSdt] = useState('');
  const [caTruc, setCaTruc] = useState('CA_NGAY');
  const [ghiChu, setGhiChu] = useState('');

  const [dangLuu, setDangLuu] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  const luu = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hoTen.trim()) return setLoi('Chưa nhập họ tên');

    setDangLuu(true);
    setLoi(null);
    try {
      await trucBanApi.them({
        ngay_truc: ngay,
        tru_so_id: truSoId,
        ho_ten: hoTen.trim(),
        chuc_vu: chucVu.trim() || null,
        so_dien_thoai: sdt.trim() || null,
        ca_truc: caTruc,
        // Dữ liệu đang chạy chỉ có trực cuối tuần; để mặc định đúng thực tế
        // thay vì bắt người nhập chọn mỗi lần.
        loai_truc: 'CUOI_TUAN',
        ghi_chu: ghiChu.trim() || null,
      });
      onXong();
    } catch (e2) {
      setLoi(errMsg(e2, 'Không lưu được'));
    } finally {
      setDangLuu(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 overflow-y-auto">
      <form onSubmit={luu} className="w-full max-w-lg rounded-xl bg-white shadow-xl my-12">
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <div>
            <h2 className="font-semibold text-gray-900">Thêm người trực</h2>
            <p className="text-xs text-gray-500">
              {ngay.split('-').reverse().join('/')} — {tenTruSo}
            </p>
          </div>
          <button
            type="button"
            onClick={onDong}
            className="rounded p-1 text-gray-500 hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-3 px-5 py-4">
          <label className="block text-sm">
            <span className="block text-gray-600 mb-1">Họ và tên *</span>
            <input
              className={oCss}
              value={hoTen}
              onChange={(e) => setHoTen(e.target.value)}
              maxLength={100}
              autoFocus
            />
          </label>

          <label className="block text-sm">
            <span className="block text-gray-600 mb-1">Chức vụ</span>
            <input
              className={oCss}
              value={chucVu}
              onChange={(e) => setChucVu(e.target.value)}
              maxLength={100}
              placeholder="Quyết định thứ tự hiển thị trong ô"
            />
          </label>

          <label className="block text-sm">
            <span className="block text-gray-600 mb-1">Số điện thoại</span>
            <input
              className={oCss}
              value={sdt}
              onChange={(e) => setSdt(e.target.value)}
              maxLength={20}
            />
          </label>

          <label className="block text-sm">
            <span className="block text-gray-600 mb-1">Ca trực</span>
            <select
              className={oCss}
              value={caTruc}
              onChange={(e) => setCaTruc(e.target.value)}
            >
              <option value="CA_NGAY">Cả ngày</option>
              <option value="SANG">Buổi sáng</option>
              <option value="CHIEU">Buổi chiều</option>
              <option value="DEM">Ban đêm</option>
            </select>
          </label>

          <label className="block text-sm">
            <span className="block text-gray-600 mb-1">Ghi chú</span>
            <input
              className={oCss}
              value={ghiChu}
              onChange={(e) => setGhiChu(e.target.value)}
            />
          </label>
        </div>

        {loi && (
          <div className="mx-5 mb-3 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
            {loi}
          </div>
        )}

        <div className="flex justify-end gap-2 border-t border-gray-200 px-5 py-3">
          <button type="button" onClick={onDong} className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm hover:bg-gray-50">
            Đóng
          </button>
          <button
            type="submit"
            disabled={dangLuu}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {dangLuu && <Loader2 className="w-4 h-4 animate-spin" />}
            Thêm
          </button>
        </div>
      </form>
    </div>
  );
}

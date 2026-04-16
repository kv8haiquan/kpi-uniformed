/**
 * src/app/(main)/dao-tao/ky-thi/[id]/ket-qua/page.tsx
 * =====================================================
 * Trang ket qua ca nhan — diem tong, xep loai, radar theo linh vuc.
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { kyThiApi } from '@/services/lms';
import type { IDgnlKetQua } from '@/types/lms';

export default function KetQuaDgnlPage() {
  const params = useParams();
  const kyThiId = params.id as string;

  const [ketQua, setKetQua] = useState<IDgnlKetQua | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await kyThiApi.ketQua(kyThiId);
        setKetQua(res.data.data);
      } catch (err: any) {
        setError(err?.response?.data?.detail?.error?.message || 'Không thể tải kết quả');
      } finally {
        setLoading(false);
      }
    };
    if (kyThiId) load();
  }, [kyThiId]);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error || !ketQua) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || 'Chưa có kết quả'}
        </div>
        <Link href="/dao-tao/ky-thi" className="mt-4 inline-block text-blue-600 hover:underline text-sm">
          Quay lại danh sách kỳ thi
        </Link>
      </div>
    );
  }

  const { ky_thi, thi_sinh, ket_qua, diem_theo_linh_vuc, lich_su_thi } = ketQua;
  const isDat = ket_qua.xep_loai === 'DAT';

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Kết quả kỳ thi</h1>
          <p className="text-sm text-gray-500">{ky_thi.ten_ky_thi}</p>
        </div>
        <Link
          href="/dao-tao/ky-thi"
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Quay lại
        </Link>
      </div>

      {/* Score card */}
      <div className={`rounded-xl p-6 mb-6 ${isDat ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
        <div className="flex items-center gap-6">
          <div className={`text-6xl font-bold ${isDat ? 'text-green-600' : 'text-red-600'}`}>
            {ket_qua.diem_tong}%
          </div>
          <div>
            <div className={`text-2xl font-bold ${isDat ? 'text-green-700' : 'text-red-700'}`}>
              {isDat ? 'ĐẠT' : 'KHÔNG ĐẠT'}
            </div>
            <div className="text-sm text-gray-600 mt-1">
              Điểm đạt: {ky_thi.diem_dat}% | Lần thi: {ket_qua.lan_thi}
            </div>
          </div>
        </div>
      </div>

      {/* Info grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Thong tin thi sinh */}
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Thông tin thí sinh</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Họ tên</span>
              <span className="font-medium">{thi_sinh.ho_ten}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Mã CC</span>
              <span className="font-medium">{thi_sinh.ma_cc}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Đơn vị</span>
              <span className="font-medium">{thi_sinh.don_vi}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Vị trí thi</span>
              <span className="font-medium">{thi_sinh.vi_tri_thi}</span>
            </div>
          </div>
        </div>

        {/* Thong ke */}
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Thống kê</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Số câu đúng</span>
              <span className="font-medium text-green-600">{ket_qua.so_cau_dung}/{ket_qua.tong_so_cau}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Số câu sai</span>
              <span className="font-medium text-red-600">{ket_qua.so_cau_sai}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Thời gian làm bài</span>
              <span className="font-medium">
                {Math.floor(ket_qua.thoi_gian_lam_giay / 60)} phút {ket_qua.thoi_gian_lam_giay % 60} giây
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Diem theo linh vuc */}
      {diem_theo_linh_vuc && diem_theo_linh_vuc.length > 0 && (
        <div className="bg-white rounded-xl border p-4 mb-6">
          <h3 className="font-semibold text-gray-700 mb-4">Điểm theo lĩnh vực</h3>
          <div className="space-y-3">
            {diem_theo_linh_vuc.map((lv, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-700">{lv.linh_vuc}</span>
                  <span className="font-medium">
                    {lv.so_cau_dung}/{lv.tong_cau} ({lv.phan_tram}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className={`h-2.5 rounded-full ${lv.phan_tram >= 50 ? 'bg-green-500' : 'bg-red-500'}`}
                    style={{ width: `${Math.min(lv.phan_tram, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lich su thi */}
      {lich_su_thi && lich_su_thi.length > 0 && (
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Lịch sử các lần thi</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-2 px-3">Lần</th>
                  <th className="py-2 px-3">Điểm</th>
                  <th className="py-2 px-3">Xếp loại</th>
                  <th className="py-2 px-3">Số câu đúng</th>
                  <th className="py-2 px-3">Thời gian nộp</th>
                </tr>
              </thead>
              <tbody>
                {lich_su_thi.map((ls: any, idx: number) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3">{ls.lan}</td>
                    <td className="py-2 px-3 font-medium">{ls.diem}%</td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        ls.xep_loai === 'DAT' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                      }`}>
                        {ls.xep_loai === 'DAT' ? 'Đạt' : 'Không đạt'}
                      </span>
                    </td>
                    <td className="py-2 px-3">{ls.so_cau_dung}</td>
                    <td className="py-2 px-3 text-gray-500">
                      {ls.thoi_gian_nop ? new Date(ls.thoi_gian_nop).toLocaleString('vi-VN') : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

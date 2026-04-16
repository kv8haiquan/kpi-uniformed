/**
 * src/app/(main)/dao-tao/ky-thi/[id]/thong-ke/page.tsx
 * =====================================================
 * Trang thong ke ket qua ky thi — QT_DAO_TAO / Lanh dao.
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { kyThiApi } from '@/services/lms';
import type { IKyThi, IDgnlThongKe, IThiSinh } from '@/types/lms';

export default function ThongKeKyThiPage() {
  const params = useParams();
  const kyThiId = params.id as string;

  const [kyThi, setKyThi] = useState<IKyThi | null>(null);
  const [thongKe, setThongKe] = useState<IDgnlThongKe | null>(null);
  const [thiSinh, setThiSinh] = useState<IThiSinh[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [ktRes, tkRes, tsRes] = await Promise.all([
          kyThiApi.chiTiet(kyThiId),
          kyThiApi.thongKe(kyThiId),
          kyThiApi.danhSachThiSinh(kyThiId, { page_size: 200 }),
        ]);
        setKyThi(ktRes.data.data);
        setThongKe(tkRes.data.data);
        setThiSinh(tsRes.data.data || []);
      } catch (err: any) {
        setError(err?.response?.data?.detail?.error?.message || 'Không thể tải thống kê');
      } finally {
        setLoading(false);
      }
    };
    if (kyThiId) load();
  }, [kyThiId]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await kyThiApi.exportExcel(kyThiId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `ket_qua_${kyThi?.ma_ky_thi || kyThiId}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Lỗi khi export file');
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
      </div>
    );
  }

  const tq = thongKe?.tong_quan;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Thống kê kỳ thi</h1>
          <p className="text-sm text-gray-500">{kyThi?.ten_ky_thi} ({kyThi?.ma_ky_thi})</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {exporting ? 'Đang xuất...' : 'Xuất Excel'}
          </button>
          <Link
            href="/dao-tao/ky-thi/quan-ly"
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Quay lại
          </Link>
        </div>
      </div>

      {/* Stat cards */}
      {tq && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 mb-6">
          <StatCard label="Tổng thí sinh" value={tq.tong_thi_sinh} color="blue" />
          <StatCard label="Đã thi" value={tq.da_thi} color="green" />
          <StatCard label="Chưa thi" value={tq.chua_thi} color="gray" />
          <StatCard label="Đạt" value={tq.dat} color="green" />
          <StatCard label="Không đạt" value={tq.khong_dat} color="red" />
          <StatCard label="Tỷ lệ đạt" value={`${tq.ti_le_dat}%`} color="purple" />
        </div>
      )}

      {/* Diem */}
      {tq && (
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="bg-white border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{tq.diem_trung_binh}</div>
            <div className="text-xs text-gray-500">Điểm trung bình</div>
          </div>
          <div className="bg-white border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{tq.diem_cao_nhat}</div>
            <div className="text-xs text-gray-500">Điểm cao nhất</div>
          </div>
          <div className="bg-white border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-red-600">{tq.diem_thap_nhat}</div>
            <div className="text-xs text-gray-500">Điểm thấp nhất</div>
          </div>
        </div>
      )}

      {/* Theo vi tri */}
      {thongKe?.theo_vi_tri && thongKe.theo_vi_tri.length > 0 && (
        <div className="bg-white rounded-xl border p-4 mb-6">
          <h3 className="font-semibold text-gray-700 mb-3">Theo vị trí</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-2 px-3">Vị trí</th>
                  <th className="py-2 px-3 text-center">Tổng</th>
                  <th className="py-2 px-3 text-center">Đạt</th>
                  <th className="py-2 px-3 text-center">Không đạt</th>
                  <th className="py-2 px-3 text-center">Điểm TB</th>
                </tr>
              </thead>
              <tbody>
                {thongKe.theo_vi_tri.map((vt, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3 font-medium">{vt.vi_tri}</td>
                    <td className="py-2 px-3 text-center">{vt.tong}</td>
                    <td className="py-2 px-3 text-center text-green-600">{vt.dat}</td>
                    <td className="py-2 px-3 text-center text-red-600">{vt.khong_dat}</td>
                    <td className="py-2 px-3 text-center font-medium">{vt.diem_tb}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Theo don vi */}
      {thongKe?.theo_don_vi && thongKe.theo_don_vi.length > 0 && (
        <div className="bg-white rounded-xl border p-4 mb-6">
          <h3 className="font-semibold text-gray-700 mb-3">Theo đơn vị</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-2 px-3">Đơn vị</th>
                  <th className="py-2 px-3 text-center">Tổng</th>
                  <th className="py-2 px-3 text-center">Đạt</th>
                  <th className="py-2 px-3 text-center">Tỷ lệ đạt</th>
                  <th className="py-2 px-3 text-center">Điểm TB</th>
                </tr>
              </thead>
              <tbody>
                {thongKe.theo_don_vi.map((dv, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3 font-medium">{dv.don_vi}</td>
                    <td className="py-2 px-3 text-center">{dv.tong}</td>
                    <td className="py-2 px-3 text-center text-green-600">{dv.dat}</td>
                    <td className="py-2 px-3 text-center">{dv.ti_le_dat}%</td>
                    <td className="py-2 px-3 text-center font-medium">{dv.diem_tb}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Danh sach thi sinh */}
      <div className="bg-white rounded-xl border p-4">
        <h3 className="font-semibold text-gray-700 mb-3">Danh sách thí sinh ({thiSinh.length})</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="py-2 px-3">STT</th>
                <th className="py-2 px-3">Mã CC</th>
                <th className="py-2 px-3">Họ tên</th>
                <th className="py-2 px-3">Đơn vị</th>
                <th className="py-2 px-3">Vị trí</th>
                <th className="py-2 px-3 text-center">Trạng thái</th>
                <th className="py-2 px-3 text-center">Điểm</th>
                <th className="py-2 px-3 text-center">Xếp loại</th>
              </tr>
            </thead>
            <tbody>
              {thiSinh.map((ts, idx) => (
                <tr key={ts.id} className="border-b hover:bg-gray-50">
                  <td className="py-2 px-3 text-gray-400">{idx + 1}</td>
                  <td className="py-2 px-3 font-mono text-xs">{ts.ma_cc}</td>
                  <td className="py-2 px-3 font-medium">{ts.ho_ten}</td>
                  <td className="py-2 px-3 text-gray-600">{ts.don_vi_ten}</td>
                  <td className="py-2 px-3">{ts.vi_tri_ten}</td>
                  <td className="py-2 px-3 text-center">
                    <TrangThaiBadge trangThai={ts.trang_thai} />
                  </td>
                  <td className="py-2 px-3 text-center font-medium">
                    {ts.diem_tong !== null ? `${ts.diem_tong}%` : '-'}
                  </td>
                  <td className="py-2 px-3 text-center">
                    {ts.xep_loai && (
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        ts.xep_loai === 'DAT' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                      }`}>
                        {ts.xep_loai === 'DAT' ? 'Đạt' : 'Không đạt'}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number | string; color: string }) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    gray: 'bg-gray-50 text-gray-700 border-gray-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
  };
  return (
    <div className={`${colorMap[color] || colorMap.blue} rounded-xl border p-3 text-center`}>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs opacity-80">{label}</div>
    </div>
  );
}

function TrangThaiBadge({ trangThai }: { trangThai: string }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    CHUA_THI: { label: 'Chưa thi', cls: 'bg-gray-100 text-gray-600' },
    DANG_THI: { label: 'Đang thi', cls: 'bg-blue-100 text-blue-700' },
    DA_NOP: { label: 'Đã nộp', cls: 'bg-green-100 text-green-700' },
    VANG: { label: 'Vắng', cls: 'bg-red-100 text-red-600' },
  };
  const c = cfg[trangThai] || cfg.CHUA_THI;
  return <span className={`${c.cls} px-2 py-0.5 rounded-full text-xs`}>{c.label}</span>;
}

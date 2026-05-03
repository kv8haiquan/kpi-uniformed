/**
 * /hop-khong-giay/thong-ke — Dashboard cá nhân.
 */

'use client';

import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { thongKeApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { IDashboardCaNhan } from '@/types/hkg';

export default function ThongKePage() {
  const [data, setData] = useState<IDashboardCaNhan | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    thongKeApi.caNhan().then(setData).catch((e) => setError(errMsg(e)));
  }, []);

  return (
    <div>
      <h2 className="text-lg font-medium mb-4">Dashboard cá nhân</h2>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
          {error}
        </div>
      )}

      {!data && !error && (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" /> Đang tải...
        </div>
      )}

      {data && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Card label="Cuộc họp tháng này" value={data.so_cuoc_hop_thang_nay} color="text-blue-700" />
          <Card label="Đã tham dự" value={data.so_cuoc_hop_tham_du} color="text-green-700" />
          <Card label="Vắng" value={data.so_lan_vang} color="text-red-700" />
          <Card
            label="Tỷ lệ tham dự"
            value={`${data.ty_le_tham_du}%`}
            color="text-purple-700"
          />
          <Card label="Nhiệm vụ đang làm" value={data.nhiem_vu_dang_lam} color="text-yellow-700" />
          <Card label="Quá hạn" value={data.nhiem_vu_qua_han} color="text-red-700" />
        </div>
      )}
    </div>
  );
}

function Card({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className="bg-white border rounded p-4">
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
      <div className="text-sm text-gray-600 mt-1">{label}</div>
    </div>
  );
}

/**
 * src/components/dashboard/RecentTransfersWidget.tsx
 * ==================================================
 * Widget "Điều chuyển & trạng thái gần đây" cho dashboard admin.
 * Hiển thị N bản ghi lich_su_dieu_chuyen mới nhất toàn cơ quan
 * (điều chuyển + vô hiệu hóa + kích hoạt).
 */
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { adminService } from '@/services/admin.service';
import { ILichSuDieuChuyenResponse, LoaiLichSuDieuChuyen } from '@/types/admin';

const LOAI_META: Record<LoaiLichSuDieuChuyen, { label: string; cls: string }> = {
  DIEU_CHUYEN: { label: 'Điều chuyển', cls: 'bg-blue-100 text-blue-700' },
  VO_HIEU_HOA: { label: 'Vô hiệu hóa', cls: 'bg-red-100 text-red-700' },
  KICH_HOAT: { label: 'Kích hoạt', cls: 'bg-green-100 text-green-700' },
};

export default function RecentTransfersWidget({ limit = 8 }: { limit?: number }) {
  const router = useRouter();
  const [items, setItems] = useState<ILichSuDieuChuyenResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    adminService
      .getRecentLichSu(limit)
      .then((data) => { if (alive) setItems(data); })
      .catch(() => { /* im lặng — widget phụ, không chặn dashboard */ })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [limit]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-orange-50 to-red-50">
        <div className="flex items-center gap-2">
          <span className="text-lg">🔄</span>
          <h3 className="font-medium text-gray-900">Điều chuyển &amp; trạng thái gần đây</h3>
        </div>
        <button
          onClick={() => router.push('/admin/lich-su-dieu-chuyen')}
          className="text-xs text-blue-600 hover:underline"
        >
          Xem tất cả →
        </button>
      </div>
      <div className="p-5">
        {loading ? (
          <div className="flex items-center justify-center py-6">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-orange-600" />
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-6">Chưa có hoạt động nào.</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {items.map((h) => {
              const meta = LOAI_META[h.loai];
              const ngay = h.ngay_hieu_luc || h.created_at;
              return (
                <li key={h.id} className="py-2.5 flex items-start gap-3">
                  <span className={`px-1.5 py-0.5 rounded text-xs font-medium shrink-0 ${meta.cls}`}>
                    {meta.label}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-gray-900 truncate">
                      {h.cong_chuc_ho_ten || 'N/A'}
                      {h.cong_chuc_ma_cc && (
                        <span className="text-gray-400 font-normal"> ({h.cong_chuc_ma_cc})</span>
                      )}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {h.loai === 'DIEU_CHUYEN' && (
                        <>{h.don_vi_cu_ten || '?'} → <span className="text-blue-600">{h.don_vi_moi_ten || '?'}</span> · </>
                      )}
                      {h.ly_do ? `${h.ly_do} · ` : ''}
                      {ngay ? new Date(ngay).toLocaleDateString('vi-VN') : ''}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

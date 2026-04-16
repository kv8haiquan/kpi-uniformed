/**
 * src/app/(main)/dao-tao/ky-thi/page.tsx
 * =======================================
 * Danh sach ky thi DGNL — CBCC thay ky thi duoc giao.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { kyThiApi } from '@/services/lms';
import type { IKyThi } from '@/types/lms';
import { useAuthStore } from '@/stores/useAuthStore';

const TRANG_THAI_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  NHAP: { label: 'Nháp', bg: 'bg-gray-100', text: 'text-gray-600' },
  CHO_DUYET: { label: 'Chờ duyệt', bg: 'bg-yellow-100', text: 'text-yellow-700' },
  DANG_MO: { label: 'Đang mở', bg: 'bg-green-100', text: 'text-green-700' },
  DA_DONG: { label: 'Đã đóng', bg: 'bg-red-100', text: 'text-red-600' },
};

const GRADIENTS = [
  'from-blue-500 to-indigo-600',
  'from-green-500 to-teal-600',
  'from-purple-500 to-pink-600',
  'from-orange-500 to-red-600',
];

export default function DanhSachKyThiPage() {
  const { user } = useAuthStore();
  const [kyThiList, setKyThiList] = useState<IKyThi[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const platformRoles: string[] = (user as any)?.platform_roles ?? [];
  const isQT = user?.is_system_admin === true || platformRoles.includes('QT_DAO_TAO');

  useEffect(() => {
    const load = async () => {
      try {
        const res = await kyThiApi.danhSach({ page_size: 50 });
        setKyThiList(res.data.data || []);
      } catch (err: any) {
        setError(err?.response?.data?.detail?.error?.message || 'Không thể tải danh sách kỳ thi');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
        <Link href="/dao-tao" className="hover:text-blue-600">Đào tạo</Link>
        <span>/</span>
        <span className="text-gray-900">Kỳ thi ĐGNL</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Kỳ thi đánh giá năng lực</h1>
          <p className="text-sm text-gray-500 mt-1">Danh sách kỳ thi ĐGNL theo vị trí việc làm</p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/dao-tao"
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Quay lại
          </Link>
          {isQT && (
            <Link
              href="/dao-tao/ky-thi/quan-ly"
              className="px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Quản lý kỳ thi
            </Link>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {kyThiList.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <div className="text-4xl mb-3">📝</div>
          <p>Chưa có kỳ thi nào được giao cho bạn</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {kyThiList.map((kt, idx) => {
            const cfg = TRANG_THAI_CONFIG[kt.trang_thai] || TRANG_THAI_CONFIG.NHAP;
            const gradient = GRADIENTS[idx % GRADIENTS.length];
            const now = new Date();
            const end = new Date(kt.ngay_ket_thuc);
            const isExpired = now > end;

            return (
              <div key={kt.id} className="bg-white rounded-xl border shadow-sm overflow-hidden hover:shadow-md transition-shadow">
                {/* Gradient header */}
                <div className={`bg-gradient-to-r ${gradient} p-4 text-white`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono opacity-80">{kt.ma_ky_thi}</span>
                    <span className={`${cfg.bg} ${cfg.text} px-2 py-0.5 rounded-full text-xs font-medium`}>
                      {cfg.label}
                    </span>
                  </div>
                  <h3 className="font-semibold text-lg leading-tight">{kt.ten_ky_thi}</h3>
                </div>

                {/* Body */}
                <div className="p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-gray-500">Thời gian:</div>
                    <div className="text-right font-medium">{kt.thoi_gian_lam_bai_phut} phút</div>
                    <div className="text-gray-500">Điểm đạt:</div>
                    <div className="text-right font-medium">{kt.diem_dat}%</div>
                    <div className="text-gray-500">Số lượt thi:</div>
                    <div className="text-right font-medium">{kt.so_lan_thi_toi_da}</div>
                  </div>

                  <div className="text-xs text-gray-400 border-t pt-2">
                    <div>Bắt đầu: {new Date(kt.ngay_bat_dau).toLocaleDateString('vi-VN')}</div>
                    <div className={isExpired ? 'text-red-500' : ''}>
                      Kết thúc: {new Date(kt.ngay_ket_thuc).toLocaleDateString('vi-VN')}
                      {isExpired && ' (Đã hết hạn)'}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-1">
                    {kt.trang_thai === 'DANG_MO' && !isExpired && (
                      <Link
                        href={`/dao-tao/ky-thi/${kt.id}/thi`}
                        className="flex-1 text-center px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                      >
                        Vào thi
                      </Link>
                    )}
                    <Link
                      href={`/dao-tao/ky-thi/${kt.id}/ket-qua`}
                      className="flex-1 text-center px-3 py-2 border border-gray-300 text-sm rounded-lg hover:bg-gray-50"
                    >
                      Kết quả
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

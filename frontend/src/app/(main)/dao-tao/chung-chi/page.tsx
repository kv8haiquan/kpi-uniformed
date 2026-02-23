/**
 * src/app/(main)/dao-tao/chung-chi/page.tsx
 * ==========================================
 * Chung chi cua toi + xac minh chung chi public.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { chungChiApi } from '@/services/lms';
import type { IChungChi, IPagination } from '@/types/lms';

const XEP_LOAI_CONFIG: Record<string, { label: string; bg: string; icon: string }> = {
  XUAT_SAC: { label: 'Xuất sắc', bg: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: '🏆' },
  GIOI: { label: 'Giỏi', bg: 'bg-blue-100 text-blue-800 border-blue-300', icon: '🥇' },
  KHA: { label: 'Khá', bg: 'bg-green-100 text-green-800 border-green-300', icon: '🥈' },
  DAT: { label: 'Đạt', bg: 'bg-gray-100 text-gray-800 border-gray-300', icon: '✅' },
  KHONG_DAT: { label: 'Không đạt', bg: 'bg-red-100 text-red-800 border-red-300', icon: '❌' },
};

export default function ChungChiPage() {
  const [chungChis, setChungChis] = useState<IChungChi[]>([]);
  const [pagination, setPagination] = useState<IPagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  // Xac minh
  const [maXacMinh, setMaXacMinh] = useState('');
  const [xacMinhResult, setXacMinhResult] = useState<any>(null);
  const [xacMinhError, setXacMinhError] = useState('');
  const [xacMinhLoading, setXacMinhLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await chungChiApi.cuaToi({ page, page_size: 12 });
        setChungChis(res.data.data || []);
        setPagination(res.data.pagination || null);
      } catch {
        // Silently handle — show empty
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [page]);

  const handleXacMinh = async () => {
    if (!maXacMinh.trim()) return;
    setXacMinhLoading(true);
    setXacMinhResult(null);
    setXacMinhError('');
    try {
      const res = await chungChiApi.xacMinh(maXacMinh.trim());
      setXacMinhResult(res.data.data);
    } catch (err: any) {
      setXacMinhError('Mã chứng chỉ không hợp lệ hoặc không tồn tại');
    } finally {
      setXacMinhLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
          <Link href="/dao-tao" className="hover:text-blue-600">Đào tạo</Link>
          <span>/</span><span className="text-gray-900">Chứng chỉ</span>
        </div>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Chứng chỉ của tôi</h1>
          {pagination && <span className="text-sm text-gray-500">Tổng: {pagination.total_items}</span>}
        </div>

        {/* Grid chung chi */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {[1,2,3].map(i => <div key={i} className="h-48 bg-gray-100 rounded-xl animate-pulse" />)}
          </div>
        ) : chungChis.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center mb-8">
            <span className="text-5xl block mb-4">🎓</span>
            <h3 className="text-lg font-medium text-gray-900">Chưa có chứng chỉ nào</h3>
            <p className="text-gray-500 mt-1 mb-4">Hoàn thành khóa học để nhận chứng chỉ!</p>
            <Link href="/dao-tao/khoa-hoc" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
              Xem khóa học
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {chungChis.map((cc) => {
              const xl = XEP_LOAI_CONFIG[cc.xep_loai || 'DAT'] || XEP_LOAI_CONFIG.DAT;
              return (
                <div key={cc.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                  {/* Header gradient */}
                  <div className="h-3 bg-gradient-to-r from-yellow-400 via-green-400 to-blue-500" />
                  <div className="p-5">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <span className="text-2xl">{xl.icon}</span>
                        <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-bold border ${xl.bg}`}>{xl.label}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-gray-900">{cc.diem_dat}</div>
                        <div className="text-xs text-gray-500">điểm</div>
                      </div>
                    </div>
                    <h3 className="font-medium text-gray-900 mb-1 line-clamp-2">{cc.khoa_hoc_ten || 'Khóa học'}</h3>
                    <div className="text-xs text-gray-500 space-y-0.5">
                      <div>Mã: <span className="font-mono font-medium">{cc.ma_chung_chi}</span></div>
                      <div>Cấp ngày: {cc.ngay_cap ? new Date(cc.ngay_cap).toLocaleDateString('vi-VN') : '—'}</div>
                    </div>
                    <div className="flex gap-2 mt-4">
                      <button onClick={() => { setMaXacMinh(cc.ma_chung_chi); }}
                        className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-xs hover:bg-gray-50 text-center">
                        Xác minh
                      </button>
                      <button className="flex-1 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-xs hover:bg-blue-100 text-center">
                        Tải PDF
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center gap-2 mb-8">
            <button onClick={() => setPage(Math.max(1, page-1))} disabled={page<=1}
              className="px-3 py-1.5 border rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50">Trước</button>
            <span className="text-sm text-gray-500">{page}/{pagination.total_pages}</span>
            <button onClick={() => setPage(Math.min(pagination.total_pages, page+1))} disabled={page>=pagination.total_pages}
              className="px-3 py-1.5 border rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50">Sau</button>
          </div>
        )}

        {/* Xac minh section */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>🔍</span> Xác minh chứng chỉ
          </h2>
          <p className="text-sm text-gray-500 mb-4">Nhập mã chứng chỉ để kiểm tra tính hợp lệ</p>
          <div className="flex gap-3">
            <input type="text" value={maXacMinh} onChange={(e) => setMaXacMinh(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleXacMinh()}
              placeholder="VD: CC-2026-000001" className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm font-mono" />
            <button onClick={handleXacMinh} disabled={xacMinhLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
              {xacMinhLoading ? 'Đang kiểm tra...' : 'Xác minh'}
            </button>
          </div>

          {xacMinhError && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {xacMinhError}
            </div>
          )}

          {xacMinhResult && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-green-600 text-lg">✅</span>
                <span className="font-semibold text-green-800">Chứng chỉ hợp lệ</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-gray-500">Mã:</span> <span className="font-mono font-medium">{xacMinhResult.ma_chung_chi}</span></div>
                <div><span className="text-gray-500">Người nhận:</span> <span className="font-medium">{xacMinhResult.ho_ten}</span></div>
                <div><span className="text-gray-500">Khóa học:</span> <span className="font-medium">{xacMinhResult.khoa_hoc_ten}</span></div>
                <div><span className="text-gray-500">Xếp loại:</span> <span className="font-medium">{xacMinhResult.xep_loai}</span></div>
                <div><span className="text-gray-500">Điểm:</span> <span className="font-medium">{xacMinhResult.diem_dat}</span></div>
                <div><span className="text-gray-500">Ngày cấp:</span> <span className="font-medium">{xacMinhResult.ngay_cap ? new Date(xacMinhResult.ngay_cap).toLocaleDateString('vi-VN') : '—'}</span></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

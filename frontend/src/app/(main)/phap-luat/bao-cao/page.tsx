/**
 * src/app/(main)/phap-luat/bao-cao/page.tsx
 * ============================================
 * Trang báo cáo tỷ lệ đọc văn bản theo đơn vị.
 * Chỉ dành cho: Lãnh đạo, QT_NOI_DUNG, ADMIN.
 *
 * Gồm:
 *   - Chọn đơn vị + tháng/năm
 *   - Thống kê: tỷ lệ đã đọc, xác nhận, quá hạn (progress bars)
 *   - Bảng: CBCC chưa đọc (tên, VB chưa đọc, VB quá hạn)
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/stores/useAuthStore';
import { legalService } from '@/services/legal';
import type { IBaoCaoDonVi } from '@/types/legal';

// =============================================================================
// PROGRESS BAR
// =============================================================================
function ProgressBar({ value, color = 'purple' }: { value: number; color?: string }) {
  const colorMap: Record<string, string> = {
    purple: 'bg-purple-500',
    green:  'bg-green-500',
    red:    'bg-red-500',
    blue:   'bg-blue-500',
  };
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-gray-200 rounded-full h-2.5">
        <div
          className={`${colorMap[color] ?? colorMap.purple} h-2.5 rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      <span className="text-sm font-semibold text-gray-700 w-12 text-right">
        {value.toFixed(1)}%
      </span>
    </div>
  );
}

// =============================================================================
// MAIN PAGE
// =============================================================================
export default function BaoCaoPage() {
  const user = useAuthStore(s => s.user);
  const platformRoles: string[] = (user as unknown as { platform_roles?: string[] })?.platform_roles ?? [];

  const coQuyen =
    user?.is_system_admin === true ||
    user?.is_lanh_dao === true ||
    platformRoles.includes('QT_NOI_DUNG');

  // Lấy tháng/năm hiện tại làm default
  const now = new Date();
  const [thang, setThang] = useState(now.getMonth() + 1);
  const [nam, setNam] = useState(now.getFullYear());
  const [donViId, setDonViId] = useState('');
  const [baoCao, setBaoCao] = useState<IBaoCaoDonVi | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Lấy đơn vị của user làm default
  useEffect(() => {
    const dv = (user as unknown as { don_vi_id?: string })?.don_vi_id;
    if (dv) setDonViId(dv);
  }, [user]);

  const loadBaoCao = async () => {
    if (!donViId) {
      setError('Vui lòng chọn đơn vị');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await legalService.getBaoCaoDonVi(donViId, { thang, nam });
      // Kiểm tra success field theo SHARED_CODING_STANDARDS §5.1
      if (res.data?.success) {
        setBaoCao(res.data.data);
      } else {
        const msg = res.data?.error?.message || 'Không thể tải báo cáo.';
        console.warn('[Legal] getBaoCaoDonVi:', res.data?.error?.code, msg);
        setError(msg);
      }
    } catch (err: unknown) {
      const e = err as { response?: { status?: number } };
      if (e?.response?.status === 403) {
        setError('Bạn không có quyền xem báo cáo đơn vị này');
      } else {
        setError('Không thể tải báo cáo. Vui lòng thử lại.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Load khi đơn vị thay đổi
  useEffect(() => {
    if (donViId) loadBaoCao();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [donViId]);

  // Không có quyền
  if (!coQuyen) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white rounded-xl border border-red-200 p-8 text-center max-w-md">
          <span className="text-4xl block mb-3">🔒</span>
          <p className="font-medium text-gray-700 mb-2">Không có quyền truy cập</p>
          <p className="text-sm text-gray-500 mb-4">
            Trang báo cáo chỉ dành cho Lãnh đạo và Quản trị nội dung.
          </p>
          <Link href="/phap-luat" className="text-sm text-purple-600 hover:underline">
            ← Về trang pháp luật
          </Link>
        </div>
      </div>
    );
  }

  const bc = baoCao;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {/* Header */}
        <div className="mb-6">
          <nav className="flex items-center gap-2 text-sm text-gray-400 mb-1">
            <Link href="/phap-luat" className="hover:text-purple-600 transition-colors">⚖️ Pháp luật</Link>
            <span>›</span>
            <span className="text-gray-700">Báo cáo</span>
          </nav>
          <h1 className="text-2xl font-bold text-gray-900">📊 Báo cáo tỷ lệ đọc văn bản</h1>
          <p className="text-sm text-gray-500 mt-1">Thống kê đơn vị theo tháng</p>
        </div>

        {/* Filter */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 shadow-sm">
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Tháng</label>
              <select
                value={thang}
                onChange={e => setThang(Number(e.target.value))}
                className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
              >
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Năm</label>
              <select
                value={nam}
                onChange={e => setNam(Number(e.target.value))}
                className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
              >
                {[2025, 2026, 2027].map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>

            <div className="flex-1 min-w-32">
              <label className="block text-xs font-medium text-gray-500 mb-1">Đơn vị</label>
              <input
                type="text"
                placeholder="UUID đơn vị..."
                value={donViId}
                onChange={e => setDonViId(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
            </div>

            <button
              onClick={loadBaoCao}
              disabled={loading}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {loading ? '...' : '🔍 Xem báo cáo'}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm mb-4">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
          </div>
        )}

        {/* Kết quả */}
        {!loading && bc && (
          <div className="space-y-5">
            {/* Tổng quan */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h2 className="font-bold text-gray-900 mb-1">
                🏛 {bc.don_vi.ten_don_vi}
              </h2>
              <p className="text-sm text-gray-500 mb-5">
                Tháng {thang}/{nam} • {bc.tong_cbcc} CBCC
              </p>

              {/* Stat boxes */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                <div className="bg-blue-50 rounded-xl p-3 text-center">
                  <div className="text-2xl font-bold text-blue-700">
                    {bc.thong_ke.vb_bat_buoc_trong_thang}
                  </div>
                  <div className="text-xs text-blue-600 mt-1">VB bắt buộc</div>
                </div>
                <div className="bg-purple-50 rounded-xl p-3 text-center">
                  <div className="text-2xl font-bold text-purple-700">
                    {bc.thong_ke.ty_le_da_doc.toFixed(0)}%
                  </div>
                  <div className="text-xs text-purple-600 mt-1">Đã đọc</div>
                </div>
                <div className="bg-green-50 rounded-xl p-3 text-center">
                  <div className="text-2xl font-bold text-green-700">
                    {bc.thong_ke.ty_le_xac_nhan.toFixed(0)}%
                  </div>
                  <div className="text-xs text-green-600 mt-1">Đã xác nhận</div>
                </div>
                <div className="bg-orange-50 rounded-xl p-3 text-center">
                  <div className="text-2xl font-bold text-orange-700">
                    {bc.thong_ke.quiz_diem_tb.toFixed(1)}
                  </div>
                  <div className="text-xs text-orange-600 mt-1">Điểm quiz TB</div>
                </div>
              </div>

              {/* Progress bars */}
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">📖 Tỷ lệ đã đọc</span>
                  </div>
                  <ProgressBar value={bc.thong_ke.ty_le_da_doc} color="blue" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">✅ Tỷ lệ đã xác nhận</span>
                  </div>
                  <ProgressBar value={bc.thong_ke.ty_le_xac_nhan} color="green" />
                </div>
                {bc.thong_ke.ty_le_qua_han > 0 && (
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-600">⚠️ Tỷ lệ quá hạn</span>
                    </div>
                    <ProgressBar value={bc.thong_ke.ty_le_qua_han} color="red" />
                  </div>
                )}
              </div>
            </div>

            {/* Bảng CBCC chưa đọc */}
            {bc.cbcc_chua_doc.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100">
                  <h2 className="font-bold text-gray-900 flex items-center gap-2">
                    <span>⚠️</span>
                    CBCC chưa hoàn thành ({bc.cbcc_chua_doc.length} người)
                  </h2>
                </div>
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Họ tên</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">VB chưa đọc</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">VB quá hạn</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {bc.cbcc_chua_doc.map((cbcc, i) => (
                      <tr key={i} className={`hover:bg-gray-50 ${cbcc.vb_qua_han > 0 ? 'bg-red-50/30' : ''}`}>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{cbcc.ho_ten}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`text-sm font-semibold ${cbcc.vb_chua_doc > 0 ? 'text-orange-600' : 'text-gray-400'}`}>
                            {cbcc.vb_chua_doc}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`text-sm font-semibold ${cbcc.vb_qua_han > 0 ? 'text-red-600' : 'text-gray-400'}`}>
                            {cbcc.vb_qua_han}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {bc.cbcc_chua_doc.length === 0 && (
              <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
                <span className="text-3xl block mb-2">🎉</span>
                <p className="font-medium text-green-700">
                  Tất cả CBCC đã hoàn thành đọc và xác nhận!
                </p>
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {!loading && !bc && !error && (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <span className="block text-5xl mb-4">📊</span>
            <p className="text-gray-500">Chọn đơn vị và nhấn &ldquo;Xem báo cáo&rdquo; để bắt đầu</p>
          </div>
        )}

      </div>
    </div>
  );
}

/**
 * src/app/(main)/dao-tao/ky-thi/[id]/giam-sat/page.tsx
 * ====================================================
 * Màn hình giám sát trực tiếp kỳ thi ĐGNL — CHỈ admin (QT_DAO_TAO/SUPER_ADMIN).
 * Poll API mỗi 7s để cập nhật tiến độ / vi phạm / online của từng thí sinh.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { kyThiApi } from '@/services/lms';
import { useAuthStore } from '@/stores/useAuthStore';
import ViPhamDetailModal from '@/components/lms/ViPhamDetailModal';
import type { IKyThi, IGiamSatResponse, IGiamSatThiSinh } from '@/types/lms';

const POLL_MS = 7000;

function fmtTime(secs: number | null): string {
  if (secs === null || secs === undefined) return '--:--';
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function trangThaiBadge(tt: string) {
  const map: Record<string, string> = {
    DANG_THI: 'bg-amber-100 text-amber-800',
    DA_NOP: 'bg-green-100 text-green-700',
    CHUA_THI: 'bg-gray-100 text-gray-600',
    VANG: 'bg-red-100 text-red-700',
  };
  const label: Record<string, string> = {
    DANG_THI: 'Đang thi', DA_NOP: 'Đã nộp', CHUA_THI: 'Chưa thi', VANG: 'Vắng',
  };
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${map[tt] || 'bg-gray-100 text-gray-600'}`}>{label[tt] || tt}</span>;
}

export default function GiamSatKyThiPage() {
  const params = useParams();
  const kyThiId = params.id as string;
  const { user } = useAuthStore();
  const platformRoles: string[] = (user as any)?.platform_roles ?? [];
  const isQT = user?.is_system_admin === true || platformRoles.includes('QT_DAO_TAO');

  const [kyThi, setKyThi] = useState<IKyThi | null>(null);
  const [data, setData] = useState<IGiamSatResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('ALL');
  const [lastUpdate, setLastUpdate] = useState<string>('');
  // Thí sinh đang xem chi tiết vi phạm (modal)
  const [viPhamTarget, setViPhamTarget] = useState<{ ccId: string; hoTen?: string } | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await kyThiApi.giamSat(kyThiId);
      setData(res.data.data);
      setError(null);
      setLastUpdate(new Date().toLocaleTimeString('vi-VN'));
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Không tải được dữ liệu giám sát');
    } finally {
      setLoading(false);
    }
  }, [kyThiId]);

  useEffect(() => {
    if (!isQT || !kyThiId) return;
    kyThiApi.chiTiet(kyThiId).then((r) => setKyThi(r.data.data)).catch(() => {});
    fetchData();
    const interval = setInterval(fetchData, POLL_MS);
    return () => clearInterval(interval);
  }, [isQT, kyThiId, fetchData]);

  if (!isQT) {
    return (
      <div className="max-w-3xl mx-auto p-8 text-center">
        <div className="text-4xl mb-3">🔒</div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Không có quyền truy cập</h2>
        <p className="text-gray-600">Chỉ Quản trị đào tạo (QT_DAO_TAO) được giám sát kỳ thi đánh giá năng lực.</p>
      </div>
    );
  }

  const tq = data?.tong_quan;
  const rows: IGiamSatThiSinh[] = (data?.thi_sinh || []).filter(
    (t) => filter === 'ALL' || t.trang_thai === filter,
  );

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-6">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Giám sát trực tiếp</h1>
          <p className="text-sm text-gray-500">{kyThi?.ten_ky_thi}</p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="flex items-center gap-1.5 text-gray-500">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
            </span>
            Tự cập nhật {POLL_MS / 1000}s {lastUpdate && `· ${lastUpdate}`}
          </span>
          <Link href="/dao-tao/ky-thi/quan-ly" className="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50">
            Quản lý kỳ thi
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      {/* Thống kê tổng quan */}
      {tq && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-5">
          {[
            { label: 'Tổng', val: tq.tong_thi_sinh, color: 'text-gray-900' },
            { label: 'Đang thi', val: tq.dang_thi, color: 'text-amber-600' },
            { label: 'Online', val: tq.online, color: 'text-green-600' },
            { label: 'Đã nộp', val: tq.da_nop, color: 'text-blue-600' },
            { label: 'Chưa thi', val: tq.chua_thi, color: 'text-gray-500' },
            { label: 'Có vi phạm', val: tq.co_vi_pham, color: 'text-red-600' },
          ].map((s) => (
            <div key={s.label} className="bg-white border rounded-xl p-3 text-center">
              <div className={`text-2xl font-bold ${s.color}`}>{s.val}</div>
              <div className="text-xs text-gray-500 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2 mb-3 flex-wrap">
        {[
          { k: 'ALL', l: 'Tất cả' },
          { k: 'DANG_THI', l: 'Đang thi' },
          { k: 'DA_NOP', l: 'Đã nộp' },
          { k: 'CHUA_THI', l: 'Chưa thi' },
          { k: 'VANG', l: 'Vắng' },
        ].map((f) => (
          <button
            key={f.k}
            onClick={() => setFilter(f.k)}
            className={`px-3 py-1.5 rounded-lg text-sm border ${
              filter === f.k ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
            }`}
          >
            {f.l}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : (
        <div className="bg-white border rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3">Thí sinh</th>
                <th className="text-left px-4 py-3">Đơn vị</th>
                <th className="text-center px-4 py-3">Trạng thái</th>
                <th className="text-center px-4 py-3">Tiến độ</th>
                <th className="text-center px-4 py-3">Còn lại</th>
                <th className="text-center px-4 py-3">Vi phạm</th>
                <th className="text-center px-4 py-3">Kết nối</th>
                <th className="text-center px-4 py-3">Bài làm</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.length === 0 && (
                <tr><td colSpan={8} className="text-center py-10 text-gray-400">Không có thí sinh</td></tr>
              )}
              {rows.map((t) => {
                const pct = t.tong_so_cau > 0 ? Math.round((t.so_cau_da_lam / t.tong_so_cau) * 100) : 0;
                return (
                  <tr key={t.cong_chuc_id} className={t.trang_thai === 'DANG_THI' ? 'bg-amber-50/40' : ''}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{t.ho_ten || '—'}</div>
                      <div className="text-xs text-gray-400">{t.ma_cc}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{t.don_vi_ten || '—'}</td>
                    <td className="px-4 py-3 text-center">{trangThaiBadge(t.trang_thai)}</td>
                    <td className="px-4 py-3">
                      {t.trang_thai === 'CHUA_THI' ? (
                        <span className="text-gray-300">—</span>
                      ) : (
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden min-w-[60px]">
                            <div className="h-full bg-blue-500" style={{ width: `${pct}%` }} />
                          </div>
                          <span className="text-xs text-gray-500 whitespace-nowrap">{t.so_cau_da_lam}/{t.tong_so_cau}</span>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center font-mono text-xs">
                      {t.trang_thai === 'DANG_THI' ? (
                        <span className={(t.thoi_gian_con_lai_giay ?? 0) < 300 ? 'text-red-600 font-bold' : 'text-gray-700'}>
                          {fmtTime(t.thoi_gian_con_lai_giay)}
                        </span>
                      ) : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {t.so_lan_vi_pham > 0 ? (
                        <button
                          type="button"
                          onClick={() => setViPhamTarget({ ccId: t.cong_chuc_id, hoTen: t.ho_ten || undefined })}
                          className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-bold hover:bg-red-200 hover:underline cursor-pointer"
                          title="Bấm để xem chi tiết: giờ vi phạm + lý do giải trình"
                        >
                          {t.so_lan_vi_pham}
                        </button>
                      ) : <span className="text-gray-300">0</span>}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {t.online ? (
                        <span className="inline-flex items-center gap-1 text-green-600 text-xs font-medium">
                          <span className="h-2 w-2 rounded-full bg-green-500" /> Online
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-gray-400 text-xs">
                          <span className="h-2 w-2 rounded-full bg-gray-300" /> Offline
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {t.trang_thai === 'DA_NOP' ? (
                        <Link
                          href={`/dao-tao/ky-thi/${kyThiId}/thi-sinh/${t.cong_chuc_id}/bai-lam`}
                          className="text-blue-600 hover:underline text-xs"
                        >
                          Xem
                        </Link>
                      ) : <span className="text-gray-300 text-xs">—</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {viPhamTarget && (
        <ViPhamDetailModal
          kyThiId={kyThiId}
          congChucId={viPhamTarget.ccId}
          hoTen={viPhamTarget.hoTen}
          onClose={() => setViPhamTarget(null)}
        />
      )}
    </div>
  );
}

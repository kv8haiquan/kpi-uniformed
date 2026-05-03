/**
 * /hop-khong-giay/ — Lịch họp.
 *
 * MVP: table view (calendar lib chưa có trong codebase, không cài thêm).
 * Filter: ngày, đơn vị, khối, trạng thái.
 *
 * 03/05/2026: thêm cột "Hành động" với nút "Sửa" cho chu_toa / thu_ky /
 * admin / TRUONG_CNTT / CHANH_VP. Mở SuaCuocHopModal sửa meta cuộc họp.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { CalendarPlus, Loader2, Pencil, Users, UsersRound } from 'lucide-react';
import { cuocHopApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import { useAuthStore } from '@/stores/useAuthStore';
import { getPlatformRolesFromToken } from '@/lib/jwt-claims';
import SuaCuocHopModal from '@/components/hkg/SuaCuocHopModal';
import SuaThanhPhanModalById from '@/components/hkg/SuaThanhPhanModalById';
import type { ICuocHopListItem, Khoi, TrangThaiCuocHop } from '@/types/hkg';

const KHOI_LABELS: Record<Khoi, string> = {
  DANG: 'Đảng',
  CHUYEN_MON: 'Chuyên môn',
  HANH_CHINH: 'Hành chính',
  BAN_NHOM: 'Ban / Nhóm',
};

const TRANG_THAI_LABELS: Record<TrangThaiCuocHop, string> = {
  LEN_KE_HOACH: 'Lên kế hoạch',
  DA_THONG_BAO: 'Đã thông báo',
  DANG_DIEN_RA: 'Đang diễn ra',
  HOAN_THANH: 'Hoàn thành',
  HUY: 'Hủy',
};

const TRANG_THAI_BADGE: Record<TrangThaiCuocHop, string> = {
  LEN_KE_HOACH: 'bg-gray-100 text-gray-800',
  DA_THONG_BAO: 'bg-blue-100 text-blue-800',
  DANG_DIEN_RA: 'bg-yellow-100 text-yellow-800',
  HOAN_THANH: 'bg-green-100 text-green-800',
  HUY: 'bg-red-100 text-red-800',
};

export default function LichHopPage() {
  const [items, setItems] = useState<ICuocHopListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterKhoi, setFilterKhoi] = useState<string>('');
  const [filterTrangThai, setFilterTrangThai] = useState<string>('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingThanhPhanId, setEditingThanhPhanId] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const { user } = useAuthStore();

  // Tính các flag user-level (không phụ thuộc từng row) — memo để tránh re-decode JWT.
  const userFlags = useMemo(() => {
    if (!user) return null;
    const vt = (user.vai_tro?.ma_vai_tro as string | undefined) || '';
    const isOrgAdmin =
      user.is_system_admin ||
      vt === 'CCT' ||
      vt === 'PCCT' ||
      vt === 'SUPER_ADMIN' ||
      vt === 'ADMIN';
    const platformRoles = user.platform_roles ?? getPlatformRolesFromToken();
    const hasPlatformEdit =
      platformRoles.includes('TRUONG_CNTT') || platformRoles.includes('CHANH_VP');
    return {
      userId: user.id,
      isOrgAdmin,
      hasPlatformEdit,
    };
  }, [user]);

  const canEditItem = (it: ICuocHopListItem): boolean => {
    if (!userFlags) return false;
    if (userFlags.isOrgAdmin || userFlags.hasPlatformEdit) return true;
    if (it.chu_toa_id === userFlags.userId) return true;
    if (it.thu_ky_id && it.thu_ky_id === userFlags.userId) return true;
    return false;
  };

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      setError(null);
      try {
        const params: Record<string, string> = {};
        if (filterKhoi) params.khoi = filterKhoi;
        if (filterTrangThai) params.trang_thai = filterTrangThai;
        const resp = await cuocHopApi.danhSach({ ...params, page: 1, limit: 50 });
        setItems(resp.data.data);
      } catch (e: unknown) {
        setError(errMsg(e, 'Lỗi tải danh sách'));
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [filterKhoi, filterTrangThai, reloadKey]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-3">
          <select
            value={filterKhoi}
            onChange={(e) => setFilterKhoi(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded text-sm bg-white"
          >
            <option value="">Mọi khối</option>
            {Object.entries(KHOI_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <select
            value={filterTrangThai}
            onChange={(e) => setFilterTrangThai(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded text-sm bg-white"
          >
            <option value="">Mọi trạng thái</option>
            {Object.entries(TRANG_THAI_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/hop-khong-giay/nhom"
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 bg-white text-gray-700 rounded text-sm font-medium hover:bg-gray-50"
          >
            <UsersRound className="w-4 h-4" />
            Nhóm thành phần
          </Link>
          <Link
            href="/hop-khong-giay/tao-hop"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700"
          >
            <CalendarPlus className="w-4 h-4" />
            Tạo cuộc họp
          </Link>
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 p-6 text-gray-600">
          <Loader2 className="w-4 h-4 animate-spin" /> Đang tải...
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="p-8 text-center text-gray-500 bg-white rounded border">
          Chưa có cuộc họp nào.
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="overflow-x-auto bg-white rounded border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-700">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Tiêu đề</th>
                <th className="px-4 py-2 text-left font-medium">Khối</th>
                <th className="px-4 py-2 text-left font-medium">Ngày họp</th>
                <th className="px-4 py-2 text-left font-medium">Giờ</th>
                <th className="px-4 py-2 text-left font-medium">Trạng thái</th>
                <th className="px-4 py-2 text-left font-medium">Thành phần</th>
                <th className="px-4 py-2 text-left font-medium">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map((it) => {
                const editable = canEditItem(it);
                const isCancelled = it.trang_thai === 'HUY';
                const isFinalised = it.trang_thai === 'HOAN_THANH';
                const lockReason = isCancelled
                  ? 'Cuộc họp đã hủy — không sửa được'
                  : isFinalised
                  ? 'Cuộc họp đã hoàn thành — không sửa được'
                  : '';
                const showButton = editable;
                return (
                  <tr key={it.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2">
                      <Link
                        href={`/hop-khong-giay/chi-tiet/${it.id}`}
                        className="text-blue-600 hover:underline font-medium"
                      >
                        {it.tieu_de}
                      </Link>
                    </td>
                    <td className="px-4 py-2">{KHOI_LABELS[it.khoi]}</td>
                    <td className="px-4 py-2">{it.ngay_hop}</td>
                    <td className="px-4 py-2">{it.gio_bat_dau}</td>
                    <td className="px-4 py-2">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${TRANG_THAI_BADGE[it.trang_thai]}`}
                      >
                        {TRANG_THAI_LABELS[it.trang_thai]}
                      </span>
                    </td>
                    <td className="px-4 py-2">{it.so_thanh_phan}</td>
                    <td className="px-4 py-2">
                      {showButton ? (
                        <div className="flex flex-wrap gap-1">
                          <button
                            onClick={() => setEditingId(it.id)}
                            disabled={isCancelled || isFinalised}
                            title={lockReason || 'Sửa thông tin cuộc họp'}
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs border border-blue-300 text-blue-700 rounded hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                            Sửa
                          </button>
                          <button
                            onClick={() => setEditingThanhPhanId(it.id)}
                            disabled={isCancelled || isFinalised}
                            title={lockReason || 'Sửa thành phần tham dự'}
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs border border-blue-300 text-blue-700 rounded hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <Users className="w-3.5 h-3.5" />
                            Thành phần
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {editingId && (
        <SuaCuocHopModal
          cuocHopId={editingId}
          onClose={() => setEditingId(null)}
          onSaved={() => setReloadKey((k) => k + 1)}
        />
      )}

      {editingThanhPhanId && (
        <SuaThanhPhanModalById
          cuocHopId={editingThanhPhanId}
          onClose={() => setEditingThanhPhanId(null)}
          onSaved={() => setReloadKey((k) => k + 1)}
        />
      )}
    </div>
  );
}

/**
 * Layout chi tiết cuộc họp — header + 4 tabs + share state qua MeetingContext.
 *
 * G4-fix-4 (01/05/2026): banner đỏ "ĐÃ HỦY" khi trang_thai=HUY,
 * isLocked context để tabs hide mutation buttons.
 */

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import { AlertOctagon, ArrowLeft, Lock } from 'lucide-react';
import { cuocHopApi } from '@/services/hkg';
import type { ICuocHop, TrangThaiCuocHop } from '@/types/hkg';
import { MeetingProvider } from '@/components/hkg/MeetingContext';
import { useAuthStore } from '@/stores/useAuthStore';
import { getPlatformRolesFromToken } from '@/lib/jwt-claims';

const TABS = [
  { key: '', label: 'Tổng quan' },
  { key: 'tai-lieu', label: 'Tài liệu' },
  { key: 'diem-danh', label: 'Điểm danh' },
  { key: 'bien-ban', label: 'Biên bản' },
  { key: 'ket-luan', label: 'Kết luận' },
];

const TRANG_THAI_LABELS: Record<TrangThaiCuocHop, string> = {
  LEN_KE_HOACH: 'Lên kế hoạch',
  DA_THONG_BAO: 'Đã thông báo',
  DANG_DIEN_RA: 'Đang diễn ra',
  HOAN_THANH: 'Hoàn thành',
  HUY: 'Đã hủy',
};

export default function ChiTietLayout({ children }: { children: React.ReactNode }) {
  const { id } = useParams<{ id: string }>();
  const pathname = usePathname();
  const { user } = useAuthStore();
  const [ch, setCh] = useState<ICuocHop | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await cuocHopApi.chiTiet(id);
      setCh(data);
    } catch {
      setCh(null);
    }
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const isCancelled = ch?.trang_thai === 'HUY';
  const isLocked = isCancelled || ch?.trang_thai === 'HOAN_THANH';

  // G4-fix-7: tính canEdit từ user + ch
  const currentUserId = user?.id ?? null;
  const canEdit = useMemo(() => {
    if (!ch || !user) return false;
    if (user.is_system_admin) return true;
    // Cast vai_tro qua string để bypass MaVaiTro narrow (BE có thể trả ADMIN/SUPER_ADMIN
    // ngoài MaVaiTro enum định nghĩa).
    const vt = user.vai_tro?.ma_vai_tro as string | undefined;
    if (vt === 'CCT' || vt === 'PCCT' || vt === 'SUPER_ADMIN' || vt === 'ADMIN') {
      return true;
    }
    const platformRoles = user.platform_roles ?? getPlatformRolesFromToken();
    if (
      platformRoles.includes('TRUONG_CNTT') ||
      platformRoles.includes('CHANH_VP')
    ) {
      return true;
    }
    if (ch.chu_toa_id === user.id || ch.thu_ky_id === user.id) return true;
    return false;
  }, [ch, user]);

  return (
    <MeetingProvider value={{ ch, isCancelled, isLocked, canEdit, currentUserId, refresh }}>
      <div>
        <div className="mb-3">
          <Link
            href="/hop-khong-giay"
            className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-blue-700"
          >
            <ArrowLeft className="w-4 h-4" />
            Quay lại danh sách họp
          </Link>
        </div>

        {isCancelled && (
          <div className="mb-4 p-4 bg-red-50 border-2 border-red-300 rounded flex items-start gap-3">
            <AlertOctagon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-800">Cuộc họp đã hủy</p>
              <p className="text-sm text-red-700 mt-1">
                Trang chi tiết hiển thị ở chế độ <strong>chỉ đọc</strong>. Mọi thao tác chỉnh sửa
                (upload tài liệu, ký biên bản, giao nhiệm vụ, v.v.) đã bị vô hiệu hoá.
              </p>
            </div>
          </div>
        )}

        {!isCancelled && ch?.trang_thai === 'HOAN_THANH' && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-300 rounded flex items-start gap-2 text-sm">
            <Lock className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-amber-800">
              Cuộc họp đã hoàn thành — chỉ đọc. Có thể xem biên bản, kết luận và cập nhật tiến độ
              nhiệm vụ.
            </div>
          </div>
        )}

        <div className="bg-white border rounded p-4 mb-4">
          {ch ? (
            <>
              <h2 className="text-xl font-semibold">
                {ch.tieu_de}{' '}
                {isCancelled && (
                  <span className="ml-2 px-2 py-0.5 bg-red-600 text-white text-xs font-medium rounded">
                    ĐÃ HỦY
                  </span>
                )}
              </h2>
              <div className="text-sm text-gray-600 mt-2 flex flex-wrap gap-x-6 gap-y-1">
                <span>Ngày: {ch.ngay_hop}</span>
                <span>Giờ: {ch.gio_bat_dau}</span>
                <span>Trạng thái: {TRANG_THAI_LABELS[ch.trang_thai]}</span>
                <span>Khối: {ch.khoi}</span>
              </div>
            </>
          ) : (
            <div className="text-gray-500">Đang tải...</div>
          )}
        </div>

        <div className="flex border-b mb-4 bg-white rounded-t">
          {TABS.map((tab) => {
            const href = `/hop-khong-giay/chi-tiet/${id}${tab.key ? '/' + tab.key : ''}`;
            const isActive =
              tab.key === ''
                ? pathname === href || pathname === `${href}/`
                : pathname.endsWith('/' + tab.key);
            return (
              <Link
                key={tab.key}
                href={href}
                className={`px-4 py-2 text-sm font-medium border-b-2 ${
                  isActive
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>

        <div>{children}</div>
      </div>
    </MeetingProvider>
  );
}

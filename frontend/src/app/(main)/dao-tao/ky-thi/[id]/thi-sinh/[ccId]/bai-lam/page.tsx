/**
 * src/app/(main)/dao-tao/ky-thi/[id]/thi-sinh/[ccId]/bai-lam/page.tsx
 * ====================================================================
 * Trang admin xem bai lam chi tiet cua 1 thi sinh trong ky thi DGNL.
 * Yeu cau quyen: SUPER_ADMIN / QT_DAO_TAO / CCT / PCCT.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { kyThiApi } from '@/services/lms';
import type { IDgnlKetQua } from '@/types/lms';
import DgnlKetQuaDetail from '@/components/lms/DgnlKetQuaDetail';

export default function BaiLamThiSinhPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const kyThiId = params.id as string;
  const ccId = params.ccId as string;
  // Optional ?lan=N -> drill-down 1 lan thi cu the. Khong co thi mac dinh lan hien tai.
  const lanParam = searchParams.get('lan');
  const lan = lanParam ? Number(lanParam) : null;

  const [ketQua, setKetQua] = useState<IDgnlKetQua | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<number | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = lan && Number.isFinite(lan)
          ? await kyThiApi.ketQuaLan(kyThiId, ccId, lan)
          : await kyThiApi.ketQuaCBCC(kyThiId, ccId);
        setKetQua(res.data.data);
      } catch (err: any) {
        const status = err?.response?.status;
        setErrorCode(status || null);
        if (status === 403) {
          setError('Bạn không có quyền xem bài làm của thí sinh này.');
        } else if (status === 404) {
          setError(
            lan
              ? `Không tìm thấy dữ liệu lần thi ${lan} — có thể là lần thi cũ chưa lưu chi tiết.`
              : 'Không tìm thấy bài làm — thí sinh có thể chưa nộp bài.'
          );
        } else {
          setError(
            err?.response?.data?.detail?.error?.message || 'Không thể tải bài làm thí sinh'
          );
        }
      } finally {
        setLoading(false);
      }
    };
    if (kyThiId && ccId) load();
  }, [kyThiId, ccId, lan]);

  const backHref = `/dao-tao/ky-thi/${kyThiId}/thong-ke`;

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
        <div
          className={`border rounded-lg p-4 ${
            errorCode === 403
              ? 'bg-amber-50 border-amber-200 text-amber-800'
              : 'bg-red-50 border-red-200 text-red-700'
          }`}
        >
          {error || 'Chưa có dữ liệu bài làm'}
        </div>
        <Link
          href={backHref}
          className="mt-4 inline-block text-blue-600 hover:underline text-sm"
        >
          ← Quay lại thống kê kỳ thi
        </Link>
      </div>
    );
  }

  // Khi xem lan cu (lan != lan_thi_hien_tai), hien badge "Lần cũ" o header
  const isLanCu = lan !== null && lan !== ketQua.ket_qua.lan_thi;

  return (
    <DgnlKetQuaDetail
      ketQua={ketQua}
      backHref={backHref}
      backLabel="← Quay lại thống kê"
      title="Bài làm của thí sinh"
      adminViewBanner
      lanHienThi={lan ?? undefined}
      isLanCu={isLanCu}
      lanSelector={
        <LanSelector
          ketQua={ketQua}
          currentLan={lan ?? ketQua.ket_qua.lan_thi}
          onChange={(newLan) => {
            const isLatest = newLan === ketQua.ket_qua.lan_thi;
            // Khi chon lan moi nhat -> xoa ?lan de URL goi /ket-qua/{ccId} canonical
            const url = isLatest
              ? `/dao-tao/ky-thi/${kyThiId}/thi-sinh/${ccId}/bai-lam`
              : `/dao-tao/ky-thi/${kyThiId}/thi-sinh/${ccId}/bai-lam?lan=${newLan}`;
            router.replace(url);
          }}
        />
      }
    />
  );
}

function LanSelector({
  ketQua, currentLan, onChange,
}: {
  ketQua: IDgnlKetQua;
  currentLan: number;
  onChange: (lan: number) => void;
}) {
  // Build danh sach lan tu lich_su_thi (summary), bo sung lan hien tai neu thieu.
  const options = useMemo(() => {
    const lichSu = ketQua.lich_su_thi || [];
    const lanHienTai = ketQua.ket_qua.lan_thi;
    const items = lichSu.map((e) => ({
      lan: e.lan,
      hasChiTiet: e.has_chi_tiet,
      isCurrent: e.lan === lanHienTai,
    }));
    if (!items.some((it) => it.lan === lanHienTai) && lanHienTai > 0) {
      // Lan hien tai luon co chi_tiet thong qua endpoint /ket-qua/{ccId}
      items.push({ lan: lanHienTai, hasChiTiet: true, isCurrent: true });
    }
    items.sort((a, b) => a.lan - b.lan);
    return items;
  }, [ketQua]);

  if (options.length <= 1) return null;

  return (
    <label className="ml-2 inline-flex items-center gap-1.5 text-xs font-normal text-gray-600">
      <span>Xem lần:</span>
      <select
        value={currentLan}
        onChange={(e) => onChange(Number(e.target.value))}
        className="border border-gray-300 rounded px-2 py-1 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
      >
        {options.map((opt) => (
          <option
            key={opt.lan}
            value={opt.lan}
            disabled={!opt.hasChiTiet}
            title={!opt.hasChiTiet ? 'Lần thi cũ chưa lưu chi tiết câu trả lời' : undefined}
          >
            Lần {opt.lan}
            {opt.isCurrent ? ' (mới nhất)' : ''}
            {!opt.hasChiTiet ? ' — không có chi tiết' : ''}
          </option>
        ))}
      </select>
    </label>
  );
}

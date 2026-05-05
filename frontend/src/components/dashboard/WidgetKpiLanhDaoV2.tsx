/**
 * src/components/dashboard/WidgetKpiLanhDaoV2.tsx
 * ===============================================
 * Widget hiển thị KPI lãnh đạo công thức MỚI (từ tháng 4/2026).
 *
 * Hiển thị cho user có cap_bac ∈ {PDV, TDV, PCCT, CCT} khi tháng đang xem
 * ≥ tháng triển khai (mặc định 4/2026).
 *
 * Dữ liệu: GET /api/v1/kpi-lanh-dao-v2/me?thang=&nam=
 *
 * Phiên bản: 1.0 (05/05/2026)
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { kpiLanhDaoV2Service } from '@/services/kpiLanhDaoV2.service';
import { IKpiLanhDaoV2 } from '@/types/kpiLanhDaoV2';

interface Props {
  thang: number;
  nam: number;
  /** Cấp bậc của user — chỉ render widget nếu là LĐ */
  capBac: string | null | undefined;
  /** Có phải Admin không (để hiển thị nút seed phân công nếu missing) */
  isAdmin?: boolean;
  /** Có phải CCT không (để hiển thị nút seed phân công nếu missing) */
  isCCT?: boolean;
}

const LANH_DAO_CAP_BAC = new Set([
  'PHO_DON_VI',
  'TRUONG_DON_VI',
  'PHO_CHI_CUC_TRUONG',
  'CHI_CUC_TRUONG',
]);

const FROM_THANG = 4;
const FROM_NAM = 2026;

function isV2Active(thang: number, nam: number): boolean {
  return nam > FROM_NAM || (nam === FROM_NAM && thang >= FROM_THANG);
}

function pct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}

function kpiBadgeColor(kpi: number): string {
  if (kpi >= 0.9) return 'bg-green-100 text-green-800 border-green-300';
  if (kpi >= 0.75) return 'bg-blue-100 text-blue-800 border-blue-300';
  if (kpi >= 0.5) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
  return 'bg-red-100 text-red-800 border-red-300';
}

const CAP_BAC_LABEL: Record<string, string> = {
  PDV: 'Phó đơn vị',
  TDV: 'Trưởng đơn vị',
  PCCT: 'Phó Chi cục trưởng',
  CCT: 'Chi cục trưởng',
};

export default function WidgetKpiLanhDaoV2({ thang, nam, capBac, isAdmin, isCCT }: Props) {
  const router = useRouter();
  const [data, setData] = useState<IKpiLanhDaoV2 | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isLeader = !!capBac && LANH_DAO_CAP_BAC.has(capBac);
  const v2Active = isV2Active(thang, nam);

  useEffect(() => {
    if (!isLeader || !v2Active) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    kpiLanhDaoV2Service
      .getMyKpi(thang, nam)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) {
          const msg =
            e?.response?.data?.detail?.error?.message ||
            e?.response?.data?.detail ||
            'Không tải được KPI lãnh đạo';
          setError(typeof msg === 'string' ? msg : 'Không tải được KPI lãnh đạo');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [thang, nam, isLeader, v2Active]);

  if (!isLeader) return null;

  // Nếu tháng chưa active V2 → ẩn widget (không gây nhiễu)
  if (!v2Active) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <span className="text-xl">🎯</span>
            KPI Lãnh đạo (công thức mới)
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Tháng {thang}/{nam} — {data ? CAP_BAC_LABEL[data.cap_bac] || data.cap_bac : '...'}
          </p>
        </div>
        {data && (
          <span
            className={`px-3 py-1 rounded-full border text-sm font-bold ${kpiBadgeColor(data.kpi_tong)}`}
          >
            {pct(data.kpi_tong)}
          </span>
        )}
      </div>

      {loading && (
        <div className="text-center py-6 text-sm text-gray-500">Đang tải KPI...</div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && data && (
        <>
          {/* Cảnh báo: chưa có phân công cho PCCT/CCT */}
          {(data.cap_bac === 'PCCT' || data.cap_bac === 'CCT') && data.has_phan_cong === false && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded text-sm">
              <div className="flex items-start gap-2">
                <span className="text-lg">⚠️</span>
                <div>
                  <p className="font-medium text-amber-900">Chưa có phân công đơn vị phụ trách</p>
                  <p className="text-xs text-amber-700 mt-1">
                    KPI hiện tại chỉ tính d/đ/e (= 0.5). Để tính đủ, vui lòng cấu hình
                    phân công đơn vị phụ trách.
                  </p>
                  {(isAdmin || isCCT) && (
                    <button
                      onClick={() => router.push('/phan-cong-phu-trach')}
                      className="mt-2 text-xs font-medium text-amber-900 underline hover:text-amber-700"
                    >
                      → Đi tới trang phân công
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Tổng quan SP */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <Stat label="Tổng CV" value={data.tong_cv.toLocaleString()} />
            <Stat label="Hoàn thành" value={data.tong_hoan_thanh.toLocaleString()} />
            <Stat
              label="CV của CC / LĐ"
              value={`${data.tong_cv_cc.toLocaleString()} / ${data.tong_cv_ld.toLocaleString()}`}
              small
            />
          </div>

          {/* 6 chỉ số */}
          <div className="border-t border-gray-100 pt-3">
            <p className="text-xs font-medium text-gray-600 mb-2">
              6 chỉ số KPI (trung bình → KPI tổng)
            </p>
            <div className="grid grid-cols-6 gap-2">
              <ChiSo label="a" tooltip="Tỉ lệ hoàn thành" value={data.a} />
              <ChiSo label="b" tooltip="Đúng tiến độ" value={data.b} />
              <ChiSo label="c" tooltip="Đạt chất lượng" value={data.c} />
              <ChiSo label="d" tooltip="Kết quả đơn vị" value={data.d} />
              <ChiSo label="đ" tooltip="Tổ chức triển khai" value={data.dd} />
              <ChiSo label="e" tooltip="Đoàn kết nội bộ" value={data.e} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value, small }: { label: string; value: string; small?: boolean }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <div className={`font-bold text-gray-900 ${small ? 'text-sm' : 'text-xl'}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}

function ChiSo({ label, tooltip, value }: { label: string; tooltip: string; value: number }) {
  const pctStr = (value * 100).toFixed(1);
  const color =
    value >= 0.9 ? 'text-green-700' : value >= 0.75 ? 'text-blue-700' : value >= 0.5 ? 'text-yellow-700' : 'text-red-700';
  return (
    <div className="text-center" title={tooltip}>
      <div className="text-xs text-gray-500 font-medium">{label}</div>
      <div className={`font-bold text-base ${color}`}>{pctStr}%</div>
    </div>
  );
}

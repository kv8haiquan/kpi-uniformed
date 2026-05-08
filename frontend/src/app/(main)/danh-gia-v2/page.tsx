'use client';

/**
 * src/app/(main)/danh-gia-v2/page.tsx
 * ====================================
 * Trang Đánh giá KPI V2_PL3 (29/04/2026).
 *
 * Khác /danh-gia (V1):
 * - Mẫu số = TỔNG SP đã kê khai (sum so_sp_goc_quy_doi) — KHÔNG phải ngày × 96.
 * - 3 chỉ số a/b/c = SP đạt / Mẫu số V2.
 * - Bỏ block ngày làm việc / target SP1 cũ.
 * - Tab Tạm tính (NHAP+CHO+DA) vs Chính thức (chỉ DA).
 *
 * KPI = (a + b + c) / 3 × 70  →  cộng tiêu chí chung 30 → tổng 100.
 */

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { kpiV2Service } from '@/services/kpi-v2.service';
import { tieuChiChungService } from '@/services/tieu-chi-chung.service';
import { kpiLanhDaoV2Service } from '@/services/kpiLanhDaoV2.service';
import { IKpiLanhDaoV2 } from '@/types/kpiLanhDaoV2';
import LeaderCongViecTable from '@/components/danh-gia-v2/LeaderCongViecTable';
import LichSuDieuChinhModal from '@/components/danh-gia-v2/LichSuDieuChinhModal';
import { isApiError } from '@/lib/axios';
import { IThongKeKeKhaiThangV2, IKeKhaiV2Response } from '@/types/kpi-v2';
import {
  IKetQuaTieuChiChungResponse,
  TrangThaiTieuChiChung,
} from '@/types/tieu-chi-chung';

// =============================================================================
// HELPERS
// =============================================================================

type XepLoai = 'A' | 'B' | 'C' | 'D' | 'E';
type KPITab = 'tam_tinh' | 'chinh_thuc';

function tinhXepLoai(diem: number): XepLoai {
  if (diem === 0) return 'E';
  if (diem < 50) return 'D';
  if (diem < 70) return 'C';
  if (diem < 90) return 'B';
  return 'A';
}

function getXepLoaiColor(xl: XepLoai) {
  const map: Record<XepLoai, { bg: string; text: string; border: string }> = {
    A: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300' },
    B: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300' },
    C: { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-300' },
    D: { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300' },
    E: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300' },
  };
  return map[xl];
}


function fmt(n: number, _digits = 6) {
  if (!Number.isFinite(n)) return '0';
  return n.toFixed(6).replace(/\.?0+$/, '');
}
function pct(v: number, _digits = 6) {
  // Hiển thị tối đa 6 chữ số thập phân (strip trailing zeros). Tránh nhảy lên
  // 100% khi v thực sự < 1 (do làm tròn floating-point).
  const value = v * 100;
  if (v < 1 && value >= 100) {
    const truncated = Math.floor(value * 1e6) / 1e6;
    return truncated.toFixed(6).replace(/\.?0+$/, '') + '%';
  }
  return value.toFixed(6).replace(/\.?0+$/, '') + '%';
}

const TRANG_THAI_LABEL: Record<string, string> = {
  NHAP: 'Nháp',
  CHO_PHE_DUYET: 'Chờ duyệt',
  DA_PHE_DUYET: 'Đã duyệt',
  TU_CHOI: 'Bị từ chối',
  HUY: 'Đã hủy',
};
const TRANG_THAI_BADGE: Record<string, string> = {
  NHAP: 'bg-gray-100 text-gray-700',
  CHO_PHE_DUYET: 'bg-yellow-100 text-yellow-800',
  DA_PHE_DUYET: 'bg-green-100 text-green-800',
  TU_CHOI: 'bg-red-100 text-red-800',
  HUY: 'bg-gray-200 text-gray-500',
};

// =============================================================================
// SUB COMPONENTS
// =============================================================================

function StatBox({
  label,
  value,
  subLabel,
  bgColor,
  textColor,
}: {
  label: string;
  value: string | number;
  subLabel?: string;
  bgColor: string;
  textColor: string;
}) {
  return (
    <div className={`${bgColor} rounded-lg p-3 text-center`}>
      <p className={`text-xs ${textColor}`}>{label}</p>
      <p className={`text-xl font-bold ${textColor.replace('600', '700')}`}>
        {value}
      </p>
      {subLabel && (
        <p className="text-xs text-gray-400 mt-0.5">{subLabel}</p>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  subValue,
  color,
  percent,
}: {
  label: string;
  value: string;
  subValue: string;
  color: 'indigo' | 'emerald' | 'amber';
  percent: number;
}) {
  const colorMap = {
    indigo: { bg: 'bg-indigo-600', text: 'text-indigo-700' },
    emerald: { bg: 'bg-emerald-600', text: 'text-emerald-700' },
    amber: { bg: 'bg-amber-600', text: 'text-amber-700' },
  };
  const c = colorMap[color];
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{label}</span>
        <span className={`text-xl font-bold ${c.text}`}>{value}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div
          className={`${c.bg} h-2 rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
      <p className="text-xs text-gray-500">{subValue}</p>
    </div>
  );
}

/** Card hiển thị 1 chỉ số (a/b/c) cho LĐ — 2 dòng: LĐ tự kê + Tổng phụ trách */
function LeaderAbcCard({
  label,
  color,
  selfPercent,
  selfSubValue,
  totalPercent,
  totalSubValue,
}: {
  label: string;
  color: 'indigo' | 'emerald' | 'amber';
  selfPercent: number;
  selfSubValue: string;
  totalPercent: number;
  totalSubValue: string;
}) {
  const colorMap = {
    indigo: { bg: 'bg-indigo-600', text: 'text-indigo-700', soft: 'bg-indigo-50' },
    emerald: { bg: 'bg-emerald-600', text: 'text-emerald-700', soft: 'bg-emerald-50' },
    amber: { bg: 'bg-amber-600', text: 'text-amber-700', soft: 'bg-amber-50' },
  };
  const c = colorMap[color];
  const fmtPct = (p: number) => `${p.toFixed(6).replace(/\.?0+$/, '')}%`;
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
      <div className="text-sm font-semibold text-gray-800 mb-3">{label}</div>

      {/* Hàng 1: LĐ tự kê */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-500 font-medium">LĐ tự kê</span>
          <span className={`text-sm font-bold ${c.text}`}>{fmtPct(selfPercent)}</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-1.5 mb-1">
          <div
            className={`${c.bg} h-1.5 rounded-full transition-all duration-500`}
            style={{ width: `${Math.min(selfPercent, 100)}%` }}
          />
        </div>
        <p className="text-[11px] text-gray-400">{selfSubValue}</p>
      </div>

      {/* Hàng 2: Tổng phụ trách */}
      <div className={`${c.soft} -mx-4 -mb-4 p-3 rounded-b-xl border-t border-gray-100`}>
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-700 font-semibold">Tổng phụ trách</span>
          <span className={`text-base font-bold ${c.text}`}>{fmtPct(totalPercent)}</span>
        </div>
        <div className="w-full bg-white/60 rounded-full h-2 mb-1">
          <div
            className={`${c.bg} h-2 rounded-full transition-all duration-500`}
            style={{ width: `${Math.min(totalPercent, 100)}%` }}
          />
        </div>
        <p className="text-[11px] text-gray-600">{totalSubValue}</p>
      </div>
    </div>
  );
}

function ScoreCard({
  title,
  subtitle,
  value,
  maxValue,
  color,
  onClick,
}: {
  title: string;
  subtitle: string;
  value: number;
  maxValue: number;
  color: 'emerald' | 'indigo' | 'purple';
  onClick?: () => void;
}) {
  const colorMap = {
    emerald: {
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-700',
      accent: 'text-emerald-600',
    },
    indigo: {
      bg: 'bg-indigo-50',
      border: 'border-indigo-200',
      text: 'text-indigo-700',
      accent: 'text-indigo-600',
    },
    purple: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      text: 'text-purple-700',
      accent: 'text-purple-600',
    },
  };
  const c = colorMap[color];
  const percent = maxValue > 0 ? (value / maxValue) * 100 : 0;
  return (
    <div
      className={`${c.bg} ${c.border} border rounded-xl p-5 ${
        onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className={`text-sm font-medium ${c.accent}`}>{title}</p>
          <p className="text-xs text-gray-500">{subtitle}</p>
        </div>
        <div className="text-right">
          <p className={`text-3xl font-bold ${c.text}`}>{value.toFixed(6).replace(/\.?0+$/, '')}</p>
          <p className="text-xs text-gray-500">/ {maxValue} điểm</p>
        </div>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${
            color === 'emerald'
              ? 'bg-emerald-500'
              : color === 'indigo'
              ? 'bg-indigo-500'
              : 'bg-purple-500'
          }`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
      {onClick && (
        <p className={`text-xs ${c.accent} mt-2 text-center`}>
          Bấm để xem chi tiết →
        </p>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function DanhGiaV2Page() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  const currentDate = new Date();
  const [selectedThang, setSelectedThang] = useState(currentDate.getMonth() + 1);
  const [selectedNam, setSelectedNam] = useState(currentDate.getFullYear());

  const [thongKe, setThongKe] = useState<IThongKeKeKhaiThangV2 | null>(null);
  const [list, setList] = useState<IKeKhaiV2Response[]>([]);
  const [tieuChi, setTieuChi] = useState<IKetQuaTieuChiChungResponse | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [tab, setTab] = useState<KPITab>('chinh_thuc');
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);
  // Modal lịch sử điều chỉnh CV (Yêu cầu 2)
  const [lichSuKkId, setLichSuKkId] = useState<string | null>(null);

  // Force LĐ V2 về tab "Chính thức" (V2 service chưa hỗ trợ tạm tính scope mở rộng)

  // Phase 3 KPI LĐ V2 (05/05/2026): KPI mới cho LĐ thật + tháng ≥ 4/2026
  const isLanhDao = user?.is_lanh_dao ?? false;
  const isHd111 = user?.is_hd_111 ?? false;
  const isV2ActiveForLeader =
    isLanhDao && !isHd111 &&
    (selectedNam > 2026 || (selectedNam === 2026 && selectedThang >= 4));
  const [kpiV2LD, setKpiV2LD] = useState<IKpiLanhDaoV2 | null>(null);

  // Auth gate
  useEffect(() => {
    if (!isAuthenticated) router.push('/login');
  }, [isAuthenticated, router]);

  // (LĐ V2 đã hỗ trợ tab tạm tính từ 05/05/2026 — không force tab nữa.)

  // Redirect:
  // - HĐ 111 → /danh-gia (form cũ)
  // - LĐ thật + tháng < 4/2026 → /danh-gia (form cũ)
  // - CC pinned V1 → /danh-gia
  // - LĐ thật V2 + CC V2 → ở lại /danh-gia-v2
  useEffect(() => {
    if (!user) return;
    if (user.is_hd_111) {
      router.replace('/danh-gia');
      return;
    }
    if (user.is_lanh_dao && !isV2ActiveForLeader) {
      router.replace('/danh-gia');
      return;
    }
    if (!user.is_lanh_dao && user.effective_kpi_version === 'V1') {
      router.replace('/danh-gia');
    }
  }, [user, router, isV2ActiveForLeader]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [thongKeRes, listRes, tcRes, kpiV2LDRes] = await Promise.allSettled([
        kpiV2Service.getThongKeThang(selectedThang, selectedNam),
        kpiV2Service.getMyKeKhai({
          thang: selectedThang,
          nam: selectedNam,
          page_size: 100,
        }),
        tieuChiChungService.getKetQuaThang(selectedThang, selectedNam),
        // LĐ thật + tháng ≥ 4/2026: load KPI V2 theo TAB (chính thức / tạm tính)
        isV2ActiveForLeader
          ? kpiLanhDaoV2Service.getMyKpi(selectedThang, selectedNam, tab === 'tam_tinh')
          : Promise.resolve(null),
      ]);
      if (thongKeRes.status === 'fulfilled') setThongKe(thongKeRes.value);
      if (listRes.status === 'fulfilled') setList(listRes.value.data);
      if (tcRes.status === 'fulfilled') setTieuChi(tcRes.value);
      if (kpiV2LDRes.status === 'fulfilled' && kpiV2LDRes.value) {
        setKpiV2LD(kpiV2LDRes.value as IKpiLanhDaoV2);
      } else {
        setKpiV2LD(null);
      }
    } catch (err: unknown) {
      console.error(err);
      setError(isApiError(err) ? err.message : 'Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  }, [selectedThang, selectedNam, isV2ActiveForLeader, tab]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ===========================================================================
  // TÍNH KPI
  // ===========================================================================

  // Mẫu số: tab tạm tính = du_kien (NHAP+CHO+DA), tab chính thức = da_duyet
  // LĐ V2: ƯU TIÊN số liệu từ /kpi-lanh-dao-v2/me (scope mở rộng) cho CẢ 2 tab
  // — backend reload data theo tab (tam_tinh=true/false).
  const useLeaderV2 = kpiV2LD !== null && isV2ActiveForLeader;

  const mauSoChinhThuc = useLeaderV2
    ? kpiV2LD!.tong_sp_ke_khai
    : thongKe?.tong_sp_da_duyet ?? 0;
  const mauSoTamTinh = thongKe?.tong_sp_du_kien ?? 0;
  const mauSo = tab === 'chinh_thuc' ? mauSoChinhThuc : mauSoTamTinh;

  const tongSpHoanThanh = useLeaderV2
    ? kpiV2LD!.tong_sp_hoan_thanh
    : (tab === 'chinh_thuc' ? mauSoChinhThuc : mauSoTamTinh);
  const tongSpCL = useLeaderV2
    ? kpiV2LD!.sp_chat_luong
    : (tab === 'chinh_thuc'
        ? thongKe?.tong_sp_chat_luong_da_duyet ?? 0
        : thongKe?.tong_sp_chat_luong_tam_tinh ?? 0);
  const tongSpTD = useLeaderV2
    ? kpiV2LD!.sp_tien_do
    : (tab === 'chinh_thuc'
        ? thongKe?.tong_sp_tien_do_da_duyet ?? 0
        : thongKe?.tong_sp_tien_do_tam_tinh ?? 0);

  // 3 chỉ số (V2: mẫu số = tổng SP kê khai)
  const a = useLeaderV2 ? kpiV2LD!.a : (mauSo > 0 ? Math.min(tongSpHoanThanh / mauSo, 1) : 0);
  const b = useLeaderV2 ? kpiV2LD!.b : (mauSo > 0 ? Math.min(tongSpCL / mauSo, 1) : 0);
  const c = useLeaderV2 ? kpiV2LD!.c : (mauSo > 0 ? Math.min(tongSpTD / mauSo, 1) : 0);

  // d, đ, e — chỉ áp cho LĐ thật V2
  const d = useLeaderV2 ? kpiV2LD!.d : 0;
  const dd = useLeaderV2 ? kpiV2LD!.dd : 0;
  const e = useLeaderV2 ? kpiV2LD!.e : 0;

  // KPI ratio:
  // - LĐ V2: (a+b+c+d+đ+e)/6
  // - CC V2: (a+b+c)/3
  const kpiRatio = useLeaderV2
    ? (a + b + c + d + dd + e) / 6
    : (a + b + c) / 3;
  const diemKPI = kpiRatio * 70;

  // ===========================================================================
  // TIÊU CHÍ CHUNG
  // ===========================================================================
  const isNewTC = !tieuChi || tieuChi.is_new_record;
  const tcDaPheDuyet = tieuChi?.trang_thai === TrangThaiTieuChiChung.DA_PHE_DUYET;
  const tcChuaPheDuyet = !isNewTC && !tcDaPheDuyet;
  const diemTieuChi = tieuChi?.tong_hop?.tong_diem ?? 0;

  // Tab chính thức + chưa duyệt → TC = 0; tab tạm tính → tự chấm
  const diemTCHienThi = tab === 'chinh_thuc' && tcChuaPheDuyet ? 0 : diemTieuChi;
  const diemTong = diemTCHienThi + diemKPI;
  const xepLoai = tinhXepLoai(diemTong);
  const xlColor = getXepLoaiColor(xepLoai);

  // Stats kê khai (CC V2: từ thongKe; LĐ V2: từ kpiV2LD scope mở rộng)
  const soDaDuyet = useLeaderV2
    ? (kpiV2LD!.so_kekhai_records ?? 0)
    : (thongKe?.so_kekhai_da_duyet ?? 0);
  const soChoDuyet = useLeaderV2 ? 0 : (thongKe?.so_kekhai_cho_duyet ?? 0);
  const soNhap = useLeaderV2 ? 0 : (thongKe?.so_kekhai_nhap ?? 0);
  const tongTamTinh = soDaDuyet + soChoDuyet + soNhap;

  // Empty state: CC V2 = 0 kê khai; LĐ V2 LUÔN có d/đ/e (mặc định 1.0)
  // → không bao giờ empty, vẫn render widget để LĐ thấy đủ 6 chỉ số.
  const isEmptyKPI = useLeaderV2 ? false : (tongTamTinh === 0);

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Banner phiên bản */}
        <div className="mb-4 rounded-md border border-blue-200 bg-blue-50 px-4 py-3 flex items-start justify-between gap-3 text-sm">
          <div className="text-blue-900">
            <strong>Phiên bản KPI V2_PL3.</strong> Mẫu số ={' '}
            <strong>tổng điểm đã kê khai</strong> (không phải ngày × 96).{' '}
            Xem chi tiết tại{' '}
            <a href="/ke-khai-v2" className="font-semibold underline">
              /ke-khai-v2
            </a>
            .
          </div>
        </div>

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.push('/dashboard')}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title="Quay lại Dashboard"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  📊 Đánh giá KPI (V2_PL3)
                </h1>
                <p className="text-gray-600 mt-1">
                  Tháng {selectedThang}/{selectedNam} • Công thức V2 (mẫu số = tổng điểm kê khai)
                </p>
              </div>
            </div>
            <div className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-700">
              {user?.ho_ten ?? '—'}
            </div>
          </div>

          <div className="flex items-center gap-4 mt-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Tháng:</label>
              <select
                value={selectedThang}
                onChange={(e) => setSelectedThang(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>
                    Tháng {m}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Năm:</label>
              <select
                value={selectedNam}
                onChange={(e) => setSelectedNam(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              >
                {[2025, 2026, 2027].map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Tab selector */}
        {!loading && !error && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1.5 mb-6 flex gap-2">
            <button
              onClick={() => setTab('tam_tinh')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                tab === 'tam_tinh'
                  ? 'bg-amber-50 text-amber-700 border-2 border-amber-300 shadow-sm'
                  : 'text-gray-500 hover:bg-gray-50 border-2 border-transparent'
              }`}
            >
              <span>📝</span>
              <span>Tạm tính</span>
              <span className={`px-2 py-0.5 text-xs rounded-full ${
                tab === 'tam_tinh' ? 'bg-amber-200 text-amber-800' : 'bg-gray-100 text-gray-600'
              }`}>
                {tongTamTinh}
              </span>
            </button>
            <button
              onClick={() => setTab('chinh_thuc')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                tab === 'chinh_thuc'
                  ? 'bg-green-50 text-green-700 border-2 border-green-300 shadow-sm'
                  : 'text-gray-500 hover:bg-gray-50 border-2 border-transparent'
              }`}
            >
              <span>✅</span>
              <span>Chính thức</span>
              <span className={`px-2 py-0.5 text-xs rounded-full ${
                tab === 'chinh_thuc' ? 'bg-green-200 text-green-800' : 'bg-gray-100 text-gray-600'
              }`}>
                {soDaDuyet}
              </span>
            </button>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <span className="ml-3 text-gray-600">Đang tải dữ liệu...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-6">
            {/* TỔNG HỢP */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">
                  🎯 Tổng hợp điểm tháng {selectedThang}/{selectedNam}
                </h2>
                {tab === 'chinh_thuc' && tcChuaPheDuyet ? (
                  <div className="bg-gray-100 border border-gray-300 rounded-lg px-4 py-2">
                    <p className="text-xs text-gray-500">Mức đánh giá</p>
                    <p className="text-lg font-bold text-gray-400">—</p>
                    <p className="text-xs text-gray-400">Chờ phê duyệt TC</p>
                  </div>
                ) : (
                  <div
                    className={`${xlColor.bg} ${xlColor.border} border rounded-lg px-4 py-2`}
                  >
                    <p className="text-xs text-gray-500">
                      Mức đánh giá {tab === 'tam_tinh' ? '(Tạm tính)' : ''}
                    </p>
                    <p className={`text-2xl font-bold ${xlColor.text}`}>{xepLoai}</p>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <ScoreCard
                  title="Tiêu chí chung"
                  subtitle={
                    tab === 'tam_tinh'
                      ? 'Điểm tự chấm'
                      : tcChuaPheDuyet
                      ? 'Chờ phê duyệt'
                      : 'Đã phê duyệt'
                  }
                  value={diemTCHienThi}
                  maxValue={30}
                  color="emerald"
                  onClick={() => router.push('/danh-gia/tu-cham-diem')}
                />
                <ScoreCard
                  title={`Điểm KPI ${tab === 'tam_tinh' ? '(Tạm tính)' : ''}`}
                  subtitle={useLeaderV2 ? '6 chỉ số (a, b, c, d, đ, e)' : '3 chỉ số V2 (a, b, c)'}
                  value={diemKPI}
                  maxValue={70}
                  color="indigo"
                  onClick={() => router.push('/ke-khai-v2')}
                />
                <ScoreCard
                  title={`Điểm tổng ${tab === 'tam_tinh' ? '(Tạm tính)' : ''}`}
                  subtitle="= TC chung + KPI"
                  value={diemTong}
                  maxValue={100}
                  color="purple"
                />
              </div>

              {tab === 'tam_tinh' && (
                <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <p className="text-sm text-amber-700">
                    ⚠️ <strong>Lưu ý:</strong> Điểm tạm tính dựa trên TẤT CẢ kê khai
                    (Nháp + Chờ duyệt + Đã duyệt) và điểm tự chấm tiêu chí chung. Điểm
                    chính thức tính sau khi lãnh đạo phê duyệt từng bản.
                  </p>
                </div>
              )}
            </div>

            {/* BLOCK KPI V2 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">
                  📊 KPI V2_PL3 (70 điểm)
                </h2>
                <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium text-white">
                  {tab === 'tam_tinh' ? 'Tạm tính' : 'Chính thức'}
                </span>
              </div>
              <div className="p-6">
                {isEmptyKPI ? (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Chưa có kê khai V2
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Bạn chưa kê khai công việc tháng này.
                    </p>
                    <button
                      onClick={() => router.push('/ke-khai-v2')}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                    >
                      Bắt đầu kê khai V2
                    </button>
                  </div>
                ) : (
                  <>
                    {/* StatBox */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
                      <StatBox
                        label="Mẫu số V2 (điểm)"
                        value={fmt(mauSo, 2)}
                        subLabel={
                          useLeaderV2
                            ? `${soDaDuyet} bản trong scope`
                            : tab === 'tam_tinh'
                              ? `${tongTamTinh} bản`
                              : `${soDaDuyet} bản đã duyệt`
                        }
                        bgColor="bg-blue-50"
                        textColor="text-blue-600"
                      />
                      <StatBox
                        label="Tổng điểm hoàn thành"
                        value={fmt(tongSpHoanThanh, 2)}
                        bgColor="bg-green-50"
                        textColor="text-green-600"
                      />
                      <StatBox
                        label="Tổng điểm đạt CL"
                        value={fmt(tongSpCL, 2)}
                        bgColor="bg-emerald-50"
                        textColor="text-emerald-600"
                      />
                      <StatBox
                        label="Tổng điểm đạt TĐ"
                        value={fmt(tongSpTD, 2)}
                        bgColor="bg-amber-50"
                        textColor="text-amber-600"
                      />
                      <StatBox
                        label="Điểm KPI"
                        value={`${diemKPI.toFixed(6).replace(/\.?0+$/, '')}/70`}
                        bgColor="bg-purple-50"
                        textColor="text-purple-600"
                      />
                    </div>

                    {/* Chỉ số KPI: CC V2 = 3 cards a/b/c; LĐ V2 = 6 cards với
                        a/b/c có 2 dòng (LĐ tự kê + Tổng phụ trách) + d/đ/e */}
                    <h3 className="text-sm font-medium text-gray-700 mb-4">
                      {useLeaderV2 ? 'Sáu chỉ số KPI Lãnh đạo (a, b, c, d, đ, e)' : 'Ba chỉ số (a, b, c)'}
                    </h3>

                    {useLeaderV2 ? (
                      <>
                        {/* HÀNG 1: a / b / c — mỗi card 2 dòng (Tự kê + Tổng) */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <LeaderAbcCard
                            label="a. Tỷ lệ Số lượng"
                            color="indigo"
                            selfPercent={kpiV2LD!.a_self * 100}
                            selfSubValue={`${fmt(kpiV2LD!.tong_sp_ke_khai_self, 2)} / ${fmt(kpiV2LD!.tong_sp_ke_khai_self, 2)} điểm`}
                            totalPercent={a * 100}
                            totalSubValue={`${fmt(tongSpHoanThanh, 2)} / ${fmt(mauSo, 2)} điểm`}
                          />
                          <LeaderAbcCard
                            label="b. Tỷ lệ Chất lượng"
                            color="emerald"
                            selfPercent={kpiV2LD!.b_self * 100}
                            selfSubValue={`${fmt(kpiV2LD!.sp_chat_luong_self, 2)} / ${fmt(kpiV2LD!.tong_sp_ke_khai_self, 2)} điểm`}
                            totalPercent={b * 100}
                            totalSubValue={`${fmt(tongSpCL, 2)} / ${fmt(mauSo, 2)} điểm`}
                          />
                          <LeaderAbcCard
                            label="c. Tỷ lệ Tiến độ"
                            color="amber"
                            selfPercent={kpiV2LD!.c_self * 100}
                            selfSubValue={`${fmt(kpiV2LD!.sp_tien_do_self, 2)} / ${fmt(kpiV2LD!.tong_sp_ke_khai_self, 2)} điểm`}
                            totalPercent={c * 100}
                            totalSubValue={`${fmt(tongSpTD, 2)} / ${fmt(mauSo, 2)} điểm`}
                          />
                        </div>

                        {/* HÀNG 2: d/đ/e từ danh_gia_dde */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                          <MetricCard
                            label="d. Kết quả đơn vị"
                            value={pct(d)}
                            subValue={d >= 1 ? '100% (đạt)' : '50% (không đạt)'}
                            color="indigo"
                            percent={d * 100}
                          />
                          <MetricCard
                            label="đ. Tổ chức triển khai"
                            value={pct(dd)}
                            subValue={dd >= 1 ? '100% (đạt)' : '50% (không đạt)'}
                            color="emerald"
                            percent={dd * 100}
                          />
                          <MetricCard
                            label="e. Đoàn kết nội bộ"
                            value={pct(e)}
                            subValue={e >= 1 ? '100% (đạt)' : '50% (không đạt)'}
                            color="amber"
                            percent={e * 100}
                          />
                        </div>
                      </>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <MetricCard
                          label="a. Tỷ lệ Số lượng"
                          value={pct(a)}
                          subValue={`${fmt(tongSpHoanThanh, 2)} / ${fmt(mauSo, 2)} điểm`}
                          color="indigo"
                          percent={a * 100}
                        />
                        <MetricCard
                          label="b. Tỷ lệ Chất lượng"
                          value={pct(b)}
                          subValue={`${fmt(tongSpCL, 2)} / ${fmt(mauSo, 2)} điểm`}
                          color="emerald"
                          percent={b * 100}
                        />
                        <MetricCard
                          label="c. Tỷ lệ Tiến độ"
                          value={pct(c)}
                          subValue={`${fmt(tongSpTD, 2)} / ${fmt(mauSo, 2)} điểm`}
                          color="amber"
                          percent={c * 100}
                        />
                      </div>
                    )}

                    {/* Công thức */}
                    <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
                      {useLeaderV2 ? (
                        <>
                          <p className="text-sm text-gray-600 text-center">
                            <strong>Công thức Lãnh đạo V2:</strong> Điểm KPI =
                            (a + b + c + d + đ + e) / 6 × 70
                          </p>
                          <p className="text-sm text-gray-700 text-center mt-1">
                            ({pct(a, 2)} + {pct(b, 2)} + {pct(c, 2)} +{' '}
                            {pct(d, 2)} + {pct(dd, 2)} + {pct(e, 2)}) / 6 × 70 ={' '}
                            <strong className="text-indigo-700">
                              {diemKPI.toFixed(6).replace(/\.?0+$/, '')} điểm
                            </strong>
                          </p>
                          <p className="text-xs text-gray-500 text-center mt-2">
                            Mẫu số = Σ điểm đã kê khai trong scope phụ trách (
                            {kpiV2LD?.cap_bac === 'PDV' && 'điểm tự kê + điểm CC do mình duyệt'}
                            {kpiV2LD?.cap_bac === 'TDV' && 'toàn bộ điểm đơn vị'}
                            {(kpiV2LD?.cap_bac === 'PCCT' || kpiV2LD?.cap_bac === 'CCT') &&
                              'gộp điểm các đơn vị phụ trách'}
                            ) — chỉ tính bản đã DA_PHE_DUYET
                          </p>
                          {(kpiV2LD?.cap_bac === 'PCCT' || kpiV2LD?.cap_bac === 'CCT') &&
                            kpiV2LD?.has_phan_cong === false && (
                              <p className="text-xs text-amber-700 text-center mt-2 font-medium">
                                ⚠️ Chưa có phân công đơn vị phụ trách — KPI hiện chỉ tính d/đ/e.
                              </p>
                            )}
                        </>
                      ) : (
                        <>
                          <p className="text-sm text-gray-600 text-center">
                            <strong>Công thức V2:</strong> Điểm KPI = (a + b + c) / 3 × 70 ={' '}
                            <span className="text-indigo-600 font-medium">
                              ({pct(a, 2)} + {pct(b, 2)} + {pct(c, 2)}) / 3 × 70
                            </span>{' '}
                            ={' '}
                            <strong className="text-indigo-700">
                              {diemKPI.toFixed(6).replace(/\.?0+$/, '')} điểm
                            </strong>
                          </p>
                          <p className="text-xs text-gray-500 text-center mt-1">
                            Mẫu số V2 = Σ điểm kê khai (
                            {tab === 'tam_tinh'
                              ? 'Nháp + Chờ + Đã duyệt'
                              : 'chỉ Đã duyệt'}
                            )
                          </p>
                        </>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* BLOCK CHI TIẾT CV TRONG SCOPE LĐ (Yêu cầu 1, 06/05/2026) — chỉ LĐ thật V2 */}
            {useLeaderV2 && (
              <LeaderCongViecTable
                thang={selectedThang}
                nam={selectedNam}
                tamTinh={tab === 'tam_tinh'}
              />
            )}

            {/* BLOCK CHI TIẾT KÊ KHAI V2 (collapsible chi tiết lỗi) — CC V2 */}
            {list.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-base font-medium text-gray-900">
                    Chi tiết các bản kê khai ({list.length})
                  </h2>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Bấm vào dòng có badge lỗi để xem mô tả. Bấm <b>Lịch sử</b> để xem các lần lãnh đạo điều chỉnh CV (nếu có).
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Mã</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Công việc</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">SL</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Hệ số</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Điểm gốc</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Điểm CL</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Điểm TĐ</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Lỗi</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Trạng thái</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Lịch sử</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                      {list.map((kk) => {
                        const tdgCl = kk.tu_danh_gia_chat_luong || 0;
                        const tdgTd = kk.tu_danh_gia_tien_do || 0;
                        const ldCl = kk.so_loi_chat_luong || 0;
                        const ldTd = kk.so_loi_tien_do || 0;
                        const hasErr = tdgCl + tdgTd + ldCl + ldTd > 0;
                        const hasDesc = !!(
                          kk.ghi_chu_tu_dg_chat_luong ||
                          kk.ghi_chu_tu_dg_tien_do ||
                          kk.ghi_chu_loi_chat_luong ||
                          kk.ghi_chu_loi_tien_do ||
                          kk.ghi_chu_tu_danh_gia ||
                          kk.y_kien_lanh_dao
                        );
                        const isExpanded = expandedRowId === kk.id;
                        return (
                          <>
                            <tr
                              key={kk.id}
                              className={isExpanded ? 'bg-gray-50' : 'hover:bg-gray-50'}
                            >
                              <td className="px-4 py-2 text-xs font-mono text-gray-600">
                                {kk.danh_muc_sp?.ma_danh_muc ?? '—'}
                              </td>
                              <td className="px-4 py-2 text-sm">
                                <p className="text-gray-900 line-clamp-2">
                                  {kk.danh_muc_sp?.ten_cong_viec ?? '—'}
                                </p>
                                <p className="text-[11px] text-gray-500 mt-0.5">
                                  Lĩnh vực {kk.linh_vuc_snapshot} • Nhóm{' '}
                                  {kk.nhom_pl3_snapshot}
                                </p>
                              </td>
                              <td className="px-4 py-2 text-right text-sm">{kk.so_luong}</td>
                              <td className="px-4 py-2 text-right text-sm font-mono text-blue-700">
                                {kk.he_so_quy_doi_snapshot?.toFixed(6).replace(/\.?0+$/, '') ?? '—'}
                              </td>
                              <td className="px-4 py-2 text-right text-sm font-mono">
                                {kk.so_sp_goc_quy_doi?.toFixed(6).replace(/\.?0+$/, '') ?? '—'}
                              </td>
                              <td className="px-4 py-2 text-right text-sm font-mono text-emerald-700">
                                {kk.so_sp_chat_luong?.toFixed(6).replace(/\.?0+$/, '') ?? '—'}
                              </td>
                              <td className="px-4 py-2 text-right text-sm font-mono text-amber-700">
                                {kk.so_sp_tien_do?.toFixed(6).replace(/\.?0+$/, '') ?? '—'}
                              </td>
                              <td className="px-4 py-2 text-center">
                                {hasErr ? (
                                  <button
                                    onClick={() =>
                                      setExpandedRowId(isExpanded ? null : kk.id)
                                    }
                                    className="inline-flex flex-col items-center gap-0.5 group cursor-pointer"
                                    title="Bấm xem chi tiết"
                                  >
                                    {(tdgCl > 0 || tdgTd > 0) && (
                                      <span className="text-[11px] px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 group-hover:bg-orange-200">
                                        TĐG: CL{tdgCl}/TĐ{tdgTd}
                                      </span>
                                    )}
                                    {(ldCl > 0 || ldTd > 0) && (
                                      <span className="text-[11px] px-1.5 py-0.5 rounded bg-red-100 text-red-700 group-hover:bg-red-200">
                                        LĐ: CL{ldCl}/TĐ{ldTd}
                                      </span>
                                    )}
                                    {hasDesc && (
                                      <svg
                                        className={`w-3.5 h-3.5 text-gray-400 transition-transform ${
                                          isExpanded ? 'rotate-180' : ''
                                        }`}
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                      >
                                        <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M19 9l-7 7-7-7"
                                        />
                                      </svg>
                                    )}
                                  </button>
                                ) : (
                                  <span className="text-gray-300 text-xs">—</span>
                                )}
                              </td>
                              <td className="px-4 py-2 text-center">
                                <span
                                  className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                                    TRANG_THAI_BADGE[kk.trang_thai] ??
                                    'bg-gray-100 text-gray-600'
                                  }`}
                                >
                                  {TRANG_THAI_LABEL[kk.trang_thai] ?? kk.trang_thai}
                                </span>
                              </td>
                              <td className="px-4 py-2 text-center">
                                <button
                                  onClick={() => setLichSuKkId(kk.id)}
                                  className="text-xs text-blue-600 hover:text-blue-800 hover:underline font-medium"
                                  title="Xem lịch sử lãnh đạo điều chỉnh CV này"
                                >
                                  Xem
                                </button>
                              </td>
                            </tr>
                            {isExpanded && hasErr && (
                              <tr key={`${kk.id}-detail`} className="bg-gray-50">
                                <td colSpan={10} className="px-6 py-3">
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                    {(tdgCl > 0 || tdgTd > 0) && (
                                      <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                                        <h4 className="font-medium text-orange-800 mb-2">
                                          🧑 Tự đánh giá
                                        </h4>
                                        <div className="space-y-1.5">
                                          {tdgCl > 0 && (
                                            <div>
                                              <span className="text-orange-700 font-medium">
                                                Lỗi chất lượng: {tdgCl}
                                              </span>
                                              {kk.ghi_chu_tu_dg_chat_luong && (
                                                <p className="text-orange-600 mt-0.5 pl-3 border-l-2 border-orange-300 whitespace-pre-wrap">
                                                  {kk.ghi_chu_tu_dg_chat_luong}
                                                </p>
                                              )}
                                            </div>
                                          )}
                                          {tdgTd > 0 && (
                                            <div>
                                              <span className="text-orange-700 font-medium">
                                                Lỗi tiến độ: {tdgTd}
                                              </span>
                                              {kk.ghi_chu_tu_dg_tien_do && (
                                                <p className="text-orange-600 mt-0.5 pl-3 border-l-2 border-orange-300 whitespace-pre-wrap">
                                                  {kk.ghi_chu_tu_dg_tien_do}
                                                </p>
                                              )}
                                            </div>
                                          )}
                                          {kk.ghi_chu_tu_danh_gia && (
                                            <div className="mt-1 pt-1 border-t border-orange-200">
                                              <span className="text-orange-600 text-xs">
                                                Ghi chú chung:
                                              </span>
                                              <p className="text-orange-600 whitespace-pre-wrap">
                                                {kk.ghi_chu_tu_danh_gia}
                                              </p>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    )}
                                    {(ldCl > 0 || ldTd > 0) && (
                                      <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                                        <h4 className="font-medium text-red-800 mb-2">
                                          🛡 Lãnh đạo chốt
                                        </h4>
                                        <div className="space-y-1.5">
                                          {ldCl > 0 && (
                                            <div>
                                              <span className="text-red-700 font-medium">
                                                Lỗi chất lượng: {ldCl}
                                              </span>
                                              {kk.ghi_chu_loi_chat_luong && (
                                                <p className="text-red-600 mt-0.5 pl-3 border-l-2 border-red-300 whitespace-pre-wrap">
                                                  {kk.ghi_chu_loi_chat_luong}
                                                </p>
                                              )}
                                            </div>
                                          )}
                                          {ldTd > 0 && (
                                            <div>
                                              <span className="text-red-700 font-medium">
                                                Lỗi tiến độ: {ldTd}
                                              </span>
                                              {kk.ghi_chu_loi_tien_do && (
                                                <p className="text-red-600 mt-0.5 pl-3 border-l-2 border-red-300 whitespace-pre-wrap">
                                                  {kk.ghi_chu_loi_tien_do}
                                                </p>
                                              )}
                                            </div>
                                          )}
                                          {kk.y_kien_lanh_dao && (
                                            <div className="mt-1 pt-1 border-t border-red-200">
                                              <span className="text-red-600 text-xs">
                                                Ý kiến lãnh đạo:
                                              </span>
                                              <p className="text-red-600 whitespace-pre-wrap">
                                                {kk.y_kien_lanh_dao}
                                              </p>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            )}
                          </>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* THANG XẾP LOẠI */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="font-medium text-gray-900 mb-4">
                📊 Thang điểm mức đánh giá
              </h3>
              <div className="grid grid-cols-5 gap-3">
                {(['A', 'B', 'C', 'D', 'E'] as XepLoai[]).map((loai) => {
                  const cl = getXepLoaiColor(loai);
                  const isActive = loai === xepLoai;
                  return (
                    <div
                      key={loai}
                      className={`${cl.bg} ${cl.border} border rounded-lg p-3 text-center ${
                        isActive ? 'ring-2 ring-offset-2 ring-blue-500' : ''
                      }`}
                    >
                      <p className={`text-2xl font-bold ${cl.text}`}>{loai}</p>
                      <p className="text-xs text-gray-600 mt-1">
                        {loai === 'A' && '≥ 90đ'}
                        {loai === 'B' && '70-89đ'}
                        {loai === 'C' && '50-69đ'}
                        {loai === 'D' && '< 50đ'}
                        {loai === 'E' && '0đ'}
                      </p>
                    </div>
                  );
                })}
              </div>
              <p className="text-xs text-gray-500 mt-4 text-center">
                * Mức E: nghỉ thai sản hoặc mẫu số = 0
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Modal lịch sử điều chỉnh CV */}
      <LichSuDieuChinhModal
        open={lichSuKkId !== null}
        keKhaiId={lichSuKkId}
        onClose={() => setLichSuKkId(null)}
      />
    </div>
  );
}

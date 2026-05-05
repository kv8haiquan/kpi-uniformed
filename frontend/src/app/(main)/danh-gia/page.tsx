/**
 * src/app/(main)/danh-gia/page.tsx
 * ==================================
 * Trang Dashboard Đánh giá KPI Tổng hợp - Chi cục Hải quan KV8
 *
 * Hỗ trợ cả 2 đối tượng:
 * - Công chức: 3 chỉ số (a, b, c) từ SP
 * - Lãnh đạo: 6 chỉ số (a, b, c, d, đ, e) từ công việc + đánh giá DDE
 *
 * Version: 2.11.0 (02/02/2026)
 * UPDATE v2.11.0:
 * - FIX: Nút "Xuất báo cáo" hiện ở cả tab Tạm tính (label "Xuất tạm tính") 
 *   và tab Chính thức (label "Xuất báo cáo")
 * UPDATE v2.10.0:
 * - ADD: Global Tab Selector (Tạm tính / Chính thức) lên trên đầu trang
 *   để công chức nhìn rõ hơn, ảnh hưởng toàn bộ trang
 * - FIX: Tab Chính thức - Tiêu chí chung phải check trạng thái phê duyệt:
 *   + Nếu DA_PHE_DUYET → hiện điểm bình thường
 *   + Nếu chưa → hiện cảnh báo "Chờ lãnh đạo phê duyệt", điểm tự chấm mờ
 *   + Điểm tổng + xếp loại phần chính thức cũng ẩn khi TC chưa duyệt
 * - ADD: Badge trạng thái phê duyệt trên header Tiêu chí chung
 * UPDATE v2.9.0:
 * - ADD: Nút "Xuất báo cáo" DOCX/PDF cá nhân (Mẫu 01 + 02)
 * - Import ExportButton + exportService
 * UPDATE v2.8.3:
 * - FIX: Bỏ tất cả (thongKeLD as any) - IThongKeKeKhaiLanhDao đã có đủ typed fields
 * - FIX: Bỏ fallback null cho tong_diem_* - backend schema default=0 đảm bảo luôn có giá trị
 * - FIX: b, c lãnh đạo luôn dùng diemTienDoHienThi / diemChatLuongHienThi (không fallback)
 * - Logic công chức: GIỮ NGUYÊN 100%
 * UPDATE v2.8.2:
 * - FIX: Tab tạm tính dùng targetSP riêng (tính cả ngày nghỉ CHỜ PHÊ DUYỆT)
 *   Trước đây: targetSP cả 2 tab đều chỉ tính ngày nghỉ DA_PHE_DUYET → sai
 *   Sau fix: tab tạm tính dùng tamTinhTargetSP (CHO_PHE_DUYET + DA_PHE_DUYET)
 * - Hiển thị chi tiết "(Nghỉ: X duyệt + Y chờ)" khi tab tạm tính
 * UPDATE v2.8.1:
 * - FIX: Công thức tính b, c cho Lãnh đạo:
 *   b = Σ(max(0, 1 - lỗi_i × 0.25)) / Tổng CV
 *   c = Σ(max(0, 1 - lỗi_i × 0.25)) / Tổng CV
 * - Sử dụng tong_diem_tien_do, tong_diem_chat_luong từ backend
 * - Hiển thị số lỗi thay vì số CV đạt
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore, useIsHd111 } from '@/stores/useAuthStore';
import { kpiService } from '@/services/kpi.service';
import { tieuChiChungService } from '@/services/tieu-chi-chung.service';
import { leaveService } from '@/services/leave.service';
import { leaderKPIService } from '@/services/leader-kpi.service';
import { isApiError } from '@/lib/axios';
import { IKeKhaiMonthSummary } from '@/types/kpi';
import { IKetQuaTieuChiChungResponse, TrangThaiTieuChiChung } from '@/types/tieu-chi-chung';
import { IThongKeKeKhaiLanhDao, IDanhGiaDDEResponse } from '@/types/leader-kpi';
import ExportButton, { ExportFormat } from '@/components/common/ExportButton';
import { exportService } from '@/services/export.service';
import WidgetKpiLanhDaoV2 from '@/components/dashboard/WidgetKpiLanhDaoV2';

// =============================================================================
// CONSTANTS & HELPERS
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

function getXepLoaiColor(xepLoai: XepLoai): { bg: string; text: string; border: string } {
  const colors: Record<XepLoai, { bg: string; text: string; border: string }> = {
    'A': { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300' },
    'B': { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300' },
    'C': { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-300' },
    'D': { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300' },
    'E': { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300' },
  };
  return colors[xepLoai];
}

function getXepLoaiLabel(xepLoai: XepLoai): string {
  const labels: Record<XepLoai, string> = {
    'A': 'Hoàn thành xuất sắc',
    'B': 'Hoàn thành tốt',
    'C': 'Hoàn thành',
    'D': 'Không hoàn thành',
    'E': 'Không đánh giá',
  };
  return labels[xepLoai];
}

function formatPercent(value: number, decimals: number = 2): string {
  // Tránh làm tròn LÊN 100% khi tỷ lệ thực < 1.0
  // (vd 0.999 × 100 = 99.9 nhưng 0.99977 × 100 = 99.977, toFixed(1) → "100.0%" sai).
  const v = value * 100;
  if (value < 1) {
    const factor = Math.pow(10, decimals);
    return (Math.floor(v * factor) / factor).toFixed(decimals) + '%';
  }
  return v.toFixed(decimals) + '%';
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return '0';
  return Math.round(value).toLocaleString('vi-VN');
}

function getDaysInMonth(month: number, year: number): number {
  return new Date(year, month, 0).getDate();
}

// =============================================================================
// SUB COMPONENTS
// =============================================================================

interface ScoreCardProps {
  title: string;
  subtitle: string;
  value: number;
  maxValue: number;
  color: 'emerald' | 'indigo' | 'purple';
  onClick?: () => void;
}

function ScoreCard({ title, subtitle, value, maxValue, color, onClick }: ScoreCardProps) {
  const colorMap = {
    emerald: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700', accent: 'text-emerald-600' },
    indigo: { bg: 'bg-indigo-50', border: 'border-indigo-200', text: 'text-indigo-700', accent: 'text-indigo-600' },
    purple: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', accent: 'text-purple-600' },
  };
  const c = colorMap[color];
  const percent = maxValue > 0 ? (value / maxValue) * 100 : 0;

  return (
    <div 
      className={`${c.bg} ${c.border} border rounded-xl p-5 ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className={`text-sm font-medium ${c.accent}`}>{title}</p>
          <p className="text-xs text-gray-500">{subtitle}</p>
        </div>
        <div className="text-right">
          <p className={`text-3xl font-bold ${c.text}`}>{value.toFixed(2)}</p>
          <p className="text-xs text-gray-500">/ {maxValue} điểm</p>
        </div>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full transition-all duration-500 ${
            color === 'emerald' ? 'bg-emerald-500' : 
            color === 'indigo' ? 'bg-indigo-500' : 'bg-purple-500'
          }`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
      {onClick && <p className={`text-xs ${c.accent} mt-2 text-center`}>Bấm để xem chi tiết →</p>}
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  subValue: string;
  color: 'indigo' | 'emerald' | 'amber' | 'purple' | 'pink' | 'cyan';
  percent: number;
}

function MetricCard({ label, value, subValue, color, percent }: MetricCardProps) {
  const colorMap = {
    indigo: { bg: 'bg-indigo-600', text: 'text-indigo-700' },
    emerald: { bg: 'bg-emerald-600', text: 'text-emerald-700' },
    amber: { bg: 'bg-amber-600', text: 'text-amber-700' },
    purple: { bg: 'bg-purple-600', text: 'text-purple-700' },
    pink: { bg: 'bg-pink-600', text: 'text-pink-700' },
    cyan: { bg: 'bg-cyan-600', text: 'text-cyan-700' },
  };
  const c = colorMap[color];

  return (
    <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{label}</span>
        <span className={`text-xl font-bold ${c.text}`}>{value}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div className={`${c.bg} h-2 rounded-full transition-all duration-500`} style={{ width: `${Math.min(percent, 100)}%` }} />
      </div>
      <p className="text-xs text-gray-500">{subValue}</p>
    </div>
  );
}

// =============================================================================
// STAT BOX COMPONENT
// =============================================================================

interface StatBoxProps {
  label: string;
  value: string | number;
  subLabel?: string;
  bgColor: string;
  textColor: string;
}

function StatBox({ label, value, subLabel, bgColor, textColor }: StatBoxProps) {
  return (
    <div className={`${bgColor} rounded-lg p-3 text-center`}>
      <p className={`text-xs ${textColor}`}>{label}</p>
      <p className={`text-xl font-bold ${textColor.replace('600', '700')}`}>{value}</p>
      {subLabel && <p className="text-xs text-gray-400 mt-0.5">{subLabel}</p>}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function DanhGiaPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const isLanhDao = user?.is_lanh_dao ?? false;
  const isHd111 = useIsHd111();
  // HD-111 dùng cùng form kê khai lãnh đạo (kê khai từng CV với lỗi CL/TĐ)
  // nhưng chỉ tính 3 chỉ số (a, b, c) — không có d, đ, e.
  const usesLeaderForm = isLanhDao || isHd111;

  // State chung
  const [tieuChiChung, setTieuChiChung] = useState<IKetQuaTieuChiChungResponse | null>(null);
  const [nghiPhepData, setNghiPhepData] = useState<{
    tong_ngay_nghi: number;
    so_ngay_trong_thang: number;
    so_ngay_lam_viec: number;
    // v3.1: Tạm tính
    tam_tinh_ngay_nghi: number;
    tam_tinh_ngay_lam_viec: number;
    tam_tinh_sp_duoc_giao: number;
    cho_duyet_ngay_nghi: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State cho Công chức
  const [keKhaiSummaryCC, setKeKhaiSummaryCC] = useState<IKeKhaiMonthSummary | null>(null);

  // State cho Lãnh đạo
  const [thongKeLD, setThongKeLD] = useState<IThongKeKeKhaiLanhDao | null>(null);
  const [ddeData, setDdeData] = useState<IDanhGiaDDEResponse | null>(null);

  // State cho tab KPI (v2.7.0)
  const [kpiTab, setKpiTab] = useState<KPITab>('chinh_thuc');

  // Tháng/Năm
  const currentDate = new Date();
  const [selectedThang, setSelectedThang] = useState(currentDate.getMonth() + 1);
  const [selectedNam, setSelectedNam] = useState(currentDate.getFullYear());

  useEffect(() => {
    if (!isAuthenticated) router.push('/login');
  }, [isAuthenticated, router]);

  // V2 REDIRECT (02/05/2026) — chặn user vào nhầm trang đánh giá V1.
  // Lãnh đạo + HĐ 111 luôn được auth.py ép effective_kpi_version='V1'.
  useEffect(() => {
    if (user?.effective_kpi_version === 'V2_PL3') {
      router.replace('/danh-gia-v2');
    }
  }, [user?.effective_kpi_version, router]);

  // =========================================================================
  // LOAD DATA
  // =========================================================================
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (usesLeaderForm) {
        // LÃNH ĐẠO + HĐ 111: Load thống kê kê khai LĐ + Tiêu chí chung.
        // HĐ 111 không có d/đ/e (backend chặn) → bỏ qua DDE.
        const [thongKeResult, tcResult, ddeResult] = await Promise.allSettled([
          leaderKPIService.getThongKe(selectedThang, selectedNam),
          tieuChiChungService.getKetQuaThang(selectedThang, selectedNam),
          isHd111
            ? Promise.resolve(null)
            : leaderKPIService.getDanhGiaDDE(selectedThang, selectedNam),
        ]);

        if (thongKeResult.status === 'fulfilled') setThongKeLD(thongKeResult.value);
        if (tcResult.status === 'fulfilled') setTieuChiChung(tcResult.value);
        if (!isHd111 && ddeResult.status === 'fulfilled' && ddeResult.value) {
          console.log('[DanhGia] DDE data:', ddeResult.value);
          setDdeData(ddeResult.value as IDanhGiaDDEResponse);
        } else if (!isHd111 && ddeResult.status === 'rejected') {
          console.warn('[DanhGia] DDE load failed:', ddeResult.reason);
        }
      } else {
        // CÔNG CHỨC: Load kê khai SP + ngày nghỉ + tiêu chí chung
        const [keKhaiResult, nghiResult, tcResult] = await Promise.allSettled([
          kpiService.getMonthSummary(selectedThang, selectedNam),
          leaveService.getTongNgayNghiThangChiTiet(selectedThang, selectedNam),
          tieuChiChungService.getKetQuaThang(selectedThang, selectedNam),
        ]);

        if (keKhaiResult.status === 'fulfilled') setKeKhaiSummaryCC(keKhaiResult.value);
        if (nghiResult.status === 'fulfilled') setNghiPhepData(nghiResult.value);
        if (tcResult.status === 'fulfilled') setTieuChiChung(tcResult.value);
      }
    } catch (err) {
      setError(isApiError(err) ? err.message : 'Có lỗi xảy ra khi tải dữ liệu');
    } finally {
      setIsLoading(false);
    }
  }, [selectedThang, selectedNam, usesLeaderForm, isHd111]);

  useEffect(() => { loadData(); }, [loadData]);

  // =========================================================================
  // TÍNH TOÁN ĐIỂM - CÔNG CHỨC
  // =========================================================================
  const diemTieuChiChung = tieuChiChung?.tong_hop?.tong_diem ?? 0;
  const soNgayTrongThang = nghiPhepData?.so_ngay_trong_thang ?? getDaysInMonth(selectedThang, selectedNam);
  
  // Chính thức: chỉ DA_PHE_DUYET
  const tongNgayNghi = nghiPhepData?.tong_ngay_nghi ?? 0;
  const soNgayLamViec = nghiPhepData?.so_ngay_lam_viec ?? (soNgayTrongThang - tongNgayNghi);
  const targetSP = soNgayLamViec * 96;

  // ✅ FIX v3.1: Tạm tính ngày nghỉ (CHO_PHE_DUYET + DA_PHE_DUYET)
  const tamTinhNgayNghi = nghiPhepData?.tam_tinh_ngay_nghi ?? tongNgayNghi;
  const tamTinhNgayLamViec = nghiPhepData?.tam_tinh_ngay_lam_viec ?? soNgayLamViec;
  const tamTinhTargetSP = tamTinhNgayLamViec * 96;
  const choDuyetNgayNghi = nghiPhepData?.cho_duyet_ngay_nghi ?? 0;

  // Chính thức (chỉ DA_PHE_DUYET)
  const tongSPHoanThanh = keKhaiSummaryCC?.tong_sp_quy_doi ?? 0;
  const tongSPChatLuong = keKhaiSummaryCC?.tong_sp_chat_luong ?? 0;
  const tongSPTienDo = keKhaiSummaryCC?.tong_sp_tien_do ?? 0;

  // Tạm tính (NHAP + CHO_PHE_DUYET + DA_PHE_DUYET) - v2.7.0
  const tamTinhSPQuyDoi = keKhaiSummaryCC?.tam_tinh_sp_quy_doi ?? tongSPHoanThanh;
  const tamTinhSPChatLuong = keKhaiSummaryCC?.tam_tinh_sp_chat_luong ?? tongSPChatLuong;
  const tamTinhSPTienDo = keKhaiSummaryCC?.tam_tinh_sp_tien_do ?? tongSPTienDo;

  // Số lượng kê khai theo trạng thái
  const tongNhapChoDuyet = (keKhaiSummaryCC?.tong_nhap ?? 0) + (keKhaiSummaryCC?.tong_cho_duyet ?? 0);
  const tongDaDuyet = keKhaiSummaryCC?.tong_da_duyet ?? 0;

  // Chọn data theo tab
  const spQuyDoiHienThi = kpiTab === 'chinh_thuc' ? tongSPHoanThanh : tamTinhSPQuyDoi;
  const spChatLuongHienThi = kpiTab === 'chinh_thuc' ? tongSPChatLuong : tamTinhSPChatLuong;
  const spTienDoHienThi = kpiTab === 'chinh_thuc' ? tongSPTienDo : tamTinhSPTienDo;

  // ✅ FIX v3.1: Target SP phải dùng đúng ngày nghỉ theo tab
  const targetSPHienThi = kpiTab === 'chinh_thuc' ? targetSP : tamTinhTargetSP;
  const soNgayLamViecHienThi = kpiTab === 'chinh_thuc' ? soNgayLamViec : tamTinhNgayLamViec;
  const tongNgayNghiHienThi = kpiTab === 'chinh_thuc' ? tongNgayNghi : tamTinhNgayNghi;

  // Tính a, b, c cho công chức
  const aSoLuongCC = targetSPHienThi > 0 ? Math.min(spQuyDoiHienThi / targetSPHienThi, 1) : 0;
  const bChatLuongCC = targetSPHienThi > 0 ? Math.min(spChatLuongHienThi / targetSPHienThi, 1) : 0;
  const cTienDoCC = targetSPHienThi > 0 ? Math.min(spTienDoHienThi / targetSPHienThi, 1) : 0;

  const diemKPICC = (aSoLuongCC + bChatLuongCC + cTienDoCC) / 3;
  const diemKPIQuyDoiCC = diemKPICC * 70;

  // =========================================================================
  // TÍNH TOÁN ĐIỂM - LÃNH ĐẠO
  // =========================================================================
  // FIX v2.8.3: Bỏ tất cả (as any) - IThongKeKeKhaiLanhDao đã có đủ fields
  //             Bỏ fallback null - backend schema đã có default=0

  // Chính thức (chỉ DA_PHE_DUYET)
  const targetLD = thongKeLD?.tong_da_duyet ?? 0;
  const tongCVHoanThanh = thongKeLD?.tong_hoan_thanh ?? 0;

  // v2.6.5: Tổng điểm & lỗi từ backend (typed, không cần as any)
  const tongDiemChatLuong = thongKeLD?.tong_diem_chat_luong ?? 0;
  const tongDiemTienDo = thongKeLD?.tong_diem_tien_do ?? 0;
  const tongLoiChatLuong = thongKeLD?.tong_loi_chat_luong ?? 0;
  const tongLoiTienDo = thongKeLD?.tong_loi_tien_do ?? 0;

  // Tạm tính (v2.7.0) - typed access
  const tamTinhTargetLD = thongKeLD?.tam_tinh_tong_cong_viec ?? targetLD;
  const tamTinhCVHoanThanh = thongKeLD?.tam_tinh_hoan_thanh ?? tongCVHoanThanh;
  const tamTinhDiemChatLuong = thongKeLD?.tam_tinh_diem_chat_luong ?? 0;
  const tamTinhDiemTienDo = thongKeLD?.tam_tinh_diem_tien_do ?? 0;
  const tamTinhLoiChatLuong = thongKeLD?.tam_tinh_loi_chat_luong ?? tongLoiChatLuong;
  const tamTinhLoiTienDo = thongKeLD?.tam_tinh_loi_tien_do ?? tongLoiTienDo;

  // Số lượng kê khai theo trạng thái (lãnh đạo)
  const tongNhapChoDuyetLD = (thongKeLD?.tong_nhap ?? 0) + (thongKeLD?.tong_cho_duyet ?? 0);
  const tongDaDuyetLD = thongKeLD?.tong_da_duyet ?? 0;

  // Chọn data theo tab (lãnh đạo)
  const targetLDHienThi = kpiTab === 'chinh_thuc' ? targetLD : tamTinhTargetLD;
  const cvHoanThanhHienThi = kpiTab === 'chinh_thuc' ? tongCVHoanThanh : tamTinhCVHoanThanh;
  // v2.6.5: Hiển thị số lỗi
  const loiChatLuongHienThi = kpiTab === 'chinh_thuc' ? tongLoiChatLuong : tamTinhLoiChatLuong;
  const loiTienDoHienThi = kpiTab === 'chinh_thuc' ? tongLoiTienDo : tamTinhLoiTienDo;
  // Tổng điểm để tính b, c
  const diemChatLuongHienThi = kpiTab === 'chinh_thuc' ? tongDiemChatLuong : tamTinhDiemChatLuong;
  const diemTienDoHienThi = kpiTab === 'chinh_thuc' ? tongDiemTienDo : tamTinhDiemTienDo;

  // v2.8.3: Tính a, b, c cho lãnh đạo - KHÔNG CÒN FALLBACK
  // a = Số việc hoàn thành / Tổng việc
  // b = Tổng điểm tiến độ / Tổng việc (mỗi CV: điểm = max(0, 1 - lỗi × 0.25))
  // c = Tổng điểm chất lượng / Tổng việc
  const aLD = targetLDHienThi > 0 ? Math.min(cvHoanThanhHienThi / targetLDHienThi, 1) : 0;
  const bLD = targetLDHienThi > 0
    ? Math.min(diemTienDoHienThi / targetLDHienThi, 1)
    : 0;
  const cLD = targetLDHienThi > 0
    ? Math.min(diemChatLuongHienThi / targetLDHienThi, 1)
    : 0;

  // d, đ, e từ DDE (100 hoặc 50 → convert thành tỷ lệ)
  // v2.7.3: Dùng d_final (ưu tiên giá trị phê duyệt, fallback về tự đánh giá)
  const dLD = (ddeData?.d_final ?? ddeData?.d_ket_qua_don_vi ?? 100) / 100;
  const ddLD = (ddeData?.dd_final ?? ddeData?.dd_to_chuc_trien_khai ?? 100) / 100;
  const eLD = (ddeData?.e_final ?? ddeData?.e_doan_ket_noi_bo ?? 100) / 100;

  // Điểm KPI Lãnh đạo = (a + b + c + d + đ + e) / 6 × 70
  const diemKPILD = (aLD + bLD + cLD + dLD + ddLD + eLD) / 6;
  const diemKPIQuyDoiLD = diemKPILD * 70;

  // Điểm KPI HĐ 111 = (a + b + c) / 3 × 70 (cùng a/b/c như LĐ, bỏ d/đ/e)
  const diemKPIHd111 = (aLD + bLD + cLD) / 3;
  const diemKPIQuyDoiHd111 = diemKPIHd111 * 70;

  // =========================================================================
  // TỔNG ĐIỂM VÀ XẾP LOẠI
  // =========================================================================
  const diemKPIQuyDoi = isHd111
    ? diemKPIQuyDoiHd111
    : isLanhDao
      ? diemKPIQuyDoiLD
      : diemKPIQuyDoiCC;
  const diemTong = diemTieuChiChung + diemKPIQuyDoi;
  const xepLoai = tinhXepLoai(diemTong);
  const xepLoaiColor = getXepLoaiColor(xepLoai);

  // Kiểm tra dữ liệu mới
  const isNewKPI = usesLeaderForm
    ? (!thongKeLD || (thongKeLD.tong_da_duyet === 0 && thongKeLD.tong_cho_duyet === 0 && thongKeLD.tong_nhap === 0))
    : (!keKhaiSummaryCC || (keKhaiSummaryCC.tong_da_duyet === 0 && keKhaiSummaryCC.tong_cho_duyet === 0 && keKhaiSummaryCC.tong_nhap === 0));
  const isNewTC = !tieuChiChung || tieuChiChung.is_new_record;

  // Trạng thái kê khai
  const getTrangThaiKeKhai = () => {
    if (usesLeaderForm) {
      if (thongKeLD && thongKeLD.tong_da_duyet > 0) return 'DA_PHE_DUYET';
      if (thongKeLD && thongKeLD.tong_cho_duyet > 0) return 'CHO_PHE_DUYET';
      return 'NHAP';
    } else {
      if (keKhaiSummaryCC && keKhaiSummaryCC.tong_da_duyet > 0) return 'DA_PHE_DUYET';
      if (keKhaiSummaryCC && keKhaiSummaryCC.tong_cho_duyet > 0) return 'CHO_PHE_DUYET';
      return 'NHAP';
    }
  };
  const trangThaiKeKhai = getTrangThaiKeKhai();

  // =========================================================================
  // v2.10: TRẠNG THÁI PHÊ DUYỆT TIÊU CHÍ CHUNG
  // =========================================================================
  // Khi tab "Chính thức": tiêu chí chung phải DA_PHE_DUYET mới hiện điểm
  // Khi tab "Tạm tính": hiện điểm tự chấm (diem_tu_cham) luôn
  const tcDaPheDuyet = tieuChiChung?.trang_thai === TrangThaiTieuChiChung.DA_PHE_DUYET;
  const tcChuaPheDuyet = !isNewTC && !tcDaPheDuyet;
  
  // Điểm tiêu chí chung theo tab
  // Chính thức: chỉ lấy điểm khi đã phê duyệt, ngược lại = 0
  // Tạm tính: lấy điểm tự chấm (tong_hop.tong_diem bao gồm cả tự chấm)
  const diemTCHienThi = kpiTab === 'chinh_thuc'
    ? (tcDaPheDuyet ? diemTieuChiChung : 0)
    : diemTieuChiChung;

  // Tổng điểm hiển thị theo tab (tiêu chí chung + KPI)
  const diemTongHienThi = diemTCHienThi + diemKPIQuyDoi;
  const xepLoaiHienThi = kpiTab === 'chinh_thuc' && tcChuaPheDuyet
    ? tinhXepLoai(diemTongHienThi)  // Tạm tính xếp loại dù TC chung = 0
    : tinhXepLoai(diemTongHienThi);
  const xepLoaiColorHienThi = getXepLoaiColor(xepLoaiHienThi);

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* PL3 V2 banner (29/04/2026): user pin V2 cảnh báo trang này V1-style */}
        {user?.effective_kpi_version === 'V2_PL3' && (
          <div className="mb-4 rounded-md border border-blue-200 bg-blue-50 px-4 py-3 flex items-start justify-between gap-3 text-sm">
            <div className="text-blue-900">
              <strong>Bạn đang dùng phiên bản KPI mới (V2_PL3).</strong>{' '}
              Trang này hiển thị công thức V1 (ngày × 96). Vào{' '}
              <a href="/danh-gia-v2" className="font-semibold underline">/danh-gia-v2</a>{' '}
              để xem điểm KPI theo công thức V2 mới (mẫu số = tổng SP đã kê khai).
            </div>
            <button
              onClick={() => router.push('/danh-gia-v2')}
              className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 whitespace-nowrap"
            >
              Chuyển V2
            </button>
          </div>
        )}

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
                  📊 Đánh giá KPI {isLanhDao ? '(Lãnh đạo)' : isHd111 ? '(HĐ 111)' : '(Công chức)'}
                </h1>
                <p className="text-gray-600 mt-1">Tổng hợp kết quả đánh giá tháng {selectedThang}/{selectedNam}</p>
              </div>
            </div>

            {/* Badge loại người dùng */}
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              isLanhDao
                ? 'bg-purple-100 text-purple-700'
                : isHd111
                  ? 'bg-teal-100 text-teal-700'
                  : 'bg-blue-100 text-blue-700'
            }`}>
              {isLanhDao ? '👔 Lãnh đạo' : isHd111 ? '🤝 HĐ 111' : '👤 Công chức'}
            </div>
          </div>

          {/* Bộ chọn tháng/năm + Nút xuất báo cáo */}
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-600">Tháng:</label>
                <select
                  value={selectedThang}
                  onChange={(e) => setSelectedThang(Number(e.target.value))}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <option key={m} value={m}>Tháng {m}</option>
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
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Nút xuất báo cáo cá nhân - hiện cả tab Tạm tính và Chính thức */}
            {!isLoading && !isNewKPI && !isNewTC && (
              <ExportButton
                label={kpiTab === 'tam_tinh' ? 'Xuất tạm tính' : 'Xuất báo cáo'}
                size="sm"
                onExport={async (format: ExportFormat) => {
                  await exportService.exportCaNhan({
                    thang: selectedThang,
                    nam: selectedNam,
                    format,
                  });
                }}
              />
            )}
          </div>
        </div>

        {/* ========== Phase 3 KPI LĐ V2 (05/05/2026): widget cho LĐ thật + tháng ≥ 5/2026 ========== */}
        {isLanhDao && !isHd111 && (selectedNam > 2026 || (selectedNam === 2026 && selectedThang >= 5)) && (
          <div className="mb-6">
            <WidgetKpiLanhDaoV2
              thang={selectedThang}
              nam={selectedNam}
              capBac={user?.vai_tro?.cap_bac}
              isAdmin={user?.is_system_admin}
              isCCT={user?.vai_tro?.ma_vai_tro === 'CCT'}
            />
          </div>
        )}

        {/* ========== v2.10: GLOBAL TAB SELECTOR ========== */}
        {!isLoading && !error && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1.5 mb-6 flex gap-2">
            <button
              onClick={() => setKpiTab('tam_tinh')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                kpiTab === 'tam_tinh'
                  ? 'bg-amber-50 text-amber-700 border-2 border-amber-300 shadow-sm'
                  : 'text-gray-500 hover:bg-gray-50 border-2 border-transparent'
              }`}
            >
              <span>📝</span>
              <span>Tạm tính</span>
              <span className={`px-2 py-0.5 text-xs rounded-full ${
                kpiTab === 'tam_tinh' ? 'bg-amber-200 text-amber-800' : 'bg-gray-100 text-gray-600'
              }`}>
                {usesLeaderForm ? (tongNhapChoDuyetLD + tongDaDuyetLD) : (tongNhapChoDuyet + tongDaDuyet)}
              </span>
            </button>
            <button
              onClick={() => setKpiTab('chinh_thuc')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                kpiTab === 'chinh_thuc'
                  ? 'bg-green-50 text-green-700 border-2 border-green-300 shadow-sm'
                  : 'text-gray-500 hover:bg-gray-50 border-2 border-transparent'
              }`}
            >
              <span>✅</span>
              <span>Chính thức</span>
              <span className={`px-2 py-0.5 text-xs rounded-full ${
                kpiTab === 'chinh_thuc' ? 'bg-green-200 text-green-800' : 'bg-gray-100 text-gray-600'
              }`}>
                {usesLeaderForm ? tongDaDuyetLD : tongDaDuyet}
              </span>
            </button>
          </div>
        )}

        {/* Loading / Error */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <span className="ml-3 text-gray-600">Đang tải dữ liệu...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {!isLoading && !error && (
          <div className="space-y-6">
            {/* ========== TỔNG HỢP ĐIỂM ========== */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">🎯 Tổng hợp điểm tháng {selectedThang}/{selectedNam}</h2>
                {/* Xếp loại: nếu chính thức + TC chưa duyệt → cảnh báo */}
                {kpiTab === 'chinh_thuc' && tcChuaPheDuyet ? (
                  <div className="bg-gray-100 border border-gray-300 rounded-lg px-4 py-2">
                    <p className="text-xs text-gray-500">Xếp loại</p>
                    <p className="text-lg font-bold text-gray-400">—</p>
                    <p className="text-xs text-gray-400">Chờ phê duyệt TC</p>
                  </div>
                ) : (
                  <div className={`${xepLoaiColorHienThi.bg} ${xepLoaiColorHienThi.border} border rounded-lg px-4 py-2`}>
                    <p className="text-xs text-gray-500">Xếp loại {kpiTab === 'tam_tinh' ? '(Tạm tính)' : ''}</p>
                    <p className={`text-2xl font-bold ${xepLoaiColorHienThi.text}`}>{xepLoaiHienThi}</p>
                    <p className={`text-xs ${xepLoaiColorHienThi.text}`}>{getXepLoaiLabel(xepLoaiHienThi)}</p>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Tiêu chí chung ScoreCard: tab chính thức + chưa duyệt → hiện cảnh báo */}
                {kpiTab === 'chinh_thuc' && tcChuaPheDuyet ? (
                  <div 
                    className="bg-amber-50 border-amber-200 border rounded-xl p-5 cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => router.push('danh-gia/tu-cham-diem')}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="text-sm font-medium text-amber-600">Tiêu chí chung</p>
                        <p className="text-xs text-gray-500">Phẩm chất, năng lực, đổi mới</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-amber-500">⏳</p>
                      </div>
                    </div>
                    <div className="bg-amber-100 rounded-lg px-3 py-2 text-center">
                      <p className="text-sm font-medium text-amber-700">Chờ lãnh đạo phê duyệt</p>
                      <p className="text-xs text-amber-600 mt-0.5">Điểm tự chấm: {diemTieuChiChung}/30</p>
                    </div>
                    <p className="text-xs text-amber-600 mt-2 text-center">Bấm để xem chi tiết →</p>
                  </div>
                ) : (
                  <ScoreCard
                    title="Tiêu chí chung"
                    subtitle={kpiTab === 'tam_tinh' ? 'Điểm tự chấm (chưa duyệt)' : 'Phẩm chất, năng lực, đổi mới'}
                    value={diemTCHienThi}
                    maxValue={30}
                    color="emerald"
                    onClick={() => router.push('danh-gia/tu-cham-diem')}
                  />
                )}
                <ScoreCard
                  title={`Điểm KPI ${kpiTab === 'tam_tinh' ? '(Tạm tính)' : ''}`}
                  subtitle={
                    isLanhDao
                      ? '6 chỉ số (a, b, c, d, đ, e)'
                      : isHd111
                        ? '3 chỉ số (a, b, c) — kê khai LĐ'
                        : '3 chỉ số (a, b, c)'
                  }
                  value={diemKPIQuyDoi}
                  maxValue={70}
                  color="indigo"
                  onClick={() => router.push('/ke-khai')}
                />
                {kpiTab === 'chinh_thuc' && tcChuaPheDuyet ? (
                  <div className="bg-gray-50 border-gray-200 border rounded-xl p-5">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="text-sm font-medium text-gray-500">Điểm tổng</p>
                        <p className="text-xs text-gray-400">= TC chung + KPI</p>
                      </div>
                      <div className="text-right">
                        <p className="text-3xl font-bold text-gray-400">—</p>
                        <p className="text-xs text-gray-400">/ 100 điểm</p>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="h-2 rounded-full bg-gray-300" style={{ width: '0%' }} />
                    </div>
                    <p className="text-xs text-gray-400 mt-2 text-center">Chờ TC chung được phê duyệt</p>
                  </div>
                ) : (
                  <ScoreCard
                    title={`Điểm tổng ${kpiTab === 'tam_tinh' ? '(Tạm tính)' : ''}`}
                    subtitle="= TC chung + KPI"
                    value={diemTongHienThi}
                    maxValue={100}
                    color="purple"
                  />
                )}
              </div>

              {kpiTab === 'tam_tinh' && (
                <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <p className="text-sm text-amber-700">
                    ⚠️ <strong>Lưu ý:</strong> Điểm tạm tính dựa trên tất cả kê khai (bao gồm chưa duyệt) và điểm tự chấm tiêu chí chung. 
                    Điểm chính thức sẽ được tính sau khi lãnh đạo phê duyệt.
                  </p>
                </div>
              )}
            </div>

            {/* ========== TIÊU CHÍ CHUNG ========== */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">📋 Tiêu chí chung (30 điểm)</h2>
                {/* Badge trạng thái phê duyệt */}
                {!isNewTC && (
                  tcDaPheDuyet ? (
                    <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium text-white">✅ Đã phê duyệt</span>
                  ) : (
                    <span className="px-3 py-1 bg-amber-400/30 rounded-full text-xs font-medium text-yellow-100">⏳ Chờ phê duyệt</span>
                  )
                )}
              </div>
              <div className="p-6">
                {isNewTC ? (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa tự đánh giá tiêu chí chung</h3>
                    <p className="text-gray-600 mb-4">Bạn cần hoàn thành tự đánh giá tiêu chí chung cho tháng này.</p>
                    <button
                      onClick={() => router.push('danh-gia/tu-cham-diem')}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                    >
                      Bắt đầu đánh giá
                    </button>
                  </div>
                ) : kpiTab === 'chinh_thuc' && tcChuaPheDuyet ? (
                  /* v2.10: Tab chính thức + chưa phê duyệt → cảnh báo */
                  <div>
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">⏳</span>
                        <div>
                          <p className="font-medium text-amber-800">Tiêu chí chung chưa được phê duyệt</p>
                          <p className="text-sm text-amber-700 mt-1">
                            Bạn đã tự chấm <strong>{diemTieuChiChung}/30 điểm</strong>. 
                            Điểm chính thức sẽ hiển thị sau khi lãnh đạo phê duyệt.
                          </p>
                        </div>
                      </div>
                    </div>
                    {/* Vẫn hiện 3 nhóm nhưng mờ đi + nhãn "Tự chấm" */}
                    <div className="grid grid-cols-3 gap-4 mb-4 opacity-50">
                      <StatBox
                        label="Nhóm I: Phẩm chất"
                        value={`${tieuChiChung?.tong_hop?.nhom_1_diem ?? 0}/10`}
                        subLabel="Tự chấm"
                        bgColor="bg-emerald-50"
                        textColor="text-emerald-600"
                      />
                      <StatBox
                        label="Nhóm II: Năng lực"
                        value={`${tieuChiChung?.tong_hop?.nhom_2_diem ?? 0}/10`}
                        subLabel="Tự chấm"
                        bgColor="bg-teal-50"
                        textColor="text-teal-600"
                      />
                      <StatBox
                        label="Nhóm III: Đổi mới"
                        value={`${tieuChiChung?.tong_hop?.nhom_3_diem ?? 0}/10`}
                        subLabel="Tự chấm"
                        bgColor="bg-cyan-50"
                        textColor="text-cyan-600"
                      />
                    </div>
                    <button
                      onClick={() => router.push('danh-gia/tu-cham-diem')}
                      className="text-emerald-600 hover:text-emerald-800 text-sm font-medium"
                    >
                      Xem chi tiết tiêu chí →
                    </button>
                  </div>
                ) : (
                  <div>
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <StatBox
                        label="Nhóm I: Phẩm chất"
                        value={`${tieuChiChung?.tong_hop?.nhom_1_diem ?? 0}/10`}
                        bgColor="bg-emerald-50"
                        textColor="text-emerald-600"
                      />
                      <StatBox
                        label="Nhóm II: Năng lực"
                        value={`${tieuChiChung?.tong_hop?.nhom_2_diem ?? 0}/10`}
                        bgColor="bg-teal-50"
                        textColor="text-teal-600"
                      />
                      <StatBox
                        label="Nhóm III: Đổi mới"
                        value={`${tieuChiChung?.tong_hop?.nhom_3_diem ?? 0}/10`}
                        bgColor="bg-cyan-50"
                        textColor="text-cyan-600"
                      />
                    </div>
                    <button
                      onClick={() => router.push('danh-gia/tu-cham-diem')}
                      className="text-emerald-600 hover:text-emerald-800 text-sm font-medium"
                    >
                      Xem chi tiết tiêu chí →
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* ========== KPI - CÔNG CHỨC ========== */}
            {!isLanhDao && !isHd111 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-white">📊 Kê khai công việc - Công chức (70 điểm)</h2>
                  {trangThaiKeKhai === 'DA_PHE_DUYET' && (
                    <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium text-white">Đã phê duyệt</span>
                  )}
                </div>
                <div className="p-6">
                  {isNewKPI ? (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có kê khai</h3>
                      <p className="text-gray-600 mb-4">Bạn chưa kê khai công việc cho tháng này.</p>
                      <button
                        onClick={() => router.push('/ke-khai')}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                      >
                        Bắt đầu kê khai
                      </button>
                    </div>
                  ) : (
                    <>
                      {/* Thông tin cơ bản - 6 ô */}
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
                        <StatBox
                          label="Ngày làm việc"
                          value={soNgayLamViecHienThi}
                          subLabel={
                            tongNgayNghiHienThi > 0
                              ? kpiTab === 'tam_tinh' && choDuyetNgayNghi > 0
                                ? `(Nghỉ: ${tongNgayNghi} duyệt + ${choDuyetNgayNghi} chờ)`
                                : `(Nghỉ: ${tongNgayNghiHienThi})`
                              : undefined
                          }
                          bgColor="bg-gray-50"
                          textColor="text-gray-600"
                        />
                        <StatBox
                          label="Tổng SP1 được giao"
                          value={formatNumber(targetSPHienThi)}
                          bgColor="bg-blue-50"
                          textColor="text-blue-600"
                        />
                        <StatBox
                          label="Tổng SP1 hoàn thành"
                          value={formatNumber(spQuyDoiHienThi)}
                          bgColor="bg-green-50"
                          textColor="text-green-600"
                        />
                        <StatBox
                          label="Tổng SP1 đạt CL"
                          value={formatNumber(spChatLuongHienThi)}
                          bgColor="bg-emerald-50"
                          textColor="text-emerald-600"
                        />
                        <StatBox
                          label="Tổng SP1 đạt TĐ"
                          value={formatNumber(spTienDoHienThi)}
                          bgColor="bg-amber-50"
                          textColor="text-amber-600"
                        />
                        <StatBox
                          label="Điểm KPI"
                          value={`${diemKPIQuyDoiCC.toFixed(2)}/70`}
                          bgColor="bg-purple-50"
                          textColor="text-purple-600"
                        />
                      </div>

                      {/* 3 Chỉ số a, b, c */}
                      <h3 className="text-sm font-medium text-gray-700 mb-4">Ba chỉ số chính (a, b, c)</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <MetricCard
                          label="a. Tỷ lệ Số lượng"
                          value={formatPercent(aSoLuongCC)}
                          subValue={`${formatNumber(spQuyDoiHienThi)} / ${formatNumber(targetSPHienThi)} SP1`}
                          color="indigo"
                          percent={aSoLuongCC * 100}
                        />
                        <MetricCard
                          label="b. Tỷ lệ Chất lượng"
                          value={formatPercent(bChatLuongCC)}
                          subValue={`${formatNumber(spChatLuongHienThi)} / ${formatNumber(targetSPHienThi)} SP1`}
                          color="emerald"
                          percent={bChatLuongCC * 100}
                        />
                        <MetricCard
                          label="c. Tỷ lệ Tiến độ"
                          value={formatPercent(cTienDoCC)}
                          subValue={`${formatNumber(spTienDoHienThi)} / ${formatNumber(targetSPHienThi)} SP1`}
                          color="amber"
                          percent={cTienDoCC * 100}
                        />
                      </div>

                      {/* Công thức */}
                      <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
                        <p className="text-sm text-gray-600 text-center">
                          <strong>Công thức:</strong> Điểm KPI = (a + b + c) / 3 × 70 = 
                          <span className="text-indigo-600 font-medium"> ({formatPercent(aSoLuongCC, 2)} + {formatPercent(bChatLuongCC, 2)} + {formatPercent(cTienDoCC, 2)}) / 3 × 70 </span>
                          = <strong className="text-indigo-700">{diemKPIQuyDoiCC.toFixed(2)} điểm</strong>
                        </p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* ========== KPI - HĐ 111 ========== */}
            {/* HĐ 111 kê khai cùng form lãnh đạo (từng CV với lỗi CL/TĐ),    */}
            {/* nhưng chỉ tính 3 chỉ số a, b, c — không có d, đ, e.            */}
            {isHd111 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-cyan-600 to-teal-600 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-white">📊 Kê khai công việc - HĐ 111 (70 điểm)</h2>
                  {trangThaiKeKhai === 'DA_PHE_DUYET' && (
                    <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium text-white">Đã phê duyệt</span>
                  )}
                </div>
                <div className="p-6">
                  {isNewKPI ? (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có công việc</h3>
                      <p className="text-gray-600 mb-4">Bạn chưa kê khai công việc cho tháng này.</p>
                      <button
                        onClick={() => router.push('/ke-khai')}
                        className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                      >
                        Bắt đầu kê khai
                      </button>
                    </div>
                  ) : (
                    <>
                      {/* Thông tin cơ bản - 5 ô (giống lãnh đạo) */}
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
                        <StatBox
                          label="Tổng CV được giao"
                          value={targetLDHienThi}
                          bgColor="bg-cyan-50"
                          textColor="text-cyan-600"
                        />
                        <StatBox
                          label="CV hoàn thành"
                          value={cvHoanThanhHienThi}
                          bgColor="bg-green-50"
                          textColor="text-green-600"
                        />
                        <StatBox
                          label="Lỗi chất lượng"
                          value={loiChatLuongHienThi}
                          bgColor={loiChatLuongHienThi > 0 ? "bg-red-50" : "bg-blue-50"}
                          textColor={loiChatLuongHienThi > 0 ? "text-red-600" : "text-blue-600"}
                        />
                        <StatBox
                          label="Lỗi tiến độ"
                          value={loiTienDoHienThi}
                          bgColor={loiTienDoHienThi > 0 ? "bg-red-50" : "bg-amber-50"}
                          textColor={loiTienDoHienThi > 0 ? "text-red-600" : "text-amber-600"}
                        />
                        <StatBox
                          label="Điểm KPI"
                          value={`${diemKPIQuyDoiHd111.toFixed(2)}/70`}
                          bgColor="bg-teal-50"
                          textColor="text-teal-600"
                        />
                      </div>

                      {/* 3 Chỉ số a, b, c (không có d, đ, e) */}
                      <h3 className="text-sm font-medium text-gray-700 mb-4">Ba chỉ số (a, b, c)</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <MetricCard
                          label="a. Tỷ lệ hoàn thành"
                          value={formatPercent(aLD)}
                          subValue={`${cvHoanThanhHienThi} / ${targetLDHienThi} CV`}
                          color="indigo"
                          percent={aLD * 100}
                        />
                        <MetricCard
                          label="b. Tiến độ"
                          value={formatPercent(bLD)}
                          subValue={loiTienDoHienThi > 0 ? `${loiTienDoHienThi} lỗi (-${loiTienDoHienThi * 25}%)` : 'Không có lỗi'}
                          color={loiTienDoHienThi > 0 ? "amber" : "emerald"}
                          percent={bLD * 100}
                        />
                        <MetricCard
                          label="c. Chất lượng"
                          value={formatPercent(cLD)}
                          subValue={loiChatLuongHienThi > 0 ? `${loiChatLuongHienThi} lỗi (-${loiChatLuongHienThi * 25}%)` : 'Không có lỗi'}
                          color={loiChatLuongHienThi > 0 ? "amber" : "emerald"}
                          percent={cLD * 100}
                        />
                      </div>

                      {/* Công thức */}
                      <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
                        <p className="text-sm text-gray-600 text-center">
                          <strong>Công thức:</strong> Điểm KPI = (a + b + c) / 3 × 70
                        </p>
                        <p className="text-sm text-teal-600 font-medium text-center mt-1">
                          = ({formatPercent(aLD, 2)} + {formatPercent(bLD, 2)} + {formatPercent(cLD, 2)}) / 3 × 70
                          = <strong className="text-teal-700">{diemKPIQuyDoiHd111.toFixed(2)} điểm</strong>
                        </p>
                      </div>

                      {/* Link đến chi tiết kê khai */}
                      <div className="mt-4 text-center">
                        <button
                          onClick={() => router.push('/ke-khai')}
                          className="text-teal-600 hover:text-teal-800 text-sm font-medium"
                        >
                          Xem chi tiết kê khai →
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* ========== KPI - LÃNH ĐẠO ========== */}
            {isLanhDao && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-white">📊 Kê khai công việc - Lãnh đạo (70 điểm)</h2>
                  {trangThaiKeKhai === 'DA_PHE_DUYET' && (
                    <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium text-white">Đã phê duyệt</span>
                  )}
                </div>
                <div className="p-6">
                  {isNewKPI ? (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có công việc</h3>
                      <p className="text-gray-600 mb-4">Bạn chưa kê khai công việc cho tháng này.</p>
                      <button
                        onClick={() => router.push('/ke-khai')}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                      >
                        Bắt đầu kê khai
                      </button>
                    </div>
                  ) : (
                    <>
                      {/* Thông tin cơ bản - 5 ô */}
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
                        <StatBox
                          label="Tổng CV được giao"
                          value={targetLDHienThi}
                          bgColor="bg-purple-50"
                          textColor="text-purple-600"
                        />
                        <StatBox
                          label="CV hoàn thành"
                          value={cvHoanThanhHienThi}
                          bgColor="bg-green-50"
                          textColor="text-green-600"
                        />
                        <StatBox
                          label="Lỗi chất lượng"
                          value={loiChatLuongHienThi}
                          bgColor={loiChatLuongHienThi > 0 ? "bg-red-50" : "bg-blue-50"}
                          textColor={loiChatLuongHienThi > 0 ? "text-red-600" : "text-blue-600"}
                        />
                        <StatBox
                          label="Lỗi tiến độ"
                          value={loiTienDoHienThi}
                          bgColor={loiTienDoHienThi > 0 ? "bg-red-50" : "bg-amber-50"}
                          textColor={loiTienDoHienThi > 0 ? "text-red-600" : "text-amber-600"}
                        />
                        <StatBox
                          label="Điểm KPI"
                          value={`${diemKPIQuyDoiLD.toFixed(2)}/70`}
                          bgColor="bg-pink-50"
                          textColor="text-pink-600"
                        />
                      </div>

                      {/* 6 Chỉ số a, b, c, d, đ, e */}
                      <h3 className="text-sm font-medium text-gray-700 mb-4">Sáu chỉ số (a, b, c, d, đ, e)</h3>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        <MetricCard
                          label="a. Tỷ lệ hoàn thành"
                          value={formatPercent(aLD)}
                          subValue={`${cvHoanThanhHienThi} / ${targetLDHienThi} CV`}
                          color="indigo"
                          percent={aLD * 100}
                        />
                        <MetricCard
                          label="b. Tiến độ"
                          value={formatPercent(bLD)}
                          subValue={loiTienDoHienThi > 0 ? `${loiTienDoHienThi} lỗi (-${loiTienDoHienThi * 25}%)` : 'Không có lỗi'}
                          color={loiTienDoHienThi > 0 ? "amber" : "emerald"}
                          percent={bLD * 100}
                        />
                        <MetricCard
                          label="c. Chất lượng"
                          value={formatPercent(cLD)}
                          subValue={loiChatLuongHienThi > 0 ? `${loiChatLuongHienThi} lỗi (-${loiChatLuongHienThi * 25}%)` : 'Không có lỗi'}
                          color={loiChatLuongHienThi > 0 ? "amber" : "emerald"}
                          percent={cLD * 100}
                        />
                        <MetricCard
                          label="d. Kết quả đơn vị"
                          value={formatPercent(dLD)}
                          subValue={dLD === 1 ? 'Đạt' : 'Chưa đạt'}
                          color="purple"
                          percent={dLD * 100}
                        />
                        <MetricCard
                          label="đ. Tổ chức triển khai"
                          value={formatPercent(ddLD)}
                          subValue={ddLD === 1 ? 'Đạt' : 'Chưa đạt'}
                          color="pink"
                          percent={ddLD * 100}
                        />
                        <MetricCard
                          label="e. Đoàn kết nội bộ"
                          value={formatPercent(eLD)}
                          subValue={eLD === 1 ? 'Đạt' : 'Chưa đạt'}
                          color="cyan"
                          percent={eLD * 100}
                        />
                      </div>

                      {/* Công thức */}
                      <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
                        <p className="text-sm text-gray-600 text-center">
                          <strong>Công thức:</strong> Điểm KPI = (a + b + c + d + đ + e) / 6 × 70
                        </p>
                        <p className="text-sm text-purple-600 font-medium text-center mt-1">
                          = ({formatPercent(aLD, 2)} + {formatPercent(bLD, 2)} + {formatPercent(cLD, 2)} + {formatPercent(dLD, 2)} + {formatPercent(ddLD, 2)} + {formatPercent(eLD, 2)}) / 6 × 70 
                          = <strong className="text-purple-700">{diemKPIQuyDoiLD.toFixed(2)} điểm</strong>
                        </p>
                      </div>

                      {/* Link đến đánh giá d, đ, e */}
                      <div className="mt-4 text-center">
                        <button
                          onClick={() => router.push('/ke-khai')}
                          className="text-purple-600 hover:text-purple-800 text-sm font-medium"
                        >
                          Xem chi tiết kê khai & đánh giá d, đ, e →
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* ========== BẢNG XẾP LOẠI THAM KHẢO ========== */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="font-medium text-gray-900 mb-4">📊 Thang điểm xếp loại</h3>
              <div className="grid grid-cols-5 gap-3">
                {(['A', 'B', 'C', 'D', 'E'] as XepLoai[]).map((loai) => {
                  const c = getXepLoaiColor(loai);
                  const isActive = loai === xepLoai;
                  return (
                    <div 
                      key={loai} 
                      className={`${c.bg} ${c.border} border rounded-lg p-3 text-center ${isActive ? 'ring-2 ring-offset-2 ring-blue-500' : ''}`}
                    >
                      <p className={`text-2xl font-bold ${c.text}`}>{loai}</p>
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
                * Loại A: Tỷ lệ ≤ 20% CC mức B trong đơn vị | Loại E: Không đánh giá (nghỉ cả tháng)
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
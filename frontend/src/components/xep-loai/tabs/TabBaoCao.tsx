/**
 * src/components/xep-loai/tabs/TabBaoCao.tsx
 * ===========================================
 * Tab "Báo cáo xếp loại" - Báo cáo xếp loại cuối tháng.
 * 
 * Version: 3.3.3 - TABLE DESIGN (30/01/2026)
 * 
 * DESIGN MỚI:
 * - Dạng bảng với các cột: STT, Họ tên/Mã CC, Đơn vị, Ngày LV, Ngày nghỉ, 
 *   Điểm TC, Điểm CV, Điểm KPI, XL Đề xuất, Thao tác
 * - Tự động tính từ dữ liệu đã duyệt
 * - Phó ĐT/ĐT/Phó CCT/CCT đều xem được
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/axios';
import { ITabProps, CapBacVaiTro } from '@/types/xep-loai';
import {
  LoadingSpinner,
  EmptyState,
  ErrorMessage,
  StatusBadge,
} from '../shared';

import ExportButton, { ExportFormat } from '@/components/common/ExportButton';
import { exportService } from '@/services/export.service';
import { useAuthStore } from '@/stores/useAuthStore';

// =============================================================================
// TYPES
// =============================================================================

interface IChiTietXepLoai {
  id: string;
  cong_chuc_id?: string;
  cong_chuc?: {
    id: string;
    ma_cc: string;
    ho_ten: string;
    chuc_vu?: string;
  };
  don_vi?: {
    id: string;
    ten_don_vi: string;
  };
  // Điểm chi tiết
  diem_tieu_chi_chung?: number;
  diem_kpi?: number;
  diem_tong?: number;
  // Ngày công
  so_ngay_lam_viec?: number;
  so_ngay_nghi?: number;
  // Xếp loại
  xep_loai_he_thong?: string;
  xep_loai_tu_dong?: string; // backward compat
  xep_loai_de_xuat?: string;
  xep_loai_quyet_dinh?: string;
  ly_do_dieu_chinh_dt?: string;
  ly_do_de_xuat?: string; // backward compat
  ghi_chu?: string;
  // v1.4: Số CV khó (C3+) - computed by backend
  so_cv_c3_plus?: number;
  // Phân loại lãnh đạo/công chức
  is_lanh_dao?: boolean;
  // HĐ 111 (Phase 3 — 29/04/2026): kê khai form LĐ, không có d/đ/e
  is_hd_111?: boolean;
}

interface IBaoCaoXepLoai {
  id: string;
  don_vi_id?: string;
  don_vi?: {
    id: string;
    ma_don_vi?: string;
    ten_don_vi?: string;
  };
  thang: number;
  nam: number;
  trang_thai: string;
  tong_cong_chuc: number;
  so_loai_a: number;
  so_loai_b: number;
  so_loai_c: number;
  so_loai_d: number;
  so_loai_e?: number;
  canh_bao_ty_le_a?: boolean;
  chi_tiet?: IChiTietXepLoai[];
  can_edit?: boolean;
  can_approve?: boolean;
}

// Thông tin kê khai công việc
interface IKeKhaiCongViecBrief {
  id: string;
  // Nested objects from backend ke_khai_to_response
  danh_muc_sp?: {
    id: string;
    ma_danh_muc: string;
    ten_cong_viec: string;
    ma_sp?: string;
    he_so_quy_doi?: number;
  } | null;
  cap_do?: {
    id: string;
    ma_cap_do: string;
    ten_cap_do: string;
    he_so_sp1: number;
    he_so_sp2: number;
    is_theo_thuc_te: boolean;
  } | null;
  so_luong: number;
  so_sp_goc_quy_doi?: number | null;
  so_sp_chat_luong?: number | null;
  so_sp_tien_do?: number | null;
  trang_thai: string;
  so_loi_chat_luong?: number;
  so_loi_tien_do?: number;
  tu_danh_gia_chat_luong?: number;
  tu_danh_gia_tien_do?: number;
  ngay_thuc_hien?: string | null;
  mo_ta_cong_viec?: string | null;
  is_doi_moi_sang_tao?: boolean;
  // Flat fields (backward-compatible, derived for display convenience)
  danh_muc_ten?: string;
  cap_do_ma?: string;
  cap_do_ten?: string;
}

// Thông tin tiêu chí chung — khớp DanhGiaThangTieuChiResponse từ backend
interface ITieuChiItem {
  ma_tieu_chi: string;
  ten_tieu_chi: string;
  nhom_tieu_chi: number;
  diem_toi_da: number;
  is_achieved_cc?: boolean;
  is_achieved_ld?: boolean;
  diem_tu_cham: number;
  diem_phe_duyet?: number | null;
  diem: number;
  trang_thai: string;
  ghi_chu_cc?: string | null;
  ghi_chu_ld?: string | null;
}

interface ITieuChiChungBrief {
  trang_thai?: string;
  trang_thai_danh_gia_thang?: string;
  is_new_record?: boolean;
  tong_hop?: {
    nhom_1_diem: number;
    nhom_2_diem: number;
    nhom_3_diem: number;
    tong_diem: number;
  };
  tieu_chi?: ITieuChiItem[];
  // Legacy flat fields (backward-compatible)
  diem_cc?: number;
  diem_ld?: number;
  nhom_1?: { diem_cc?: number; diem_ld?: number };
  nhom_2?: { diem_cc?: number; diem_ld?: number };
  nhom_3?: { diem_cc?: number; diem_ld?: number };
}

// Thông tin nghỉ phép — khớp build_nghi_phep_response từ backend
interface INghiPhepBrief {
  id: string;
  loai_nghi: string;
  loai_nghi_ten?: string;
  tu_ngay: string;
  den_ngay: string;
  so_ngay: number;
  ly_do?: string;
  trang_thai: string;
  trang_thai_ten?: string;
  nguoi_phe_duyet?: { id: string; ho_ten: string } | null;
}

// Kê khai công việc lãnh đạo — khớp build_ke_khai_response từ ke_khai_lanh_dao.py
interface IKeKhaiLanhDaoBrief {
  id: string;
  ten_cong_viec: string;
  mo_ta?: string;
  ngay_thuc_hien?: string;
  trang_thai_hoan_thanh?: string;
  so_luong: number;
  so_loi_chat_luong?: number;
  so_loi_tien_do?: number;
  ghi_chu_loi_chat_luong?: string;
  ghi_chu_loi_tien_do?: string;
  trang_thai: string;
}

// Đánh giá d, đ, e lãnh đạo — khớp build_dde_response từ danh_gia_lanh_dao.py
interface IDanhGiaDDE {
  id: string;
  d_ket_qua_don_vi?: number;
  d_ghi_chu?: string;
  dd_to_chuc_trien_khai?: number;
  dd_ghi_chu?: string;
  e_doan_ket_noi_bo?: number;
  e_ghi_chu?: string;
  d_phe_duyet?: number | null;
  dd_phe_duyet?: number | null;
  e_phe_duyet?: number | null;
  d_final?: number;
  dd_final?: number;
  e_final?: number;
  trang_thai: string;
}

// Hệ số quy đổi cấp độ để tính "độ khó trung bình"
const CAP_DO_HE_SO: Record<string, number> = {
  C1: 1, C2: 4, C3: 12, C4: 24, C5: 48,
};

/**
 * Sắp xếp chi tiết xếp loại:
 * 1. Điểm tổng giảm dần
 * 2. Nếu bằng nhau → ưu tiên CC làm nhiều CV khó (C3+) hơn
 * 3. Nếu vẫn bằng → ưu tiên điểm KPI cao hơn
 */
function sortChiTietByDiem(chiTiet: IChiTietXepLoai[]): IChiTietXepLoai[] {
  return [...chiTiet].sort((a, b) => {
    const diemA = a.diem_tong ?? 0;
    const diemB = b.diem_tong ?? 0;
    if (diemB !== diemA) return diemB - diemA;
    // Tiebreaker 1: ưu tiên nhiều CV khó (C3+) hơn
    const c3A = a.so_cv_c3_plus ?? 0;
    const c3B = b.so_cv_c3_plus ?? 0;
    if (c3B !== c3A) return c3B - c3A;
    // Tiebreaker 2: ưu tiên điểm KPI cao hơn
    const kpiA = a.diem_kpi ?? 0;
    const kpiB = b.diem_kpi ?? 0;
    return kpiB - kpiA;
  });
}

const LOAI_NGHI_MAP: Record<string, string> = {
  NGHI_TUAN: 'Nghỉ tuần',
  NGHI_PHEP_NAM: 'Nghỉ phép năm',
  NGHI_OM: 'Nghỉ ốm',
  NGHI_THAI_SAN: 'Nghỉ thai sản',
  NGHI_VIEC_RIENG_KHONG_LUONG: 'Nghỉ không lương',
  NGHI_LE_TET: 'Nghỉ lễ/tết',
  NGHI_KHAC: 'Nghỉ khác',
  CONG_TAC: 'Đi công tác',
  HOC_TAP: 'Học tập',
};

const TRANG_THAI_MAP: Record<string, { label: string; color: string }> = {
  NHAP: { label: 'Nháp', color: 'bg-gray-100 text-gray-700' },
  CHO_PHE_DUYET: { label: 'Chờ duyệt', color: 'bg-amber-100 text-amber-700' },
  DA_PHE_DUYET: { label: 'Đã duyệt', color: 'bg-green-100 text-green-700' },
  TU_CHOI: { label: 'Từ chối', color: 'bg-red-100 text-red-700' },
  TRA_LAI: { label: 'Trả lại', color: 'bg-red-100 text-red-700' },
};

// Map trạng thái riêng cho nghỉ phép (TrangThaiNghi không có NHAP)
const TRANG_THAI_NGHI_MAP: Record<string, { label: string; color: string }> = {
  CHO_PHE_DUYET: { label: 'Chờ duyệt', color: 'bg-amber-100 text-amber-700' },
  DA_PHE_DUYET: { label: 'Đã duyệt', color: 'bg-green-100 text-green-700' },
  TU_CHOI: { label: 'Từ chối', color: 'bg-red-100 text-red-700' },
  HUY: { label: 'Đã hủy', color: 'bg-gray-100 text-gray-500' },
};

const XEP_LOAI_COLORS: Record<string, string> = {
  A: 'bg-green-100 text-green-700 border-green-300',
  B: 'bg-blue-100 text-blue-700 border-blue-300',
  C: 'bg-amber-100 text-amber-700 border-amber-300',
  D: 'bg-orange-100 text-orange-700 border-orange-300',
  E: 'bg-red-100 text-red-700 border-red-300',
};

// =============================================================================
// API FUNCTIONS
// =============================================================================

const baoCaoApi = {
  async getBaoCaoDonVi(thang: number, nam: number): Promise<IBaoCaoXepLoai | null> {
    try {
      const response = await apiClient.get(`/bao-cao-xep-loai/don-vi/thang/${thang}/nam/${nam}`);
      return response.data?.data || response.data || null;
    } catch (err) {
      const error = err as { response?: { status: number } };
      if (error.response?.status === 404) return null;
      throw err;
    }
  },

  async deXuatXepLoai(chiTietId: string, payload: {
    xep_loai_de_xuat: string;
    ly_do_dieu_chinh?: string;
    ghi_chu?: string;
  }): Promise<void> {
    await apiClient.put(`/bao-cao-xep-loai/chi-tiet/${chiTietId}/de-xuat`, payload);
  },

  async guiDuyet(baoCaoId: string): Promise<void> {
    await apiClient.post(`/bao-cao-xep-loai/${baoCaoId}/gui-duyet`);
  },

  async getChoPheDuyet(): Promise<IBaoCaoXepLoai[]> {
    const response = await apiClient.get('/bao-cao-xep-loai/cho-phe-duyet');
    if (Array.isArray(response.data)) return response.data;
    if (response.data?.data && Array.isArray(response.data.data)) return response.data.data;
    return [];
  },

  async getChiTiet(baoCaoId: string): Promise<IBaoCaoXepLoai | null> {
    const response = await apiClient.get(`/bao-cao-xep-loai/${baoCaoId}`);
    return response.data?.data || response.data || null;
  },

  async pheDuyet(baoCaoId: string, payload: {
    action: 'APPROVE' | 'REJECT';
    y_kien?: string;
  }): Promise<void> {
    await apiClient.post(`/bao-cao-xep-loai/${baoCaoId}/phe-duyet`, payload);
  },

  async traLai(baoCaoId: string, lyDo: string): Promise<void> {
    await apiClient.post(`/xep-loai/${baoCaoId}/tra-lai`, { ly_do: lyDo });
  },
  // v1.1.0: Lấy danh sách tất cả báo cáo (có filter trạng thái)
  async getDanhSach(thang: number, nam: number, trangThai?: string): Promise<IBaoCaoXepLoai[]> {
    try {
      const params: Record<string, string> = {};
      if (trangThai) params.trang_thai = trangThai;
      const response = await apiClient.get(`/bao-cao-xep-loai/danh-sach/thang/${thang}/nam/${nam}`, { params });
      if (Array.isArray(response.data)) return response.data;
      if (response.data?.data?.danh_sach && Array.isArray(response.data.data.danh_sach)) return response.data.data.danh_sach;
      if (response.data?.data && Array.isArray(response.data.data)) return response.data.data;
      if (response.data?.danh_sach && Array.isArray(response.data.danh_sach)) return response.data.danh_sach;
      return [];
    } catch {
      return [];
    }
  },

  // APIs cho xem chi tiết công chức
  async getKeKhaiCongChuc(congChucId: string, thang: number, nam: number): Promise<IKeKhaiCongViecBrief[]> {
    try {
      const response = await apiClient.get(`/ke-khai/cong-chuc/${congChucId}`, {
        params: { thang, nam },
      });
      const data = response.data?.data;
      if (Array.isArray(data)) return data;
      if (data?.items && Array.isArray(data.items)) return data.items;
      return [];
    } catch {
      return [];
    }
  },

  async getTieuChiChung(congChucId: string, thang: number, nam: number): Promise<ITieuChiChungBrief | null> {
    try {
      const response = await apiClient.get(`/danh-gia/tieu-chi/cong-chuc/${congChucId}/thang/${thang}/nam/${nam}`);
      return response.data?.data || null;
    } catch {
      return null;
    }
  },

  async getNghiPhep(congChucId: string, thang: number, nam: number): Promise<INghiPhepBrief[]> {
    try {
      const response = await apiClient.get(`/nghi-phep/cong-chuc/${congChucId}`, {
        params: { thang, nam },
      });
      const data = response.data?.data;
      if (Array.isArray(data)) return data;
      return [];
    } catch {
      return [];
    }
  },

  // --- Lãnh đạo specific ---

  async getKeKhaiLanhDao(congChucId: string, thang: number, nam: number): Promise<IKeKhaiLanhDaoBrief[]> {
    try {
      const response = await apiClient.get(`/ke-khai-lanh-dao/cong-chuc/${congChucId}`, {
        params: { thang, nam },
      });
      const data = response.data?.data;
      if (Array.isArray(data)) return data;
      return [];
    } catch {
      return [];
    }
  },

  async getDanhGiaDDE(congChucId: string, thang: number, nam: number): Promise<IDanhGiaDDE | null> {
    try {
      const response = await apiClient.get(
        `/danh-gia-lanh-dao/dde/cong-chuc/${congChucId}/thang/${thang}/nam/${nam}`
      );
      return response.data?.data || null;
    } catch {
      return null;
    }
  },
};

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

function XepLoaiBadge({ xepLoai, size = 'sm' }: { xepLoai?: string; size?: 'sm' | 'md' }) {
  if (!xepLoai) return <span className="text-gray-400">-</span>;
  const sizeClass = size === 'md' ? 'px-3 py-1 text-sm' : 'px-2 py-0.5 text-xs';
  return (
    <span className={`${sizeClass} font-bold rounded border ${XEP_LOAI_COLORS[xepLoai] || 'bg-gray-100 text-gray-700 border-gray-300'}`}>
      {xepLoai}
    </span>
  );
}

function NghiPhepStatusBadge({ trangThai, trangThaiTen }: { trangThai: string; trangThaiTen?: string }) {
  const info = TRANG_THAI_NGHI_MAP[trangThai] || { label: trangThaiTen || trangThai, color: 'bg-gray-100 text-gray-600' };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${info.color}`}>
      {info.label}
    </span>
  );
}

function StatsSummary({ baoCao }: { baoCao: IBaoCaoXepLoai }) {
  const stats = [
    { label: 'A', value: baoCao.so_loai_a, color: 'bg-green-500' },
    { label: 'B', value: baoCao.so_loai_b, color: 'bg-blue-500' },
    { label: 'C', value: baoCao.so_loai_c, color: 'bg-amber-500' },
    { label: 'D', value: baoCao.so_loai_d, color: 'bg-orange-500' },
    { label: 'E', value: baoCao.so_loai_e || 0, color: 'bg-red-500' },
  ];
  const total = baoCao.tong_cong_chuc || stats.reduce((sum, s) => sum + s.value, 0);

  // Tính tỷ lệ A/B theo business rule: A ≤ 20% số CC mức B và A
  const tongAB = baoCao.so_loai_a + baoCao.so_loai_b;
  const tyLeA = tongAB > 0
    ? ((baoCao.so_loai_a / tongAB) * 100)
    : 0;
  const isVuotNguong = baoCao.canh_bao_ty_le_a || (tongAB > 0 && tyLeA > 20);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-4">
        {stats.map((s) => (
          <div key={s.label} className="flex items-center gap-1.5">
            <div className={`w-3 h-3 rounded ${s.color}`} />
            <span className="text-sm font-medium text-gray-700">{s.label}:</span>
            <span className="text-sm font-bold text-gray-900">{s.value}</span>
          </div>
        ))}
        <div className="border-l border-gray-300 pl-4 ml-2">
          <span className="text-sm text-gray-500">Tổng:</span>
          <span className="text-sm font-bold text-gray-900 ml-1">{total}</span>
        </div>
      </div>
      {isVuotNguong && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.27 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span className="text-xs text-red-700 font-medium">
            Cảnh báo: Tỷ lệ A/(A+B) = {tyLeA.toFixed(0)}% (vượt ngưỡng 20%). Theo Quy chế, mức A ≤ 20% số CC mức B trở lên.
          </span>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MODAL XEM CHI TIẾT CÔNG CHỨC
// =============================================================================

interface ChiTietCongChucModalProps {
  congChuc: IChiTietXepLoai;
  thang: number;
  nam: number;
  onClose: () => void;
}

function ChiTietCongChucModal({ congChuc, thang, nam, onClose }: ChiTietCongChucModalProps) {
  const isLanhDao = congChuc.is_lanh_dao === true;
  // Phase 3 (29/04/2026): HĐ 111 kê khai form LĐ — load đúng bảng,
  // nhưng KHÔNG có tab d/đ/e (backend chặn endpoint).
  const isHd111 = congChuc.is_hd_111 === true;
  const usesLeaderForm = isLanhDao || isHd111;
  const [activeDetailTab, setActiveDetailTab] = useState<'ke-khai' | 'tieu-chi' | 'dde' | 'nghi-phep'>('ke-khai');
  const [keKhaiList, setKeKhaiList] = useState<IKeKhaiCongViecBrief[]>([]);
  const [keKhaiLDList, setKeKhaiLDList] = useState<IKeKhaiLanhDaoBrief[]>([]);
  const [tieuChi, setTieuChi] = useState<ITieuChiChungBrief | null>(null);
  const [ddeData, setDdeData] = useState<IDanhGiaDDE | null>(null);
  const [nghiPhepList, setNghiPhepList] = useState<INghiPhepBrief[]>([]);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const congChucId = congChuc.cong_chuc_id || congChuc.cong_chuc?.id || '';

  useEffect(() => {
    if (!congChucId) return;
    setIsLoadingDetail(true);

    if (usesLeaderForm) {
      // Lãnh đạo / HĐ 111: lấy kê khai LD + tiêu chí + nghỉ phép.
      // d/đ/e chỉ load cho LĐ thật (HĐ 111 không có).
      Promise.all([
        baoCaoApi.getKeKhaiLanhDao(congChucId, thang, nam),
        baoCaoApi.getTieuChiChung(congChucId, thang, nam),
        isHd111
          ? Promise.resolve<IDanhGiaDDE | null>(null)
          : baoCaoApi.getDanhGiaDDE(congChucId, thang, nam),
        baoCaoApi.getNghiPhep(congChucId, thang, nam),
      ]).then(([kkLD, tc, dde, np]) => {
        setKeKhaiLDList(kkLD);
        setTieuChi(tc);
        setDdeData(dde);
        setNghiPhepList(np);
      }).finally(() => setIsLoadingDetail(false));
    } else {
      // CC thường: lấy kê khai CC + tiêu chí + nghỉ phép
      Promise.all([
        baoCaoApi.getKeKhaiCongChuc(congChucId, thang, nam),
        baoCaoApi.getTieuChiChung(congChucId, thang, nam),
        baoCaoApi.getNghiPhep(congChucId, thang, nam),
      ]).then(([kk, tc, np]) => {
        setKeKhaiList(kk);
        setTieuChi(tc);
        setNghiPhepList(np);
      }).finally(() => setIsLoadingDetail(false));
    }
  }, [congChucId, thang, nam, usesLeaderForm, isHd111]);

  const detailTabs = isLanhDao
    ? [
        { key: 'ke-khai' as const, label: 'Công việc lãnh đạo', count: keKhaiLDList.length },
        { key: 'tieu-chi' as const, label: 'Tiêu chí chung', count: null },
        { key: 'dde' as const, label: 'Đánh giá d, đ, e', count: null },
        { key: 'nghi-phep' as const, label: 'Nghỉ phép', count: nghiPhepList.length },
      ]
    : isHd111
    ? [
        { key: 'ke-khai' as const, label: 'Công việc HĐ 111', count: keKhaiLDList.length },
        { key: 'tieu-chi' as const, label: 'Tiêu chí chung', count: null },
        { key: 'nghi-phep' as const, label: 'Nghỉ phép', count: nghiPhepList.length },
      ]
    : [
        { key: 'ke-khai' as const, label: 'Kê khai công việc', count: keKhaiList.length },
        { key: 'tieu-chi' as const, label: 'Tiêu chí chung', count: null },
        { key: 'nghi-phep' as const, label: 'Nghỉ phép', count: nghiPhepList.length },
      ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[55] p-4">
      <div className="bg-white rounded-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-gray-900">{congChuc.cong_chuc?.ho_ten}</h3>
                {isLanhDao && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-purple-100 text-purple-700 font-medium" title="Lãnh đạo - công thức 6 chỉ số">👔 Lãnh đạo</span>
                )}
                {isHd111 && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-teal-100 text-teal-700 font-medium" title="HĐ 111 — kê khai form LĐ, công thức 3 chỉ số (a, b, c)">🤝 HĐ 111</span>
                )}
              </div>
              <p className="text-sm text-gray-500">{congChuc.cong_chuc?.ma_cc} {congChuc.cong_chuc?.chuc_vu ? `• ${congChuc.cong_chuc.chuc_vu}` : ''}</p>
              <div className="flex items-center gap-4 mt-2">
                <span className="text-sm text-gray-600">Điểm TC: <strong>{congChuc.diem_tieu_chi_chung?.toFixed(1) || '-'}</strong></span>
                <span className="text-sm text-gray-600">Điểm KPI: <strong>{congChuc.diem_kpi?.toFixed(1) || '-'}</strong></span>
                <span className="text-sm text-gray-600">Tổng: <strong className="text-lg">{congChuc.diem_tong?.toFixed(1) || '-'}</strong></span>
                <XepLoaiBadge xepLoai={congChuc.xep_loai_he_thong || congChuc.xep_loai_tu_dong} size="md" />
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Detail Tabs */}
          <div className="flex gap-1 mt-4">
            {detailTabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveDetailTab(tab.key)}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                  activeDetailTab === tab.key
                    ? 'bg-white text-blue-700 border border-b-0 border-gray-200'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-white/50'
                }`}
              >
                {tab.label}
                {tab.count !== null && (
                  <span className="ml-1.5 px-1.5 py-0.5 text-xs rounded-full bg-gray-200 text-gray-600">{tab.count}</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoadingDetail ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <>
              {/* Tab Kê khai công việc */}
              {activeDetailTab === 'ke-khai' && (
                <div>
                  {usesLeaderForm ? (
                    /* ============== KÊ KHAI LÃNH ĐẠO / HĐ 111 ============== */
                    keKhaiLDList.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        Không có công việc {isHd111 ? 'HĐ 111' : 'lãnh đạo'} trong tháng {thang}/{nam}
                      </div>
                    ) : (
                      <>
                        <div className="border border-gray-200 rounded-lg overflow-hidden">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="bg-gray-50 border-b border-gray-200">
                                <th className="px-3 py-2.5 text-left font-semibold text-gray-700 w-10">STT</th>
                                <th className="px-3 py-2.5 text-left font-semibold text-gray-700">Tên công việc</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-16">SL</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-24">Hoàn thành</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-16">Lỗi CL</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-16">Lỗi TĐ</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-24">Trạng thái</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {keKhaiLDList.map((kk, idx) => {
                                const htLabel: Record<string, string> = {
                                  HOAN_THANH: 'Hoàn thành',
                                  DANG_THUC_HIEN: 'Đang thực hiện',
                                  CHUA_THUC_HIEN: 'Chưa thực hiện',
                                };
                                return (
                                  <tr key={kk.id} className="hover:bg-gray-50">
                                    <td className="px-3 py-2 text-gray-500">{idx + 1}</td>
                                    <td className="px-3 py-2">
                                      <div className="font-medium text-gray-900">{kk.ten_cong_viec}</div>
                                      {kk.mo_ta && <div className="text-xs text-gray-500 mt-0.5 line-clamp-2">{kk.mo_ta}</div>}
                                    </td>
                                    <td className="px-3 py-2 text-center font-medium">{kk.so_luong}</td>
                                    <td className="px-3 py-2 text-center">
                                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                                        kk.trang_thai_hoan_thanh === 'HOAN_THANH'
                                          ? 'bg-green-100 text-green-700'
                                          : kk.trang_thai_hoan_thanh === 'DANG_THUC_HIEN'
                                            ? 'bg-blue-100 text-blue-700'
                                            : 'bg-gray-100 text-gray-600'
                                      }`}>
                                        {htLabel[kk.trang_thai_hoan_thanh || ''] || kk.trang_thai_hoan_thanh || '-'}
                                      </span>
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                      {(kk.so_loi_chat_luong || 0) > 0
                                        ? <span className="text-red-600 font-medium">{kk.so_loi_chat_luong}</span>
                                        : <span className="text-gray-400">0</span>}
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                      {(kk.so_loi_tien_do || 0) > 0
                                        ? <span className="text-red-600 font-medium">{kk.so_loi_tien_do}</span>
                                        : <span className="text-gray-400">0</span>}
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                      <StatusBadge status={kk.trang_thai as any} />
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                        <div className="mt-4 grid grid-cols-3 gap-3">
                          <div className="bg-blue-50 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold text-blue-700">{keKhaiLDList.length}</div>
                            <div className="text-xs text-blue-600">Tổng công việc</div>
                          </div>
                          <div className="bg-green-50 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold text-green-700">
                              {keKhaiLDList.filter(kk => kk.trang_thai_hoan_thanh === 'HOAN_THANH').length}
                            </div>
                            <div className="text-xs text-green-600">Đã hoàn thành</div>
                          </div>
                          <div className="bg-red-50 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold text-red-700">
                              {keKhaiLDList.reduce((s, kk) => s + (kk.so_loi_chat_luong || 0) + (kk.so_loi_tien_do || 0), 0)}
                            </div>
                            <div className="text-xs text-red-600">Tổng lỗi CL+TĐ</div>
                          </div>
                        </div>
                      </>
                    )
                  ) : (
                    /* ============== KÊ KHAI CÔNG CHỨC THƯỜNG ============== */
                    keKhaiList.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">Không có kê khai công việc trong tháng {thang}/{nam}</div>
                    ) : (
                      <>
                        <div className="border border-gray-200 rounded-lg overflow-hidden">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="bg-gray-50 border-b border-gray-200">
                                <th className="px-3 py-2.5 text-left font-semibold text-gray-700 w-10">STT</th>
                                <th className="px-3 py-2.5 text-left font-semibold text-gray-700">Tên công việc</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-20">Cấp độ</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-16">SL</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-20">Quy đổi SP1</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-16">Lỗi CL</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-16">Lỗi TĐ</th>
                                <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-24">Trạng thái</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                          {keKhaiList.map((kk, idx) => {
                            const tenCongViec = kk.danh_muc_sp?.ten_cong_viec || kk.danh_muc_ten || '-';
                            const maCapDo = kk.cap_do?.ma_cap_do || kk.cap_do_ma || '';
                            return (
                            <tr key={kk.id} className="hover:bg-gray-50">
                              <td className="px-3 py-2 text-gray-500">{idx + 1}</td>
                              <td className="px-3 py-2">
                                <div className="font-medium text-gray-900">{tenCongViec}</div>
                                {kk.is_doi_moi_sang_tao && (
                                  <span className="text-xs text-purple-600 font-medium">⭐ Đổi mới sáng tạo</span>
                                )}
                              </td>
                              <td className="px-3 py-2 text-center">
                                <span className={`px-2 py-0.5 text-xs font-bold rounded ${
                                  (['C3', 'C4', 'C5'].includes(maCapDo))
                                    ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                                }`}>
                                  {maCapDo || '-'}
                                </span>
                              </td>
                              <td className="px-3 py-2 text-center font-medium">{kk.so_luong}</td>
                              <td className="px-3 py-2 text-center font-medium text-blue-700">{kk.so_sp_goc_quy_doi || '-'}</td>
                              <td className="px-3 py-2 text-center">
                                {(kk.so_loi_chat_luong || 0) > 0 ? (
                                  <span className="text-red-600 font-medium">{kk.so_loi_chat_luong}</span>
                                ) : <span className="text-gray-400">0</span>}
                              </td>
                              <td className="px-3 py-2 text-center">
                                {(kk.so_loi_tien_do || 0) > 0 ? (
                                  <span className="text-red-600 font-medium">{kk.so_loi_tien_do}</span>
                                ) : <span className="text-gray-400">0</span>}
                              </td>
                              <td className="px-3 py-2 text-center">
                                <StatusBadge status={kk.trang_thai as any} />
                              </td>
                            </tr>
                            );
                          })}
                            </tbody>
                          </table>
                        </div>

                        {/* Thống kê nhanh */}
                        {keKhaiList.length > 0 && (
                          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="bg-blue-50 rounded-lg p-3 text-center">
                          <div className="text-2xl font-bold text-blue-700">{keKhaiList.length}</div>
                          <div className="text-xs text-blue-600">Tổng kê khai</div>
                        </div>
                        <div className="bg-green-50 rounded-lg p-3 text-center">
                          <div className="text-2xl font-bold text-green-700">
                            {keKhaiList.reduce((sum, kk) => sum + (kk.so_sp_goc_quy_doi || 0), 0)}
                          </div>
                          <div className="text-xs text-green-600">Tổng SP1 quy đổi</div>
                        </div>
                        <div className="bg-amber-50 rounded-lg p-3 text-center">
                          <div className="text-2xl font-bold text-amber-700">
                            {keKhaiList.filter(kk => {
                              const ma = kk.cap_do?.ma_cap_do || kk.cap_do_ma || '';
                              return ['C3', 'C4', 'C5'].includes(ma);
                            }).length}
                          </div>
                          <div className="text-xs text-amber-600">CV khó (C3+)</div>
                        </div>
                        <div className="bg-purple-50 rounded-lg p-3 text-center">
                          <div className="text-2xl font-bold text-purple-700">
                            {keKhaiList.filter(kk => kk.is_doi_moi_sang_tao).length}
                          </div>
                          <div className="text-xs text-purple-600">Đổi mới sáng tạo</div>
                        </div>
                      </div>
                    )}
                      </>
                    )
                  )}
                </div>
              )}

              {/* Tab Tiêu chí chung */}
              {activeDetailTab === 'tieu-chi' && (
                <div>
                  {!tieuChi ? (
                    <div className="text-center py-8 text-gray-500">Chưa có dữ liệu tiêu chí chung tháng {thang}/{nam}</div>
                  ) : (
                    <div className="space-y-4">
                      {/* Tổng điểm — lấy từ tong_hop */}
                      {(() => {
                        const tongHop = tieuChi.tong_hop;
                        const tieuChiArr = tieuChi.tieu_chi || [];
                        // Tính điểm CC (tự chấm) và LĐ (phê duyệt) từ mảng tieu_chi
                        const calcNhom = (nhom: number) => {
                          const items = tieuChiArr.filter(tc => tc.nhom_tieu_chi === nhom);
                          const cc = items.reduce((s, tc) => s + (tc.diem_tu_cham || 0), 0);
                          const ld = items.reduce((s, tc) => s + (tc.diem_phe_duyet ?? tc.diem_tu_cham ?? 0), 0);
                          return { cc, ld };
                        };
                        const n1 = calcNhom(1), n2 = calcNhom(2), n3 = calcNhom(3);
                        const totalCC = n1.cc + n2.cc + n3.cc;
                        const totalLD = tongHop?.tong_diem ?? (n1.ld + n2.ld + n3.ld);
                        return (
                          <>
                            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <span className="text-sm text-gray-500">Điểm tự chấm (CC)</span>
                                  <div className="text-2xl font-bold text-gray-900">{totalCC.toFixed(1)} <span className="text-sm text-gray-500">/ 30</span></div>
                                </div>
                                <div>
                                  <span className="text-sm text-gray-500">Điểm lãnh đạo duyệt</span>
                                  <div className="text-2xl font-bold text-blue-700">{totalLD.toFixed(1)} <span className="text-sm text-gray-500">/ 30</span></div>
                                </div>
                              </div>
                            </div>

                            {/* Chi tiết nhóm */}
                            <div className="border border-gray-200 rounded-lg overflow-hidden">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="bg-gray-50 border-b border-gray-200">
                                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Nhóm tiêu chí</th>
                                    <th className="px-4 py-3 text-center font-semibold text-gray-700 w-28">Điểm tối đa</th>
                                    <th className="px-4 py-3 text-center font-semibold text-gray-700 w-28">CC tự chấm</th>
                                    <th className="px-4 py-3 text-center font-semibold text-gray-700 w-28">LĐ duyệt</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                  <tr className="hover:bg-gray-50">
                                    <td className="px-4 py-3 font-medium text-gray-900">Nhóm I: Phẩm chất chính trị, đạo đức</td>
                                    <td className="px-4 py-3 text-center text-gray-500">10</td>
                                    <td className="px-4 py-3 text-center font-medium">{n1.cc.toFixed(1)}</td>
                                    <td className="px-4 py-3 text-center font-medium text-blue-700">{(tongHop?.nhom_1_diem ?? n1.ld).toFixed(1)}</td>
                                  </tr>
                                  <tr className="hover:bg-gray-50">
                                    <td className="px-4 py-3 font-medium text-gray-900">Nhóm II: Năng lực chuyên môn, nghiệp vụ</td>
                                    <td className="px-4 py-3 text-center text-gray-500">10</td>
                                    <td className="px-4 py-3 text-center font-medium">{n2.cc.toFixed(1)}</td>
                                    <td className="px-4 py-3 text-center font-medium text-blue-700">{(tongHop?.nhom_2_diem ?? n2.ld).toFixed(1)}</td>
                                  </tr>
                                  <tr className="hover:bg-gray-50">
                                    <td className="px-4 py-3 font-medium text-gray-900">Nhóm III: Năng lực đổi mới, sáng tạo</td>
                                    <td className="px-4 py-3 text-center text-gray-500">10</td>
                                    <td className="px-4 py-3 text-center font-medium">{n3.cc.toFixed(1)}</td>
                                    <td className="px-4 py-3 text-center font-medium text-blue-700">{(tongHop?.nhom_3_diem ?? n3.ld).toFixed(1)}</td>
                                  </tr>
                                </tbody>
                                <tfoot>
                                  <tr className="bg-gray-50 border-t border-gray-200 font-semibold">
                                    <td className="px-4 py-3 text-gray-900">Tổng cộng</td>
                                    <td className="px-4 py-3 text-center text-gray-700">30</td>
                                    <td className="px-4 py-3 text-center">{totalCC.toFixed(1)}</td>
                                    <td className="px-4 py-3 text-center text-blue-700">{totalLD.toFixed(1)}</td>
                                  </tr>
                                </tfoot>
                              </table>
                            </div>

                            {/* Chi tiết từng tiêu chí */}
                            {tieuChiArr.length > 0 && (
                              <div className="border border-gray-200 rounded-lg overflow-hidden">
                                <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
                                  <h4 className="text-sm font-semibold text-gray-700">Chi tiết 10 tiêu chí</h4>
                                </div>
                                <table className="w-full text-xs">
                                  <thead>
                                    <tr className="bg-gray-50 border-b">
                                      <th className="px-3 py-2 text-left text-gray-600 w-12">Mã</th>
                                      <th className="px-3 py-2 text-left text-gray-600">Tiêu chí</th>
                                      <th className="px-3 py-2 text-center text-gray-600 w-16">Tối đa</th>
                                      <th className="px-3 py-2 text-center text-gray-600 w-16">CC</th>
                                      <th className="px-3 py-2 text-center text-gray-600 w-16">LĐ</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-gray-100">
                                    {tieuChiArr.map((tc) => (
                                      <tr key={tc.ma_tieu_chi} className="hover:bg-gray-50">
                                        <td className="px-3 py-1.5 font-medium text-gray-500">{tc.ma_tieu_chi}</td>
                                        <td className="px-3 py-1.5 text-gray-900">{tc.ten_tieu_chi}</td>
                                        <td className="px-3 py-1.5 text-center text-gray-500">{tc.diem_toi_da}</td>
                                        <td className="px-3 py-1.5 text-center font-medium">{tc.diem_tu_cham}</td>
                                        <td className="px-3 py-1.5 text-center font-medium text-blue-700">{tc.diem_phe_duyet ?? '-'}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </>
                        );
                      })()}

                      {tieuChi.trang_thai && (
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-gray-500">Trạng thái:</span>
                          <StatusBadge status={tieuChi.trang_thai as any} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Tab d, đ, e (chỉ lãnh đạo) */}
              {activeDetailTab === 'dde' && isLanhDao && (
                <div>
                  {!ddeData ? (
                    <div className="text-center py-8 text-gray-500">Chưa có đánh giá d, đ, e tháng {thang}/{nam}</div>
                  ) : (
                    <div className="space-y-4">
                      {/* Tổng quan */}
                      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-4">
                        <div className="text-sm text-gray-500 mb-2">Điểm KPI lãnh đạo = (a + b + c + d + đ + e) / 6 × 70</div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-500">Trạng thái:</span>
                          <StatusBadge status={ddeData.trang_thai as any} />
                        </div>
                      </div>

                      {/* Bảng chi tiết d, đ, e */}
                      <div className="border border-gray-200 rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="bg-gray-50 border-b border-gray-200">
                              <th className="px-4 py-3 text-left font-semibold text-gray-700">Tiêu chí</th>
                              <th className="px-4 py-3 text-center font-semibold text-gray-700 w-32">Tự đánh giá</th>
                              <th className="px-4 py-3 text-center font-semibold text-gray-700 w-32">Phê duyệt</th>
                              <th className="px-4 py-3 text-center font-semibold text-gray-700 w-32">Điểm áp dụng</th>
                              <th className="px-4 py-3 text-left font-semibold text-gray-700">Ghi chú</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {[
                              { label: 'd - Kết quả đơn vị', self: ddeData.d_ket_qua_don_vi, approved: ddeData.d_phe_duyet, final: ddeData.d_final, note: ddeData.d_ghi_chu },
                              { label: 'đ - Tổ chức triển khai', self: ddeData.dd_to_chuc_trien_khai, approved: ddeData.dd_phe_duyet, final: ddeData.dd_final, note: ddeData.dd_ghi_chu },
                              { label: 'e - Đoàn kết nội bộ', self: ddeData.e_doan_ket_noi_bo, approved: ddeData.e_phe_duyet, final: ddeData.e_final, note: ddeData.e_ghi_chu },
                            ].map((row) => (
                              <tr key={row.label} className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900">{row.label}</td>
                                <td className="px-4 py-3 text-center">
                                  {row.self != null ? (
                                    <span className={`font-medium ${row.self === 100 ? 'text-green-700' : 'text-amber-700'}`}>
                                      {row.self}%
                                    </span>
                                  ) : '-'}
                                </td>
                                <td className="px-4 py-3 text-center">
                                  {row.approved != null ? (
                                    <span className={`font-medium ${row.approved === 100 ? 'text-green-700' : 'text-amber-700'}`}>
                                      {row.approved}%
                                    </span>
                                  ) : <span className="text-gray-400">-</span>}
                                </td>
                                <td className="px-4 py-3 text-center">
                                  {row.final != null ? (
                                    <span className={`font-bold text-lg ${row.final === 100 ? 'text-green-700' : 'text-amber-700'}`}>
                                      {row.final}%
                                    </span>
                                  ) : '-'}
                                </td>
                                <td className="px-4 py-3 text-gray-600 text-xs">{row.note || '-'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Tóm tắt */}
                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="text-sm text-gray-700">
                          <strong>Tổng hợp:</strong>{' '}
                          d = {ddeData.d_final ?? '-'}%,{' '}
                          đ = {ddeData.dd_final ?? '-'}%,{' '}
                          e = {ddeData.e_final ?? '-'}%{' '}
                          → Trung bình: <strong>
                            {ddeData.d_final != null && ddeData.dd_final != null && ddeData.e_final != null
                              ? (((ddeData.d_final + ddeData.dd_final + ddeData.e_final) / 3)).toFixed(1)
                              : '-'}%
                          </strong>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Tab Nghỉ phép */}
              {activeDetailTab === 'nghi-phep' && (
                <div>
                  {nghiPhepList.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">Không có đơn nghỉ phép trong tháng {thang}/{nam}</div>
                  ) : (
                    <div className="border border-gray-200 rounded-lg overflow-hidden">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-gray-50 border-b border-gray-200">
                            <th className="px-3 py-2.5 text-left font-semibold text-gray-700 w-10">STT</th>
                            <th className="px-3 py-2.5 text-left font-semibold text-gray-700">Loại nghỉ</th>
                            <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-28">Từ ngày</th>
                            <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-28">Đến ngày</th>
                            <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-20">Số ngày</th>
                            <th className="px-3 py-2.5 text-left font-semibold text-gray-700">Lý do</th>
                            <th className="px-3 py-2.5 text-center font-semibold text-gray-700 w-24">Trạng thái</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {nghiPhepList.map((np, idx) => (
                            <tr key={np.id} className="hover:bg-gray-50">
                              <td className="px-3 py-2 text-gray-500">{idx + 1}</td>
                              <td className="px-3 py-2 font-medium text-gray-900">
                                {np.loai_nghi_ten || LOAI_NGHI_MAP[np.loai_nghi] || np.loai_nghi}
                              </td>
                              <td className="px-3 py-2 text-center">{np.tu_ngay ? new Date(np.tu_ngay).toLocaleDateString('vi-VN') : '-'}</td>
                              <td className="px-3 py-2 text-center">{np.den_ngay ? new Date(np.den_ngay).toLocaleDateString('vi-VN') : '-'}</td>
                              <td className="px-3 py-2 text-center font-medium">{np.so_ngay}</td>
                              <td className="px-3 py-2 text-gray-600 text-xs">{np.ly_do || '-'}</td>
                              <td className="px-3 py-2 text-center">
                                <NghiPhepStatusBadge trangThai={np.trang_thai} trangThaiTen={np.trang_thai_ten} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Tổng kết nghỉ phép */}
                  {nghiPhepList.length > 0 && (
                    <div className="mt-4 bg-amber-50 rounded-lg p-3 flex items-center gap-4">
                      <span className="text-sm text-amber-700 font-medium">
                        Tổng ngày nghỉ: <strong className="text-lg">{nghiPhepList.reduce((sum, np) => sum + np.so_ngay, 0).toFixed(1)}</strong> ngày
                      </span>
                      <span className="text-sm text-gray-500">
                        ({nghiPhepList.filter(np => np.trang_thai === 'DA_PHE_DUYET' || np.trang_thai === 'DA_DUYET').length} đã duyệt)
                      </span>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-200 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg font-medium transition-colors"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN TABLE VIEW (cho cả ĐT và CCT)
// =============================================================================

interface BaoCaoTableViewProps {
  baoCao: IBaoCaoXepLoai;
  canEdit: boolean;
  canApprove: boolean;
  onRefresh: () => void;
  isProcessing: boolean;
  setIsProcessing: (v: boolean) => void;
  selectedThang: number;
  selectedNam: number;
}

function BaoCaoTableView({ 
  baoCao, 
  canEdit, 
  canApprove, 
  onRefresh,
  isProcessing,
  setIsProcessing,
  selectedThang,
  selectedNam,
}: BaoCaoTableViewProps) {
  const [selectedChiTiet, setSelectedChiTiet] = useState<IChiTietXepLoai | null>(null);
  const [deXuatXepLoai, setDeXuatXepLoai] = useState('B');
  const [lyDoDeXuat, setLyDoDeXuat] = useState('');
  const [detailCongChuc, setDetailCongChuc] = useState<IChiTietXepLoai | null>(null);

  // Luôn sắp xếp theo điểm tổng giảm dần, tiebreaker: ưu tiên CV khó
  const sortedChiTiet = baoCao.chi_tiet ? sortChiTietByDiem(baoCao.chi_tiet) : [];

  const trangThaiInfo = TRANG_THAI_MAP[baoCao.trang_thai] || TRANG_THAI_MAP.NHAP;
  const canGuiDuyet = canEdit && (baoCao.trang_thai === 'NHAP' || baoCao.trang_thai === 'TRA_LAI' || baoCao.trang_thai === 'TU_CHOI');

  const handleDeXuat = (ct: IChiTietXepLoai) => {
    setSelectedChiTiet(ct);
    setDeXuatXepLoai(ct.xep_loai_de_xuat || ct.xep_loai_he_thong || ct.xep_loai_tu_dong || 'B');
    setLyDoDeXuat(ct.ly_do_dieu_chinh_dt || ct.ly_do_de_xuat || '');
  };

  const handleDeXuatSubmit = async () => {
    if (!selectedChiTiet) return;
    setIsProcessing(true);
    try {
      await baoCaoApi.deXuatXepLoai(selectedChiTiet.id, {
        xep_loai_de_xuat: deXuatXepLoai,
        ly_do_dieu_chinh: lyDoDeXuat || undefined,
      });
      await onRefresh();
      setSelectedChiTiet(null);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleGuiDuyet = async () => {
    if (!window.confirm('Gửi báo cáo lên Chi cục trưởng phê duyệt?')) return;
    setIsProcessing(true);
    try {
      await baoCaoApi.guiDuyet(baoCao.id);
      await onRefresh();
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header Card */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold text-gray-900">
                Báo cáo tháng {baoCao.thang}/{baoCao.nam}
              </h3>
              <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${trangThaiInfo.color}`}>
                {trangThaiInfo.label}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">{baoCao.don_vi?.ten_don_vi}</p>
          </div>
          
          <StatsSummary baoCao={baoCao} />
          
          {canGuiDuyet && (
            <button
              onClick={handleGuiDuyet}
              disabled={isProcessing}
              className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              Gửi phê duyệt
            </button>
          )}
          {/* Nút xuất báo cáo - hiện khi có dữ liệu */}
          {baoCao.chi_tiet && baoCao.chi_tiet.length > 0 && (
            <ExportButton
              label={baoCao.trang_thai === 'NHAP' || baoCao.trang_thai === 'TRA_LAI' ? 'Xuất tạm' : 'Xuất báo cáo'}
              size="sm"
              onExport={async (format: ExportFormat) => {
                await exportService.exportDonVi({
                  thang: selectedThang,
                  nam: selectedNam,
                  donViId: baoCao.don_vi?.id,
                  format,
                });
              }}
            />
          )}
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-3 py-3 text-left font-semibold text-gray-700 w-12">STT</th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700 min-w-[180px]">Họ tên / Mã CC</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">Ngày LV</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">Ngày nghỉ</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">
                  <div>CV khó</div>
                  <div className="text-xs font-normal text-gray-500">(C3+)</div>
                </th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-24">
                  <div>Điểm TC</div>
                  <div className="text-xs font-normal text-gray-500">(30đ)</div>
                </th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-24">
                  <div>Điểm CV</div>
                  <div className="text-xs font-normal text-gray-500">(70đ)</div>
                </th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-24">
                  <div className="flex items-center justify-center gap-1">
                    <span>Tổng KPI</span>
                    <svg className="w-3 h-3 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                  <div className="text-xs font-normal text-gray-500">(100đ)</div>
                </th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">XL Tự động</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">XL Đề xuất</th>
                {canEdit && canGuiDuyet && (
                  <th className="px-3 py-3 text-center font-semibold text-gray-700 w-20">Thao tác</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sortedChiTiet.map((ct, index) => {
                const xepLoaiHeThong = ct.xep_loai_he_thong || ct.xep_loai_tu_dong;
                const hasCustomDeXuat = ct.xep_loai_de_xuat && ct.xep_loai_de_xuat !== xepLoaiHeThong;
                
                return (
                  <tr key={ct.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setDetailCongChuc(ct)}>
                    <td className="px-3 py-3 text-gray-500">{index + 1}</td>
                    <td className="px-3 py-3">
                      <div className="font-medium text-gray-900">{ct.cong_chuc?.ho_ten}</div>
                      <div className="text-xs text-gray-500">{ct.cong_chuc?.ma_cc}</div>
                      {ct.cong_chuc?.chuc_vu && (
                        <div className="text-xs text-blue-600">{ct.cong_chuc.chuc_vu}</div>
                      )}
                    </td>
                    <td className="px-3 py-3 text-center font-medium text-gray-900">
                      {ct.so_ngay_lam_viec?.toFixed(0) || '-'}
                    </td>
                    <td className="px-3 py-3 text-center">
                      {ct.so_ngay_nghi ? (
                        <span className="text-red-600 font-medium">{ct.so_ngay_nghi.toFixed(1)}</span>
                      ) : (
                        <span className="text-gray-400">0</span>
                      )}
                    </td>
                    <td className="px-3 py-3 text-center">
                      {(ct.so_cv_c3_plus || 0) > 0 ? (
                        <span className="font-bold text-amber-700">{ct.so_cv_c3_plus}</span>
                      ) : (
                        <span className="text-gray-400">0</span>
                      )}
                    </td>
                    <td className="px-3 py-3 text-center font-medium text-gray-900">
                      {ct.diem_tieu_chi_chung?.toFixed(1) || '-'}
                    </td>
                    <td className="px-3 py-3 text-center font-medium text-gray-900">
                      {ct.diem_kpi?.toFixed(1) || '-'}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className="font-bold text-lg text-gray-900">
                        {ct.diem_tong?.toFixed(1) || '-'}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <XepLoaiBadge xepLoai={xepLoaiHeThong} />
                    </td>
                    <td className="px-3 py-3 text-center">
                      {hasCustomDeXuat ? (
                        <div className="flex flex-col items-center gap-1">
                          <XepLoaiBadge xepLoai={ct.xep_loai_de_xuat} />
                          <span className="text-[10px] text-amber-600">Đã điều chỉnh</span>
                        </div>
                      ) : (
                        <XepLoaiBadge xepLoai={ct.xep_loai_de_xuat || xepLoaiHeThong} />
                      )}
                    </td>
                    {canEdit && canGuiDuyet && (
                      <td className="px-3 py-3 text-center">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDeXuat(ct); }}
                          className="px-2.5 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded border border-blue-200 transition-colors"
                        >
                          Sửa
                        </button>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {(!baoCao.chi_tiet || baoCao.chi_tiet.length === 0) && (
          <div className="py-12 text-center text-gray-500">
            Không có dữ liệu chi tiết
          </div>
        )}

        {sortedChiTiet.length > 0 && (
          <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-500 flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Sắp xếp theo điểm tổng từ cao đến thấp. Nhấn vào dòng để xem chi tiết kê khai, tiêu chí, nghỉ phép.
          </div>
        )}
      </div>

      {/* Modal xem chi tiết công chức */}
      {detailCongChuc && (
        <ChiTietCongChucModal
          congChuc={detailCongChuc}
          thang={baoCao.thang}
          nam={baoCao.nam}
          onClose={() => setDetailCongChuc(null)}
        />
      )}

      {/* Modal Đề xuất xếp loại */}
      {selectedChiTiet && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Điều chỉnh xếp loại đề xuất</h3>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="font-medium text-gray-900">{selectedChiTiet.cong_chuc?.ho_ten}</p>
              <p className="text-sm text-gray-600">{selectedChiTiet.cong_chuc?.ma_cc}</p>
              <div className="flex items-center gap-4 mt-2 text-sm">
                <span className="text-gray-500">
                  Điểm: <strong>{selectedChiTiet.diem_tong?.toFixed(1)}</strong>
                </span>
                <span className="text-gray-500">
                  Tự động: <XepLoaiBadge xepLoai={selectedChiTiet.xep_loai_he_thong || selectedChiTiet.xep_loai_tu_dong} />
                </span>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Xếp loại đề xuất</label>
              <div className="grid grid-cols-4 gap-2">
                {['A', 'B', 'C', 'D'].map((xl) => (
                  <button
                    key={xl}
                    onClick={() => setDeXuatXepLoai(xl)}
                    className={`py-2 px-3 rounded-lg border-2 font-bold text-center transition-all ${
                      deXuatXepLoai === xl 
                        ? `${XEP_LOAI_COLORS[xl]} border-current` 
                        : 'bg-gray-50 text-gray-400 border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {xl}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lý do điều chỉnh 
                {deXuatXepLoai !== (selectedChiTiet.xep_loai_he_thong || selectedChiTiet.xep_loai_tu_dong) && (
                  <span className="text-red-500 ml-1">*</span>
                )}
              </label>
              <textarea
                value={lyDoDeXuat}
                onChange={(e) => setLyDoDeXuat(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Nhập lý do nếu khác xếp loại tự động..."
              />
            </div>
            
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setSelectedChiTiet(null)} 
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium"
              >
                Hủy
              </button>
              <button 
                onClick={handleDeXuatSubmit} 
                disabled={isProcessing}
                className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-50"
              >
                {isProcessing ? 'Đang lưu...' : 'Lưu'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// ĐƠN VỊ VIEW (Phó ĐT, ĐT)
// =============================================================================

interface DonViViewProps {
  thang: number;
  nam: number;
  canApprove: boolean;
}

function DonViView({ thang, nam, canApprove }: DonViViewProps) {
  const [baoCao, setBaoCao] = useState<IBaoCaoXepLoai | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await baoCaoApi.getBaoCaoDonVi(thang, nam);
      setBaoCao(response);
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsLoading(false);
    }
  }, [thang, nam]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadData} />;
  }

  if (!baoCao) {
    return (
      <EmptyState 
        title="Chưa có dữ liệu" 
        description={`Chưa có dữ liệu xếp loại tháng ${thang}/${nam}`} 
      />
    );
  }

  // can_edit từ API hoặc dựa vào canApprove prop
  const canEdit = baoCao.can_edit ?? canApprove;

  return (
    <BaoCaoTableView
      baoCao={baoCao}
      canEdit={canEdit}
      canApprove={false}
      onRefresh={loadData}
      isProcessing={isProcessing}
      setIsProcessing={setIsProcessing}
      selectedThang={thang}
      selectedNam={nam}
    />
  );
}

// =============================================================================
// CCT VIEW
// =============================================================================

interface CCTViewProps {
  thang: number;
  nam: number;
  canApprove: boolean;
  onPendingCountChange?: (count: number) => void;
}

function CCTView({ thang, nam, canApprove, onPendingCountChange }: CCTViewProps) {
  const [pendingList, setPendingList] = useState<IBaoCaoXepLoai[]>([]);
  const [selectedBaoCao, setSelectedBaoCao] = useState<IBaoCaoXepLoai | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [pheDuyetAction, setPheDuyetAction] = useState<'approve' | 'reject' | null>(null);
  const [lyDoPheDuyet, setLyDoPheDuyet] = useState('');
  // v1.1.0: Filter trạng thái
  const [filterTrangThai, setFilterTrangThai] = useState<string>('');

  // Trả lại báo cáo đã duyệt
  const [traLaiBaoCao, setTraLaiBaoCao] = useState<IBaoCaoXepLoai | null>(null);
  const [traLaiLyDo, setTraLaiLyDo] = useState('');
  const [isTraLai, setIsTraLai] = useState(false);

  const handleTraLaiBaoCao = (bc: IBaoCaoXepLoai) => {
    setTraLaiBaoCao(bc);
    setTraLaiLyDo('');
  };

  const handleSubmitTraLai = async () => {
    if (!traLaiBaoCao || !traLaiLyDo.trim()) return;
    setIsTraLai(true);
    try {
      await baoCaoApi.traLai(traLaiBaoCao.id, traLaiLyDo);
      await loadData();
      setTraLaiBaoCao(null);
      setTraLaiLyDo('');
      setSelectedBaoCao(null);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra khi trả lại');
    } finally {
      setIsTraLai(false);
    }
  };
  const [detailCongChucCCT, setDetailCongChucCCT] = useState<IChiTietXepLoai | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // v1.1.0: Gọi API danh sách thay vì chỉ chờ phê duyệt
      const items = await baoCaoApi.getDanhSach(thang, nam, filterTrangThai || undefined);
      setPendingList(items);
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsLoading(false);
    }
  }, [thang, nam, filterTrangThai]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    onPendingCountChange?.(pendingList.length);
  }, [pendingList, onPendingCountChange]);

  const handleSelectBaoCao = async (baoCaoId: string) => {
    try {
      const detail = await baoCaoApi.getChiTiet(baoCaoId);
      setSelectedBaoCao(detail);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    }
  };

  const handlePheDuyetSubmit = async () => {
    if (!selectedBaoCao || !pheDuyetAction) return;
    if (pheDuyetAction === 'reject' && !lyDoPheDuyet.trim()) {
      alert('Vui lòng nhập lý do từ chối');
      return;
    }

    setIsProcessing(true);
    try {
      await baoCaoApi.pheDuyet(selectedBaoCao.id, {
        action: pheDuyetAction === 'approve' ? 'APPROVE' : 'REJECT',
        y_kien: lyDoPheDuyet || undefined,
      });
      await loadData();
      setSelectedBaoCao(null);
      setPheDuyetAction(null);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadData} />;
  }

  const TRANG_THAI_OPTIONS = [
    { value: '', label: 'Tất cả' },
    { value: 'NHAP', label: 'Nháp' },
    { value: 'CHO_PHE_DUYET', label: 'Chờ duyệt' },
    { value: 'DA_PHE_DUYET', label: 'Đã duyệt' },
    { value: 'TU_CHOI', label: 'Từ chối' },
  ];
  const trangThaiLabel = (tt: string) => {
    const map: Record<string, { label: string; color: string }> = {
      NHAP: { label: 'Nháp', color: 'bg-gray-100 text-gray-700' },
      CHO_PHE_DUYET: { label: 'Chờ duyệt', color: 'bg-amber-100 text-amber-700' },
      DA_PHE_DUYET: { label: 'Đã duyệt', color: 'bg-green-100 text-green-700' },
      TU_CHOI: { label: 'Từ chối', color: 'bg-red-100 text-red-700' },
    };
    return map[tt] || { label: tt, color: 'bg-gray-100 text-gray-700' };
  };
  if (pendingList.length === 0 && !filterTrangThai) {
    return (
      <div>
        <div className="flex items-center gap-3 mb-4">
          <label className="text-sm font-medium text-gray-700">Trạng thái:</label>
          <select
            value={filterTrangThai}
            onChange={(e) => setFilterTrangThai(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500"
          >
            {TRANG_THAI_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <EmptyState
          title="Không có báo cáo"
          description={`Không có báo cáo xếp loại nào tháng ${thang}/${nam}`}
        />
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {/* v1.1.0: Filter trạng thái */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-700">Trạng thái:</label>
        <select
          value={filterTrangThai}
          onChange={(e) => setFilterTrangThai(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500"
        >
          {TRANG_THAI_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label} ({pendingList.filter(bc => opt.value ? bc.trang_thai === opt.value : true).length})
            </option>
          ))}
        </select>
        <span className="text-sm text-gray-500">{pendingList.length} báo cáo</span>
      </div>
      {/* Danh sách báo cáo */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {pendingList.map((bc) => (
          <div
            key={bc.id}
            className="bg-white rounded-lg border border-gray-200 p-4 hover:border-blue-300 hover:shadow-md cursor-pointer transition-all"
            onClick={() => handleSelectBaoCao(bc.id)}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-medium text-gray-900">{bc.don_vi?.ten_don_vi}</h4>
                <p className="text-sm text-gray-500">Tháng {bc.thang}/{bc.nam}</p>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${trangThaiLabel(bc.trang_thai).color}`}>
                {trangThaiLabel(bc.trang_thai).label}
              </span>
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded font-medium">A: {bc.so_loai_a}</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded font-medium">B: {bc.so_loai_b}</span>
              <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded font-medium">C: {bc.so_loai_c}</span>
              <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded font-medium">D: {bc.so_loai_d}</span>
            </div>
            <p className="text-xs text-gray-400 mt-2">Tổng: {bc.tong_cong_chuc} công chức</p>
          </div>
        ))}
      </div>

      {/* Modal chi tiết báo cáo */}
      {selectedBaoCao && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-xl">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{selectedBaoCao.don_vi?.ten_don_vi}</h3>
                <p className="text-sm text-gray-500">Báo cáo xếp loại tháng {selectedBaoCao.thang}/{selectedBaoCao.nam}</p>
              </div>
              <div className="flex items-center gap-3">
                {selectedBaoCao?.chi_tiet && selectedBaoCao.chi_tiet.length > 0 && (
                  <ExportButton
                    label="Xuất báo cáo"
                    size="sm"
                    onExport={async (format: ExportFormat) => {
                      await exportService.exportDonVi({
                        thang: selectedBaoCao.thang,
                        nam: selectedBaoCao.nam,
                        donViId: selectedBaoCao.don_vi?.id,
                        format,
                      });
                    }}
                  />
                )}
                <button
                  onClick={() => setSelectedBaoCao(null)}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Stats */}
              <div className="mb-6">
                <StatsSummary baoCao={selectedBaoCao} />
              </div>

              {/* Table */}
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="px-3 py-2.5 text-left font-semibold text-gray-700">STT</th>
                      <th className="px-3 py-2.5 text-left font-semibold text-gray-700">Họ tên / Mã CC</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">Điểm TC</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">Điểm CV</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">Tổng KPI</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">CV C3+</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">XL Tự động</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">XL Đề xuất</th>
                      <th className="px-3 py-2.5 text-center font-semibold text-gray-700">XL Quyết định</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {(selectedBaoCao.chi_tiet ? sortChiTietByDiem(selectedBaoCao.chi_tiet) : []).map((ct, index) => (
                      <tr key={ct.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setDetailCongChucCCT(ct)}>
                        <td className="px-3 py-2 text-gray-500">{index + 1}</td>
                        <td className="px-3 py-2">
                          <div className="font-medium text-gray-900">{ct.cong_chuc?.ho_ten}</div>
                          <div className="text-xs text-gray-500">{ct.cong_chuc?.ma_cc}</div>
                        </td>
                        <td className="px-3 py-2 text-center">{ct.diem_tieu_chi_chung?.toFixed(1) || '-'}</td>
                        <td className="px-3 py-2 text-center">{ct.diem_kpi?.toFixed(1) || '-'}</td>
                        <td className="px-3 py-2 text-center font-bold">{ct.diem_tong?.toFixed(1) || '-'}</td>
                        <td className="px-3 py-2 text-center">
                          {(ct.so_cv_c3_plus || 0) > 0 ? (
                            <span className="font-bold text-amber-700">{ct.so_cv_c3_plus}</span>
                          ) : (
                            <span className="text-gray-400">0</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <XepLoaiBadge xepLoai={ct.xep_loai_he_thong || ct.xep_loai_tu_dong} />
                        </td>
                        <td className="px-3 py-2 text-center">
                          <XepLoaiBadge xepLoai={ct.xep_loai_de_xuat} />
                        </td>
                        <td className="px-3 py-2 text-center">
                          <XepLoaiBadge xepLoai={ct.xep_loai_quyet_dinh} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end items-center">
              {/* Nút phê duyệt - bên phải */}
              {canApprove && (
                <div className="flex gap-3">
                  {selectedBaoCao?.trang_thai === 'DA_PHE_DUYET' ? (
                  <button
                    onClick={() => handleTraLaiBaoCao(selectedBaoCao!)}
                    disabled={isProcessing}
                    className="px-4 py-2 text-orange-700 bg-orange-50 border border-orange-200 hover:bg-orange-100 rounded-lg font-medium transition-colors"
                  >
                    ↩ Trả lại đã duyệt
                  </button>
                ) : (
                  <>
                    <button
                      onClick={() => { setPheDuyetAction('reject'); setLyDoPheDuyet(''); }}
                      disabled={isProcessing}
                      className="px-4 py-2 text-red-600 bg-white border border-red-200 hover:bg-red-50 rounded-lg font-medium transition-colors"
                    >
                      Từ chối
                    </button>
                    <button
                      onClick={() => { setPheDuyetAction('approve'); setLyDoPheDuyet(''); }}
                      disabled={isProcessing}
                      className="px-4 py-2 text-white bg-green-600 hover:bg-green-700 rounded-lg font-medium transition-colors"
                    >
                      Phê duyệt
                    </button>
                  </>
                )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal xác nhận phê duyệt/từ chối */}
      {pheDuyetAction && selectedBaoCao && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {pheDuyetAction === 'approve' ? '✅ Xác nhận phê duyệt' : '❌ Xác nhận từ chối'}
            </h3>
            <p className="text-gray-600 mb-4">
              {pheDuyetAction === 'approve'
                ? `Phê duyệt báo cáo xếp loại của ${selectedBaoCao.don_vi?.ten_don_vi}?`
                : `Từ chối báo cáo xếp loại của ${selectedBaoCao.don_vi?.ten_don_vi}?`}
            </p>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ý kiến {pheDuyetAction === 'reject' && <span className="text-red-500">*</span>}
              </label>
              <textarea
                value={lyDoPheDuyet}
                onChange={(e) => setLyDoPheDuyet(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder={pheDuyetAction === 'reject' ? 'Nhập lý do từ chối...' : 'Nhập ý kiến (không bắt buộc)...'}
              />
            </div>
            
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setPheDuyetAction(null)} 
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium"
              >
                Hủy
              </button>
              <button
                onClick={handlePheDuyetSubmit}
                disabled={isProcessing}
                className={`px-4 py-2 text-white rounded-lg font-medium disabled:opacity-50 ${
                  pheDuyetAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {isProcessing ? 'Đang xử lý...' : 'Xác nhận'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Trả lại báo cáo đã duyệt */}
      {traLaiBaoCao && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-orange-700">↩ Trả lại báo cáo xếp loại đã duyệt</h3>
              <button onClick={() => setTraLaiBaoCao(null)} className="p-1 text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg text-sm text-orange-800">
                ⚠️ Báo cáo xếp loại của <strong>{traLaiBaoCao.don_vi?.ten_don_vi || 'N/A'}</strong> sẽ được chuyển về trạng thái <strong>Chờ phê duyệt</strong>.
                Xếp loại quyết định của từng công chức sẽ bị xóa.
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lý do trả lại <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={traLaiLyDo}
                  onChange={(e) => setTraLaiLyDo(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm"
                  rows={3}
                  maxLength={500}
                  placeholder="Nhập lý do trả lại..."
                  required
                />
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <button onClick={() => setTraLaiBaoCao(null)} className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">Hủy</button>
              <button
                onClick={handleSubmitTraLai}
                disabled={isTraLai || !traLaiLyDo.trim()}
                className="px-4 py-2 text-white bg-orange-600 hover:bg-orange-700 rounded-lg transition-colors disabled:opacity-50"
              >
                {isTraLai ? 'Đang xử lý...' : 'Xác nhận trả lại'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal xem chi tiết công chức (CCT view) */}
      {detailCongChucCCT && selectedBaoCao && (
        <ChiTietCongChucModal
          congChuc={detailCongChucCCT}
          thang={selectedBaoCao.thang || thang}
          nam={selectedBaoCao.nam || nam}
          onClose={() => setDetailCongChucCCT(null)}
        />
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TabBaoCao({ thang, nam, canApprove, capBac, onPendingCountChange }: ITabProps) {
  const user = useAuthStore((state) => state.user);
  const isCCT = capBac === CapBacVaiTro.CHI_CUC_TRUONG;
  const hasViewAll = user?.can_view_all_units === true;
  // CCT hoặc user có can_view_all_units → xem tất cả đơn vị
  if (isCCT || hasViewAll) {
    return <CCTView thang={thang} nam={nam} canApprove={isCCT ? canApprove : false} onPendingCountChange={onPendingCountChange} />;
  }
  // Phó ĐT, ĐT, Phó CCT xem báo cáo đơn vị
  return <DonViView thang={thang} nam={nam} canApprove={canApprove} />;
} 
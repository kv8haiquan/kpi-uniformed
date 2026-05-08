/**
 * src/components/xep-loai/tabs/TabTamTinh.tsx
 * =============================================
 * Tab "Tạm tính" - Tổng hợp tạm tính điểm KPI của công chức trong đơn vị.
 *
 * Version: 3.0.0 (15/03/2026)
 *
 * FIX v3.0: Lãnh đạo dùng công thức 6 chỉ số (a+b+c+d+đ+e)/6 × 70
 *           Công chức dùng công thức 3 chỉ số (a+b+c)/3 × 70
 * FIX v2.0: Tính lại a, b, c theo đúng công thức danh-gia/page.tsx
 * - Match items by cong_chuc_id (không dùng index)
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/axios';
import { ITabProps, CapBacVaiTro } from '@/types/xep-loai';
import { useAuthStore } from '@/stores/useAuthStore';
import {
  LoadingSpinner,
} from '../shared';

// =============================================================================
// TYPES
// =============================================================================

interface IRawItem {
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu?: string;
  don_vi_id?: string;
  don_vi_ten?: string;
  cap_bac?: string;

  // Ngày làm việc
  so_ngay_trong_thang: number;
  so_ngay_nghi: number;
  so_ngay_lam_viec: number;

  // SP (raw data từ backend)
  sp_duoc_giao: number;
  tong_sp_hoan_thanh: number;
  sp_chat_luong: number;
  sp_tien_do: number;

  // Tỷ lệ (từ backend - KHÔNG dùng, tự tính lại)
  a_so_luong: number;
  b_chat_luong: number;
  c_tien_do: number;

  // Điểm (từ backend - KHÔNG dùng, tự tính lại)
  diem_30: number;
  diem_70: number;
  diem_kpi: number;
  diem_tong: number;
  xep_loai: string;

  // Lãnh đạo
  is_lanh_dao?: boolean;
  // HĐ 111 (Phase 3 — 29/04/2026): kê khai form LĐ, công thức 3 chỉ số (a, b, c)
  is_hd_111?: boolean;
  tong_cong_viec?: number;
  tong_hoan_thanh?: number;
  tong_diem_chat_luong?: number;
  tong_diem_tien_do?: number;
  d_ket_qua?: number;
  dd_to_chuc?: number;
  e_doan_ket?: number;

  // Trạng thái
  trang_thai_tc?: string;
}

interface IDonVi {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
}

interface IApiResponse {
  thang: number;
  nam: number;
  don_vi_id?: string;
  items: IRawItem[];
  thong_ke_xep_loai: {
    A: number;
    B: number;
    C: number;
    D: number;
  };
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

// Item đã tính lại theo công thức danh-gia/page.tsx
interface IComputedItem {
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu?: string;
  don_vi_ten?: string;
  is_lanh_dao?: boolean;
  is_hd_111?: boolean;

  // Raw data (công chức)
  so_ngay_nghi: number;
  so_ngay_lam_viec: number;
  sp_duoc_giao: number;
  tong_sp_hoan_thanh: number;
  sp_chat_luong: number;
  sp_tien_do: number;

  // Leader fields
  tong_cong_viec?: number;
  tong_hoan_thanh?: number;
  d_ket_qua?: number;
  dd_to_chuc?: number;
  e_doan_ket?: number;

  // Tỷ lệ (tính lại theo danh-gia/page.tsx)
  a_so_luong: number;
  b_chat_luong: number;
  c_tien_do: number;

  // Điểm (tính lại)
  diem_30: number;
  diem_70: number;
  diem_tong: number;
  xep_loai: string;
}

// =============================================================================
// HELPERS - Công thức giống danh-gia/page.tsx
// =============================================================================

function tinhXepLoai(diem: number): string {
  if (diem === 0) return 'E';
  if (diem < 50) return 'D';
  if (diem < 70) return 'C';
  if (diem < 90) return 'B';
  return 'A';
}

/**
 * Tính lại điểm từ raw data theo đúng công thức danh-gia/page.tsx
 *
 * CÔNG CHỨC (3 chỉ số):
 * a = min(SP_hoàn_thành / SP_được_giao, 1)
 * b = min(SP_chất_lượng / SP_được_giao, 1)
 * c = min(SP_tiến_độ / SP_được_giao, 1)
 * Điểm KPI = (a + b + c) / 3 × 70
 *
 * LÃNH ĐẠO (6 chỉ số):
 * a = CV_hoàn_thành / Tổng_CV
 * b = Tổng_điểm_tiến_độ / Tổng_CV
 * c = Tổng_điểm_chất_lượng / Tổng_CV
 * d, đ, e = giá trị DDE / 100
 * Điểm KPI = (a + b + c + d + đ + e) / 6 × 70
 */
function computeItem(raw: IRawItem): IComputedItem {
  const diem30 = raw.diem_30;
  let diem70: number;

  if (raw.is_lanh_dao || raw.is_hd_111) {
    // Lãnh đạo (6 chỉ số) + HĐ 111 (3 chỉ số, không có d/đ/e):
    // backend đã tính đúng theo công thức tương ứng → dùng trực tiếp.
    diem70 = raw.diem_70;
  } else {
    // Công chức: tính lại từ raw SP data
    const spDuocGiao = raw.sp_duoc_giao;
    const a = spDuocGiao > 0 ? Math.min(raw.tong_sp_hoan_thanh / spDuocGiao, 1) : 0;
    const b = spDuocGiao > 0 ? Math.min(raw.sp_chat_luong / spDuocGiao, 1) : 0;
    const c = spDuocGiao > 0 ? Math.min(raw.sp_tien_do / spDuocGiao, 1) : 0;
    const diemKPI = (a + b + c) / 3;
    diem70 = diemKPI * 70;
  }

  const diemTong = diem30 + diem70;

  return {
    cong_chuc_id: raw.cong_chuc_id,
    ma_cc: raw.ma_cc,
    ho_ten: raw.ho_ten,
    chuc_vu: raw.chuc_vu,
    don_vi_ten: raw.don_vi_ten,
    is_lanh_dao: raw.is_lanh_dao,
    is_hd_111: raw.is_hd_111,

    so_ngay_nghi: raw.so_ngay_nghi,
    so_ngay_lam_viec: raw.so_ngay_lam_viec,
    sp_duoc_giao: raw.sp_duoc_giao,
    tong_sp_hoan_thanh: raw.tong_sp_hoan_thanh,
    sp_chat_luong: raw.sp_chat_luong,
    sp_tien_do: raw.sp_tien_do,

    // Leader fields
    tong_cong_viec: raw.tong_cong_viec,
    tong_hoan_thanh: raw.tong_hoan_thanh,
    d_ket_qua: raw.d_ket_qua,
    dd_to_chuc: raw.dd_to_chuc,
    e_doan_ket: raw.e_doan_ket,

    a_so_luong: raw.a_so_luong,
    b_chat_luong: raw.b_chat_luong,
    c_tien_do: raw.c_tien_do,

    diem_30: diem30,
    diem_70: diem70,
    diem_tong: diemTong,
    xep_loai: tinhXepLoai(diemTong),
  };
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TabTamTinh({ thang, nam, capBac, onPendingCountChange }: ITabProps) {
  const { user } = useAuthStore();

  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [danhSachDonVi, setDanhSachDonVi] = useState<IDonVi[]>([]);
  const [selectedDonViId, setSelectedDonViId] = useState<string>('');

  // Data state - 2 bộ dữ liệu: thực tế và tạm tính
  const [dataThucTe, setDataThucTe] = useState<IApiResponse | null>(null);
  const [dataTamTinh, setDataTamTinh] = useState<IApiResponse | null>(null);

  const [page, setPage] = useState(1);
  const pageSize = 50;

  const isCCTorPCCT = [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG].includes(capBac);

  // =============================================================================
  // API CALLS
  // =============================================================================

  const fetchDanhSachDonVi = useCallback(async () => {
    if (!isCCTorPCCT) return;
    try {
      const response = await apiClient.get<{ success: boolean; data: IDonVi[] }>(
        '/xep-loai/danh-sach-don-vi'
      );
      if (response.data.success) {
        setDanhSachDonVi(response.data.data);
      }
    } catch (err) {
      console.error('Lỗi khi lấy danh sách đơn vị:', err);
    }
  }, [isCCTorPCCT]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params: any = {
        thang,
        nam,
        page,
        page_size: pageSize,
      };

      if (selectedDonViId) {
        params.don_vi_id = selectedDonViId;
      }

      // Gọi 2 API: 1 cho thực tế, 1 cho tạm tính
      const [responseThucTe, responseTamTinh] = await Promise.all([
        apiClient.get<{ success: boolean; data: IApiResponse }>(
          '/xep-loai/tong-hop',
          { params: { ...params, tam_tinh: false } }
        ),
        apiClient.get<{ success: boolean; data: IApiResponse }>(
          '/xep-loai/tong-hop',
          { params: { ...params, tam_tinh: true } }
        ),
      ]);

      if (responseThucTe.data.success && responseTamTinh.data.success) {
        setDataThucTe(responseThucTe.data.data);
        setDataTamTinh(responseTamTinh.data.data);
      } else {
        setError('Không thể tải dữ liệu');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Đã xảy ra lỗi khi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  }, [thang, nam, page, selectedDonViId]);

  // =============================================================================
  // EFFECTS
  // =============================================================================

  useEffect(() => {
    fetchDanhSachDonVi();
  }, [fetchDanhSachDonVi]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (onPendingCountChange) {
      onPendingCountChange(0);
    }
  }, [onPendingCountChange]);

  // =============================================================================
  // COMPUTED DATA - Tính lại theo công thức danh-gia/page.tsx
  // =============================================================================

  // Build map tạm tính theo cong_chuc_id để match chính xác
  const tamTinhMap = new Map<string, IRawItem>();
  if (dataTamTinh) {
    for (const item of dataTamTinh.items) {
      tamTinhMap.set(item.cong_chuc_id, item);
    }
  }

  // Tính lại items với công thức đúng
  const computedRows: { thucTe: IComputedItem; tamTinh: IComputedItem }[] = [];
  if (dataThucTe) {
    for (const rawTT of dataThucTe.items) {
      const rawTamTinh = tamTinhMap.get(rawTT.cong_chuc_id);
      if (!rawTamTinh) continue;
      computedRows.push({
        thucTe: computeItem(rawTT),
        tamTinh: computeItem(rawTamTinh),
      });
    }
  }

  // Tính lại thống kê xếp loại từ computed data
  const thongKeTamTinh = { A: 0, B: 0, C: 0, D: 0 };
  for (const row of computedRows) {
    const xl = row.tamTinh.xep_loai;
    if (xl === 'A') thongKeTamTinh.A++;
    else if (xl === 'B') thongKeTamTinh.B++;
    else if (xl === 'C') thongKeTamTinh.C++;
    else thongKeTamTinh.D++;
  }

  // =============================================================================
  // HELPERS
  // =============================================================================

  const getXepLoaiColor = (xepLoai: string) => {
    switch (xepLoai) {
      case 'A':
        return 'bg-green-100 text-green-800';
      case 'B':
        return 'bg-blue-100 text-blue-800';
      case 'C':
        return 'bg-yellow-100 text-yellow-800';
      case 'D':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // =============================================================================
  // RENDER
  // =============================================================================

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Đang tải dữ liệu tạm tính...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 font-medium">Lỗi: {error}</p>
        <button
          onClick={fetchData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Thử lại
        </button>
      </div>
    );
  }

  if (computedRows.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-600 text-lg font-medium">Chưa có dữ liệu</p>
        <p className="text-gray-500 mt-2">Chưa có dữ liệu tạm tính cho tháng {thang}/{nam}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header & Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Tổng hợp tạm tính điểm KPI tháng {thang}/{nam}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Bao gồm cả công việc và nghỉ phép CHỜ PHÊ DUYỆT
            </p>
          </div>

          {isCCTorPCCT && danhSachDonVi.length > 0 && (
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Đơn vị:</label>
              <select
                value={selectedDonViId}
                onChange={(e) => {
                  setSelectedDonViId(e.target.value);
                  setPage(1);
                }}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              >
                <option value="">Tất cả đơn vị</option>
                {danhSachDonVi.map((dv) => (
                  <option key={dv.id} value={dv.id}>
                    {dv.ten_don_vi}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Thống kê tóm tắt */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Thống kê xếp loại (tạm tính)</h3>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{thongKeTamTinh.A}</div>
            <div className="text-sm text-gray-600">Loại A</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{thongKeTamTinh.B}</div>
            <div className="text-sm text-gray-600">Loại B</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{thongKeTamTinh.C}</div>
            <div className="text-sm text-gray-600">Loại C</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{thongKeTamTinh.D}</div>
            <div className="text-sm text-gray-600">Loại D</div>
          </div>
        </div>
      </div>

      {/* Bảng dữ liệu */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th rowSpan={2} className="px-4 py-3 text-left font-semibold text-gray-700 border-r">
                  STT
                </th>
                <th rowSpan={2} className="px-4 py-3 text-left font-semibold text-gray-700 border-r">
                  Họ tên / Mã CC
                </th>
                <th rowSpan={2} className="px-4 py-3 text-left font-semibold text-gray-700 border-r">
                  Đơn vị
                </th>
                <th colSpan={2} className="px-4 py-3 text-center font-semibold text-gray-700 border-r">
                  Ngày nghỉ
                </th>
                <th colSpan={2} className="px-4 py-3 text-center font-semibold text-gray-700 border-r">
                  Ngày LV
                </th>
                <th colSpan={2} className="px-4 py-3 text-center font-semibold text-gray-700 border-r">
                  Điểm được giao
                </th>
                <th colSpan={2} className="px-4 py-3 text-center font-semibold text-gray-700 border-r">
                  Điểm hoàn thành
                </th>
                <th colSpan={2} className="px-4 py-3 text-center font-semibold text-gray-700 border-r">
                  Điểm đạt CL
                </th>
                <th colSpan={2} className="px-4 py-3 text-center font-semibold text-gray-700 border-r">
                  Điểm đạt TĐ
                </th>
                <th colSpan={2} className="px-4 py-3 text-center font-semibold text-gray-700 border-r">
                  Điểm TC (30đ)
                </th>
                <th colSpan={2} className="px-4 py-3 text-center font-semibold text-gray-700 border-r">
                  Điểm CV (70đ)
                </th>
                <th colSpan={2} className="px-4 py-3 text-center font-semibold text-gray-700 border-r">
                  Tổng điểm
                </th>
                <th colSpan={2} className="px-4 py-3 text-center font-semibold text-gray-700">
                  Xếp loại
                </th>
              </tr>
              <tr className="bg-gray-100">
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border-r">Thực tế</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-amber-700 border-r bg-amber-50">Tạm tính</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border-r">Thực tế</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-amber-700 border-r bg-amber-50">Tạm tính</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border-r">Thực tế</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-amber-700 border-r bg-amber-50">Tạm tính</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border-r">Thực tế</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-amber-700 border-r bg-amber-50">Tạm tính</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border-r">Thực tế</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-amber-700 border-r bg-amber-50">Tạm tính</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border-r">Thực tế</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-amber-700 border-r bg-amber-50">Tạm tính</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border-r">Thực tế</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-amber-700 border-r bg-amber-50">Tạm tính</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border-r">Thực tế</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-amber-700 border-r bg-amber-50">Tạm tính</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border-r">Thực tế</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-amber-700 border-r bg-amber-50">Tạm tính</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border-r">Thực tế</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-amber-700 bg-amber-50">Tạm tính</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {computedRows.map(({ thucTe, tamTinh }, index) => (
                <tr key={thucTe.cong_chuc_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-900 border-r">
                    {(page - 1) * pageSize + index + 1}
                  </td>
                  <td className="px-4 py-3 border-r">
                    <div className="font-medium text-gray-900">
                      {thucTe.ho_ten}
                      {thucTe.is_lanh_dao && (
                        <span className="ml-1 text-xs text-purple-600 font-normal" title="Lãnh đạo - công thức 6 chỉ số">(LĐ)</span>
                      )}
                      {thucTe.is_hd_111 && (
                        <span className="ml-1 text-xs text-teal-600 font-normal" title="HĐ 111 — kê khai form LĐ, công thức 3 chỉ số (a, b, c)">(HĐ 111)</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">{thucTe.ma_cc}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-600 border-r text-xs">
                    {thucTe.don_vi_ten}
                  </td>
                  {(thucTe.is_lanh_dao || thucTe.is_hd_111) ? (
                    <>
                      <td className="px-2 py-3 text-center text-gray-400 border-r">-</td>
                      <td className="px-2 py-3 text-center text-gray-400 border-r bg-amber-50">-</td>
                      <td className="px-2 py-3 text-center text-gray-400 border-r">-</td>
                      <td className="px-2 py-3 text-center text-gray-400 border-r bg-amber-50">-</td>
                    </>
                  ) : (
                    <>
                      <td className="px-2 py-3 text-center text-gray-900 border-r">{thucTe.so_ngay_nghi}</td>
                      <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium">{tamTinh.so_ngay_nghi}</td>
                      <td className="px-2 py-3 text-center text-gray-900 border-r">{thucTe.so_ngay_lam_viec}</td>
                      <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium">{tamTinh.so_ngay_lam_viec}</td>
                    </>
                  )}
                  {(thucTe.is_lanh_dao || thucTe.is_hd_111) ? (
                    <>
                      <td className="px-2 py-3 text-center text-gray-900 border-r">{thucTe.tong_cong_viec ?? 0}</td>
                      <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium">{tamTinh.tong_cong_viec ?? 0}</td>
                      <td className="px-2 py-3 text-center text-gray-900 border-r">{thucTe.tong_hoan_thanh ?? 0}</td>
                      <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium">{tamTinh.tong_hoan_thanh ?? 0}</td>
                      {/* Cột d/đ/e: HĐ 111 không có, gạch "-" */}
                      {thucTe.is_hd_111 ? (
                        <>
                          <td className="px-2 py-3 text-center text-gray-400 border-r">-</td>
                          <td className="px-2 py-3 text-center text-gray-400 border-r bg-amber-50">-</td>
                        </>
                      ) : (
                        <>
                          <td className="px-2 py-3 text-center text-gray-900 border-r" title={`d=${((thucTe.d_ket_qua ?? 1) * 100).toFixed(6).replace(/\.?0+$/, '')}% đ=${((thucTe.dd_to_chuc ?? 1) * 100).toFixed(6).replace(/\.?0+$/, '')}% e=${((thucTe.e_doan_ket ?? 1) * 100).toFixed(6).replace(/\.?0+$/, '')}%`}>
                            d/đ/e
                          </td>
                          <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium" title={`d=${((tamTinh.d_ket_qua ?? 1) * 100).toFixed(6).replace(/\.?0+$/, '')}% đ=${((tamTinh.dd_to_chuc ?? 1) * 100).toFixed(6).replace(/\.?0+$/, '')}% e=${((tamTinh.e_doan_ket ?? 1) * 100).toFixed(6).replace(/\.?0+$/, '')}%`}>
                            d/đ/e
                          </td>
                        </>
                      )}
                      <td className="px-2 py-3 text-center text-gray-400 border-r">-</td>
                      <td className="px-2 py-3 text-center text-gray-400 border-r bg-amber-50">-</td>
                    </>
                  ) : (
                    <>
                      <td className="px-2 py-3 text-center text-gray-900 border-r">{Math.round(thucTe.sp_duoc_giao)}</td>
                      <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium">{Math.round(tamTinh.sp_duoc_giao)}</td>
                      <td className="px-2 py-3 text-center text-gray-900 border-r">{Math.round(thucTe.tong_sp_hoan_thanh)}</td>
                      <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium">{Math.round(tamTinh.tong_sp_hoan_thanh)}</td>
                      <td className="px-2 py-3 text-center text-gray-900 border-r">{Math.round(thucTe.sp_chat_luong)}</td>
                      <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium">{Math.round(tamTinh.sp_chat_luong)}</td>
                      <td className="px-2 py-3 text-center text-gray-900 border-r">{Math.round(thucTe.sp_tien_do)}</td>
                      <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium">{Math.round(tamTinh.sp_tien_do)}</td>
                    </>
                  )}
                  <td className="px-2 py-3 text-center text-gray-900 border-r">{thucTe.diem_30.toFixed(6).replace(/\.?0+$/, '')}</td>
                  <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium">{tamTinh.diem_30.toFixed(6).replace(/\.?0+$/, '')}</td>
                  <td className="px-2 py-3 text-center text-gray-900 border-r">{thucTe.diem_70.toFixed(6).replace(/\.?0+$/, '')}</td>
                  <td className="px-2 py-3 text-center text-amber-700 border-r bg-amber-50 font-medium">{tamTinh.diem_70.toFixed(6).replace(/\.?0+$/, '')}</td>
                  <td className="px-2 py-3 text-center text-gray-900 border-r font-semibold">{thucTe.diem_tong.toFixed(6).replace(/\.?0+$/, '')}</td>
                  <td className="px-2 py-3 text-center text-amber-700 bg-amber-50 font-bold">{tamTinh.diem_tong.toFixed(6).replace(/\.?0+$/, '')}</td>
                  <td className="px-2 py-3 text-center border-r">
                    <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${getXepLoaiColor(thucTe.xep_loai)}`}>
                      {thucTe.xep_loai}
                    </span>
                  </td>
                  <td className="px-2 py-3 text-center bg-amber-50">
                    <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${getXepLoaiColor(tamTinh.xep_loai)}`}>
                      {tamTinh.xep_loai}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {dataThucTe && dataThucTe.pagination.total_pages > 1 && (
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Trang {dataThucTe.pagination.page} / {dataThucTe.pagination.total_pages} •{' '}
              Tổng {dataThucTe.pagination.total} công chức
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Trước
              </button>
              <button
                onClick={() => setPage((p) => Math.min(dataThucTe!.pagination.total_pages, p + 1))}
                disabled={page === dataThucTe.pagination.total_pages}
                className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Sau
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

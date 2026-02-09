/**
 * src/components/xep-loai/tabs/TabTieuChi.tsx
 * ============================================
 * Tab "Duyệt tiêu chí" - Phê duyệt tiêu chí chung 2 cấp.
 * 
 * ✅ VERIFIED API ENDPOINTS (29/01/2026):
 * ┌────────┬────────────────────────────────────────────────┬──────────────────────────────┐
 * │ Method │ Endpoint                                       │ Mô tả                        │
 * ├────────┼────────────────────────────────────────────────┼──────────────────────────────┤
 * │ GET    │ /danh-gia/tieu-chi-chung                       │ Lấy danh mục tiêu chí chung  │
 * │ GET    │ /danh-gia/tieu-chi/cho-phe-duyet               │ DS chờ phê duyệt             │
 * │ GET    │ /danh-gia/tieu-chi/{danh_gia_thang_id}/chi-tiet│ Chi tiết tiêu chí            │
 * │ POST   │ /danh-gia/{danh_gia_thang_id}/phe-duyet-tieu-chi│ Phê duyệt 1 tiêu chí        │
 * │ POST   │ /danh-gia/phe-duyet-tieu-chi-bulk              │ Phê duyệt bulk               │
 * │ POST   │ /danh-gia/{id}/tu-choi-tieu-chi               │ ⭐ v3.5: Từ chối tiêu chí     │
 * └────────┴────────────────────────────────────────────────┴──────────────────────────────┘
 * 
 * Version: 3.5.0 - Hỗ trợ CHO_CAP2, TU_CHOI + hiển thị lý do từ chối (02/02/2026)
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { format } from 'date-fns';
import apiClient from '@/lib/axios';
import { ITabProps } from '@/types/xep-loai';
import {
  LoadingSpinner,
  EmptyState,
  ErrorMessage,
  StatusBadge,
} from '../shared';

// =============================================================================
// TYPES
// =============================================================================

interface ITieuChiItem {
  danh_gia_thang_id: string;
  cong_chuc_id: string;
  ma_cc: string;
  ho_ten: string;
  don_vi_ten?: string;
  thang: number;
  nam: number;
  diem_tu_cham: number;
  trang_thai: string;
  ngay_gui?: string;
  nguoi_phe_duyet_tc_cap1_id?: string;
  nguoi_phe_duyet_tc_cap1?: { ho_ten: string } | null;
  ngay_phe_duyet_tc_cap1?: string | null;
  diem_tc_cap1?: number | null;  // ✅ v3.4: Điểm Phó duyệt
  nguoi_phe_duyet_tc_cap2_id?: string;
  nguoi_phe_duyet_tc_cap2?: { ho_ten: string } | null;
  ngay_phe_duyet_tc_cap2?: string | null;
  diem_tc_cap2?: number | null;  // ✅ v3.4: Điểm Trưởng duyệt
  diem_tieu_chi_chung?: number | null;  // ✅ v3.4: Điểm final
  // ⭐ v3.5: Từ chối tiêu chí
  ly_do_tu_choi_tc?: string | null;
  nguoi_tu_choi_tc?: { ho_ten: string } | null;
  ngay_tu_choi_tc?: string | null;
  cap_phe_duyet_hien_tai?: string | null;  // "cap1" | "cap2"
  // Thêm cho lịch sử
  trang_thai_tieu_chi?: string;
  // compat
  cong_chuc?: { ho_ten?: string; ma_cc?: string; don_vi_ten?: string };
  trang_thai_tc?: string;
  diem_tieu_chi_chung_val?: number;
}

interface ITieuChiChiTiet {
  id: string;
  danh_gia_thang_id?: string;
  tieu_chi_id: string;
  ma_tieu_chi: string;
  ten_tieu_chi: string;
  nhom_tieu_chi: number;
  diem_toi_da: number;
  gia_tri_mac_dinh?: boolean;
  is_achieved_cc?: boolean;
  is_achieved_ld?: boolean | null;
  is_achieved?: boolean;
  diem_tu_cham: number;
  diem_phe_duyet?: number | null;
  diem?: number;
  trang_thai?: string;
  ghi_chu_cc?: string | null;
  ghi_chu_ld?: string | null;
  ly_do_dieu_chinh?: string | null;
  ngay_gui?: string | null;
  ngay_phe_duyet?: string | null;
  has_difference?: boolean;
}

type StatusFilter = 'all' | 'pending' | 'approved' | 'rejected';
type ApprovalLevel = 'all' | 'cap1' | 'cap2' | 'thang';

// =============================================================================
// API FUNCTIONS - VERIFIED ENDPOINTS
// =============================================================================

const tieuChiApi = {
  /**
   * GET /danh-gia/tieu-chi/cho-phe-duyet
   */
  async getChoPheDuyet(params?: { thang?: number; nam?: number }): Promise<ITieuChiItem[]> {
    console.log('[TabTieuChi] Calling GET /danh-gia/tieu-chi/cho-phe-duyet');
    const response = await apiClient.get('/danh-gia/tieu-chi/cho-phe-duyet', { params });
    console.log('[TabTieuChi] Response cho-phe-duyet:', response.data);
    
    // Handle nhiều format response
    let data: ITieuChiItem[] = [];
    if (Array.isArray(response.data)) {
      data = response.data;
    } else if (response.data?.data?.danh_sach && Array.isArray(response.data.data.danh_sach)) {
      // Backend trả về format { data: { danh_sach: [...] } }
      data = response.data.data.danh_sach;
    } else if (response.data?.data && Array.isArray(response.data.data)) {
      data = response.data.data;
    } else if (response.data?.danh_sach && Array.isArray(response.data.danh_sach)) {
      data = response.data.danh_sach;
    } else if (response.data?.success && response.data?.data) {
      data = Array.isArray(response.data.data) ? response.data.data : [];
    }
    
    console.log('[TabTieuChi] Parsed pending data:', data.length, 'items');
    return data;
  },

  /**
   * GET /danh-gia/tieu-chi/lich-su
   * Lấy lịch sử phê duyệt tiêu chí (đã duyệt + từ chối)
   */
  async getLichSu(params?: { thang?: number; nam?: number; trang_thai?: string }): Promise<ITieuChiItem[]> {
    console.log('[TabTieuChi] Calling GET /danh-gia/tieu-chi/lich-su with params:', params);
    
    try {
      const response = await apiClient.get('/danh-gia/tieu-chi/lich-su', { params });
      console.log('[TabTieuChi] Response lich-su:', response.data);
      
      let data: ITieuChiItem[] = [];
      
      if (Array.isArray(response.data)) {
        data = response.data;
      } else if (response.data?.data?.items && Array.isArray(response.data.data.items)) {
        data = response.data.data.items;
      } else if (response.data?.data?.danh_sach && Array.isArray(response.data.data.danh_sach)) {
        // Backend trả về format { data: { danh_sach: [...] } }
        data = response.data.data.danh_sach;
      } else if (response.data?.data && Array.isArray(response.data.data)) {
        data = response.data.data;
      } else if (response.data?.items && Array.isArray(response.data.items)) {
        data = response.data.items;
      } else if (response.data?.danh_sach && Array.isArray(response.data.danh_sach)) {
        data = response.data.danh_sach;
      }
      
      console.log('[TabTieuChi] Parsed lich-su data:', data.length, 'items');
      return data.map(item => ({
        ...item,
        ho_ten: item.ho_ten || item.cong_chuc?.ho_ten || '',
        ma_cc: item.ma_cc || item.cong_chuc?.ma_cc || '',
        don_vi_ten: item.don_vi_ten || item.cong_chuc?.don_vi_ten || '',
        trang_thai: item.trang_thai || item.trang_thai_tc || '',
        diem_tu_cham: item.diem_tu_cham || item.diem_tieu_chi_chung || 0,
      }));
    } catch (error) {
      console.warn('[TabTieuChi] /danh-gia/tieu-chi/lich-su error:', error);
      return [];
    }
  },

  /**
   * GET /danh-gia/tieu-chi/{danh_gia_thang_id}/chi-tiet
   */
  /**
   * GET /danh-gia/tieu-chi/{danh_gia_thang_id}/chi-tiet
   * ✅ FIX: Trả về cả metadata (diem_tc_cap1, trang_thai_tc...) + tieu_chi list
   */
  async getChiTiet(danhGiaThangId: string): Promise<{ tieu_chi: ITieuChiChiTiet[]; metadata?: Partial<ITieuChiItem> }> {
    console.log('[TabTieuChi] Calling GET /danh-gia/tieu-chi/' + danhGiaThangId + '/chi-tiet');
    const response = await apiClient.get(`/danh-gia/tieu-chi/${danhGiaThangId}/chi-tiet`);
    console.log('[TabTieuChi] Response chi-tiet:', response.data);
    
    const rawData = response.data?.data || response.data;
    
    // Parse tieu_chi array
    let tieuChi: ITieuChiChiTiet[] = [];
    if (rawData?.tieu_chi && Array.isArray(rawData.tieu_chi)) {
      tieuChi = rawData.tieu_chi;
    } else if (Array.isArray(rawData)) {
      tieuChi = rawData;
    }
    
    // Parse metadata (diem_tc_cap1, diem_tc_cap2, trang_thai_tc, etc.)
    const metadata: Partial<ITieuChiItem> = {};
    if (rawData && typeof rawData === 'object' && !Array.isArray(rawData)) {
      if (rawData.diem_tc_cap1 !== undefined) metadata.diem_tc_cap1 = rawData.diem_tc_cap1;
      if (rawData.diem_tc_cap2 !== undefined) metadata.diem_tc_cap2 = rawData.diem_tc_cap2;
      if (rawData.diem_tieu_chi_chung !== undefined) metadata.diem_tieu_chi_chung = rawData.diem_tieu_chi_chung;
      if (rawData.trang_thai_tc) metadata.trang_thai_tc = rawData.trang_thai_tc;
      if (rawData.trang_thai) metadata.trang_thai = rawData.trang_thai;
      if (rawData.ngay_phe_duyet_tc_cap1) metadata.ngay_phe_duyet_tc_cap1 = rawData.ngay_phe_duyet_tc_cap1;
      if (rawData.ngay_phe_duyet_tc_cap2) metadata.ngay_phe_duyet_tc_cap2 = rawData.ngay_phe_duyet_tc_cap2;
      if (rawData.nguoi_phe_duyet_tc_cap1) metadata.nguoi_phe_duyet_tc_cap1 = rawData.nguoi_phe_duyet_tc_cap1;
      if (rawData.nguoi_phe_duyet_tc_cap2) metadata.nguoi_phe_duyet_tc_cap2 = rawData.nguoi_phe_duyet_tc_cap2;
      if (rawData.cap_phe_duyet_hien_tai) metadata.cap_phe_duyet_hien_tai = rawData.cap_phe_duyet_hien_tai;
      if (rawData.ly_do_tu_choi_tc) metadata.ly_do_tu_choi_tc = rawData.ly_do_tu_choi_tc;
      // Cong chuc info
      if (rawData.cong_chuc) {
        metadata.ho_ten = rawData.cong_chuc.ho_ten;
        metadata.ma_cc = rawData.cong_chuc.ma_cc;
        metadata.don_vi_ten = rawData.cong_chuc.don_vi_ten;
      }
      // Tong hop CC
      if (rawData.tong_hop_cc) {
        metadata.diem_tu_cham = rawData.tong_hop_cc.tong_diem;
      }
    }
    
    return { tieu_chi: tieuChi, metadata };
  },

  /**
   * POST /danh-gia/{danh_gia_thang_id}/phe-duyet-tieu-chi
   * ✅ FIX v3.4: Payload đúng backend PheDuyetTieuChiRequest
   */
  async pheDuyet(
    danhGiaThangId: string,
    payload: {
      ghi_chu?: string;
      dieu_chinh?: Array<{ 
        ma_tieu_chi: string;
        is_achieved_ld: boolean;
        ly_do_dieu_chinh?: string;
      }>;
    }
  ): Promise<void> {
    await apiClient.post(`/danh-gia/${danhGiaThangId}/phe-duyet-tieu-chi`, payload);
  },

  /**
   * POST /danh-gia/{danh_gia_thang_id}/tu-choi-tieu-chi
   * ✅ FIX v3.4: Tách endpoint từ chối riêng
   */
  async tuChoi(
    danhGiaThangId: string,
    lyDo: string
  ): Promise<void> {
    await apiClient.post(`/danh-gia/${danhGiaThangId}/tu-choi-tieu-chi`, {
      ly_do_tu_choi: lyDo,
    });
  },

  /**
   * POST /danh-gia/phe-duyet-tieu-chi-bulk
   */
  async pheDuyetBulk(payload: {
    danh_gia_thang_ids: string[];
    ghi_chu?: string;
  }): Promise<void> {
    await apiClient.post('/danh-gia/phe-duyet-tieu-chi-bulk', payload);
  },
};

// =============================================================================
// SUB COMPONENTS
// =============================================================================

interface TieuChiRowProps {
  item: ITieuChiItem;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  onViewDetail: (id: string) => void;
  canApprove: boolean;
  currentUserId?: string;
}

function TieuChiRow({ item, isSelected, onSelect, onApprove, onReject, onViewDetail, canApprove, currentUserId }: TieuChiRowProps) {
  // ⭐ v3.5: Detect status
  const trangThaiTC = item.trang_thai_tc || item.trang_thai_tieu_chi || item.trang_thai;
  const capHienTai = item.cap_phe_duyet_hien_tai;
  
  const isPending = trangThaiTC === 'CHO_PHE_DUYET' || 
    trangThaiTC === 'CHO_PHE_DUYET_TC' ||
    trangThaiTC === 'CHO_CAP2' ||
    (!trangThaiTC && !item.ngay_phe_duyet_tc_cap2);
  const isApproved = trangThaiTC === 'DA_PHE_DUYET';
  const isRejected = trangThaiTC === 'TU_CHOI';
  
  const isWaitingCap1 = capHienTai === 'cap1' || (isPending && !item.ngay_phe_duyet_tc_cap1);
  const isWaitingCap2 = capHienTai === 'cap2' || (isPending && !!item.ngay_phe_duyet_tc_cap1 && !item.ngay_phe_duyet_tc_cap2);
  const getCurrentLevel = (): number => isWaitingCap1 ? 1 : isWaitingCap2 ? 2 : 0;
  
  const canApproveCap1 = !!(currentUserId && 
    item.nguoi_phe_duyet_tc_cap1_id === currentUserId && 
    !item.ngay_phe_duyet_tc_cap1);
  
  const canApproveCap2 = !!(currentUserId && 
    item.nguoi_phe_duyet_tc_cap2_id === currentUserId && 
    item.ngay_phe_duyet_tc_cap1 && 
    !item.ngay_phe_duyet_tc_cap2);
  
  const userAlreadyApprovedCap1 = !!(currentUserId && 
    item.nguoi_phe_duyet_tc_cap1_id === currentUserId && 
    item.ngay_phe_duyet_tc_cap1);
  
  const canShowApproveButtons = canApprove && isPending && (canApproveCap1 || canApproveCap2);

  // ⭐ v3.6: Detect "gửi thẳng ĐT" = cap1 chưa duyệt + không có cap2
  const isDirectApproval = isPending && !item.ngay_phe_duyet_tc_cap1 && !item.nguoi_phe_duyet_tc_cap2_id;

  // Status badge
  const getStatusBadge = () => {
    if (isApproved) return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-700">Đã duyệt</span>;
    if (isRejected) return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-700">Từ chối</span>;
    if (trangThaiTC === 'NHAP' && item.ly_do_tu_choi_tc) return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-orange-100 text-orange-700">Cần chấm lại</span>;
    if (isPending) {
      if (isDirectApproval) {
        return (
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
            Chờ duyệt thẳng
          </span>
        );
      }
      if (getCurrentLevel() > 0) {
        return (
          <span className={`px-2 py-0.5 text-xs font-medium rounded-full
            ${getCurrentLevel() === 1 ? 'bg-amber-100 text-amber-700' : 'bg-purple-100 text-purple-700'}`}>
            Chờ cấp {getCurrentLevel()}
          </span>
        );
      }
    }
    return null;
  };

  // 2-tier progress inline (hoặc 1-step nếu gửi thẳng)
  const getProgressIndicator = () => {
    if (isDirectApproval) {
      // Gửi thẳng ĐT: chỉ 1 bước
      return (
        <div className="flex items-center gap-1.5 text-xs">
          <span className={`w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] font-bold
            ${isApproved ? 'bg-green-500' : 'bg-blue-400'}`}>✓</span>
          <span className="text-[10px] text-gray-500">Thẳng</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1.5 text-xs">
        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] font-bold
          ${item.ngay_phe_duyet_tc_cap1 ? 'bg-green-500' : 'bg-gray-300'}`}>1</span>
        <div className="w-6 h-0.5 bg-gray-200">
          <div className={`h-full ${item.ngay_phe_duyet_tc_cap1 ? 'bg-green-500 w-full' : 'w-0'}`} />
        </div>
        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] font-bold
          ${item.ngay_phe_duyet_tc_cap2 || isApproved ? 'bg-green-500' : 'bg-gray-300'}`}>2</span>
      </div>
    );
  };

  return (
    <tr className={`hover:bg-gray-50 transition-colors ${isSelected ? 'bg-blue-50' : ''}`}>
      {/* Checkbox */}
      {canApprove && (
        <td className="w-10 px-3 py-3 text-center">
          {canShowApproveButtons && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => onSelect(item.danh_gia_thang_id, e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
          )}
        </td>
      )}

      {/* Họ tên + mã CC */}
      <td className="px-3 py-3">
        <div>
          <p className="font-medium text-gray-900 text-sm">{item.ho_ten}</p>
          <p className="text-xs text-gray-500">{item.ma_cc}</p>
          {item.don_vi_ten && <p className="text-xs text-gray-400">{item.don_vi_ten}</p>}
        </div>
      </td>

      {/* Tháng/Năm */}
      <td className="px-3 py-3 text-center text-sm text-gray-600 whitespace-nowrap">
        {item.thang}/{item.nam}
      </td>

      {/* Điểm CC tự chấm */}
      <td className="px-3 py-3 text-center">
        <span className="text-blue-600 font-semibold">{item.diem_tu_cham}</span>
      </td>

      {/* Phó duyệt */}
      <td className="px-3 py-3 text-center">
        {item.diem_tc_cap1 != null 
          ? <span className="text-green-600 font-semibold">{item.diem_tc_cap1}</span>
          : <span className="text-gray-300">—</span>
        }
      </td>

      {/* Trưởng duyệt */}
      <td className="px-3 py-3 text-center">
        {item.diem_tc_cap2 != null 
          ? <span className="text-green-700 font-semibold">{item.diem_tc_cap2}</span>
          : <span className="text-gray-300">—</span>
        }
      </td>

      {/* Tiến trình 2 cấp */}
      <td className="px-3 py-3 text-center">
        {getProgressIndicator()}
      </td>

      {/* Trạng thái */}
      <td className="px-3 py-3 text-center">
        <div className="flex flex-col items-center gap-1">
          {getStatusBadge()}
          {userAlreadyApprovedCap1 && isWaitingCap2 && !isDirectApproval && (
            <span className="text-[10px] text-amber-600">Chờ ĐT duyệt cấp 2</span>
          )}
        </div>
      </td>

      {/* Lý do từ chối (nếu có) */}
      <td className="px-3 py-3 max-w-[200px]">
        {item.ly_do_tu_choi_tc ? (
          <div className="text-xs">
            <span className="text-red-600">{item.ly_do_tu_choi_tc}</span>
            {item.ngay_tu_choi_tc && (
              <p className="text-red-400 text-[10px]">
                {format(new Date(item.ngay_tu_choi_tc), 'dd/MM/yyyy')}
              </p>
            )}
          </div>
        ) : (
          <span className="text-gray-300 text-xs">—</span>
        )}
      </td>

      {/* Actions */}
      <td className="px-3 py-3">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onViewDetail(item.danh_gia_thang_id)}
            className="px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors border border-gray-200"
            title="Xem chi tiết"
          >
            Chi tiết
          </button>
          {canShowApproveButtons && (
            <>
              <button
                onClick={() => onApprove(item.danh_gia_thang_id)}
                className="px-2.5 py-1 text-xs font-medium text-white bg-green-600 hover:bg-green-700 rounded transition-colors"
              >
                Duyệt
              </button>
              <button
                onClick={() => onReject(item.danh_gia_thang_id)}
                className="px-2.5 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded transition-colors"
              >
                Từ chối
              </button>
            </>
          )}
        </div>
      </td>
    </tr>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TabTieuChi({ thang, nam, canApprove, onPendingCountChange }: ITabProps) {
  const [data, setData] = useState<ITieuChiItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [levelFilter, setLevelFilter] = useState<ApprovalLevel>('all');
  const [congChucFilter, setCongChucFilter] = useState<string>('all');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | undefined>(undefined);
  
  // Counts state
  const [counts, setCounts] = useState({ pending: 0, approved: 0, rejected: 0, total: 0 });
  
  // Modal state
  const [selectedItem, setSelectedItem] = useState<ITieuChiItem | null>(null);
  const [modalAction, setModalAction] = useState<'approve' | 'reject' | 'detail' | null>(null);
  const [lyDoTuChoi, setLyDoTuChoi] = useState('');
  const [ghiChuPheDuyet, setGhiChuPheDuyet] = useState('');
  const [chiTietData, setChiTietData] = useState<ITieuChiChiTiet[]>([]);
  // State cho điều chỉnh điểm khi phê duyệt
  const [dieuChinhDiem, setDieuChinhDiem] = useState<Record<string, boolean>>({});
  // ✅ v3.4: Lý do điều chỉnh per tiêu chí
  const [lyDoDieuChinhPerTC, setLyDoDieuChinhPerTC] = useState<Record<string, string>>({});

  // ✅ v3.4: Sort tiêu chí theo nhóm + mã (1.1, 1.2, 2.1, ..., 3.4)
  const sortTieuChi = (items: ITieuChiChiTiet[]): ITieuChiChiTiet[] => {
    return [...items].sort((a, b) => {
      if (a.nhom_tieu_chi !== b.nhom_tieu_chi) return a.nhom_tieu_chi - b.nhom_tieu_chi;
      // So sánh mã: "1.1" < "1.2" < "2.1" ...
      const [aMajor, aMinor] = a.ma_tieu_chi.split('.').map(Number);
      const [bMajor, bMinor] = b.ma_tieu_chi.split('.').map(Number);
      if (aMajor !== bMajor) return aMajor - bMajor;
      return (aMinor || 0) - (bMinor || 0);
    });
  };

  // Lấy currentUserId từ localStorage khi mount
  useEffect(() => {
    try {
      const authStr = localStorage.getItem('kpi-auth-storage');
      if (authStr) {
        const auth = JSON.parse(authStr);
        // Cấu trúc: { state: { user: { id: ..., cong_chuc_id: ... } } }
        const userId = auth?.state?.user?.id || auth?.state?.user?.cong_chuc_id || auth?.user?.id;
        console.log('[TabTieuChi] Current user ID:', userId);
        setCurrentUserId(userId);
      }
    } catch (e) {
      console.warn('[TabTieuChi] Cannot get user from localStorage:', e);
    }
  }, []);

  // ✅ FIX: Counts tính trực tiếp trong loadData, không cần loadCounts riêng

  // ✅ FIX: Load ALL data 1 lần, filter client-side thay vì gọi nhiều API
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Luôn load cả pending + lịch sử
      const [pending, lichSu] = await Promise.all([
        tieuChiApi.getChoPheDuyet({ thang, nam }),
        tieuChiApi.getLichSu({ thang, nam }),
      ]);
      
      // Deduplicate bằng danh_gia_thang_id
      const seen = new Set<string>();
      const allItems: ITieuChiItem[] = [];
      for (const item of [...pending, ...lichSu]) {
        if (!seen.has(item.danh_gia_thang_id)) {
          seen.add(item.danh_gia_thang_id);
          allItems.push(item);
        }
      }
      
      setData(allItems);
      
      // ✅ Tính counts từ dữ liệu đã load
      const pendingCount = allItems.filter(d => {
        const t = d.trang_thai_tc || d.trang_thai_tieu_chi || d.trang_thai;
        return t === 'CHO_PHE_DUYET' || t === 'CHO_PHE_DUYET_TC' || t === 'CHO_CAP2';
      }).length;
      const approvedCount = allItems.filter(d => {
        const t = d.trang_thai_tc || d.trang_thai_tieu_chi || d.trang_thai;
        return t === 'DA_PHE_DUYET';
      }).length;
      const rejectedCount = allItems.filter(d => {
        const t = d.trang_thai_tc || d.trang_thai_tieu_chi || d.trang_thai;
        return t === 'TU_CHOI';
      }).length;
      
      setCounts({ pending: pendingCount, approved: approvedCount, rejected: rejectedCount, total: allItems.length });
      if (onPendingCountChange) onPendingCountChange(pendingCount);
      
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Có lỗi xảy ra khi tải dữ liệu');
      setData([]);
    } finally {
      setIsLoading(false);
    }
  }, [thang, nam, onPendingCountChange]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Refresh data
  const refreshAll = useCallback(async () => {
    await loadData();
  }, [loadData]);

  // Handlers
  const handleSelect = (id: string, selected: boolean) => {
    const newSelected = new Set(selectedIds);
    selected ? newSelected.add(id) : newSelected.delete(id);
    setSelectedIds(newSelected);
  };

  const handleSelectAll = () => {
    setSelectedIds(selectedIds.size === finalFilteredData.length ? new Set() : new Set(finalFilteredData.map(d => d.danh_gia_thang_id)));
  };

  const handleViewDetail = async (id: string) => {
    const item = data.find(d => d.danh_gia_thang_id === id);
    if (item) {
      setSelectedItem(item);
      setModalAction('detail');
      try {
        const { tieu_chi: chiTiet, metadata } = await tieuChiApi.getChiTiet(id);
        setChiTietData(sortTieuChi(chiTiet));
        // ✅ FIX: Update selectedItem với metadata mới nhất từ backend
        if (metadata && Object.keys(metadata).length > 0) {
          setSelectedItem(prev => prev ? { ...prev, ...metadata } : prev);
        }
      } catch {
        setChiTietData([]);
      }
    }
  };

  const handleApprove = async (id: string) => {
    const item = data.find(d => d.danh_gia_thang_id === id);
    if (item) {
      setSelectedItem(item);
      setModalAction('approve');
      setGhiChuPheDuyet('');
      setLyDoDieuChinhPerTC({});
      try {
        const { tieu_chi: chiTiet, metadata } = await tieuChiApi.getChiTiet(id);
        setChiTietData(sortTieuChi(chiTiet));
        // ✅ FIX: Update selectedItem với metadata mới nhất
        if (metadata && Object.keys(metadata).length > 0) {
          setSelectedItem(prev => prev ? { ...prev, ...metadata } : prev);
        }
        // Init dieuChinhDiem - ✅ FIX: Khi cấp 2 duyệt, init từ is_achieved_ld (kết quả cấp 1)
        const initDiem: Record<string, boolean> = {};
        chiTiet.forEach(tc => {
          // Nếu đã có is_achieved_ld (cấp 1 đã duyệt), dùng giá trị đó
          initDiem[tc.ma_tieu_chi] = tc.is_achieved_ld !== null && tc.is_achieved_ld !== undefined
            ? tc.is_achieved_ld
            : (tc.is_achieved_cc ?? tc.is_achieved ?? false);
        });
        setDieuChinhDiem(initDiem);
      } catch {
        setChiTietData([]);
        setDieuChinhDiem({});
      }
    }
  };

  const handleReject = (id: string) => {
    const item = data.find(d => d.danh_gia_thang_id === id);
    if (item) {
      setSelectedItem(item);
      setModalAction('reject');
      setLyDoTuChoi('');
    }
  };

  const handleModalSubmit = async () => {
    if (!selectedItem) return;
    if (modalAction === 'reject' && !lyDoTuChoi.trim()) {
      alert('Vui lòng nhập lý do từ chối');
      return;
    }

    setIsProcessing(true);
    try {
      if (modalAction === 'approve') {
        // ✅ v3.4: Build dieu_chinh đúng backend PheDuyetTieuChiRequest
        // Chỉ gửi các tiêu chí mà LĐ thay đổi so với CC
        const dieuChinh = chiTietData
          .filter(tc => {
            const originalValue = tc.is_achieved_cc ?? tc.is_achieved ?? false;
            const newValue = dieuChinhDiem[tc.ma_tieu_chi] ?? originalValue;
            return originalValue !== newValue;
          })
          .map(tc => ({
            ma_tieu_chi: tc.ma_tieu_chi,
            is_achieved_ld: dieuChinhDiem[tc.ma_tieu_chi] ?? false,
            ly_do_dieu_chinh: lyDoDieuChinhPerTC[tc.ma_tieu_chi] || undefined,
          }));

        // ✅ v3.4: Validate - mỗi TC thay đổi phải có lý do
        const missingLyDo = dieuChinh.filter(dc => !dc.ly_do_dieu_chinh);
        if (missingLyDo.length > 0) {
          alert(`Vui lòng nhập lý do điều chỉnh cho: ${missingLyDo.map(d => d.ma_tieu_chi).join(', ')}`);
          setIsProcessing(false);
          return;
        }

        await tieuChiApi.pheDuyet(selectedItem.danh_gia_thang_id, {
          ghi_chu: ghiChuPheDuyet || undefined,
          dieu_chinh: dieuChinh.length > 0 ? dieuChinh : undefined,
        });
      } else if (modalAction === 'reject') {
        // ✅ v3.4: Gọi endpoint từ chối riêng
        await tieuChiApi.tuChoi(selectedItem.danh_gia_thang_id, lyDoTuChoi);
      }

      await refreshAll();
      setSelectedItem(null);
      setModalAction(null);
      setChiTietData([]);
      setDieuChinhDiem({});
      setLyDoDieuChinhPerTC({});
    } catch (err) {
      // ⭐ v3.5: Better error message from backend response
      const error = err as Error & { response?: { data?: { detail?: string; message?: string } } };
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || 'Có lỗi xảy ra';
      alert(errorMsg);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) return;
    if (!window.confirm(`Phê duyệt ${selectedIds.size} đánh giá đã chọn?`)) return;

    setIsProcessing(true);
    try {
      await tieuChiApi.pheDuyetBulk({ danh_gia_thang_ids: Array.from(selectedIds) });
      await refreshAll();
      setSelectedIds(new Set());
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  // Filter data theo levelFilter và currentUserId
  // Phó ĐT chỉ thấy items chờ cấp 1 (chưa duyệt)
  // ĐT thấy items chờ cấp 2 (đã qua cấp 1)
  const canUserApproveItem = (item: ITieuChiItem): boolean => {
    // ⭐ v3.5: Dùng trang_thai_tc nếu có
    const trangThaiTC = item.trang_thai_tc || item.trang_thai_tieu_chi || item.trang_thai;
    const isPending = trangThaiTC === 'CHO_PHE_DUYET_TC' || 
      trangThaiTC === 'CHO_PHE_DUYET' ||
      trangThaiTC === 'CHO_CAP2' ||
      (!trangThaiTC && !item.ngay_phe_duyet_tc_cap2);
    if (!isPending) return false;
    
    const canApproveCap1 = !!(currentUserId && 
      item.nguoi_phe_duyet_tc_cap1_id === currentUserId && 
      !item.ngay_phe_duyet_tc_cap1);
      
    console.log('canApproveCap1:', canApproveCap1);
    
    const canApproveCap2 = !!(currentUserId && 
      item.nguoi_phe_duyet_tc_cap2_id === currentUserId && 
      item.ngay_phe_duyet_tc_cap1 && 
      !item.ngay_phe_duyet_tc_cap2);
    
    return canApproveCap1 || canApproveCap2;
  };

  const pendingItems = data.filter(d => {
    const trangThaiTC = d.trang_thai_tc || d.trang_thai_tieu_chi || d.trang_thai;
    const isPending = trangThaiTC === 'CHO_PHE_DUYET_TC' || 
      trangThaiTC === 'CHO_PHE_DUYET' ||
      trangThaiTC === 'CHO_CAP2' ||
      (!trangThaiTC && !d.ngay_phe_duyet_tc_cap2);
    return isPending;
  });
  
  // Items mà user hiện tại có thể duyệt (chưa duyệt)
  const approvableItems = pendingItems.filter(canUserApproveItem);
  
  // Items mà user đã duyệt (cấp 1 hoặc cấp 2)
  const userApprovedItems = data.filter(item => {
    const approvedCap1 = !!(currentUserId && item.nguoi_phe_duyet_tc_cap1_id === currentUserId && item.ngay_phe_duyet_tc_cap1);
    const approvedCap2 = !!(currentUserId && item.nguoi_phe_duyet_tc_cap2_id === currentUserId && item.ngay_phe_duyet_tc_cap2);
    return approvedCap1 || approvedCap2;
  });
  
  const filteredData = data.filter(item => {
    const trangThaiTC = item.trang_thai_tc || item.trang_thai_tieu_chi || item.trang_thai;
    const isPending = trangThaiTC === 'CHO_PHE_DUYET_TC' || 
      trangThaiTC === 'CHO_PHE_DUYET' ||
      trangThaiTC === 'CHO_CAP2' ||
      (!trangThaiTC && !item.ngay_phe_duyet_tc_cap2);
    const isFullyApproved = trangThaiTC === 'DA_PHE_DUYET';
    const isRejected = trangThaiTC === 'TU_CHOI';
    
    // User đã duyệt item này chưa? (cấp 1 hoặc cấp 2)
    const userApprovedCap1 = !!(currentUserId && item.nguoi_phe_duyet_tc_cap1_id === currentUserId && item.ngay_phe_duyet_tc_cap1);
    const userApprovedCap2 = !!(currentUserId && item.nguoi_phe_duyet_tc_cap2_id === currentUserId && item.ngay_phe_duyet_tc_cap2);
    const userApprovedThis = userApprovedCap1 || userApprovedCap2;
    
    // Status filter
    if (statusFilter === 'pending') {
      return canUserApproveItem(item);
    }
    if (statusFilter === 'approved') {
      // ✅ FIX: "Đã duyệt" = items mà user đã duyệt (cấp 1 hoặc 2) HOẶC DA_PHE_DUYET
      return userApprovedThis || isFullyApproved;
    }
    if (statusFilter === 'rejected') {
      return isRejected;
    }
    
    // Tab "all" - hiện items liên quan đến user
    if (isPending && !canUserApproveItem(item) && !userApprovedThis) {
      return false;
    }
    
    return true;
  });

  // ✅ FIX: Phân loại cấp duyệt đúng
  // - Cấp 1: Phó ĐT duyệt CC (có nguoi_phe_duyet_tc_cap1_id, chưa duyệt cap1)
  // - Cấp 2: ĐT duyệt sau Phó (đã qua cap1, chưa duyệt cap2)  
  // - Duyệt thẳng: CC gửi thẳng ĐT (nguoi_phe_duyet_tc_cap2_id = currentUser, KHÔNG có cap1)
  const cap1Count = approvableItems.filter(d => {
    return d.nguoi_phe_duyet_tc_cap1_id === currentUserId && !d.ngay_phe_duyet_tc_cap1;
  }).length;
  
  const cap2Count = approvableItems.filter(d => {
    return !!d.ngay_phe_duyet_tc_cap1 && d.nguoi_phe_duyet_tc_cap2_id === currentUserId && !d.ngay_phe_duyet_tc_cap2;
  }).length;
  
  const thangCount = approvableItems.filter(d => {
    // Duyệt thẳng: user là cap2 approver, KHÔNG có cap1 (hoặc cap1 = cap2 = cùng người)
    return !d.ngay_phe_duyet_tc_cap1 && 
           d.nguoi_phe_duyet_tc_cap2_id === currentUserId && 
           d.nguoi_phe_duyet_tc_cap1_id !== currentUserId;
  }).length;

  // ✅ Danh sách công chức unique để filter
  const uniqueCongChuc = React.useMemo(() => {
    const map = new Map<string, { id: string; ho_ten: string; ma_cc: string }>();
    data.forEach(item => {
      const id = item.cong_chuc_id || item.cong_chuc?.ho_ten || item.ho_ten;
      if (id && !map.has(id)) {
        map.set(id, {
          id,
          ho_ten: item.ho_ten || item.cong_chuc?.ho_ten || '',
          ma_cc: item.ma_cc || item.cong_chuc?.ma_cc || '',
        });
      }
    });
    return Array.from(map.values()).sort((a, b) => a.ho_ten.localeCompare(b.ho_ten, 'vi'));
  }, [data]);

  // Apply congChucFilter + levelFilter vào filteredData
  const finalFilteredData = React.useMemo(() => {
    let result = filteredData;
    
    // ✅ FIX: Apply levelFilter
    if (levelFilter !== 'all') {
      result = result.filter(item => {
        const isWaitCap1 = !item.ngay_phe_duyet_tc_cap1 && item.nguoi_phe_duyet_tc_cap1_id === currentUserId;
        const isWaitCap2 = !!item.ngay_phe_duyet_tc_cap1 && !item.ngay_phe_duyet_tc_cap2 && item.nguoi_phe_duyet_tc_cap2_id === currentUserId;
        const isDuyetThang = !item.ngay_phe_duyet_tc_cap1 && 
                             item.nguoi_phe_duyet_tc_cap2_id === currentUserId && 
                             item.nguoi_phe_duyet_tc_cap1_id !== currentUserId;
        
        if (levelFilter === 'cap1') return isWaitCap1;
        if (levelFilter === 'cap2') return isWaitCap2 || isDuyetThang; // Duyệt thẳng gộp vào cấp 2
        if (levelFilter === 'thang') return isDuyetThang;
        return true;
      });
    }
    
    // Apply congChucFilter
    if (congChucFilter !== 'all') {
      result = result.filter(item => {
        const itemCCId = item.cong_chuc_id || item.cong_chuc?.ho_ten || item.ho_ten;
        return itemCCId === congChucFilter;
      });
    }
    
    return result;
  }, [filteredData, congChucFilter, levelFilter, currentUserId]);

  // Render
  if (isLoading) {
    return <div className="flex items-center justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadData} />;
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white rounded-lg p-4 border border-gray-200">
        <div className="flex items-center gap-4">
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Trạng thái:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả ({approvableItems.length + userApprovedItems.length})</option>
              <option value="pending">Chờ duyệt ({approvableItems.length})</option>
              <option value="approved">Đã duyệt ({userApprovedItems.length})</option>
              <option value="rejected">Từ chối ({counts.rejected})</option>
            </select>
          </div>

          {/* Level Filter - chỉ hiện khi xem pending */}
          {(statusFilter === 'pending' || statusFilter === 'all') && approvableItems.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Cấp duyệt:</span>
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value as ApprovalLevel)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Tất cả</option>
                {cap1Count > 0 && <option value="cap1">Cấp 1 ({cap1Count})</option>}
                <option value="cap2">Cấp 2 ({cap2Count + thangCount})</option>
              </select>
            </div>
          )}

          {/* ✅ Công chức Filter */}
          {uniqueCongChuc.length > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Công chức:</span>
              <select
                value={congChucFilter}
                onChange={(e) => setCongChucFilter(e.target.value)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 max-w-[220px]"
              >
                <option value="all">Tất cả ({uniqueCongChuc.length})</option>
                {uniqueCongChuc.map(cc => (
                  <option key={cc.id} value={cc.id}>
                    {cc.ho_ten} {cc.ma_cc ? `(${cc.ma_cc})` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {canApprove && approvableItems.length > 0 && statusFilter !== 'approved' && statusFilter !== 'rejected' && (
          <div className="flex items-center gap-3">
            <button
              onClick={handleSelectAll}
              className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {selectedIds.size === approvableItems.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
            </button>
            {selectedIds.size > 0 && (
              <button
                onClick={handleBulkApprove}
                disabled={isProcessing}
                className="px-4 py-1.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50"
              >
                {isProcessing ? 'Đang xử lý...' : `Duyệt ${selectedIds.size} đã chọn`}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {canApprove && (
                  <th className="w-10 px-3 py-3">
                    {finalFilteredData.some(d => {
                      const t = d.trang_thai_tc || d.trang_thai_tieu_chi || d.trang_thai;
                      return t === 'CHO_PHE_DUYET' || t === 'CHO_PHE_DUYET_TC' || t === 'CHO_CAP2';
                    }) && (
                      <input
                        type="checkbox"
                        checked={selectedIds.size > 0 && selectedIds.size === finalFilteredData.length}
                        onChange={handleSelectAll}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded"
                        title="Chọn tất cả"
                      />
                    )}
                  </th>
                )}
                <th className="px-3 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Công chức</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider w-20">Tháng</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider w-20">CC chấm</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider w-20">Phó duyệt</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider w-24">Trưởng duyệt</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider w-24">Tiến trình</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider w-24">Trạng thái</th>
                <th className="px-3 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider w-40">Ghi chú</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider w-40">Thao tác</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {finalFilteredData.length === 0 ? (
                <tr>
                  <td colSpan={canApprove ? 10 : 9} className="px-4 py-8 text-center text-gray-500 italic">
                    {statusFilter === 'pending' ? 'Không có đánh giá tiêu chí nào chờ phê duyệt' : congChucFilter !== 'all' ? 'Không có dữ liệu cho công chức đã chọn' : 'Không có dữ liệu'}
                  </td>
                </tr>
              ) : (
                finalFilteredData.map((item) => (
                  <TieuChiRow
                    key={item.danh_gia_thang_id}
                    item={item}
                    isSelected={selectedIds.has(item.danh_gia_thang_id)}
                    onSelect={handleSelect}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    onViewDetail={handleViewDetail}
                    canApprove={canApprove}
                    currentUserId={currentUserId}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedItem && modalAction === 'detail' && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Chi tiết tiêu chí chung</h3>
              <button onClick={() => { setSelectedItem(null); setModalAction(null); }} className="p-1 text-gray-400 hover:text-gray-600">✕</button>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="font-medium text-gray-900">{selectedItem.ho_ten}</p>
              <p className="text-sm text-gray-600 mt-1">{selectedItem.ma_cc} • {selectedItem.don_vi_ten}</p>
              <div className="flex flex-wrap gap-3 mt-2 text-sm">
                <span className="text-gray-500">Tháng {selectedItem.thang}/{selectedItem.nam}</span>
                <span className="text-blue-600 font-medium">CC tự chấm: {selectedItem.diem_tu_cham}</span>
                {/* ✅ FIX: Tính Phó duyệt từ chi tiết */}
                {chiTietData.some(tc => tc.is_achieved_ld !== null && tc.is_achieved_ld !== undefined) && (
                  <span className="text-green-600 font-medium">Phó duyệt: {
                    chiTietData.reduce((s, tc) => {
                      if (tc.is_achieved_ld === null || tc.is_achieved_ld === undefined) return s;
                      return s + (tc.is_achieved_ld ? tc.diem_toi_da : 0);
                    }, 0)
                  }</span>
                )}
                {selectedItem.diem_tc_cap2 != null && (
                  <span className="text-green-700 font-medium">Trưởng duyệt: {selectedItem.diem_tc_cap2}</span>
                )}
              </div>
            </div>

            {chiTietData.length > 0 ? (
              <table className="w-full text-sm">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-gray-700">Mã</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-700">Tiêu chí</th>
                    <th className="px-3 py-2 text-center font-medium text-gray-700">Tối đa</th>
                    <th className="px-3 py-2 text-center font-medium text-gray-700">CC tự chấm</th>
                    <th className="px-3 py-2 text-center font-medium text-gray-700">Phó duyệt</th>
                    <th className="px-3 py-2 text-center font-medium text-gray-700">Trưởng duyệt</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {chiTietData.map((tc) => {
                    // ✅ v3.4: Điểm CC = diem_toi_da nếu is_achieved_cc, ngược lại 0
                    const diemCC = (tc.is_achieved_cc ?? false) ? tc.diem_toi_da : 0;
                    // Điểm Phó duyệt (cấp 1) - nếu đã duyệt
                    const diemPho = tc.is_achieved_ld !== null && tc.is_achieved_ld !== undefined
                      ? (tc.is_achieved_ld ? tc.diem_toi_da : 0)
                      : null;
                    // Điểm Trưởng duyệt (cấp 2) = diem_phe_duyet (final)
                    const diemTruong = tc.diem_phe_duyet;
                    const hasChange = tc.has_difference || (tc.is_achieved_ld !== null && tc.is_achieved_cc !== tc.is_achieved_ld);
                    return (
                      <tr key={tc.id} className={`hover:bg-gray-50 ${hasChange ? 'bg-yellow-50' : ''}`}>
                        <td className="px-3 py-2 text-gray-500 font-mono text-xs">{tc.ma_tieu_chi}</td>
                        <td className="px-3 py-2 text-gray-900 text-xs">{tc.ten_tieu_chi}</td>
                        <td className="px-3 py-2 text-center text-gray-600">{tc.diem_toi_da}</td>
                        <td className="px-3 py-2 text-center">
                          <span className={`font-medium ${diemCC > 0 ? 'text-blue-600' : 'text-gray-400'}`}>{diemCC}</span>
                        </td>
                        <td className="px-3 py-2 text-center">
                          {diemPho !== null ? (
                            <span className={`font-medium ${diemPho > 0 ? 'text-green-600' : 'text-red-500'}`}>{diemPho}</span>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-center">
                          {diemTruong !== null && diemTruong !== undefined ? (
                            <span className={`font-medium ${diemTruong > 0 ? 'text-green-600' : 'text-red-500'}`}>{diemTruong}</span>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot className="bg-gray-50 font-bold">
                  <tr>
                    <td colSpan={3} className="px-3 py-2 text-right text-gray-700">Tổng:</td>
                    <td className="px-3 py-2 text-center text-blue-600">
                      {chiTietData.reduce((s, tc) => s + ((tc.is_achieved_cc ?? false) ? tc.diem_toi_da : 0), 0)}
                    </td>
                    <td className="px-3 py-2 text-center text-green-600">
                      {/* ✅ FIX: Tính tổng Phó duyệt từ is_achieved_ld (không dùng diem_tc_cap1 có thể sai) */}
                      {chiTietData.some(tc => tc.is_achieved_ld !== null && tc.is_achieved_ld !== undefined)
                        ? chiTietData.reduce((s, tc) => {
                            if (tc.is_achieved_ld === null || tc.is_achieved_ld === undefined) return s;
                            return s + (tc.is_achieved_ld ? tc.diem_toi_da : 0);
                          }, 0)
                        : '-'
                      }
                    </td>
                    <td className="px-3 py-2 text-center text-green-600">
                      {/* ✅ FIX: Tính tổng Trưởng duyệt từ diem_phe_duyet (khi đã duyệt cấp 2) */}
                      {chiTietData.some(tc => tc.diem_phe_duyet !== null && tc.diem_phe_duyet !== undefined && tc.trang_thai === 'DA_PHE_DUYET')
                        ? chiTietData.reduce((s, tc) => s + (tc.diem_phe_duyet ?? 0), 0)
                        : '-'
                      }
                    </td>
                  </tr>
                </tfoot>
              </table>
            ) : (
              <p className="text-gray-500 text-center py-4">Không có dữ liệu chi tiết</p>
            )}

            <div className="flex justify-end mt-4">
              <button onClick={() => { setSelectedItem(null); setModalAction(null); }} className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg">Đóng</button>
            </div>
          </div>
        </div>
      )}

      {/* Approve/Reject Modal */}
      {selectedItem && (modalAction === 'approve' || modalAction === 'reject') && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {modalAction === 'approve' ? 'Phê duyệt tiêu chí' : 'Từ chối tiêu chí'}
            </h3>

            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="font-medium text-gray-900">{selectedItem.ho_ten}</p>
              <p className="text-sm text-gray-600 mt-1">{selectedItem.ma_cc} • {selectedItem.don_vi_ten}</p>
              <div className="flex flex-wrap gap-3 mt-2 text-sm">
                <span className="text-gray-500">Tháng {selectedItem.thang}/{selectedItem.nam}</span>
                <span className="text-blue-600 font-medium">CC tự chấm: {selectedItem.diem_tu_cham}</span>
                {/* ✅ FIX: Tính Phó duyệt từ chi tiết */}
                {chiTietData.some(tc => tc.is_achieved_ld !== null && tc.is_achieved_ld !== undefined) && (
                  <span className="text-green-600 font-medium">Phó duyệt: {
                    chiTietData.reduce((s, tc) => {
                      if (tc.is_achieved_ld === null || tc.is_achieved_ld === undefined) return s;
                      return s + (tc.is_achieved_ld ? tc.diem_toi_da : 0);
                    }, 0)
                  }</span>
                )}
              </div>
            </div>

            {modalAction === 'approve' ? (
              <>
                {/* Bảng điều chỉnh điểm */}
                {chiTietData.length > 0 && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Điều chỉnh tiêu chí (bỏ tick = không đạt, tick = đạt)
                    </label>
                    <div className="border rounded-lg overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-100">
                          <tr>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 w-16">Mã</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700">Tiêu chí</th>
                            <th className="px-3 py-2 text-center font-medium text-gray-700 w-16">Tối đa</th>
                            <th className="px-3 py-2 text-center font-medium text-gray-700 w-20">CC chấm</th>
                            <th className="px-3 py-2 text-center font-medium text-gray-700 w-20">LĐ duyệt</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 w-48">Lý do điều chỉnh</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {(() => {
                            let lastNhom = 0;
                            const nhomNames: Record<number, string> = {
                              1: 'Nhóm I: Phẩm chất chính trị, đạo đức, kỷ luật',
                              2: 'Nhóm II: Năng lực chuyên môn, nghiệp vụ',
                              3: 'Nhóm III: Năng lực đổi mới, sáng tạo',
                            };
                            return chiTietData.map((tc) => {
                              const isAchieved = dieuChinhDiem[tc.ma_tieu_chi] ?? tc.is_achieved_cc ?? false;
                              const diemCC = (tc.is_achieved_cc ?? false) ? tc.diem_toi_da : 0;
                              const diemLD = isAchieved ? tc.diem_toi_da : 0;
                              const hasChange = (tc.is_achieved_cc ?? false) !== isAchieved;
                              const showNhomHeader = tc.nhom_tieu_chi !== lastNhom;
                              lastNhom = tc.nhom_tieu_chi;
                              return (
                                <React.Fragment key={tc.id}>
                                  {showNhomHeader && (
                                    <tr className="bg-blue-50">
                                      <td colSpan={6} className="px-3 py-1.5 text-xs font-semibold text-blue-700">
                                        {nhomNames[tc.nhom_tieu_chi] || `Nhóm ${tc.nhom_tieu_chi}`}
                                      </td>
                                    </tr>
                                  )}
                                  <tr className={`hover:bg-gray-50 ${hasChange ? 'bg-yellow-50' : ''}`}>
                                    <td className="px-3 py-2 text-gray-500 font-mono text-xs">{tc.ma_tieu_chi}</td>
                                    <td className="px-3 py-2 text-gray-900 text-xs">{tc.ten_tieu_chi}</td>
                                    <td className="px-3 py-2 text-center text-gray-600">{tc.diem_toi_da}</td>
                                    <td className="px-3 py-2 text-center">
                                      <span className={`font-medium ${diemCC > 0 ? 'text-blue-600' : 'text-gray-400'}`}>
                                        {diemCC}
                                      </span>
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                      <label className="inline-flex items-center gap-1.5 cursor-pointer">
                                        <input
                                          type="checkbox"
                                          checked={isAchieved}
                                          onChange={(e) => {
                                            setDieuChinhDiem(prev => ({
                                              ...prev,
                                              [tc.ma_tieu_chi]: e.target.checked
                                            }));
                                            // Nếu quay về giá trị CC thì xóa lý do
                                            if (e.target.checked === (tc.is_achieved_cc ?? false)) {
                                              setLyDoDieuChinhPerTC(prev => {
                                                const next = { ...prev };
                                                delete next[tc.ma_tieu_chi];
                                                return next;
                                              });
                                            }
                                          }}
                                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                        />
                                        <span className={`font-medium ${isAchieved ? 'text-green-600' : 'text-gray-400'}`}>
                                          {diemLD}
                                        </span>
                                      </label>
                                    </td>
                                    <td className="px-3 py-2">
                                      {hasChange ? (
                                        <input
                                          type="text"
                                          value={lyDoDieuChinhPerTC[tc.ma_tieu_chi] || ''}
                                          onChange={(e) => setLyDoDieuChinhPerTC(prev => ({
                                            ...prev,
                                            [tc.ma_tieu_chi]: e.target.value
                                          }))}
                                          placeholder="Bắt buộc nhập lý do *"
                                          className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 ${
                                            !lyDoDieuChinhPerTC[tc.ma_tieu_chi] ? 'border-red-300 bg-red-50' : 'border-gray-300'
                                          }`}
                                        />
                                      ) : (
                                        <span className="text-gray-300 text-xs">—</span>
                                      )}
                                    </td>
                                  </tr>
                                </React.Fragment>
                              );
                            });
                          })()}
                        </tbody>
                        <tfoot className="bg-gray-50">
                          <tr>
                            <td colSpan={3} className="px-3 py-2 text-right font-medium text-gray-700">Tổng điểm:</td>
                            <td className="px-3 py-2 text-center font-bold text-blue-600">
                              {chiTietData.reduce((sum, tc) => sum + ((tc.is_achieved_cc ?? false) ? tc.diem_toi_da : 0), 0)}
                            </td>
                            <td className="px-3 py-2 text-center font-bold text-green-600">
                              {chiTietData.reduce((sum, tc) => {
                                const isAchieved = dieuChinhDiem[tc.ma_tieu_chi] ?? tc.is_achieved_cc ?? false;
                                return sum + (isAchieved ? tc.diem_toi_da : 0);
                              }, 0)}
                            </td>
                            <td></td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      * Dòng vàng = tiêu chí đã điều chỉnh. Phải nhập lý do cho mỗi điều chỉnh.
                    </p>
                  </div>
                )}

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ghi chú (không bắt buộc)</label>
                  <textarea
                    value={ghiChuPheDuyet}
                    onChange={(e) => setGhiChuPheDuyet(e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập ghi chú..."
                  />
                </div>
              </>
            ) : (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Lý do từ chối <span className="text-red-500">*</span></label>
                <textarea
                  value={lyDoTuChoi}
                  onChange={(e) => setLyDoTuChoi(e.target.value)}
                  rows={3}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Nhập lý do từ chối..."
                />
              </div>
            )}

            <div className="flex justify-end gap-3">
              <button 
                onClick={() => { setSelectedItem(null); setModalAction(null); setChiTietData([]); setDieuChinhDiem({}); setLyDoDieuChinhPerTC({}); }} 
                disabled={isProcessing} 
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
              >
                Hủy
              </button>
              <button
                onClick={handleModalSubmit}
                disabled={isProcessing}
                className={`px-4 py-2 text-white rounded-lg transition-colors disabled:opacity-50 ${modalAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
              >
                {isProcessing ? 'Đang xử lý...' : modalAction === 'approve' ? 'Phê duyệt' : 'Từ chối'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
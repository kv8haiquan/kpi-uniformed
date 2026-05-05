/**
 * src/components/xep-loai/tabs/TabCongViec.tsx
 * =============================================
 * Tab "Duyệt công việc" - Phê duyệt kê khai công việc của CC và Lãnh đạo.
 * 
 * ✅ VERIFIED API ENDPOINTS (31/01/2026):
 * ┌────────┬──────────────────────────────────────┬─────────────────────────────────┐
 * │ Method │ Endpoint                             │ Mô tả                           │
 * ├────────┼──────────────────────────────────────┼─────────────────────────────────┤
 * │ GET    │ /phe-duyet/pending                   │ Lấy DS kê khai CC chờ duyệt     │
 * │ GET    │ /phe-duyet/lich-su                   │ Lấy DS CC đã duyệt/từ chối      │
 * │ POST   │ /phe-duyet/{ke_khai_id}              │ Phê duyệt/từ chối 1 kê khai CC  │
 * │ POST   │ /phe-duyet/xu-ly                     │ Phê duyệt CC hàng loạt          │
 * ├────────┼──────────────────────────────────────┼─────────────────────────────────┤
 * │ GET    │ /ke-khai-lanh-dao/cho-phe-duyet      │ Lấy DS kê khai LĐ chờ duyệt     │
 * │ GET    │ /ke-khai-lanh-dao/lich-su            │ Lấy DS LĐ đã duyệt/từ chối      │
 * │ POST   │ /ke-khai-lanh-dao/{id}/phe-duyet     │ Phê duyệt/từ chối kê khai LĐ    │
 * └────────┴──────────────────────────────────────┴─────────────────────────────────┘
 * 
 * Version: 3.9.0 - FIX PHE DUYET BUGS (01/02/2026)
 * - FIX BUG: Bulk LD approve hardcode so_loi=0 → bỏ qua tu_danh_gia
 *   → Giờ dùng saved edits nếu có, hoặc undefined → backend fallback tu_danh_gia
 * - FIX BUG: cap_do_ma (mức độ) inline edit không được gửi khi phê duyệt
 *   → Giờ gửi cap_do_ma trong payload cả đơn lẻ và bulk
 * - FIX: Bulk CC approve không gửi so_loi → backend Optional[int]=None → fallback tu_danh_gia
 * - FIX: Cập nhật text cảnh báo bulk approve cho chính xác
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { format, parseISO } from 'date-fns';
import apiClient from '@/lib/axios';
import { ITabProps } from '@/types/xep-loai';
import {
  LoadingSpinner,
  EmptyState,
  ErrorMessage,
} from '../shared';

// =============================================================================
// TYPES
// =============================================================================

interface ICongChuc {
  id: string;
  ma_cc: string;
  ho_ten: string;
  chuc_vu?: string;
  don_vi_ten?: string;
  // Phase 3 (29/04/2026): phân biệt HĐ 111 vs LĐ thật trong tab phê duyệt
  is_hd_111?: boolean;
  is_lanh_dao?: boolean;
}

interface IKeKhai {
  id: string;
  cong_chuc_id: string;
  cong_chuc?: ICongChuc;
  ma_cc?: string;
  ho_ten?: string;
  chuc_vu?: string;
  danh_muc_id?: string;
  danh_muc_ten?: string;
  ten_cong_viec?: string;
  mo_ta_cong_viec?: string;
  mo_ta?: string;  // Lãnh đạo dùng field này
  so_luong: number;
  so_sp_goc_quy_doi?: number;
  cap_do_ma?: string;
  ngay_thuc_hien?: string;
  trang_thai: string;
  ket_qua?: string;
  tu_danh_gia_chat_luong?: number;
  tu_danh_gia_tien_do?: number;
  so_loi_chat_luong?: number;  // Lãnh đạo
  so_loi_tien_do?: number;     // Lãnh đạo
  nguoi_phe_duyet_id?: string;
  ngay_phe_duyet?: string;
  // Field để phân biệt nguồn
  source: 'CC' | 'LD';
}

type StatusFilter = 'all' | 'pending' | 'approved' | 'rejected';

// =============================================================================
// API FUNCTIONS
// =============================================================================

// Hàm helper để fetch tất cả trang
async function fetchAllPages<T>(
  fetchFn: (page: number, pageSize: number) => Promise<{ data: T[]; total: number }>,
  pageSize: number = 100
): Promise<T[]> {
  const allData: T[] = [];
  let page = 1;
  let hasMore = true;
  
  while (hasMore) {
    const result = await fetchFn(page, pageSize);
    allData.push(...result.data);
    hasMore = allData.length < result.total;
    page++;
    
    // Safety limit
    if (page > 50) break;
  }
  
  return allData;
}

const congViecApi = {
  // ===================== CÔNG CHỨC =====================
  async getCCPending(params: { thang?: number; nam?: number }): Promise<IKeKhai[]> {
    console.log('[TabCongViec] GET /phe-duyet/pending (CC) - ALL PAGES', params);
    try {
      const allData = await fetchAllPages(async (page, pageSize) => {
        const response = await apiClient.get('/phe-duyet/pending', { 
          params: { ...params, page, page_size: pageSize } 
        });
        
        let data: IKeKhai[] = [];
        let total = 0;
        
        if (Array.isArray(response.data)) {
          data = response.data;
          total = data.length;
        } else if (response.data?.data?.items) {
          data = response.data.data.items;
          total = response.data?.pagination?.total_items || response.data?.data?.pagination?.total || data.length;
        } else if (Array.isArray(response.data?.data)) {
          data = response.data.data;
          total = response.data?.pagination?.total_items || response.data?.pagination?.total || data.length;
        }
        
        return { data, total };
      });
      
      // Mark source
      return allData.map(item => ({ ...item, source: 'CC' as const }));
    } catch (err) {
      console.warn('[TabCongViec] Error loading CC pending:', err);
      return [];
    }
  },

  async getCCLichSu(params: { thang?: number; nam?: number; trang_thai?: string }): Promise<IKeKhai[]> {
    console.log('[TabCongViec] GET /phe-duyet/lich-su (CC) - ALL PAGES', params);
    try {
      const allData = await fetchAllPages(async (page, pageSize) => {
        const response = await apiClient.get('/phe-duyet/lich-su', { 
          params: { ...params, page, page_size: pageSize } 
        });
        
        let data: IKeKhai[] = [];
        let total = 0;
        
        if (Array.isArray(response.data)) {
          data = response.data;
          total = data.length;
        } else if (response.data?.data?.items) {
          data = response.data.data.items;
          total = response.data?.pagination?.total_items || response.data?.data?.pagination?.total || data.length;
        } else if (Array.isArray(response.data?.data)) {
          data = response.data.data;
          total = response.data?.pagination?.total_items || response.data?.pagination?.total || data.length;
        }
        
        return { data, total };
      });
      
      return allData.map(item => ({ ...item, source: 'CC' as const }));
    } catch {
      console.warn('[TabCongViec] /phe-duyet/lich-su không có, trả về []');
      return [];
    }
  },

  async pheDuyetCC(keKhaiId: string, payload: {
    action: 'APPROVE' | 'REJECT';
    so_loi_chat_luong?: number;
    so_loi_tien_do?: number;
    cap_do_ma?: string;
    noi_dung_trao_doi?: string;
  }): Promise<void> {
    await apiClient.post(`/phe-duyet/${keKhaiId}`, payload);
  },

  async pheDuyetCCBulk(payload: {
    ke_khai_ids: string[];
    action: 'APPROVE' | 'REJECT';
    noi_dung_trao_doi?: string;
    // Không gửi so_loi → backend dùng None → fallback tu_danh_gia CC
  }): Promise<void> {
    await apiClient.post('/phe-duyet/xu-ly', payload);
  },

  // ===================== LÃNH ĐẠO =====================
  async getLDPending(params: { thang?: number; nam?: number }): Promise<IKeKhai[]> {
    console.log('[TabCongViec] GET /ke-khai-lanh-dao/cho-phe-duyet (LD) - ALL PAGES', params);
    try {
      const allData = await fetchAllPages(async (page, pageSize) => {
        const response = await apiClient.get('/ke-khai-lanh-dao/cho-phe-duyet', { 
          params: { ...params, page, page_size: pageSize } 
        });
        
        let data: IKeKhai[] = [];
        let total = 0;
        
        if (Array.isArray(response.data)) {
          data = response.data;
          total = data.length;
        } else if (response.data?.data?.items) {
          data = response.data.data.items;
          total = response.data?.pagination?.total_items || response.data?.data?.pagination?.total || data.length;
        } else if (Array.isArray(response.data?.data)) {
          data = response.data.data;
          total = response.data?.pagination?.total_items || response.data?.pagination?.total || data.length;
        }
        
        return { data, total };
      });
      
      // Normalize field names và mark source
      return allData.map(item => ({
        ...item,
        source: 'LD' as const,
        // Normalize: Lãnh đạo dùng ten_cong_viec thay vì danh_muc_ten
        danh_muc_ten: item.ten_cong_viec || item.danh_muc_ten,
        mo_ta_cong_viec: item.mo_ta || item.mo_ta_cong_viec,
      }));
    } catch (err) {
      console.warn('[TabCongViec] Error loading LD pending:', err);
      return [];
    }
  },

  async getLDLichSu(params: { thang?: number; nam?: number; trang_thai?: string }): Promise<IKeKhai[]> {
    console.log('[TabCongViec] GET /ke-khai-lanh-dao/lich-su (LD) - ALL PAGES', params);
    try {
      const allData = await fetchAllPages(async (page, pageSize) => {
        const response = await apiClient.get('/ke-khai-lanh-dao/lich-su', { 
          params: { ...params, page, page_size: pageSize } 
        });
        
        let data: IKeKhai[] = [];
        let total = 0;
        
        if (Array.isArray(response.data)) {
          data = response.data;
          total = data.length;
        } else if (response.data?.data?.items) {
          data = response.data.data.items;
          total = response.data?.pagination?.total_items || response.data?.data?.pagination?.total || data.length;
        } else if (Array.isArray(response.data?.data)) {
          data = response.data.data;
          total = response.data?.pagination?.total_items || response.data?.pagination?.total || data.length;
        }
        
        return { data, total };
      });
      
      return allData.map(item => ({
        ...item,
        source: 'LD' as const,
        danh_muc_ten: item.ten_cong_viec || item.danh_muc_ten,
        mo_ta_cong_viec: item.mo_ta || item.mo_ta_cong_viec,
        // Normalize trang_thai - có thể là string hoặc trong object
        trang_thai: typeof item.trang_thai === 'string' ? item.trang_thai : (item.trang_thai as any)?.value || item.trang_thai,
      }));
    } catch (err) {
      console.warn('[TabCongViec] /ke-khai-lanh-dao/lich-su error:', err);
      return [];
    }
  },

  async pheDuyetLD(keKhaiId: string, payload: {
    action: 'APPROVE' | 'REJECT';
    so_loi_chat_luong?: number;
    so_loi_tien_do?: number;
    cap_do_ma?: string;
    y_kien?: string;
  }): Promise<void> {
    await apiClient.post(`/ke-khai-lanh-dao/${keKhaiId}/phe-duyet`, payload);
  },

  // ===================== TRẢ LẠI ĐÃ DUYỆT =====================
  async traLaiCC(keKhaiId: string, lyDo: string): Promise<void> {
    await apiClient.post(`/phe-duyet/${keKhaiId}/tra-lai`, { ly_do: lyDo });
  },

  async traLaiLD(keKhaiId: string, lyDo: string): Promise<void> {
    await apiClient.post(`/ke-khai-lanh-dao/${keKhaiId}/tra-lai`, { ly_do: lyDo });
  },

  // ===================== UNIFIED =====================
  async getAllPending(params: { thang?: number; nam?: number }): Promise<IKeKhai[]> {
    const [ccData, ldData] = await Promise.all([
      this.getCCPending(params),
      this.getLDPending(params),
    ]);
    console.log(`[TabCongViec] Total pending: CC=${ccData.length}, LD=${ldData.length}`);
    return [...ccData, ...ldData];
  },

  async getAllLichSu(params: { thang?: number; nam?: number }): Promise<IKeKhai[]> {
    const [ccData, ldData] = await Promise.all([
      this.getCCLichSu(params),
      this.getLDLichSu(params),
    ]);
    console.log(`[TabCongViec] Total lich su: CC=${ccData.length}, LD=${ldData.length}`);
    return [...ccData, ...ldData];
  },
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

// Page size options
const PAGE_SIZE_OPTIONS = [20, 50, 100, 200];

// ===== PERSISTENT EDITS (localStorage) =====
const EDITS_STORAGE_KEY = 'kpi-phe-duyet-edits';

interface ISavedEdit {
  cap_do_ma?: string;
  loi_cl: number;
  loi_td: number;
  updated_at: number; // timestamp
}

function getSavedEdits(): Record<string, ISavedEdit> {
  try {
    const raw = localStorage.getItem(EDITS_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    // Xóa edits cũ hơn 7 ngày
    const now = Date.now();
    const cleaned: Record<string, ISavedEdit> = {};
    for (const [id, edit] of Object.entries(parsed)) {
      if (now - (edit as ISavedEdit).updated_at < 7 * 24 * 60 * 60 * 1000) {
        cleaned[id] = edit as ISavedEdit;
      }
    }
    return cleaned;
  } catch {
    return {};
  }
}

function saveEdit(id: string, edit: ISavedEdit) {
  try {
    const edits = getSavedEdits();
    edits[id] = { ...edit, updated_at: Date.now() };
    localStorage.setItem(EDITS_STORAGE_KEY, JSON.stringify(edits));
  } catch {
    console.warn('[TabCongViec] Cannot save edit to localStorage');
  }
}

function removeEdit(id: string) {
  try {
    const edits = getSavedEdits();
    delete edits[id];
    localStorage.setItem(EDITS_STORAGE_KEY, JSON.stringify(edits));
  } catch {
    // ignore
  }
}

function removeEdits(ids: string[]) {
  try {
    const edits = getSavedEdits();
    ids.forEach(id => delete edits[id]);
    localStorage.setItem(EDITS_STORAGE_KEY, JSON.stringify(edits));
  } catch {
    // ignore
  }
}

// Merge saved edits vào data từ API
function mergeEditsIntoData(data: IKeKhai[]): IKeKhai[] {
  const edits = getSavedEdits();
  if (Object.keys(edits).length === 0) return data;
  
  return data.map(item => {
    const edit = edits[item.id];
    if (!edit) return item;
    // Chỉ merge nếu item vẫn đang CHO_PHE_DUYET
    if (item.trang_thai !== 'CHO_PHE_DUYET') {
      removeEdit(item.id); // Đã duyệt/từ chối → xóa edit cũ
      return item;
    }
    const isCC = item.source === 'CC';
    return {
      ...item,
      cap_do_ma: edit.cap_do_ma || item.cap_do_ma,
      ...(isCC
        ? { tu_danh_gia_chat_luong: edit.loi_cl, tu_danh_gia_tien_do: edit.loi_td }
        : { so_loi_chat_luong: edit.loi_cl, so_loi_tien_do: edit.loi_td }
      ),
    };
  });
}

export default function TabCongViec({ thang, nam, canApprove, onPendingCountChange }: ITabProps) {
  const [allData, setAllData] = useState<IKeKhai[]>([]); // Tất cả data
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [congChucFilter, setCongChucFilter] = useState<string>('all');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | undefined>(undefined);
  
  // Pagination - client-side
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  
  // Counts
  const [counts, setCounts] = useState({ pending: 0, pendingCC: 0, pendingLD: 0, pendingHd111: 0, approved: 0, rejected: 0, total: 0 });
  
  // Modal đơn lẻ
  const [selectedItem, setSelectedItem] = useState<IKeKhai | null>(null);
  const [modalAction, setModalAction] = useState<'approve' | 'reject' | null>(null);
  const [ghiChu, setGhiChu] = useState('');
  const [soLoiChatLuong, setSoLoiChatLuong] = useState<number>(0);
  const [soLoiTienDo, setSoLoiTienDo] = useState<number>(0);
  
  // Modal bulk
  const [bulkModalAction, setBulkModalAction] = useState<'approve' | 'reject' | null>(null);
  const [bulkGhiChu, setBulkGhiChu] = useState('');

  // Modal trả lại đã duyệt
  const [traLaiItem, setTraLaiItem] = useState<IKeKhai | null>(null);
  const [traLaiLyDo, setTraLaiLyDo] = useState('');
  const [isTraLai, setIsTraLai] = useState(false);
  
  // Chi tiết mô tả popup
  const [hoverItem, setHoverItem] = useState<IKeKhai | null>(null);
  const [pinnedItem, setPinnedItem] = useState<IKeKhai | null>(null);
  const [popupPos, setPopupPos] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
  const detailItem = pinnedItem || hoverItem;

  // Inline edit
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<{
    cap_do_ma: string;
    loi_cl: number;
    loi_td: number;
  }>({ cap_do_ma: '', loi_cl: 0, loi_td: 0 });
  
  // Computed: paginated data
  const totalItems = allData.length;
  const totalPages = Math.ceil(totalItems / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);
  const data = allData.slice(startIndex, endIndex);

  // Get currentUserId
  useEffect(() => {
    try {
      const authStr = localStorage.getItem('kpi-auth-storage');
      if (authStr) {
        const auth = JSON.parse(authStr);
        const userId = auth?.state?.user?.id || auth?.state?.user?.cong_chuc_id;
        setCurrentUserId(userId);
      }
    } catch {
      console.warn('[TabCongViec] Cannot get user from localStorage');
    }
  }, []);

  // Load counts
  const loadCounts = useCallback(async () => {
    try {
      const [pending, lichSu] = await Promise.all([
        congViecApi.getAllPending({ thang, nam }),
        congViecApi.getAllLichSu({ thang, nam }),
      ]);
      
      const pendingCC = pending.filter(d => d.source === 'CC').length;
      // Phase 3 (29/04/2026): tách số HĐ 111 khỏi LĐ thật trong nhóm "LD"
      const pendingHd111 = pending.filter(d => d.source === 'LD' && d.cong_chuc?.is_hd_111 === true).length;
      const pendingLD = pending.filter(d => d.source === 'LD').length - pendingHd111;
      const approvedCount = lichSu.filter(d => d.trang_thai === 'DA_PHE_DUYET').length;
      const rejectedCount = lichSu.filter(d => d.trang_thai === 'TU_CHOI').length;

      setCounts({
        pending: pending.length,
        pendingCC,
        pendingLD,
        pendingHd111,
        approved: approvedCount,
        rejected: rejectedCount,
        total: pending.length + approvedCount + rejectedCount,
      });
      
      onPendingCountChange?.(pending.length);
    } catch (err) {
      console.error('[TabCongViec] Error loading counts:', err);
    }
  }, [thang, nam, onPendingCountChange]);

  // Load data based on filter
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      let result: IKeKhai[] = [];
      
      if (statusFilter === 'pending') {
        result = await congViecApi.getAllPending({ thang, nam });
      } else if (statusFilter === 'approved') {
        const lichSu = await congViecApi.getAllLichSu({ thang, nam });
        result = lichSu.filter(d => d.trang_thai === 'DA_PHE_DUYET');
      } else if (statusFilter === 'rejected') {
        const lichSu = await congViecApi.getAllLichSu({ thang, nam });
        result = lichSu.filter(d => d.trang_thai === 'TU_CHOI');
      } else {
        // all
        const [pending, lichSu] = await Promise.all([
          congViecApi.getAllPending({ thang, nam }),
          congViecApi.getAllLichSu({ thang, nam }),
        ]);
        result = [...pending, ...lichSu];
      }
      
      setAllData(mergeEditsIntoData(result));
      setCurrentPage(1); // Reset to first page when data changes
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Không thể tải dữ liệu');
    } finally {
      setIsLoading(false);
    }
  }, [thang, nam, statusFilter]);

  // Reset page when filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, pageSize, congChucFilter]);

  // Reset selectedIds when filter changes (FIX BUG: xung đột filter)
  useEffect(() => {
    setSelectedIds(new Set());
  }, [statusFilter, congChucFilter]);

  useEffect(() => {
    loadCounts();
  }, [loadCounts]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const refreshAll = async () => {
    await Promise.all([loadCounts(), loadData()]);
  };

  // Handlers
  const handleSelect = (id: string, checked: boolean) => {
    const newSet = new Set(selectedIds);
    if (checked) {
      newSet.add(id);
    } else {
      newSet.delete(id);
    }
    setSelectedIds(newSet);
  };

  // Chọn tất cả pending items (cả CC + LD) — FIX BUG: dùng filtered data thay vì pendingItems
  const handleSelectAll = () => {
    // Lấy pending items từ filteredAllData (đã apply congChucFilter)
    const filteredPendingItems = filteredAllData.filter(d => d.trang_thai === 'CHO_PHE_DUYET');

    if (selectedIds.size === filteredPendingItems.length && filteredPendingItems.length > 0) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredPendingItems.map(d => d.id)));
    }
  };

  // Chọn tất cả pending items trên trang hiện tại
  const handleSelectPage = () => {
    const pendingOnPage = displayData.filter(d => d.trang_thai === 'CHO_PHE_DUYET');
    const allPageSelected = pendingOnPage.length > 0 && pendingOnPage.every(d => selectedIds.has(d.id));
    
    const newSet = new Set(selectedIds);
    if (allPageSelected) {
      pendingOnPage.forEach(d => newSet.delete(d.id));
    } else {
      pendingOnPage.forEach(d => newSet.add(d.id));
    }
    setSelectedIds(newSet);
  };

  // ===== INLINE EDIT =====
  const handleStartEdit = (item: IKeKhai) => {
    const isCC = item.source === 'CC';
    setEditingId(item.id);
    setEditValues({
      cap_do_ma: item.cap_do_ma || '',
      loi_cl: isCC ? (item.tu_danh_gia_chat_luong ?? 0) : (item.so_loi_chat_luong ?? 0),
      loi_td: isCC ? (item.tu_danh_gia_tien_do ?? 0) : (item.so_loi_tien_do ?? 0),
    });
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditValues({ cap_do_ma: '', loi_cl: 0, loi_td: 0 });
  };

  const handleSaveEdit = () => {
    if (!editingId) return;
    
    // Lưu vào localStorage (persist qua reload)
    saveEdit(editingId, {
      cap_do_ma: editValues.cap_do_ma,
      loi_cl: editValues.loi_cl,
      loi_td: editValues.loi_td,
      updated_at: Date.now(),
    });
    
    // Lưu giá trị đã chỉnh vào allData (local state)
    setAllData(prev => prev.map(item => {
      if (item.id !== editingId) return item;
      const isCC = item.source === 'CC';
      return {
        ...item,
        cap_do_ma: editValues.cap_do_ma || item.cap_do_ma,
        ...(isCC 
          ? { tu_danh_gia_chat_luong: editValues.loi_cl, tu_danh_gia_tien_do: editValues.loi_td }
          : { so_loi_chat_luong: editValues.loi_cl, so_loi_tien_do: editValues.loi_td }
        ),
      };
    }));
    setEditingId(null);
    setEditValues({ cap_do_ma: '', loi_cl: 0, loi_td: 0 });
  };

  const handleApprove = (item: IKeKhai) => {
    setSelectedItem(item);
    setModalAction('approve');
    setGhiChu('');
    // Pre-fill số lỗi từ giá trị hiện tại (có thể đã được chỉnh sửa inline)
    const isCC = item.source === 'CC';
    setSoLoiChatLuong(isCC ? (item.tu_danh_gia_chat_luong ?? 0) : (item.so_loi_chat_luong ?? 0));
    setSoLoiTienDo(isCC ? (item.tu_danh_gia_tien_do ?? 0) : (item.so_loi_tien_do ?? 0));
  };

  const handleReject = (item: IKeKhai) => {
    setSelectedItem(item);
    setModalAction('reject');
    setGhiChu('');
    setSoLoiChatLuong(0);
    setSoLoiTienDo(0);
  };

  const handleSubmitModal = async () => {
    if (!selectedItem || !modalAction) return;
    
    setIsProcessing(true);
    try {
      // Lấy saved edit (nếu LĐ đã inline edit trước đó)
      const saved = getSavedEdits()[selectedItem.id];
      const editedCapDoMa = saved?.cap_do_ma || undefined;
      
      if (selectedItem.source === 'CC') {
        // Phê duyệt Công chức
        await congViecApi.pheDuyetCC(selectedItem.id, {
          action: modalAction === 'approve' ? 'APPROVE' : 'REJECT',
          so_loi_chat_luong: modalAction === 'approve' ? soLoiChatLuong : undefined,
          so_loi_tien_do: modalAction === 'approve' ? soLoiTienDo : undefined,
          cap_do_ma: modalAction === 'approve' ? editedCapDoMa : undefined,
          noi_dung_trao_doi: ghiChu || undefined,
        });
      } else {
        // Phê duyệt Lãnh đạo
        await congViecApi.pheDuyetLD(selectedItem.id, {
          action: modalAction === 'approve' ? 'APPROVE' : 'REJECT',
          so_loi_chat_luong: modalAction === 'approve' ? soLoiChatLuong : undefined,
          so_loi_tien_do: modalAction === 'approve' ? soLoiTienDo : undefined,
          cap_do_ma: modalAction === 'approve' ? editedCapDoMa : undefined,
          y_kien: ghiChu || undefined,
        });
      }
      
      await refreshAll();
      removeEdit(selectedItem.id); // Xóa saved edit sau khi đã xử lý
      setSelectedItem(null);
      setModalAction(null);
      setGhiChu('');
      setSoLoiChatLuong(0);
      setSoLoiTienDo(0);
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  // ===== TRẢ LẠI ĐÃ DUYỆT =====
  const handleTraLai = (item: IKeKhai) => {
    setTraLaiItem(item);
    setTraLaiLyDo('');
  };

  const handleSubmitTraLai = async () => {
    if (!traLaiItem || !traLaiLyDo.trim()) return;
    setIsTraLai(true);
    try {
      if (traLaiItem.source === 'CC') {
        await congViecApi.traLaiCC(traLaiItem.id, traLaiLyDo);
      } else {
        await congViecApi.traLaiLD(traLaiItem.id, traLaiLyDo);
      }
      await refreshAll();
      setTraLaiItem(null);
      setTraLaiLyDo('');
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra khi trả lại');
    } finally {
      setIsTraLai(false);
    }
  };

  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) return;
    setBulkModalAction('approve');
    setBulkGhiChu('');
  };

  const handleBulkReject = () => {
    if (selectedIds.size === 0) return;
    setBulkModalAction('reject');
    setBulkGhiChu('');
  };

  const handleSubmitBulk = async () => {
    if (selectedIds.size === 0 || !bulkModalAction) return;
    if (bulkModalAction === 'reject' && !bulkGhiChu.trim()) {
      alert('Vui lòng nhập lý do từ chối');
      return;
    }
    
    setIsProcessing(true);
    const action = bulkModalAction === 'approve' ? 'APPROVE' : 'REJECT';
    
    try {
      // Tách CC và LD
      const selectedCC: string[] = [];
      const selectedLD: string[] = [];
      
      for (const id of selectedIds) {
        const item = allData.find(d => d.id === id);
        if (!item) continue;
        if (item.source === 'CC') selectedCC.push(id);
        else selectedLD.push(id);
      }
      
      const errors: string[] = [];
      
      // CC: dùng API bulk
      if (selectedCC.length > 0) {
        try {
          await congViecApi.pheDuyetCCBulk({
            ke_khai_ids: selectedCC,
            action,
            noi_dung_trao_doi: bulkGhiChu || undefined,
          });
        } catch (err) {
          errors.push(`CC: ${(err as Error).message}`);
        }
      }
      
      // LD: loop từng cái (API chưa hỗ trợ bulk)
      if (selectedLD.length > 0) {
        let ldFailed = 0;
        const savedEdits = getSavedEdits();
        for (const id of selectedLD) {
          try {
            const item = allData.find(d => d.id === id);
            const saved = savedEdits[id];
            await congViecApi.pheDuyetLD(id, {
              action,
              // Nếu có saved edit → gửi số lỗi đã edit; nếu không → undefined → backend fallback tu_danh_gia
              so_loi_chat_luong: saved ? saved.loi_cl : undefined,
              so_loi_tien_do: saved ? saved.loi_td : undefined,
              cap_do_ma: saved?.cap_do_ma || undefined,
              y_kien: bulkGhiChu || undefined,
            });
          } catch {
            ldFailed++;
          }
        }
        if (ldFailed > 0) {
          errors.push(`LĐ: ${ldFailed}/${selectedLD.length} thất bại`);
        }
      }
      
      await refreshAll();
      removeEdits(Array.from(selectedIds)); // Xóa saved edits sau khi đã xử lý
      setSelectedIds(new Set());
      setBulkModalAction(null);
      setBulkGhiChu('');
      
      if (errors.length > 0) {
        alert(`Hoàn tất (có lỗi):\n${errors.join('\n')}`);
      }
    } catch (err) {
      const error = err as Error;
      alert(error.message || 'Có lỗi xảy ra');
    } finally {
      setIsProcessing(false);
    }
  };

  // Filter pending items (cả CC + LD)
  const pendingItems = allData.filter(d => d.trang_thai === 'CHO_PHE_DUYET');
  const pendingCCItems = pendingItems.filter(d => d.source === 'CC');
  const pendingLDItems = pendingItems.filter(d => d.source === 'LD');

  // ✅ Danh sách công chức unique để filter
  const uniqueCongChuc = React.useMemo(() => {
    const map = new Map<string, { id: string; ho_ten: string; ma_cc: string }>();
    allData.forEach(item => {
      const id = item.cong_chuc_id || item.cong_chuc?.id || '';
      const hoTen = item.cong_chuc?.ho_ten || item.ho_ten || '';
      const maCC = item.cong_chuc?.ma_cc || item.ma_cc || '';
      if (id && !map.has(id)) {
        map.set(id, { id, ho_ten: hoTen, ma_cc: maCC });
      }
    });
    return Array.from(map.values()).sort((a, b) => a.ho_ten.localeCompare(b.ho_ten, 'vi'));
  }, [allData]);

  // Apply congChucFilter vào allData → tạo filteredAllData
  const filteredAllData = React.useMemo(() => {
    if (congChucFilter === 'all') return allData;
    return allData.filter(item => {
      const itemCCId = item.cong_chuc_id || item.cong_chuc?.id || '';
      return itemCCId === congChucFilter;
    });
  }, [allData, congChucFilter]);

  // Filtered pending items (FIX BUG: dùng cho button "Chọn tất cả")
  const filteredPendingItems = React.useMemo(() => {
    return filteredAllData.filter(d => d.trang_thai === 'CHO_PHE_DUYET');
  }, [filteredAllData]);

  // Paginated data từ filteredAllData
  const filteredTotalItems = filteredAllData.length;
  const filteredTotalPages = Math.ceil(filteredTotalItems / pageSize);
  const filteredStartIndex = (currentPage - 1) * pageSize;
  const filteredEndIndex = Math.min(filteredStartIndex + pageSize, filteredTotalItems);
  const displayData = filteredAllData.slice(filteredStartIndex, filteredEndIndex);
  
  // Đếm selected theo loại
  const selectedCCCount = Array.from(selectedIds).filter(id => {
    const item = allData.find(d => d.id === id);
    return item?.source === 'CC';
  }).length;
  const selectedLDCount = selectedIds.size - selectedCCCount;

  // Render
  if (isLoading) {
    return <div className="flex items-center justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadData} />;
  }

  return (
    <div className="space-y-4">
      {/* Header with filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Trạng thái:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Tất cả ({counts.total})</option>
                <option value="pending">
                  Chờ duyệt ({counts.pending})
                  {counts.pendingCC > 0 && counts.pendingLD > 0 
                    ? ` - CC: ${counts.pendingCC}, LĐ: ${counts.pendingLD}` 
                    : ''}
                </option>
                <option value="approved">Đã duyệt ({counts.approved})</option>
                <option value="rejected">Từ chối ({counts.rejected})</option>
              </select>
            </div>
            
            {/* Legend */}
            {counts.pending > 0 && (
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  <span className="text-gray-600">Công chức ({counts.pendingCC})</span>
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                  <span className="text-gray-600">Lãnh đạo ({counts.pendingLD})</span>
                </span>
                {counts.pendingHd111 > 0 && (
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-teal-500"></span>
                    <span className="text-gray-600">HĐ 111 ({counts.pendingHd111})</span>
                  </span>
                )}
              </div>
            )}

            {/* ✅ Công chức Filter */}
            {uniqueCongChuc.length > 1 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">CBCC:</span>
                <select
                  value={congChucFilter}
                  onChange={(e) => { setCongChucFilter(e.target.value); setCurrentPage(1); }}
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

          {/* Quick select buttons */}
          {canApprove && filteredPendingItems.length > 0 && (
            <div className="flex items-center gap-2">
              <button
                onClick={handleSelectPage}
                className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100 border border-gray-300 rounded-lg transition-colors"
              >
                Chọn trang này
              </button>
              <button
                onClick={handleSelectAll}
                className="px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50 border border-blue-300 rounded-lg transition-colors"
              >
                {selectedIds.size === filteredPendingItems.length ? 'Bỏ chọn tất cả' : `Chọn tất cả (${filteredPendingItems.length})`}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ===== FLOATING ACTION BAR khi có selection ===== */}
      {canApprove && selectedIds.size > 0 && (
        <div className="sticky top-0 z-30 bg-blue-600 text-white rounded-lg shadow-lg px-4 py-3 flex items-center justify-between flex-wrap gap-3 animate-in slide-in-from-top">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold">
              Đã chọn {selectedIds.size} công việc
            </span>
            {selectedCCCount > 0 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-500 text-blue-100">
                CC: {selectedCCCount}
              </span>
            )}
            {selectedLDCount > 0 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-500 text-purple-100">
                LĐ: {selectedLDCount}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedIds(new Set())}
              className="px-3 py-1.5 text-sm text-blue-100 hover:text-white hover:bg-blue-500 rounded-lg transition-colors"
            >
              Bỏ chọn
            </button>
            <button
              onClick={handleBulkReject}
              disabled={isProcessing}
              className="px-4 py-1.5 text-sm font-medium bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              Từ chối ({selectedIds.size})
            </button>
            <button
              onClick={handleBulkApprove}
              disabled={isProcessing}
              className="px-4 py-1.5 text-sm font-medium bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {isProcessing ? 'Đang xử lý...' : `Duyệt tất cả (${selectedIds.size})`}
            </button>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <span>📋</span>
            Công việc {statusFilter === 'pending' ? 'chờ duyệt' : statusFilter === 'approved' ? 'đã duyệt' : statusFilter === 'rejected' ? 'từ chối' : ''}
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {canApprove && (
                  <th className="w-10 px-3 py-3">
                    {displayData.some(d => d.trang_thai === 'CHO_PHE_DUYET') && (
                      <input
                        type="checkbox"
                        checked={displayData.filter(d => d.trang_thai === 'CHO_PHE_DUYET').every(d => selectedIds.has(d.id)) && displayData.some(d => d.trang_thai === 'CHO_PHE_DUYET')}
                        onChange={handleSelectPage}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded"
                        title="Chọn tất cả chờ duyệt trên trang này"
                      />
                    )}
                  </th>
                )}
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">Loại</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CBCC</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ngày</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Công việc</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kết quả</th>
                <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-12">SL</th>
                <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-16">Mức độ</th>
                <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-14" title="Số lỗi chất lượng">Lỗi CL</th>
                <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-14" title="Số lỗi tiến độ">Lỗi TĐ</th>
                <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Thao tác</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displayData.length === 0 ? (
                <tr>
                  <td colSpan={canApprove ? 11 : 10} className="px-4 py-8 text-center text-gray-500 italic">
                    Không có công việc nào {statusFilter === 'pending' ? 'chờ duyệt' : ''}{congChucFilter !== 'all' ? ' cho CBCC đã chọn' : ''}
                  </td>
                </tr>
              ) : (
                displayData.map((item) => {
                  const isPending = item.trang_thai === 'CHO_PHE_DUYET';
                  const isApproved = item.trang_thai === 'DA_PHE_DUYET';
                  const isRejected = item.trang_thai === 'TU_CHOI';
                  const isCC = item.source === 'CC';
                  const isLD = item.source === 'LD';
                  
                  return (
                    <tr
                      key={`${item.source}-${item.id}`}
                      className={`hover:bg-gray-50 ${selectedIds.has(item.id) ? 'bg-blue-50' : ''} ${editingId === item.id ? 'bg-blue-50 ring-1 ring-inset ring-blue-300' : ''}`}
                      onMouseEnter={(e) => {
                        if (!pinnedItem) {
                          const rect = e.currentTarget.getBoundingClientRect();
                          setPopupPos({ top: rect.top, left: rect.left + rect.width / 2 });
                          setHoverItem(item);
                        }
                      }}
                      onMouseLeave={() => { if (!pinnedItem) setHoverItem(null); }}
                      onClick={(e) => {
                        if (!pinnedItem) {
                          const rect = e.currentTarget.getBoundingClientRect();
                          setPopupPos({ top: rect.top, left: rect.left + rect.width / 2 });
                          setPinnedItem(item);
                        }
                      }}
                    >
                      {canApprove && (
                        <td className="px-3 py-3">
                          {isPending && (
                            <input
                              type="checkbox"
                              checked={selectedIds.has(item.id)}
                              onChange={(e) => handleSelect(item.id, e.target.checked)}
                              className="w-4 h-4 text-blue-600 border-gray-300 rounded"
                            />
                          )}
                        </td>
                      )}
                      <td className="px-3 py-3">
                        {(() => {
                          // Phase 3 (29/04/2026): phân biệt HĐ 111 với LĐ thật
                          const isHd111 = item.cong_chuc?.is_hd_111 === true;
                          const badgeClass = isCC
                            ? 'bg-blue-100 text-blue-800'
                            : isHd111
                              ? 'bg-teal-100 text-teal-800'
                              : 'bg-purple-100 text-purple-800';
                          const label = isCC ? 'CC' : isHd111 ? 'HĐ 111' : 'LĐ';
                          return (
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${badgeClass}`}>
                              {label}
                            </span>
                          );
                        })()}
                      </td>
                      <td className="px-3 py-3">
                        <div className="text-sm font-medium text-gray-900 truncate max-w-[140px]" title={item.cong_chuc?.ho_ten || item.ho_ten || '-'}>
                          {item.cong_chuc?.ho_ten || item.ho_ten || '-'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {item.cong_chuc?.ma_cc || item.ma_cc || '-'}
                        </div>
                      </td>
                      <td className="px-3 py-3 text-sm text-gray-600 whitespace-nowrap">
                        {item.ngay_thuc_hien ? format(parseISO(item.ngay_thuc_hien), 'dd/MM/yyyy') : '-'}
                      </td>
                      {/* Công việc: CHỈ hiện tên từ danh mục, KHÔNG fallback sang mô tả */}
                      <td className="px-3 py-3">
                        <div className="text-sm text-gray-900 max-w-[180px] line-clamp-2" title={item.danh_muc_ten || item.ten_cong_viec || '-'}>
                          {item.danh_muc_ten || item.ten_cong_viec || '-'}
                        </div>
                      </td>
                      {/* Kết quả = Mô tả công việc mà CC kê khai */}
                      <td className="px-3 py-3">
                        <div className="text-sm text-gray-600 max-w-[200px] line-clamp-2">
                          {item.mo_ta_cong_viec || item.mo_ta || item.ket_qua || <span className="text-gray-400">-</span>}
                        </div>
                      </td>
                      {/* SL - tách riêng */}
                      <td className="px-3 py-3 text-center text-sm font-semibold text-gray-900">
                        {item.so_luong || '-'}
                      </td>
                      {/* Mức độ - inline editable */}
                      <td className="px-3 py-3 text-center">
                        {editingId === item.id ? (
                          <select
                            value={editValues.cap_do_ma}
                            onChange={(e) => setEditValues(prev => ({ ...prev, cap_do_ma: e.target.value }))}
                            className="w-16 px-1 py-0.5 text-xs border border-blue-300 rounded bg-blue-50 focus:ring-2 focus:ring-blue-500 text-center font-semibold"
                          >
                            <option value="">-</option>
                            <option value="C1">C1</option>
                            <option value="C2">C2</option>
                            <option value="C3">C3</option>
                            <option value="C4">C4</option>
                            <option value="C5">C5</option>
                          </select>
                        ) : item.cap_do_ma ? (
                          <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold
                            ${item.cap_do_ma === 'C1' ? 'bg-slate-100 text-slate-600' :
                              item.cap_do_ma === 'C2' ? 'bg-blue-100 text-blue-700' :
                              item.cap_do_ma === 'C3' ? 'bg-orange-100 text-orange-700' :
                              item.cap_do_ma === 'C4' ? 'bg-red-100 text-red-700' :
                              'bg-purple-100 text-purple-700'}`}
                          >
                            {item.cap_do_ma}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-sm">-</span>
                        )}
                      </td>
                      {/* Lỗi CL - inline editable */}
                      <td className="px-3 py-3 text-center">
                        {editingId === item.id ? (
                          <input
                            type="number"
                            min={0}
                            value={editValues.loi_cl}
                            onChange={(e) => setEditValues(prev => ({ ...prev, loi_cl: parseInt(e.target.value) || 0 }))}
                            className="w-12 px-1 py-0.5 text-xs border border-blue-300 rounded bg-blue-50 focus:ring-2 focus:ring-blue-500 text-center font-semibold"
                          />
                        ) : (() => {
                          const loiCL = isCC ? item.tu_danh_gia_chat_luong : item.so_loi_chat_luong;
                          if (loiCL === undefined || loiCL === null) return <span className="text-gray-400 text-sm">-</span>;
                          if (loiCL === 0) return <span className="text-sm text-gray-400">0</span>;
                          return (
                            <span className="inline-flex items-center justify-center min-w-[22px] h-[22px] px-1 rounded bg-red-100 text-red-700 text-xs font-bold">
                              {loiCL}
                            </span>
                          );
                        })()}
                      </td>
                      {/* Lỗi TĐ - inline editable */}
                      <td className="px-3 py-3 text-center">
                        {editingId === item.id ? (
                          <input
                            type="number"
                            min={0}
                            value={editValues.loi_td}
                            onChange={(e) => setEditValues(prev => ({ ...prev, loi_td: parseInt(e.target.value) || 0 }))}
                            className="w-12 px-1 py-0.5 text-xs border border-blue-300 rounded bg-blue-50 focus:ring-2 focus:ring-blue-500 text-center font-semibold"
                          />
                        ) : (() => {
                          const loiTD = isCC ? item.tu_danh_gia_tien_do : item.so_loi_tien_do;
                          if (loiTD === undefined || loiTD === null) return <span className="text-gray-400 text-sm">-</span>;
                          if (loiTD === 0) return <span className="text-sm text-gray-400">0</span>;
                          return (
                            <span className="inline-flex items-center justify-center min-w-[22px] h-[22px] px-1 rounded bg-amber-100 text-amber-700 text-xs font-bold">
                              {loiTD}
                            </span>
                          );
                        })()}
                      </td>
                      {/* Thao tác - có edit mode */}
                      <td className="px-3 py-3">
                        <div className="flex items-center justify-center gap-1.5">
                          {editingId === item.id ? (
                            <>
                              <button
                                onClick={handleSaveEdit}
                                className="px-2.5 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                              >
                                Xong
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="px-2.5 py-1 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                              >
                                Hủy
                              </button>
                            </>
                          ) : isPending && canApprove ? (
                            <>
                              <button
                                onClick={() => handleStartEdit(item)}
                                disabled={editingId !== null}
                                className="px-2.5 py-1 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                                title="Chỉnh sửa mức độ, lỗi CL, lỗi TĐ"
                              >
                                Sửa
                              </button>
                              <button
                                onClick={() => handleApprove(item)}
                                disabled={editingId !== null}
                                className="px-2.5 py-1 text-xs font-medium text-white bg-green-600 hover:bg-green-700 rounded transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                              >
                                Duyệt
                              </button>
                              <button
                                onClick={() => handleReject(item)}
                                disabled={editingId !== null}
                                className="px-2.5 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                              >
                                Từ chối
                              </button>
                            </>
                          ) : isApproved ? (
                            <div className="flex items-center gap-1">
                              <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
                                Đã duyệt
                              </span>
                              {canApprove && (
                                <button
                                  onClick={() => handleTraLai(item)}
                                  className="px-2 py-1 text-xs font-medium text-orange-700 bg-orange-50 hover:bg-orange-100 border border-orange-200 rounded transition-colors"
                                  title="Trả lại kê khai đã duyệt nhầm"
                                >
                                  ↩ Trả lại
                                </button>
                              )}
                            </div>
                          ) : isRejected ? (
                            <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700">
                              Từ chối
                            </span>
                          ) : (
                            <span className="px-2 py-1 text-xs font-medium rounded-full bg-amber-100 text-amber-700">
                              Chờ duyệt
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {filteredTotalItems > 0 && (
          <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                Hiển thị {filteredStartIndex + 1} - {filteredEndIndex} / {filteredTotalItems} công việc
              </span>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Số dòng:</span>
                <select
                  value={pageSize}
                  onChange={(e) => setPageSize(Number(e.target.value))}
                  className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                >
                  {PAGE_SIZE_OPTIONS.map(size => (
                    <option key={size} value={size}>{size}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="px-2 py-1 text-sm text-gray-600 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                title="Trang đầu"
              >
                ⏮️
              </button>
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Trước
              </button>
              
              <span className="px-3 py-1 text-sm font-medium text-gray-900">
                Trang {currentPage} / {filteredTotalPages || 1}
              </span>
              
              <button
                onClick={() => setCurrentPage(p => Math.min(filteredTotalPages, p + 1))}
                disabled={currentPage >= filteredTotalPages}
                className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Sau →
              </button>
              <button
                onClick={() => setCurrentPage(filteredTotalPages)}
                disabled={currentPage >= filteredTotalPages}
                className="px-2 py-1 text-sm text-gray-600 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                title="Trang cuối"
              >
                ⏭️
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Approve/Reject Modal */}
      {selectedItem && modalAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {modalAction === 'approve' ? '✅ Phê duyệt công việc' : '❌ Từ chối công việc'}
              <span className={`ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium
                ${selectedItem.source === 'CC' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}`}
              >
                {selectedItem.source === 'CC' ? 'Công chức' : 'Lãnh đạo'}
              </span>
            </h3>
            
            <div className="bg-gray-50 rounded-lg p-3 mb-4 text-sm">
              <p><strong>CBCC:</strong> {selectedItem.cong_chuc?.ho_ten || selectedItem.ho_ten}</p>
              <p><strong>Công việc:</strong> {selectedItem.danh_muc_ten || selectedItem.ten_cong_viec || '-'}</p>
              {/* Kết quả = mô tả công việc */}
              {(selectedItem.mo_ta_cong_viec || selectedItem.mo_ta) && (
                <p><strong>Kết quả:</strong> {selectedItem.mo_ta_cong_viec || selectedItem.mo_ta}</p>
              )}
              <p><strong>Số lượng:</strong> {selectedItem.so_luong} {selectedItem.cap_do_ma && <span className="ml-2"><strong>Mức độ:</strong> {selectedItem.cap_do_ma}</span>}</p>
              {/* Hiển thị tự đánh giá của CC */}
              {selectedItem.source === 'CC' && selectedItem.tu_danh_gia_chat_luong !== undefined && (
                <p><strong>Tự đánh giá (CC):</strong> CL: {selectedItem.tu_danh_gia_chat_luong} lỗi, TĐ: {selectedItem.tu_danh_gia_tien_do} lỗi</p>
              )}
              {/* v2.6.0: Hiển thị số lỗi mà Lãnh đạo tự đánh giá */}
              {selectedItem.source === 'LD' && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <p className="font-medium text-purple-700 mb-1">📊 Lãnh đạo tự đánh giá:</p>
                  <div className="flex gap-4">
                    <span className={`${(selectedItem.so_loi_chat_luong || 0) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      Lỗi CL: {selectedItem.so_loi_chat_luong || 0}
                    </span>
                    <span className={`${(selectedItem.so_loi_tien_do || 0) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      Lỗi TĐ: {selectedItem.so_loi_tien_do || 0}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    (Mỗi lỗi trừ 25% điểm tiêu chí tương ứng)
                  </p>
                </div>
              )}
            </div>

            {modalAction === 'approve' && (
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Số lỗi chất lượng {selectedItem.source === 'LD' && <span className="text-purple-600">(xác nhận)</span>}
                  </label>
                  <input
                    type="number"
                    min={0}
                    value={soLoiChatLuong}
                    onChange={(e) => setSoLoiChatLuong(parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Số lỗi tiến độ {selectedItem.source === 'LD' && <span className="text-purple-600">(xác nhận)</span>}
                  </label>
                  <input
                    type="number"
                    min={0}
                    value={soLoiTienDo}
                    onChange={(e) => setSoLoiTienDo(parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {modalAction === 'approve' ? 'Ý kiến (tùy chọn)' : 'Lý do từ chối'}
              </label>
              <textarea
                value={ghiChu}
                onChange={(e) => setGhiChu(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder={modalAction === 'approve' ? 'Nhập ý kiến...' : 'Nhập lý do từ chối...'}
              />
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setSelectedItem(null); setModalAction(null); }}
                disabled={isProcessing}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Hủy
              </button>
              <button
                onClick={handleSubmitModal}
                disabled={isProcessing || (modalAction === 'reject' && !ghiChu.trim())}
                className={`px-4 py-2 text-white rounded-lg disabled:opacity-50
                  ${modalAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
              >
                {isProcessing ? 'Đang xử lý...' : modalAction === 'approve' ? 'Phê duyệt' : 'Từ chối'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== BULK Approve/Reject Modal ===== */}
      {bulkModalAction && selectedIds.size > 0 && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {bulkModalAction === 'approve' ? '✅ Phê duyệt hàng loạt' : '❌ Từ chối hàng loạt'}
            </h3>
            
            {/* Thống kê selection */}
            <div className="bg-gray-50 rounded-lg p-3 mb-4">
              <div className="flex items-center gap-4 text-sm">
                <span className="font-semibold text-gray-900">Tổng: {selectedIds.size} công việc</span>
                {selectedCCCount > 0 && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-100 text-blue-800 text-xs font-medium">
                    CC: {selectedCCCount}
                  </span>
                )}
                {selectedLDCount > 0 && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-xs font-medium">
                    LĐ: {selectedLDCount}
                  </span>
                )}
              </div>
              {selectedLDCount > 0 && (
                <p className="text-xs text-gray-500 mt-2">
                  Lưu ý: Lãnh đạo sẽ được xử lý từng cái một (API chưa hỗ trợ bulk).
                </p>
              )}
              {bulkModalAction === 'approve' && (
                <p className="text-xs text-amber-600 mt-2">
                  Duyệt hàng loạt sẽ sử dụng số lỗi tự đánh giá của CBCC (hoặc số lỗi đã chỉnh sửa inline). Nếu cần nhập số lỗi riêng, hãy duyệt từng công việc.
                </p>
              )}
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {bulkModalAction === 'approve' ? 'Ý kiến chung (tùy chọn)' : 'Lý do từ chối (bắt buộc)'}
              </label>
              <textarea
                value={bulkGhiChu}
                onChange={(e) => setBulkGhiChu(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder={bulkModalAction === 'approve' ? 'Nhập ý kiến chung...' : 'Nhập lý do từ chối...'}
              />
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setBulkModalAction(null); setBulkGhiChu(''); }}
                disabled={isProcessing}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Hủy
              </button>
              <button
                onClick={handleSubmitBulk}
                disabled={isProcessing || (bulkModalAction === 'reject' && !bulkGhiChu.trim())}
                className={`px-4 py-2 text-white rounded-lg disabled:opacity-50
                  ${bulkModalAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
              >
                {isProcessing ? 'Đang xử lý...' : bulkModalAction === 'approve' 
                  ? `Phê duyệt ${selectedIds.size} công việc` 
                  : `Từ chối ${selectedIds.size} công việc`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Trả lại đã duyệt */}
      {traLaiItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-orange-700">↩ Trả lại kê khai đã duyệt</h3>
              <button onClick={() => setTraLaiItem(null)} className="p-1 text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg text-sm text-orange-800">
                ⚠️ Kê khai <strong>{traLaiItem.ho_ten}</strong> sẽ được chuyển về trạng thái <strong>Nháp</strong>.
                Các giá trị phê duyệt (số lỗi, SP) sẽ bị xóa.
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
              <button onClick={() => setTraLaiItem(null)} className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">Hủy</button>
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
      {/* Popup mô tả công việc - hiện cạnh row khi hover, ghim khi click */}
      {detailItem && (
        <>
          {/* Overlay khi pinned */}
          {pinnedItem && (
            <div
              className="fixed inset-0 z-40"
              onClick={() => { setPinnedItem(null); setHoverItem(null); }}
            />
          )}
          <div
            className={`fixed z-50 ${pinnedItem ? '' : 'pointer-events-none'}`}
            style={{
              top: popupPos.top,
              left: popupPos.left,
              transform: 'translateX(-50%)',
            }}
          >
            <div className="bg-white rounded-lg shadow-xl border-2 border-blue-300 w-[360px] max-h-[280px] flex flex-col">
              <div className="flex items-center justify-between px-3 py-2 border-b bg-gray-50 rounded-t-lg">
                <h3 className="text-xs font-semibold text-gray-700 truncate pr-2">
                  {detailItem.danh_muc_ten || detailItem.ten_cong_viec || '-'}
                </h3>
                {pinnedItem && (
                  <button
                    onClick={() => { setPinnedItem(null); setHoverItem(null); }}
                    className="p-0.5 rounded hover:bg-gray-200 transition-colors flex-shrink-0"
                  >
                    <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
              <div className="px-3 py-2 overflow-y-auto text-sm">
                <p className="text-gray-900 whitespace-pre-wrap">
                  {detailItem.mo_ta_cong_viec || detailItem.mo_ta || detailItem.ket_qua || 'Không có mô tả'}
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
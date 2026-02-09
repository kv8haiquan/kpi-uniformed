/**
 * src/components/approval/TwoTierApprovalComponents.tsx
 * ======================================================
 * Shared components cho hiển thị phê duyệt 2 cấp.
 * 
 * Version: 2.6 (29/01/2026)
 */

'use client';

import React from 'react';
import { format, parseISO } from 'date-fns';
import {
  TrangThaiNghi,
  INghiPhepResponse,
  getTrangThaiNghiLabel,
  getApprovalProgress as getLeaveApprovalProgress,
} from '@/types/leave';
import {
  TrangThaiTieuChiChung,
  IKetQuaTieuChiChungResponse,
  getTrangThaiLabel,
  getApprovalProgress as getTCApprovalProgress,
} from '@/types/tieu-chi-chung';

// =============================================================================
// LEAVE APPROVAL COMPONENTS
// =============================================================================

/**
 * Badge hiển thị cấp phê duyệt cho nghỉ phép.
 */
export function LeaveApprovalLevelBadge({ trangThai }: { trangThai: TrangThaiNghi }) {
  if (trangThai === TrangThaiNghi.CHO_PHE_DUYET) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
        Cấp 1
      </span>
    );
  }
  if (trangThai === TrangThaiNghi.CHO_CAP2) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
        Cấp 2
      </span>
    );
  }
  return null;
}

/**
 * Progress bar hiển thị tiến trình phê duyệt nghỉ phép.
 */
export function LeaveApprovalProgressBar({ nghiPhep }: { nghiPhep: INghiPhepResponse }) {
  const progress = getLeaveApprovalProgress(nghiPhep);
  const quyTrinh = nghiPhep.quy_trinh;

  if (quyTrinh === 'TU_PHE_DUYET' || quyTrinh === '1_CAP') {
    return null;
  }

  return (
    <div className="mt-2">
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className={progress >= 0 ? 'text-green-600 font-medium' : ''}>Gửi</span>
        <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-amber-400 to-green-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className={progress >= 50 ? 'text-amber-600 font-medium' : ''}>Cấp 1</span>
        <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-amber-400 to-green-500 transition-all duration-300"
            style={{ width: progress >= 50 ? `${(progress - 50) * 2}%` : '0%' }}
          />
        </div>
        <span className={progress >= 100 ? 'text-green-600 font-medium' : ''}>Cấp 2</span>
      </div>
    </div>
  );
}

/**
 * Hiển thị cột "Người duyệt" trong table nghỉ phép.
 */
export function LeaveApproverCell({ item }: { item: INghiPhepResponse }) {
  if (item.quy_trinh === '2_CAP') {
    return (
      <div className="space-y-1">
        <div className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${
            item.trang_thai_cap1 === 'DA_DUYET' ? 'bg-green-500' : 
            item.trang_thai_cap1 === 'TU_CHOI' ? 'bg-red-500' : 'bg-yellow-500'
          }`} />
          <span className="text-xs">
            Cấp 1: {item.nguoi_phe_duyet_cap1?.ho_ten || '-'}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${
            item.trang_thai_cap2 === 'DA_DUYET' ? 'bg-green-500' : 
            item.trang_thai_cap2 === 'TU_CHOI' ? 'bg-red-500' : 
            item.trang_thai === TrangThaiNghi.CHO_CAP2 ? 'bg-yellow-500' : 'bg-gray-300'
          }`} />
          <span className="text-xs">
            Cấp 2: {item.nguoi_phe_duyet_cap2?.ho_ten || '-'}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="text-sm">
      {item.nguoi_phe_duyet?.ho_ten || item.nguoi_phe_duyet_cap1?.ho_ten || '-'}
    </div>
  );
}

/**
 * Thông tin cấp 1 đã duyệt (hiển thị khi đang chờ cấp 2).
 */
export function LeaveLevel1ApprovalInfo({ item }: { item: INghiPhepResponse }) {
  if (item.trang_thai !== TrangThaiNghi.CHO_CAP2 || !item.nguoi_phe_duyet_cap1) {
    return null;
  }

  return (
    <div className="mt-3 px-3 py-2 bg-amber-50 rounded-lg text-sm">
      <span className="text-amber-700">
        ✓ Đã duyệt cấp 1 bởi <strong>{item.nguoi_phe_duyet_cap1.ho_ten}</strong>
        {item.ngay_phe_duyet_cap1 && (
          <> vào {format(parseISO(item.ngay_phe_duyet_cap1), 'HH:mm dd/MM/yyyy')}</>
        )}
      </span>
    </div>
  );
}

// =============================================================================
// TIEU CHI CHUNG APPROVAL COMPONENTS
// =============================================================================

/**
 * Badge hiển thị cấp phê duyệt cho tiêu chí chung.
 */
export function TCApprovalLevelBadge({ trangThai }: { trangThai: TrangThaiTieuChiChung }) {
  if (trangThai === TrangThaiTieuChiChung.CHO_PHE_DUYET) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
        Cấp 1
      </span>
    );
  }
  if (trangThai === TrangThaiTieuChiChung.CHO_CAP2) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
        Cấp 2
      </span>
    );
  }
  return null;
}

/**
 * Progress bar hiển thị tiến trình phê duyệt tiêu chí.
 */
export function TCApprovalProgressBar({ ketQua }: { ketQua: IKetQuaTieuChiChungResponse }) {
  const progress = getTCApprovalProgress(ketQua);
  const quyTrinh = ketQua.quy_trinh;

  if (quyTrinh === 'TU_PHE_DUYET' || quyTrinh === '1_CAP') {
    return null;
  }

  return (
    <div className="mt-2">
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className={progress >= 0 ? 'text-green-600 font-medium' : ''}>Gửi</span>
        <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-amber-400 to-green-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className={progress >= 50 ? 'text-amber-600 font-medium' : ''}>Cấp 1</span>
        <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-amber-400 to-green-500 transition-all duration-300"
            style={{ width: progress >= 50 ? `${(progress - 50) * 2}%` : '0%' }}
          />
        </div>
        <span className={progress >= 100 ? 'text-green-600 font-medium' : ''}>Cấp 2</span>
      </div>
    </div>
  );
}

/**
 * Thông tin cấp 1 đã duyệt cho tiêu chí (hiển thị khi đang chờ cấp 2).
 */
export function TCLevel1ApprovalInfo({ ketQua }: { ketQua: IKetQuaTieuChiChungResponse }) {
  if (ketQua.trang_thai !== TrangThaiTieuChiChung.CHO_CAP2 || !ketQua.nguoi_phe_duyet_tc_cap1) {
    return null;
  }

  return (
    <div className="mt-3 px-3 py-2 bg-amber-50 rounded-lg text-sm">
      <span className="text-amber-700">
        ✓ Đã duyệt cấp 1 bởi <strong>{ketQua.nguoi_phe_duyet_tc_cap1.ho_ten}</strong>
        {ketQua.ngay_phe_duyet_tc_cap1 && (
          <> vào {format(parseISO(ketQua.ngay_phe_duyet_tc_cap1), 'HH:mm dd/MM/yyyy')}</>
        )}
      </span>
    </div>
  );
}

// =============================================================================
// GENERIC STATUS BADGE
// =============================================================================

type ApprovalStatus = 'pending' | 'level1' | 'level2' | 'approved' | 'rejected';

interface StatusBadgeProps {
  status: ApprovalStatus;
  className?: string;
}

export function ApprovalStatusBadge({ status, className = '' }: StatusBadgeProps) {
  const configs: Record<ApprovalStatus, { bg: string; text: string; label: string }> = {
    pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Chờ phê duyệt' },
    level1: { bg: 'bg-amber-100', text: 'text-amber-800', label: 'Chờ cấp 1' },
    level2: { bg: 'bg-indigo-100', text: 'text-indigo-800', label: 'Chờ cấp 2' },
    approved: { bg: 'bg-green-100', text: 'text-green-800', label: 'Đã phê duyệt' },
    rejected: { bg: 'bg-red-100', text: 'text-red-800', label: 'Từ chối' },
  };

  const config = configs[status];

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text} ${className}`}>
      {config.label}
    </span>
  );
}

// =============================================================================
// FILTER TABS
// =============================================================================

interface ApprovalFilterTabsProps {
  filterCap: 'all' | 'cap1' | 'cap2';
  onFilterChange: (filter: 'all' | 'cap1' | 'cap2') => void;
  counts: {
    total: number;
    cap1: number;
    cap2: number;
  };
}

export function ApprovalFilterTabs({ filterCap, onFilterChange, counts }: ApprovalFilterTabsProps) {
  return (
    <div className="flex items-center gap-3">
      <div 
        className={`px-4 py-2 rounded-lg flex items-center gap-2 cursor-pointer transition-all ${
          filterCap === 'all' ? 'bg-gray-200 ring-2 ring-gray-400' : 'bg-gray-100 hover:bg-gray-200'
        }`}
        onClick={() => onFilterChange('all')}
      >
        <span className="text-sm font-medium text-gray-700">Tất cả</span>
        <span className="px-2 py-0.5 bg-white rounded-full text-sm font-bold text-gray-900">
          {counts.total}
        </span>
      </div>
      <div 
        className={`px-4 py-2 rounded-lg flex items-center gap-2 cursor-pointer transition-all ${
          filterCap === 'cap1' ? 'bg-amber-200 ring-2 ring-amber-400' : 'bg-amber-100 hover:bg-amber-200'
        }`}
        onClick={() => onFilterChange('cap1')}
      >
        <span className="text-sm font-medium text-amber-700">Cấp 1</span>
        <span className="px-2 py-0.5 bg-white rounded-full text-sm font-bold text-amber-900">
          {counts.cap1}
        </span>
      </div>
      <div 
        className={`px-4 py-2 rounded-lg flex items-center gap-2 cursor-pointer transition-all ${
          filterCap === 'cap2' ? 'bg-indigo-200 ring-2 ring-indigo-400' : 'bg-indigo-100 hover:bg-indigo-200'
        }`}
        onClick={() => onFilterChange('cap2')}
      >
        <span className="text-sm font-medium text-indigo-700">Cấp 2</span>
        <span className="px-2 py-0.5 bg-white rounded-full text-sm font-bold text-indigo-900">
          {counts.cap2}
        </span>
      </div>
    </div>
  );
}
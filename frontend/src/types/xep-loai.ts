/**
 * src/types/xep-loai.ts
 * ======================
 * Type definitions cho module Xếp loại.
 *
 * Version: 3.4.0 - ADD: Tab Tạm tính (04/03/2026)
 */

import type { IUser } from '@/types/auth';

// =============================================================================
// ENUMS & CONSTANTS
// =============================================================================

export type TabId = 'cong-viec' | 'tieu-chi' | 'danh-gia-ld' | 'nghi-phep' | 'bao-cao' | 'tam-tinh' | 'quy';

/**
 * Cấp bậc vai trò - mapping từ ma_vai_tro
 * CCT = Chi cục trưởng
 * PCCT = Phó Chi cục trưởng
 * TDV = Trưởng đơn vị (Đội trưởng)
 * PDV = Phó đơn vị (Phó đội trưởng)
 * CC = Công chức
 */
export enum CapBacVaiTro {
  CONG_CHUC = 'CC',
  PHO_DOI_TRUONG = 'PDV',
  DOI_TRUONG = 'TDV',
  PHO_CHI_CUC_TRUONG = 'PCCT',
  CHI_CUC_TRUONG = 'CCT',
}

export interface ITabConfig {
  id: TabId;
  label: string;
  shortLabel: string;
  icon: string;
  description: string;
  allowedRoles: CapBacVaiTro[];
  approverRoles: CapBacVaiTro[];
}

export const TABS_CONFIG: ITabConfig[] = [
  {
    id: 'cong-viec',
    label: 'Duyệt công việc',
    shortLabel: 'Công việc',
    icon: '📋',
    description: 'Phê duyệt kê khai công việc của công chức',
    allowedRoles: [CapBacVaiTro.PHO_DOI_TRUONG, CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG],
    approverRoles: [CapBacVaiTro.PHO_DOI_TRUONG, CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG], // +CCT: duyệt SP Trưởng ĐV & Phó CCT (BR 8.1)
  },
  {
    id: 'tieu-chi',
    label: 'Duyệt tiêu chí',
    shortLabel: 'Tiêu chí',
    icon: '✅',
    description: 'Phê duyệt tiêu chí chung 2 cấp',
    allowedRoles: [CapBacVaiTro.PHO_DOI_TRUONG, CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG],
    approverRoles: [CapBacVaiTro.PHO_DOI_TRUONG, CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG],
  },
  {
    id: 'danh-gia-ld',
    label: 'Đánh giá lãnh đạo (d,đ,e)',
    shortLabel: 'd,đ,e',
    icon: '👔',
    description: 'ĐT duyệt d,đ,e cho Phó ĐT • CCT duyệt d,đ,e cho ĐT',
    allowedRoles: [CapBacVaiTro.PHO_DOI_TRUONG, CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG],
    approverRoles: [CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG], // ĐT duyệt Phó ĐT, CCT duyệt ĐT
  },
  {
    id: 'nghi-phep',
    label: 'Duyệt nghỉ phép',
    shortLabel: 'Nghỉ phép',
    icon: '🏖️',
    description: 'Phê duyệt đơn nghỉ phép 2 cấp',
    allowedRoles: [CapBacVaiTro.PHO_DOI_TRUONG, CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG],
    approverRoles: [CapBacVaiTro.PHO_DOI_TRUONG, CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG],
  },
  {
    id: 'bao-cao',
    label: 'Duyệt xếp loại tháng',
    shortLabel: 'Xếp loại',
    icon: '📈',
    description: 'Tổng hợp báo cáo xếp loại tháng',
    allowedRoles: [CapBacVaiTro.PHO_DOI_TRUONG, CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG],
    approverRoles: [CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG], // Chỉ ĐT và CCT duyệt
  },
  {
    id: 'tam-tinh',
    label: 'Tạm tính',
    shortLabel: 'Tạm tính',
    icon: '📊',
    description: 'Tổng hợp tạm tính điểm KPI công chức (bao gồm công việc chờ duyệt)',
    allowedRoles: [CapBacVaiTro.PHO_DOI_TRUONG, CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG],
    approverRoles: [], // Không có quyền phê duyệt, chỉ xem
  },
  {
    id: 'quy',
    label: 'Xếp loại quý',
    shortLabel: 'Quý',
    icon: '📊',
    description: 'Tổng hợp xếp loại quý (đọc từ báo cáo tháng đã duyệt)',
    allowedRoles: [CapBacVaiTro.PHO_DOI_TRUONG, CapBacVaiTro.DOI_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG],
    approverRoles: [], // Không có quyền phê duyệt, chỉ xem
  },
];

// =============================================================================
// INTERFACES
// =============================================================================

export interface ITabProps {
  thang: number;
  nam: number;
  canApprove: boolean;
  capBac: CapBacVaiTro;
  onPendingCountChange?: (count: number) => void;
}

export interface IPendingCounts {
  'cong-viec': number;
  'tieu-chi': number;
  'danh-gia-ld': number;
  'nghi-phep': number;
  'bao-cao': number;
  'tam-tinh': number;
  'quy': number;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Lấy cấp bậc vai trò từ user object (sử dụng IUser từ auth.ts)
 * 
 * User object có cấu trúc:
 * - vai_tro: { ma_vai_tro: 'CCT' | 'PCCT' | 'TDV' | 'PDV' | 'CC', ... } | null
 * - is_lanh_dao: boolean
 */
export function getCapBacFromUser(user: IUser | null): CapBacVaiTro {
  if (!user) return CapBacVaiTro.CONG_CHUC;
  // Lấy ma_vai_tro từ nested object vai_tro
  const maVaiTro = user.vai_tro?.ma_vai_tro;
  if (!maVaiTro) {
    // Fallback: check is_lanh_dao nếu không có vai_tro
    if (user.is_lanh_dao) {
      return CapBacVaiTro.DOI_TRUONG; // Default lãnh đạo = Đội trưởng
    }
    return CapBacVaiTro.CONG_CHUC;
  }
  // Map ma_vai_tro sang CapBacVaiTro
  switch (maVaiTro) {
    case 'CCT':
      return CapBacVaiTro.CHI_CUC_TRUONG;
    case 'PCCT':
      return CapBacVaiTro.PHO_CHI_CUC_TRUONG;
    case 'TDV':
      return CapBacVaiTro.DOI_TRUONG;
    case 'PDV':
      return CapBacVaiTro.PHO_DOI_TRUONG;
    case 'CC':
    default:
      return CapBacVaiTro.CONG_CHUC;
  }
}

/**
 * v1.1.0: Kiểm tra user có quyền xem toàn chi cục không.
 */
export function canViewAllUnits(user: IUser | null): boolean {
  if (!user) return false;
  if (user.is_system_admin) return true;
  if (user.can_view_all_units) return true;
  const maVaiTro = user.vai_tro?.ma_vai_tro;
  return ['CCT', 'PCCT'].includes(maVaiTro || '');
}

export function getAccessibleTabs(capBac: CapBacVaiTro, user?: IUser | null): ITabConfig[] {
  // v1.1.0: User có can_view_all_units (ví dụ TCCB) nhưng vai_tro không thuộc
  // nhóm lãnh đạo → cho xem tab báo cáo tháng + xếp loại quý (read-only).
  if (user && canViewAllUnits(user) && capBac === CapBacVaiTro.CONG_CHUC) {
    return TABS_CONFIG.filter((tab) => tab.id === 'bao-cao' || tab.id === 'quy');
  }
  return TABS_CONFIG.filter((tab) => tab.allowedRoles.includes(capBac));
}

export function canApproveInTab(capBac: CapBacVaiTro, tab: ITabConfig): boolean {
  return tab.approverRoles.includes(capBac);
}

export function getCapBacLabel(capBac: CapBacVaiTro): string {
  const labels: Record<CapBacVaiTro, string> = {
    [CapBacVaiTro.CONG_CHUC]: 'Công chức',
    [CapBacVaiTro.PHO_DOI_TRUONG]: 'Phó Đội trưởng',
    [CapBacVaiTro.DOI_TRUONG]: 'Đội trưởng',
    [CapBacVaiTro.PHO_CHI_CUC_TRUONG]: 'Phó Chi cục trưởng',
    [CapBacVaiTro.CHI_CUC_TRUONG]: 'Chi cục trưởng',
  };
  return labels[capBac] || 'Không xác định';
}

export function createDefaultPendingCounts(): IPendingCounts {
  return {
    'cong-viec': 0,
    'tieu-chi': 0,
    'danh-gia-ld': 0,
    'nghi-phep': 0,
    'bao-cao': 0,
    'tam-tinh': 0,
    'quy': 0,
  };
}
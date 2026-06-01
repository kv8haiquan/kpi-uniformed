/**
 * src/components/xep-loai/tabs/TabHdld.tsx
 * ========================================
 * Tab "Duyệt HĐLĐ" — cấp quản lý (TDV/PDV) duyệt đánh giá HĐLĐ 111 theo VB714.
 * Bọc lại Hdld111DuyetView để khớp ITabProps của trang Phê duyệt.
 */

'use client';

import { ITabProps } from '@/types/xep-loai';
import Hdld111DuyetView from '@/components/hdld/Hdld111DuyetView';

export default function TabHdld({ thang, nam, canApprove, onPendingCountChange }: ITabProps) {
  return (
    <Hdld111DuyetView
      thang={thang}
      nam={nam}
      canApprove={canApprove}
      onPendingCountChange={onPendingCountChange}
    />
  );
}

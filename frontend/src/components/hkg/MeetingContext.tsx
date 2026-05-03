/**
 * MeetingContext — share cuộc họp data + permission flags giữa layout và 4 tab.
 *
 * G4-fix-7 (01/05/2026): thêm `canEdit` để tabs ẨN HOÀN TOÀN organizer-only
 * blocks cho CBCC thường (thay vì chỉ disable). CBCC vẫn xem được tài liệu,
 * điểm danh "Tôi có mặt", cập nhật tiến độ nhiệm vụ của mình.
 */

'use client';

import { createContext, useContext } from 'react';
import type { ICuocHop } from '@/types/hkg';

export interface IMeetingCtx {
  ch: ICuocHop | null;
  isCancelled: boolean;
  isLocked: boolean; // HUY hoặc HOAN_THANH — không cho mutate
  /**
   * User hiện tại có quyền tổ chức/sửa cuộc họp không.
   * = chu_toa | thu_ky của họp này, HOẶC admin/SUPER_ADMIN, HOẶC TRUONG_CNTT/CHANH_VP.
   */
  canEdit: boolean;
  /** UUID của user hiện tại — convenience cho tabs check `kl.nguoi_phu_trach_id === currentUserId`. */
  currentUserId: string | null;
  refresh: () => Promise<void>;
}

const MeetingContext = createContext<IMeetingCtx>({
  ch: null,
  isCancelled: false,
  isLocked: false,
  canEdit: false,
  currentUserId: null,
  refresh: async () => {},
});

export const MeetingProvider = MeetingContext.Provider;

export function useMeeting(): IMeetingCtx {
  return useContext(MeetingContext);
}

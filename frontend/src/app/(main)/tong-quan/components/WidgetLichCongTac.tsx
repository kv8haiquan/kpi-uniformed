/**
 * WidgetLichCongTac.tsx
 * ======================
 * Widget tóm tắt Lịch công tác — số sự kiện hôm nay, ngày mai, tuần, tháng.
 *
 * Tự gọi API riêng thay vì nhận qua props như các widget khác, vì chỉ số này
 * lấy từ backend HKG (port 8006) chứ không nằm trong tổng hợp của portal.
 *
 * Đặt NGAY TRÊN widget Họp Không Giấy trong lưới, tương ứng vị trí ở sidebar.
 */

'use client';

import { useEffect, useState } from 'react';

import DashboardWidget from './DashboardWidget';
import { lichCongTacApi } from '@/services/lich-cong-tac';
import type { IThongKeLich } from '@/types/lich-cong-tac';

export default function WidgetLichCongTac() {
  const [dl, setDl] = useState<IThongKeLich | null>(null);
  const [dangTai, setDangTai] = useState(true);

  useEffect(() => {
    let huy = false;
    lichCongTacApi
      .thongKe()
      .then((d) => {
        if (!huy) setDl(d);
      })
      .catch(() => {
        // Widget không chặn cả trang tổng quan — im lặng rồi hiện bản rút gọn.
      })
      .finally(() => {
        if (!huy) setDangTai(false);
      });
    return () => {
      huy = true;
    };
  }, []);

  return (
    <DashboardWidget
      title="Lịch công tác"
      icon="📅"
      href="/lich-cong-tac"
      hrefLabel="Xem lịch"
      loading={dangTai}
      colorClass="bg-sky-100"
    >
      {dl ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <div className="text-center bg-sky-50 rounded-lg py-2 px-1">
              <div className="text-xl font-bold text-sky-700">{dl.hom_nay}</div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">
                Hôm nay
              </div>
            </div>
            <div className="text-center bg-blue-50 rounded-lg py-2 px-1">
              <div className="text-xl font-bold text-blue-700">{dl.ngay_mai}</div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">
                Ngày mai
              </div>
            </div>
            <div className="text-center bg-emerald-50 rounded-lg py-2 px-1">
              <div className="text-xl font-bold text-emerald-700">
                {dl.trong_tuan}
              </div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">
                Trong tuần
              </div>
            </div>
            <div className="text-center bg-amber-50 rounded-lg py-2 px-1">
              <div className="text-xl font-bold text-amber-700">
                {dl.trong_thang}
              </div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">
                Trong tháng
              </div>
            </div>
          </div>
        </div>
      ) : (
        <p className="text-sm text-gray-500">
          Xem chương trình công tác của Chi cục.
        </p>
      )}
    </DashboardWidget>
  );
}

/**
 * WidgetLMSPheDuyet.tsx
 * ======================
 * Widget cảnh báo yêu cầu phê duyệt đăng ký khóa học (LMS).
 * Chỉ render khi `data.cho_phe_duyet > 0` — luôn hiển thị nổi bật để giảng viên/QT
 * không bỏ sót yêu cầu.
 *
 * Backend `/api/v1/lms/dang-ky/cho-phe-duyet` đã lọc theo quyền:
 *  - GIANG_VIEN: chỉ thấy yêu cầu cho khóa học của mình
 *  - QT_DAO_TAO / SUPER_ADMIN: thấy tất cả
 *  - Lãnh đạo đơn vị: thấy CBCC trong đơn vị
 *  - User thường: 0
 *
 * Danh sách chi tiết được hiển thị bên trong tab "Học viên" của từng khóa học.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import axios from 'axios';

interface ChoPheDuyetItem {
  dang_ky_id: string;
  ho_ten?: string;
  khoa_hoc_ten?: string;
  khoa_hoc_id?: string;
  ngay_dang_ky?: string;
}

const TOKEN_KEY = 'kpi_access_token';

function authHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const t = localStorage.getItem(TOKEN_KEY);
  return t ? { Authorization: `Bearer ${t}` } : {};
}

function timeAgo(dateStr?: string): string {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Vừa xong';
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} ngày trước`;
  return new Date(dateStr).toLocaleDateString('vi-VN');
}

interface WidgetLMSPheDuyetProps {
  /** Số yêu cầu chờ phê duyệt (lấy từ dashboard fetch chính). */
  count: number;
}

export default function WidgetLMSPheDuyet({ count }: WidgetLMSPheDuyetProps) {
  const [items, setItems] = useState<ChoPheDuyetItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (count <= 0) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const res = await axios.get('/api/v1/lms/dang-ky/cho-phe-duyet', {
          params: { page: 1, page_size: 5 },
          headers: authHeaders(),
          timeout: 5000,
        });
        if (!cancelled) {
          setItems(res.data?.data ?? []);
        }
      } catch {
        if (!cancelled) setItems([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [count]);

  if (count <= 0) return null;

  return (
    <div className="md:col-span-2 lg:col-span-3 bg-amber-50 border border-amber-300 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-amber-200 bg-amber-100/60">
        <div className="flex items-center gap-2">
          <span className="bg-amber-200 rounded-lg w-8 h-8 flex items-center justify-center text-base">
            ⏳
          </span>
          <div>
            <div className="font-semibold text-amber-900 text-sm">
              {count} yêu cầu phê duyệt đăng ký khóa học
            </div>
            <div className="text-xs text-amber-700">
              Học viên đang chờ bạn duyệt — vui lòng kiểm tra sớm
            </div>
          </div>
        </div>
        <span className="inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-full bg-red-600 text-white text-xs font-semibold">
          {count}
        </span>
      </div>

      {/* Body — preview tối đa 5 yêu cầu mới nhất */}
      <div className="p-3">
        {loading ? (
          <div className="text-xs text-amber-700 text-center py-2">Đang tải danh sách...</div>
        ) : items.length === 0 ? (
          <div className="text-xs text-amber-700 text-center py-2">
            Mở danh sách để xem chi tiết
          </div>
        ) : (
          <ul className="divide-y divide-amber-200">
            {items.map((it) => (
              <li key={it.dang_ky_id}>
                <Link
                  href={`/dao-tao/khoa-hoc/${it.khoa_hoc_id}?tab=hoc-vien`}
                  className="flex items-center gap-3 py-2 px-1 hover:bg-amber-100/50 rounded transition-colors"
                >
                  <span className="text-base shrink-0">👤</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {it.ho_ten || 'Học viên'}
                    </div>
                    <div className="text-xs text-gray-600 truncate">
                      đăng ký <span className="font-medium">{it.khoa_hoc_ten || 'khóa học'}</span>
                    </div>
                  </div>
                  <span className="text-xs text-amber-700 shrink-0">
                    {timeAgo(it.ngay_dang_ky)}
                  </span>
                  <span className="text-amber-700 text-xs shrink-0">→</span>
                </Link>
              </li>
            ))}
          </ul>
        )}

        {count > items.length && items.length > 0 && (
          <div className="text-center mt-2">
            <span className="text-xs text-amber-700">
              ... và {count - items.length} yêu cầu khác
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

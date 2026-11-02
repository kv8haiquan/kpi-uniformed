/**
 * src/app/(main)/so-tay/page.tsx
 * ================================
 * Sổ tay số — danh sách các sổ do phòng nghiệp vụ biên soạn
 * (Sổ tay kiểm tra nội bộ, Sổ tra cứu lỗi hải quan). Mở cho mọi công chức.
 * Xem trực tuyến; được tải nguyên tệp về máy bằng nút trong sổ (02/11/2026).
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { BookMarked, ClipboardCheck } from 'lucide-react';
import { isAxiosError } from 'axios';
import { soTayApi } from '@/services/common';
import type { ISoTayItem } from '@/types/common';

const BIEU_TUONG: Record<string, typeof BookMarked> = {
  'kiem-tra-noi-bo': ClipboardCheck,
  'tra-cuu-loi': BookMarked,
};

function dinhDangDungLuong(byte: number | null): string {
  if (!byte) return '';
  return byte >= 1024 * 1024
    ? `${(byte / 1024 / 1024).toFixed(1)} MB`
    : `${Math.round(byte / 1024)} KB`;
}

export default function SoTayPage() {
  const [items, setItems] = useState<ISoTayItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    soTayApi
      .danhSach()
      .then((res) => setItems(res.data.data || []))
      .catch((err: unknown) =>
        setError(
          (isAxiosError(err) && err.response?.data?.error?.message) ||
            'Không thể tải danh sách sổ tay'
        )
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Sổ tay số</h1>
          <p className="text-sm text-gray-500 mt-1">
            Tài liệu nghiệp vụ sử dụng nội bộ — xem trực tuyến hoặc tải về máy bằng nút tải trong sổ, không đăng tải công khai
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 text-center">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {items.map((item) => {
              const Icon = BIEU_TUONG[item.ma] || BookMarked;
              const the = (
                <div
                  className={`h-full bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex gap-4 transition ${
                    item.co_san ? 'hover:border-blue-400 hover:shadow-md' : 'opacity-60'
                  }`}
                >
                  <div className="shrink-0 w-12 h-12 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="min-w-0">
                    <h2 className="font-semibold text-gray-900">{item.tieu_de}</h2>
                    <p className="text-sm text-gray-600 mt-1">{item.mo_ta}</p>
                    <p className="text-xs text-gray-400 mt-3">
                      {item.co_san
                        ? [
                            item.phien_ban && `Phiên bản ${item.phien_ban}`,
                            item.ngay_cap_nhat && `cập nhật ${item.ngay_cap_nhat}`,
                            dinhDangDungLuong(item.dung_luong),
                          ]
                            .filter(Boolean)
                            .join(' · ')
                        : 'Chưa đăng tải'}
                    </p>
                  </div>
                </div>
              );
              return item.co_san ? (
                <Link key={item.ma} href={`/so-tay/${item.ma}`}>
                  {the}
                </Link>
              ) : (
                <div key={item.ma}>{the}</div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

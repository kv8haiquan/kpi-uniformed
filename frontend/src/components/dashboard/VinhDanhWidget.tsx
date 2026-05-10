/**
 * src/components/dashboard/VinhDanhWidget.tsx
 * ============================================
 * Widget hiển thị công chức tiêu biểu tháng hiện tại trên Dashboard chính.
 *
 * - Tự ẩn nếu tháng hiện tại không có bản ghi PUBLISHED.
 * - Click "Xem chi tiết" mở modal đầy đủ lý do + lời tuyên dương.
 *
 * Phiên bản: 1.0 (10/05/2026)
 */

'use client';

import { useEffect, useState } from 'react';
import { vinhDanhApi } from '@/services/portal';
import type { IVinhDanhThang } from '@/types/vinh-danh';

const PORTAL_BASE =
  process.env.NEXT_PUBLIC_PORTAL_API_URL?.replace(/\/api\/v1$/, '') || '';

function buildAnhUrl(path?: string | null): string | null {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return `${PORTAL_BASE}${path}`;
}

export default function VinhDanhWidget() {
  const [vinhDanh, setVinhDanh] = useState<IVinhDanhThang | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDetail, setShowDetail] = useState(false);

  useEffect(() => {
    let cancelled = false;
    vinhDanhApi
      .current()
      .then((res) => {
        if (cancelled) return;
        setVinhDanh(res.data?.data ?? null);
      })
      .catch(() => {
        if (!cancelled) setVinhDanh(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return null;
  if (!vinhDanh) return null;

  const anhUrl = buildAnhUrl(vinhDanh.anh_chan_dung);

  return (
    <>
      <div className="mb-8">
        <div className="bg-gradient-to-r from-amber-50 via-yellow-50 to-orange-50 border border-amber-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-amber-200 bg-gradient-to-r from-amber-100 to-yellow-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl">🏆</span>
              <h3 className="font-semibold text-amber-900">
                Công chức tiêu biểu tháng {vinhDanh.thang}/{vinhDanh.nam}
              </h3>
            </div>
            <span className="text-xs text-amber-700 bg-white/70 px-2 py-1 rounded-full font-medium">
              Vinh danh
            </span>
          </div>

          <div className="p-5 flex flex-col sm:flex-row gap-5 items-center sm:items-start">
            <div className="flex-shrink-0">
              {anhUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={anhUrl}
                  alt={vinhDanh.cong_chuc?.ho_ten || 'Ảnh chân dung'}
                  className="w-28 h-28 rounded-full object-cover border-4 border-amber-300 shadow-md"
                />
              ) : (
                <div className="w-28 h-28 rounded-full bg-amber-200 border-4 border-amber-300 shadow-md flex items-center justify-center text-4xl">
                  👤
                </div>
              )}
            </div>

            <div className="flex-1 text-center sm:text-left">
              <h4 className="text-lg font-bold text-gray-900">
                {vinhDanh.cong_chuc?.ho_ten || '—'}
              </h4>
              {vinhDanh.cong_chuc?.chuc_vu && (
                <p className="text-sm text-gray-600 mt-0.5">
                  {vinhDanh.cong_chuc.chuc_vu}
                </p>
              )}
              <p className="text-base font-medium text-amber-900 mt-2">
                {vinhDanh.tieu_de}
              </p>
              {vinhDanh.loi_tuyen_duong && (
                <p className="text-sm text-gray-700 italic mt-2 line-clamp-2">
                  &ldquo;{vinhDanh.loi_tuyen_duong}&rdquo;
                </p>
              )}
              <button
                type="button"
                onClick={() => setShowDetail(true)}
                className="mt-3 text-sm text-amber-700 hover:text-amber-900 font-medium underline-offset-2 hover:underline"
              >
                Xem chi tiết →
              </button>
            </div>
          </div>
        </div>
      </div>

      {showDetail && (
        <div
          className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
          onClick={() => setShowDetail(false)}
        >
          <div
            className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-amber-50 to-orange-50 flex items-center justify-between sticky top-0">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🏆</span>
                <h3 className="font-semibold text-gray-900">
                  Vinh danh tháng {vinhDanh.thang}/{vinhDanh.nam}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowDetail(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <div className="p-6">
              <div className="flex flex-col sm:flex-row gap-5 mb-5">
                {anhUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={anhUrl}
                    alt={vinhDanh.cong_chuc?.ho_ten || ''}
                    className="w-32 h-32 rounded-full object-cover border-4 border-amber-300 shadow-md mx-auto sm:mx-0"
                  />
                ) : (
                  <div className="w-32 h-32 rounded-full bg-amber-200 border-4 border-amber-300 shadow-md flex items-center justify-center text-5xl mx-auto sm:mx-0">
                    👤
                  </div>
                )}
                <div className="flex-1 text-center sm:text-left">
                  <h4 className="text-xl font-bold text-gray-900">
                    {vinhDanh.cong_chuc?.ho_ten || '—'}
                  </h4>
                  {vinhDanh.cong_chuc?.ma_cc && (
                    <p className="text-sm text-gray-500 mt-0.5">
                      Mã: {vinhDanh.cong_chuc.ma_cc}
                    </p>
                  )}
                  {vinhDanh.cong_chuc?.chuc_vu && (
                    <p className="text-sm text-gray-600 mt-1">
                      {vinhDanh.cong_chuc.chuc_vu}
                    </p>
                  )}
                  <p className="text-base font-semibold text-amber-900 mt-3">
                    {vinhDanh.tieu_de}
                  </p>
                </div>
              </div>

              {vinhDanh.loi_tuyen_duong && (
                <div className="mb-4 p-4 bg-amber-50 border-l-4 border-amber-400 rounded">
                  <p className="text-sm font-medium text-amber-900 mb-1">
                    Lời tuyên dương
                  </p>
                  <p className="text-gray-800 italic">
                    &ldquo;{vinhDanh.loi_tuyen_duong}&rdquo;
                  </p>
                </div>
              )}

              <div className="mb-2">
                <p className="text-sm font-medium text-gray-700 mb-2">
                  Lý do vinh danh
                </p>
                <div className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                  {vinhDanh.ly_do}
                </div>
              </div>

              {vinhDanh.ngay_cong_bo && (
                <p className="text-xs text-gray-500 mt-4">
                  Công bố:{' '}
                  {new Date(vinhDanh.ngay_cong_bo).toLocaleDateString('vi-VN', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                  })}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

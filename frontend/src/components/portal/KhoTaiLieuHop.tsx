/**
 * components/portal/KhoTaiLieuHop.tsx
 * ====================================
 * Duyệt kho tài liệu họp ngay trong Thư viện tài liệu.
 *
 * Trước màn hình này, tài liệu họp chỉ mở được khi biết trước nó thuộc cuộc
 * họp nào — muốn tìm một văn bản mà quên mất họp hôm nào thì chịu, phải mở
 * Google Drive. Đây là chỗ duy nhất xem được cả kho.
 *
 * KHÔNG sao chép dữ liệu sang `portal.tai_lieu`: đọc thẳng `meeting.tai_lieu`
 * qua meeting_service. Sao chép sẽ nhân đôi 1,6 GB, lệch nhau khi có tài liệu
 * mới, và nguy hiểm nhất là bỏ qua phân quyền G5.4 vì portal có mô hình quyền
 * riêng. Máy chủ đã lọc theo quyền trước khi trả về.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  CalendarDays,
  Download,
  ExternalLink,
  Eye,
  FileText,
  Loader2,
  Lock,
} from 'lucide-react';

import { taiLieuApi } from '@/services/hkg';
import { errApi } from '@/lib/hkg-error';
import { coDaiFile } from '@/lib/tai-lieu-upload';
import type { ITaiLieuKhoItem, NguonKhoTaiLieu } from '@/types/hkg';

const SO_DONG = 24;

interface Props {
  /** Bỏ trống là xem cả hai nguồn. */
  nguon?: NguonKhoTaiLieu;
  /** Từ khoá do trang cha truyền xuống (ô tìm kiếm dùng chung). */
  timKiem?: string;
}

function ngayVN(s: string | null): string {
  if (!s) return '—';
  const [y, m, d] = s.split('-');
  return `${d}/${m}/${y}`;
}

export default function KhoTaiLieuHop({ nguon, timKiem }: Props) {
  const [ds, setDs] = useState<ITaiLieuKhoItem[] | null>(null);
  const [conNua, setConNua] = useState(false);
  const [trang, setTrang] = useState(1);
  const [loi, setLoi] = useState<string | null>(null);

  // Đổi bộ lọc thì phải về trang 1, nếu không sẽ hiện "trang 3" của một tập
  // kết quả chỉ có 1 trang và người dùng thấy màn hình trống.
  useEffect(() => {
    setTrang(1);
  }, [nguon, timKiem]);

  const tai = useCallback(async () => {
    setDs(null);
    setLoi(null);
    try {
      const r = await taiLieuApi.kho({ nguon, timKiem, trang, soDong: SO_DONG });
      setDs(r.data.data);
      setConNua(r.data.pagination.con_nua);
    } catch (e) {
      setDs([]);
      setLoi(errApi(e, 'Không tải được kho tài liệu'));
    }
  }, [nguon, timKiem, trang]);

  useEffect(() => {
    void tai();
  }, [tai]);

  const moFile = async (id: string, taiVe: boolean) => {
    setLoi(null);
    try {
      const r = taiVe
        ? await taiLieuApi.taiUrl(id)
        : await taiLieuApi.xemUrl(id);
      window.open(r.url, '_blank', 'noopener');
    } catch (e) {
      setLoi(errApi(e, 'Không mở được tài liệu'));
    }
  };

  if (ds === null) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white py-16 text-center">
        <Loader2 className="mx-auto h-6 w-6 animate-spin text-gray-400" />
        <p className="mt-2 text-sm text-gray-500">Đang tải kho tài liệu…</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {loi && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {loi}
        </p>
      )}

      {ds.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-white py-16 text-center">
          <FileText className="mb-3 h-9 w-9 text-gray-300" />
          <p className="text-sm font-medium text-gray-600">
            {timKiem
              ? `Không có tài liệu nào khớp “${timKiem}”`
              : 'Chưa có tài liệu nào'}
          </p>
          <p className="mt-1 text-xs text-gray-400">
            Chỉ hiện tài liệu của những cuộc họp bạn được xem.
          </p>
        </div>
      ) : (
        <ul className="divide-y divide-gray-100 overflow-hidden rounded-xl border border-gray-200 bg-white">
          {ds.map((t) => (
            <li key={t.id} className="flex items-start gap-3 px-4 py-3">
              <FileText className="mt-0.5 h-5 w-5 shrink-0 text-gray-400" />

              {/* min-w-0 là bắt buộc: không có nó thì tên file dài đẩy cả
                  hàng rộng ra ngoài màn hình thay vì tự xuống dòng. */}
              <div className="min-w-0 flex-1">
                <p
                  className="break-words text-sm font-medium text-gray-900"
                  title={t.ten_tai_lieu}
                >
                  {t.ten_tai_lieu}
                </p>

                <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
                  <span className="inline-flex items-center gap-1">
                    <CalendarDays className="h-3.5 w-3.5" />
                    {ngayVN(t.ngay_hop)}
                  </span>
                  <span className="uppercase">{t.extension || '—'}</span>
                  <span>{coDaiFile(t.file_size)}</span>
                  {t.mo_ta && <span>· {t.mo_ta}</span>}
                  {t.phan_quyen !== 'CONG_KHAI' && (
                    <span className="inline-flex items-center gap-1 rounded bg-amber-100 px-1.5 py-0.5 text-amber-900">
                      <Lock className="h-3 w-3" />
                      Hạn chế
                    </span>
                  )}
                </div>

                {/* Cuộc họp mà file thuộc về — thứ khiến kho này tra cứu được */}
                <Link
                  href={t.duong_dan_cuoc_hop}
                  className="mt-1 inline-flex max-w-full items-center gap-1 text-xs text-blue-700 hover:underline"
                  title={t.tieu_de}
                >
                  <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 font-mono text-gray-600">
                    {t.ma_lich || (t.nguon === 'HKG' ? 'HKG' : 'Lịch')}
                  </span>
                  <span className="truncate">{t.tieu_de}</span>
                  <ExternalLink className="h-3 w-3 shrink-0" />
                </Link>
              </div>

              <div className="flex shrink-0 items-center gap-1">
                <button
                  type="button"
                  title="Xem"
                  onClick={() => void moFile(t.id, false)}
                  className="rounded p-1.5 text-gray-600 hover:bg-gray-100"
                >
                  <Eye className="h-4 w-4" />
                </button>
                {t.cho_phep_tai && (
                  <button
                    type="button"
                    title="Tải về"
                    onClick={() => void moFile(t.id, true)}
                    className="rounded p-1.5 text-gray-600 hover:bg-gray-100"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {(trang > 1 || conNua) && (
        <div className="flex items-center justify-center gap-2">
          <button
            type="button"
            disabled={trang <= 1}
            onClick={() => setTrang((p) => p - 1)}
            className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm transition-colors hover:bg-gray-50 disabled:opacity-40"
          >
            ← Trước
          </button>
          <span className="text-sm text-gray-500">Trang {trang}</span>
          <button
            type="button"
            disabled={!conNua}
            onClick={() => setTrang((p) => p + 1)}
            className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm transition-colors hover:bg-gray-50 disabled:opacity-40"
          >
            Sau →
          </button>
        </div>
      )}
    </div>
  );
}

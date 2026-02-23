/**
 * src/app/(main)/phap-luat/chua-doc/page.tsx
 * ==============================================
 * Danh sách văn bản chưa đọc / cần xác nhận.
 *
 * - Gọi getVanBanChuaDoc (bat_buoc_doc=TRUE, chưa đọc/xác nhận)
 * - Sắp xếp: KHAN/RAT_KHAN → QUAN_TRONG → BINH_THUONG, rồi theo hạn xác nhận
 * - Highlight VB sắp hết hạn (< 3 ngày) và quá hạn
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { legalService } from '@/services/legal';
import type { IVanBanListItem, IPagination } from '@/types/legal';

// =============================================================================
// HELPERS
// =============================================================================

/** Thứ tự sắp xếp theo mức độ */
const MUC_DO_ORDER: Record<string, number> = {
  RAT_KHAN: 0, KHAN: 1, QUAN_TRONG: 2, BINH_THUONG: 3,
};

// Tính một lần khi module load — KHÔNG gọi Date.now() trong render (React Compiler rule)
const _MODULE_NOW = Date.now();

/**
 * Tính ngày còn lại đến hạn xác nhận.
 * Nhận `now` làm parameter để dễ test và tránh gọi Date.now() trực tiếp trong render.
 */
function tinhNgayConLai(hanXacNhan: string | null, now: number): number | null {
  if (!hanXacNhan || now === 0) return null;
  return Math.ceil((new Date(hanXacNhan).getTime() - now) / (1000 * 60 * 60 * 24));
}

// =============================================================================
// VB ROW trong danh sách chưa đọc
// =============================================================================
function VanBanChuaDocRow({ vb, now }: { vb: IVanBanListItem; now: number }) {
  const ngayConLai = tinhNgayConLai(vb.han_xac_nhan, now);
  const quaHan = ngayConLai !== null && ngayConLai < 0;
  const sapHetHan = ngayConLai !== null && ngayConLai >= 0 && ngayConLai <= 3;

  const rowCls = quaHan
    ? 'border-red-300 bg-red-50'
    : sapHetHan
    ? 'border-orange-300 bg-orange-50'
    : 'border-gray-200 bg-white';

  const mucDoMap: Record<string, { label: string; cls: string }> = {
    RAT_KHAN:    { label: '🔴 Rất khẩn',   cls: 'bg-red-100 text-red-700' },
    KHAN:        { label: '🟠 Khẩn',        cls: 'bg-orange-100 text-orange-700' },
    QUAN_TRONG:  { label: '🟡 Quan trọng',  cls: 'bg-yellow-100 text-yellow-700' },
    BINH_THUONG: { label: 'Bình thường',    cls: 'bg-gray-100 text-gray-500' },
  };
  const mdc = mucDoMap[vb.muc_do] ?? { label: vb.muc_do, cls: 'bg-gray-100 text-gray-500' };

  return (
    <div className={`rounded-xl border p-4 transition-all hover:shadow-sm ${rowCls}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* Số hiệu + mức độ */}
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs font-mono font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
              {vb.so_hieu}
            </span>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${mdc.cls}`}>
              {mdc.label}
            </span>
            {!vb.da_doc && (
              <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                📄 Chưa đọc
              </span>
            )}
            {vb.da_doc && !vb.da_xac_nhan && (
              <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">
                👁 Đã đọc, chưa xác nhận
              </span>
            )}
          </div>

          {/* Trích yếu */}
          <p className="text-sm font-medium text-gray-900 line-clamp-2 mb-2">{vb.trich_yeu}</p>

          {/* Cơ quan + ngày */}
          <p className="text-xs text-gray-400">
            🏛 {vb.co_quan_ban_hanh} •{' '}
            📅 {new Date(vb.ngay_ban_hanh).toLocaleDateString('vi-VN')}
          </p>
        </div>

        {/* Bên phải: hạn + nút */}
        <div className="shrink-0 text-right flex flex-col items-end gap-2">
          {vb.han_xac_nhan && (
            <div className={`text-xs font-semibold px-2 py-1 rounded-lg ${
              quaHan    ? 'bg-red-200 text-red-800' :
              sapHetHan ? 'bg-orange-200 text-orange-800' :
              'bg-gray-100 text-gray-600'
            }`}>
              {quaHan
                ? `⚠ Quá hạn ${Math.abs(ngayConLai!)}d`
                : sapHetHan
                ? `⏰ Còn ${ngayConLai}d`
                : `🗓 Hạn ${new Date(vb.han_xac_nhan).toLocaleDateString('vi-VN')}`}
            </div>
          )}
          <Link
            href={`/phap-luat/${vb.id}`}
            className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-medium transition-colors"
          >
            Đọc & Xác nhận →
          </Link>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN PAGE
// =============================================================================
export default function ChuaDocPage() {
  const [vanBans, setVanBans] = useState<IVanBanListItem[]>([]);
  const [pagination, setPagination] = useState<IPagination>({
    page: 1, page_size: 20, total_items: 0, total_pages: 1,
  });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await legalService.getVanBanChuaDoc({ page, page_size: 20 });
        // Kiểm tra success field theo SHARED_CODING_STANDARDS §5.1
        if (res.data?.success) {
          const raw: IVanBanListItem[] = res.data.data ?? [];

          // Sắp xếp: theo mức độ → hạn xác nhận (quá hạn lên trước)
          // Dùng _MODULE_NOW (module-level constant) — không cần Date.now() trong useEffect
          const sorted = [...raw].sort((a, b) => {
            const mA = MUC_DO_ORDER[a.muc_do] ?? 99;
            const mB = MUC_DO_ORDER[b.muc_do] ?? 99;
            if (mA !== mB) return mA - mB;
            const hA = tinhNgayConLai(a.han_xac_nhan, _MODULE_NOW) ?? 999;
            const hB = tinhNgayConLai(b.han_xac_nhan, _MODULE_NOW) ?? 999;
            return hA - hB;
          });

          setVanBans(sorted);
          setPagination(res.data.pagination ?? { page, page_size: 20, total_items: raw.length, total_pages: 1 });
        } else {
          const msg = res.data?.error?.message || 'Không thể tải danh sách văn bản chưa đọc.';
          console.warn('[Legal] getVanBanChuaDoc:', res.data?.error?.code, msg);
          setError(msg);
        }
      } catch {
        setError('Không thể tải danh sách. Vui lòng thử lại.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [page]);

  // Nhóm theo trạng thái (dùng _MODULE_NOW — module-level constant, an toàn với React Compiler)
  const quaHan = vanBans.filter(vb => {
    const d = tinhNgayConLai(vb.han_xac_nhan, _MODULE_NOW);
    return d !== null && d < 0;
  });
  const sapHetHan = vanBans.filter(vb => {
    const d = tinhNgayConLai(vb.han_xac_nhan, _MODULE_NOW);
    return d !== null && d >= 0 && d <= 3;
  });
  const conLai = vanBans.filter(vb => {
    const d = tinhNgayConLai(vb.han_xac_nhan, _MODULE_NOW);
    return d === null || d > 3;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <nav className="flex items-center gap-2 text-sm text-gray-400 mb-1">
              <Link href="/phap-luat" className="hover:text-purple-600 transition-colors">⚖️ Pháp luật</Link>
              <span>›</span>
              <span className="text-gray-700">Cần xác nhận</span>
            </nav>
            <h1 className="text-2xl font-bold text-gray-900">📬 Văn bản cần xác nhận</h1>
            <p className="text-sm text-gray-500 mt-1">
              Văn bản bắt buộc đọc mà bạn chưa xác nhận hoàn thành
            </p>
          </div>
          {!loading && (
            <div className="text-right">
              <div className="text-3xl font-bold text-red-600">{pagination.total_items}</div>
              <div className="text-xs text-gray-400">VB cần xác nhận</div>
            </div>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm mb-4">
            {error}
          </div>
        )}

        {/* Empty */}
        {!loading && !error && vanBans.length === 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <span className="block text-5xl mb-4">🎉</span>
            <p className="font-medium text-gray-700">Tuyệt vời! Bạn đã xác nhận tất cả văn bản.</p>
            <p className="text-sm text-gray-400 mt-1">Không có văn bản nào cần xác nhận</p>
            <Link
              href="/phap-luat"
              className="mt-4 inline-block px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition-colors"
            >
              ← Về danh sách
            </Link>
          </div>
        )}

        {/* Nhóm Quá hạn */}
        {quaHan.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-bold text-red-700 uppercase tracking-wide mb-3 flex items-center gap-2">
              <span>⚠</span> Quá hạn ({quaHan.length})
            </h2>
            <div className="space-y-3">
              {quaHan.map(vb => <VanBanChuaDocRow key={vb.id} vb={vb} now={_MODULE_NOW} />)}
            </div>
          </div>
        )}

        {/* Nhóm Sắp hết hạn (< 3 ngày) */}
        {sapHetHan.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-bold text-orange-700 uppercase tracking-wide mb-3 flex items-center gap-2">
              <span>⏰</span> Sắp hết hạn ({sapHetHan.length})
            </h2>
            <div className="space-y-3">
              {sapHetHan.map(vb => <VanBanChuaDocRow key={vb.id} vb={vb} now={_MODULE_NOW} />)}
            </div>
          </div>
        )}

        {/* Nhóm Còn lại */}
        {conLai.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
              Còn hạn ({conLai.length})
            </h2>
            <div className="space-y-3">
              {conLai.map(vb => <VanBanChuaDocRow key={vb.id} vb={vb} now={_MODULE_NOW} />)}
            </div>
          </div>
        )}

        {/* Phân trang */}
        {pagination.total_pages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50"
            >
              ← Trước
            </button>
            <span className="text-sm text-gray-500">
              Trang {page}/{pagination.total_pages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(pagination.total_pages, p + 1))}
              disabled={page >= pagination.total_pages}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50"
            >
              Sau →
            </button>
          </div>
        )}

      </div>
    </div>
  );
}

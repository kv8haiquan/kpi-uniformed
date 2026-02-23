/**
 * src/components/legal/VanBanCard.tsx
 * =====================================
 * Card hiển thị 1 văn bản trong danh sách.
 *
 * Badges:
 *   Mức độ: RAT_KHAN=đỏ, KHAN=cam, QUAN_TRONG=vàng, BINH_THUONG=xám
 *   Hiệu lực: CON_HIEU_LUC=xanh, HET_HIEU_LUC=xám, CHUA_HIEU_LUC=tím
 *   Đọc: Chưa đọc / Đã đọc / Đã xác nhận
 *
 * Highlight border-left theo mức độ.
 * Hiển thị cảnh báo hạn xác nhận.
 */

'use client';

import Link from 'next/link';
import type { IVanBanListItem } from '@/types/legal';

// Tính một lần khi module load — KHÔNG gọi trong render để tránh vi phạm React Compiler
// (Date.now() là hàm impure nếu gọi mỗi lần render)
const _MODULE_NOW = Date.now();

// =============================================================================
// BADGES
// =============================================================================

function MucDoBadge({ mucDo }: { mucDo: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    RAT_KHAN: { label: '🔴 Rất khẩn', cls: 'bg-red-100 text-red-700 border-red-200' },
    KHAN:     { label: '🟠 Khẩn',     cls: 'bg-orange-100 text-orange-700 border-orange-200' },
    QUAN_TRONG:  { label: '🟡 Quan trọng', cls: 'bg-yellow-100 text-yellow-700 border-yellow-200' },
    BINH_THUONG: { label: 'Bình thường',   cls: 'bg-gray-100 text-gray-500 border-gray-200' },
  };
  const info = map[mucDo] ?? { label: mucDo, cls: 'bg-gray-100 text-gray-500 border-gray-200' };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${info.cls}`}>
      {info.label}
    </span>
  );
}

function HieuLucBadge({ trangThai }: { trangThai: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    CON_HIEU_LUC:  { label: '✅ Còn hiệu lực',    cls: 'bg-green-100 text-green-700' },
    HET_HIEU_LUC:  { label: '⛔ Hết hiệu lực',    cls: 'bg-gray-100 text-gray-400' },
    CHUA_HIEU_LUC: { label: '⏳ Chưa hiệu lực',   cls: 'bg-blue-100 text-blue-600' },
  };
  const info = map[trangThai] ?? { label: trangThai, cls: 'bg-gray-100 text-gray-400' };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${info.cls}`}>
      {info.label}
    </span>
  );
}

function DocBadge({ daDoc, daXacNhan }: { daDoc: boolean; daXacNhan: boolean }) {
  if (daXacNhan) return (
    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-green-100 text-green-700">
      ✅ Đã xác nhận
    </span>
  );
  if (daDoc) return (
    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-100 text-blue-600">
      👁 Đã đọc
    </span>
  );
  return (
    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-400">
      📄 Chưa đọc
    </span>
  );
}

// =============================================================================
// CARD
// =============================================================================

interface VanBanCardProps {
  vb: IVanBanListItem;
}

export function VanBanCard({ vb }: VanBanCardProps) {
  // Dùng _MODULE_NOW (module-level constant) thay vì Date.now() trong render
  const hanCuoi = vb.han_xac_nhan ? new Date(vb.han_xac_nhan) : null;
  const ngayConLai = hanCuoi
    ? Math.ceil((hanCuoi.getTime() - _MODULE_NOW) / (1000 * 60 * 60 * 24))
    : null;
  const sapHetHan = ngayConLai !== null && ngayConLai >= 0 && ngayConLai <= 3;
  const quaHan    = ngayConLai !== null && ngayConLai < 0;

  // Border trái theo mức độ
  const borderCls =
    vb.muc_do === 'RAT_KHAN'   ? 'border-l-4 border-l-red-500' :
    vb.muc_do === 'KHAN'       ? 'border-l-4 border-l-orange-400' :
    vb.muc_do === 'QUAN_TRONG' ? 'border-l-4 border-l-yellow-400' :
    'border-gray-200';

  return (
    <Link
      href={`/phap-luat/${vb.id}`}
      className={`block bg-white rounded-xl border shadow-sm hover:shadow-md transition-all hover:border-purple-300 overflow-hidden ${borderCls}`}
    >
      <div className="p-4">
        {/* Row 1: số hiệu + loại + badges */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 flex-wrap min-w-0">
            <span className="text-xs font-mono font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded shrink-0">
              {vb.so_hieu}
            </span>
            <span className="text-xs text-gray-400">{vb.loai_van_ban.ten}</span>
          </div>
          <div className="flex items-center gap-1 shrink-0 flex-wrap justify-end">
            <MucDoBadge mucDo={vb.muc_do} />
            <HieuLucBadge trangThai={vb.trang_thai_hieu_luc} />
          </div>
        </div>

        {/* Trích yếu */}
        <p className="text-sm font-medium text-gray-900 line-clamp-2 mb-3 leading-relaxed">
          {vb.trich_yeu}
        </p>

        {/* Row 3: cơ quan + ngày ban hành */}
        <div className="flex items-center justify-between text-xs text-gray-400 mb-3">
          <span className="truncate mr-2">🏛 {vb.co_quan_ban_hanh}</span>
          <span className="shrink-0">📅 {new Date(vb.ngay_ban_hanh).toLocaleDateString('vi-VN')}</span>
        </div>

        {/* Row 4: trạng thái đọc + hạn xác nhận */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <DocBadge daDoc={vb.da_doc} daXacNhan={vb.da_xac_nhan} />

          <div className="flex items-center gap-2 flex-wrap">
            {/* Badge điểm mới */}
            {vb.co_diem_moi && (
              <span className="text-xs text-orange-600 bg-orange-50 border border-orange-200 px-2 py-0.5 rounded-full">
                ✨ Điểm mới
              </span>
            )}

            {/* Hạn xác nhận (chỉ hiện nếu bat_buoc_doc và chưa xác nhận) */}
            {vb.bat_buoc_doc && !vb.da_xac_nhan && vb.han_xac_nhan && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                quaHan    ? 'bg-red-100 text-red-700' :
                sapHetHan ? 'bg-orange-100 text-orange-700' :
                'bg-gray-100 text-gray-500'
              }`}>
                {quaHan
                  ? `⚠ Quá hạn ${Math.abs(ngayConLai!)}d`
                  : sapHetHan
                  ? `⏰ Còn ${ngayConLai}d`
                  : `🗓 Hạn ${new Date(vb.han_xac_nhan).toLocaleDateString('vi-VN')}`}
              </span>
            )}
          </div>
        </div>

        {/* Tags */}
        {(vb.tags?.length ?? 0) > 0 && (
          <div className="flex flex-wrap gap-1 mt-3 pt-3 border-t border-gray-100">
            {vb.tags?.slice(0, 4).map((tag, i) => (
              <span key={i} className="text-xs bg-purple-50 text-purple-600 px-1.5 py-0.5 rounded">
                #{tag}
              </span>
            ))}
            {(vb.tags?.length ?? 0) > 4 && (
              <span className="text-xs text-gray-400">+{(vb.tags?.length ?? 0) - 4}</span>
            )}
          </div>
        )}
      </div>
    </Link>
  );
}

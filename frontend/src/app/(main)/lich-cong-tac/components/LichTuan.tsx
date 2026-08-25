/**
 * Lưới lịch TUẦN — bảy cột thứ Hai → Chủ nhật.
 *
 * Khác lưới tháng ở chỗ không cắt bớt "+N nữa": một tuần chỉ vài chục sự kiện
 * nên hiện hết, đúng nhu cầu của Văn phòng khi rà chương trình công tác tuần.
 * Bấm vào đầu cột là mở lịch NGÀY của đúng ngày đó.
 */

'use client';

import Link from 'next/link';
import { MapPin, Users } from 'lucide-react';

import {
  gioNgan,
  ngayThangVN,
  nhanThuNgan,
  nhomTheoNgay,
  tuanCua,
} from '@/lib/lich-ngay';
import type { ISuKienLich } from '@/types/lich-cong-tac';

import { chuTri, mauLoai } from './lich-mau';

interface Props {
  /** Ngày bất kỳ trong tuần cần xem, dạng `YYYY-MM-DD`. */
  ngay: string;
  suKien: ISuKienLich[];
  homNay: string;
  /** Bấm vào một ngày → trang cha chuyển sang chế độ xem ngày. */
  onChonNgay: (ngay: string) => void;
}

export default function LichTuan({ ngay, suKien, homNay, onChonNgay }: Props) {
  const ngayTrongTuan = tuanCua(ngay);
  const theoNgay = nhomTheoNgay(
    suKien,
    ngayTrongTuan[0],
    ngayTrongTuan[6],
  );

  return (
    <div className="rounded-lg border border-gray-200 bg-white overflow-x-auto">
      {/* Bảy cột co lại rất chật trên điện thoại — cho cuộn ngang thay vì ép
          chữ xuống dòng thành một cột không đọc nổi. */}
      <div className="min-w-[64rem] grid grid-cols-7">
        {ngayTrongTuan.map((n) => {
          const laHomNay = n === homNay;
          const ds = theoNgay[n] ?? [];
          return (
            <div key={n} className="border-r border-gray-100 last:border-r-0">
              <button
                type="button"
                onClick={() => onChonNgay(n)}
                title="Xem lịch ngày này"
                className={`w-full border-b px-2 py-2 text-center ${
                  laHomNay
                    ? 'border-blue-200 bg-blue-50 text-blue-800'
                    : 'border-gray-200 bg-gray-50 text-gray-700 hover:bg-gray-100'
                }`}
              >
                <div className="text-xs font-semibold">{nhanThuNgan(n)}</div>
                <div
                  className={`text-sm ${laHomNay ? 'font-bold' : 'font-medium'}`}
                >
                  {ngayThangVN(n)}
                </div>
                <div className="text-[11px] text-gray-500">
                  {ds.length > 0 ? `${ds.length} sự kiện` : 'trống'}
                </div>
              </button>

              <div className="min-h-[16rem] space-y-1.5 p-1.5">
                {ds.map((sk) => (
                  <Link
                    key={`${sk.id}-${n}`}
                    href={`/lich-cong-tac/${sk.id}`}
                    title={sk.tieu_de}
                    className={`block rounded border px-1.5 py-1 text-[11px] leading-tight hover:brightness-95 ${mauLoai(
                      sk.loai_lich,
                    )} ${sk.trang_thai === 'HUY' ? 'line-through opacity-60' : ''}`}
                  >
                    <div className="font-semibold">
                      {gioNgan(sk.gio_bat_dau)}
                      {sk.gio_ket_thuc && `–${gioNgan(sk.gio_ket_thuc)}`}
                    </div>
                    <div className="line-clamp-3">{sk.tieu_de}</div>
                    {sk.dia_diem && (
                      <div className="mt-0.5 flex items-center gap-1 truncate opacity-80">
                        <MapPin className="w-3 h-3 shrink-0" />
                        <span className="truncate">{sk.dia_diem}</span>
                      </div>
                    )}
                    {chuTri(sk) && (
                      <div className="flex items-center gap-1 truncate opacity-80">
                        <Users className="w-3 h-3 shrink-0" />
                        <span className="truncate">{chuTri(sk)}</span>
                      </div>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

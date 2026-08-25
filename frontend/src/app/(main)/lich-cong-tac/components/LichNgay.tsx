/**
 * Lịch NGÀY — chương trình công tác của đúng một ngày.
 *
 * Chia SÁNG / CHIỀU vì chương trình công tác của Chi cục luôn đọc theo buổi;
 * sự kiện không ghi giờ gom vào nhóm riêng thay vì đoán bừa nó thuộc buổi nào.
 */

'use client';

import Link from 'next/link';
import {
  ExternalLink,
  FileText,
  Loader2,
  MapPin,
  Pencil,
  Star,
  Users,
} from 'lucide-react';

import { gioNgan, nhanThu, ngayVN, nhomTheoNgay } from '@/lib/lich-ngay';
import { NHAN_TRANG_THAI, type ISuKienLich } from '@/types/lich-cong-tac';

import { MAU_TRANG_THAI, chuTri, mauLoai } from './lich-mau';

interface Props {
  /** Ngày cần xem, dạng `YYYY-MM-DD`. */
  ngay: string;
  suKien: ISuKienLich[];
  homNay: string;
  suaDuoc: (sk: ISuKienLich) => boolean;
  onSua: (sk: ISuKienLich) => void;
  /** Id sự kiện đang nạp chi tiết để mở form sửa. */
  dangMoSua: string | null;
}

/** Mốc 12:00 — trùng cách Văn phòng tách buổi trong văn bản chương trình. */
function buoiCua(sk: ISuKienLich): 'sang' | 'chieu' | 'khac' {
  if (!sk.gio_bat_dau) return 'khac';
  return sk.gio_bat_dau < '12:00' ? 'sang' : 'chieu';
}

export default function LichNgay({
  ngay,
  suKien,
  homNay,
  suaDuoc,
  onSua,
  dangMoSua,
}: Props) {
  // Vẫn phải gom qua nhomTheoNgay: sự kiện nhiều ngày bắt đầu từ hôm trước
  // cũng phải hiện trong ngày này.
  const ds = nhomTheoNgay(suKien, ngay, ngay)[ngay] ?? [];

  const nhom: { ma: 'sang' | 'chieu' | 'khac'; nhan: string }[] = [
    { ma: 'sang', nhan: 'Buổi sáng' },
    { ma: 'chieu', nhan: 'Buổi chiều' },
    { ma: 'khac', nhan: 'Chưa xác định giờ' },
  ];

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div
        className={`flex flex-wrap items-baseline gap-x-3 border-b px-4 py-3 ${
          ngay === homNay
            ? 'border-blue-200 bg-blue-50'
            : 'border-gray-200 bg-gray-50'
        }`}
      >
        <h2 className="text-lg font-semibold text-gray-900">
          {nhanThu(ngay)}, {ngayVN(ngay)}
        </h2>
        {ngay === homNay && (
          <span className="rounded bg-blue-600 px-1.5 py-0.5 text-[11px] text-white">
            Hôm nay
          </span>
        )}
        <span className="text-sm text-gray-600">
          {ds.length > 0 ? `${ds.length} sự kiện` : 'không có sự kiện'}
        </span>
      </div>

      {ds.length === 0 ? (
        <div className="py-16 text-center text-gray-500">
          Ngày này chưa có sự kiện nào trên lịch.
        </div>
      ) : (
        <div className="divide-y divide-gray-100">
          {nhom.map(({ ma, nhan }) => {
            const cua = ds.filter((sk) => buoiCua(sk) === ma);
            if (cua.length === 0) return null;
            return (
              <section key={ma}>
                <div className="bg-gray-50/70 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {nhan}
                </div>
                <ul className="divide-y divide-gray-100">
                  {cua.map((sk) => {
                    const nhieuNgay =
                      sk.ngay_ket_thuc &&
                      sk.ngay_ket_thuc !== (sk.ngay_hien_thi ?? sk.ngay_hop);
                    return (
                      <li
                        key={sk.id}
                        className="flex gap-3 px-4 py-3 hover:bg-gray-50"
                      >
                        <div className="w-16 shrink-0 pt-0.5 text-sm font-semibold text-gray-700">
                          {gioNgan(sk.gio_bat_dau) || '—'}
                          {sk.gio_ket_thuc && (
                            <div className="text-xs font-normal text-gray-500">
                              {gioNgan(sk.gio_ket_thuc)}
                            </div>
                          )}
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="mb-1 flex flex-wrap items-center gap-2">
                            <span
                              className={`rounded border px-1.5 py-0.5 text-[11px] ${mauLoai(
                                sk.loai_lich,
                              )}`}
                            >
                              {sk.loai_lich_nhan ?? 'Lịch khác'}
                            </span>
                            <span
                              className={`rounded px-1.5 py-0.5 text-[11px] ${
                                MAU_TRANG_THAI[sk.trang_thai]
                              }`}
                            >
                              {NHAN_TRANG_THAI[sk.trang_thai]}
                            </span>
                            {sk.ma_lich && (
                              <span className="font-mono text-[11px] text-gray-500">
                                {sk.ma_lich}
                              </span>
                            )}
                            {nhieuNgay && (
                              <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-600">
                                {ngayVN(sk.ngay_hien_thi ?? sk.ngay_hop)} →{' '}
                                {ngayVN(sk.ngay_ket_thuc!)}
                              </span>
                            )}
                            {sk.co_the_mo_hkg && (
                              <span className="inline-flex items-center gap-1 rounded bg-indigo-50 px-1.5 py-0.5 text-[11px] text-indigo-700">
                                <ExternalLink className="w-3 h-3" />
                                Họp Không Giấy
                              </span>
                            )}
                          </div>

                          <Link
                            href={`/lich-cong-tac/${sk.id}`}
                            className={`font-medium text-gray-900 hover:text-blue-700 ${
                              sk.trang_thai === 'HUY' ? 'line-through' : ''
                            }`}
                          >
                            {sk.tieu_de}
                          </Link>

                          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
                            {sk.dia_diem && (
                              <span className="inline-flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                {sk.dia_diem}
                              </span>
                            )}
                            {chuTri(sk) && (
                              <span className="inline-flex items-center gap-1">
                                <Users className="w-3 h-3" />
                                {chuTri(sk)}
                              </span>
                            )}
                            {sk.don_vi_chuan_bi && (
                              <span>Chuẩn bị: {sk.don_vi_chuan_bi}</span>
                            )}
                            {sk.so_tai_lieu > 0 && (
                              <span className="inline-flex items-center gap-1">
                                <FileText className="w-3 h-3" />
                                {sk.so_tai_lieu} tài liệu
                              </span>
                            )}
                            {(sk.so_luot_cham ?? 0) > 0 && (
                              <span
                                className="inline-flex items-center gap-1 text-amber-700"
                                title={`Điểm công tác chuẩn bị — ${sk.so_luot_cham} lượt chấm`}
                              >
                                <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                                {sk.diem_chuan_bi?.toFixed(1)}
                              </span>
                            )}
                          </div>
                        </div>

                        {suaDuoc(sk) && (
                          <button
                            type="button"
                            title="Sửa sự kiện"
                            disabled={dangMoSua === sk.id}
                            onClick={() => onSua(sk)}
                            className="h-8 shrink-0 rounded-lg border border-gray-300 p-1.5 text-gray-600 hover:bg-white hover:text-blue-700 disabled:opacity-40"
                          >
                            {dangMoSua === sk.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Pencil className="w-4 h-4" />
                            )}
                          </button>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}

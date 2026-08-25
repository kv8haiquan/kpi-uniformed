/**
 * Lịch NGÀY — xem TOÀN BỘ cuộc họp của một ngày.
 *
 * Màn hình này cố ý giống hệt trang xem một cuộc họp, chỉ khác là xếp nhiều
 * cuộc nối nhau: mỗi cuộc là một thẻ `ChiTietSuKien` đầy đủ — thành phần tham
 * dự, đơn vị chuẩn bị, số văn bản, ghi chú, tài liệu, chấm sao chuẩn bị — kèm
 * nguyên bộ nút Sửa / Huỷ / Xoá / Nhật ký. Người dùng không phải mở từng cuộc
 * một rồi bấm quay lại, vốn là cách duy nhất trước đây khi một ngày có tới 8
 * cuộc họp.
 *
 * Danh sách sự kiện của cha chỉ có phần tóm tắt (thiếu ghi chú, thành phần ghi
 * tay), nên thẻ nào cũng cần bản CHI TIẾT — nạp song song một lượt cho cả ngày.
 * Một ngày đông nhất trong sáu tháng dữ liệu là 8 cuộc, trung bình 3,2.
 */

'use client';

import { useEffect, useState } from 'react';
import { CalendarDays, Loader2 } from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import { errMsg } from '@/lib/hkg-error';
import { gioNgan, nhanThu, ngayVN, nhomTheoNgay } from '@/lib/lich-ngay';
import type {
  IQuyenLich,
  ISuKienChiTiet,
  ISuKienLich,
} from '@/types/lich-cong-tac';

import ChiTietSuKien from './ChiTietSuKien';

interface Props {
  /** Ngày cần xem, dạng `YYYY-MM-DD`. */
  ngay: string;
  /** Sự kiện thô của khoảng đang xem — cha đã nạp sẵn. */
  suKien: ISuKienLich[];
  homNay: string;
  quyen: IQuyenLich | null;
  /** Sự kiện vừa sửa/huỷ/xoá — cha nạp lại vì sửa ngày là nó nhảy sang ngày khác. */
  onLamMoi: () => void;
}

/** Mốc 12:00 — trùng cách Văn phòng tách buổi trong văn bản chương trình. */
function buoiCua(sk: { gio_bat_dau?: string | null }): 'sang' | 'chieu' | 'khac' {
  if (!sk.gio_bat_dau) return 'khac';
  return sk.gio_bat_dau < '12:00' ? 'sang' : 'chieu';
}

const NHOM_BUOI = [
  { ma: 'sang', nhan: 'Buổi sáng' },
  { ma: 'chieu', nhan: 'Buổi chiều' },
  { ma: 'khac', nhan: 'Chưa xác định giờ' },
] as const;

export default function LichNgay({
  ngay,
  suKien,
  homNay,
  quyen,
  onLamMoi,
}: Props) {
  // Vẫn phải gom qua nhomTheoNgay: sự kiện nhiều ngày bắt đầu từ hôm trước
  // cũng phải hiện trong ngày này.
  const tomTat = nhomTheoNgay(suKien, ngay, ngay)[ngay] ?? [];
  const khoa = `${ngay}|${tomTat.map((s) => s.id).join(',')}`;

  // Gói cả khoá vào state thay vì có thêm cờ "đang tải": đổi ngày là khoá đổi
  // theo, nên biết ngay dữ liệu đang giữ có phải của ngày đang xem hay không —
  // không cần xoá state rồi vẽ lại một nhịp trắng.
  const [duLieu, setDuLieu] = useState<{
    khoa: string;
    ds: ISuKienChiTiet[];
  } | null>(null);
  const [loi, setLoi] = useState<string | null>(null);

  useEffect(() => {
    if (tomTat.length === 0) return;
    let bo = false;
    const chay = async () => {
      try {
        const ds = await Promise.all(
          tomTat.map((s) => lichCongTacApi.chiTiet(s.id)),
        );
        if (bo) return;
        setDuLieu({ khoa, ds });
        setLoi(null);
      } catch (e) {
        if (!bo) setLoi(errMsg(e, 'Không tải được chi tiết các cuộc họp'));
      }
    };
    void chay();
    return () => {
      bo = true;
    };
    // `tomTat` dựng lại mỗi lần vẽ nên không đưa vào phụ thuộc — `khoa` đã
    // gói đủ ngày và danh sách id, đúng thứ quyết định phải nạp lại hay không.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [khoa]);

  const sanSang = duLieu?.khoa === khoa;
  const chiTiet = sanSang ? duLieu.ds : [];

  /**
   * Sửa hoặc huỷ một cuộc: thay ngay bản trong tay rồi mới báo cha nạp lại.
   *
   * Bảo cha nạp lại KHÔNG đủ: danh sách id của ngày không đổi khi chỉ sửa tiêu
   * đề hay giờ, nên khoá không đổi, nên hiệu ứng không chạy lại — thẻ sẽ đứng
   * nguyên dữ liệu cũ. Còn khi sửa làm sự kiện nhảy sang ngày khác thì id rời
   * khỏi ngày này, khoá đổi, hiệu ứng tự nạp lại và thẻ biến mất.
   */
  const thayThe = (moi: ISuKienChiTiet) => {
    setDuLieu((tr) =>
      tr === null
        ? tr
        : { ...tr, ds: tr.ds.map((s) => (s.id === moi.id ? moi : s)) },
    );
    onLamMoi();
  };

  return (
    <div className="space-y-4">
      <div
        className={`flex flex-wrap items-baseline gap-x-3 gap-y-1 rounded-lg border px-4 py-3 ${
          ngay === homNay
            ? 'border-blue-200 bg-blue-50'
            : 'border-gray-200 bg-white'
        }`}
      >
        <CalendarDays className="w-5 h-5 shrink-0 self-center text-gray-400" />
        <h2 className="text-lg font-semibold text-gray-900">
          {nhanThu(ngay)}, {ngayVN(ngay)}
        </h2>
        {ngay === homNay && (
          <span className="rounded bg-blue-600 px-1.5 py-0.5 text-[11px] text-white">
            Hôm nay
          </span>
        )}
        <span className="text-sm text-gray-600">
          {tomTat.length > 0
            ? `${tomTat.length} cuộc họp / sự kiện`
            : 'không có sự kiện'}
        </span>
        {/* Mục lục giờ giấc: một ngày 8 cuộc thì cuộn tìm rất mệt. */}
        {tomTat.length > 1 && (
          <span className="flex flex-wrap gap-1.5 text-xs text-gray-500">
            {tomTat.map((sk) => (
              <a
                key={sk.id}
                href={`#su-kien-${sk.id}`}
                className="rounded bg-gray-100 px-1.5 py-0.5 hover:bg-gray-200 hover:text-gray-900"
                title={sk.tieu_de}
              >
                {gioNgan(sk.gio_bat_dau) || '—'}
              </a>
            ))}
          </span>
        )}
      </div>

      {loi && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {loi}
        </div>
      )}

      {tomTat.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white py-16 text-center text-gray-500">
          Ngày này chưa có sự kiện nào trên lịch.
        </div>
      ) : !sanSang ? (
        <div className="flex items-center justify-center rounded-lg border border-gray-200 bg-white py-16 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          Đang tải chi tiết {tomTat.length} cuộc họp…
        </div>
      ) : (
        NHOM_BUOI.map(({ ma, nhan }) => {
          const cua = chiTiet.filter((sk) => buoiCua(sk) === ma);
          if (cua.length === 0) return null;
          return (
            <section key={ma} className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                {nhan}
              </h3>
              {cua.map((sk) => (
                <div key={sk.id} id={`su-kien-${sk.id}`} className="scroll-mt-4">
                  <ChiTietSuKien
                    sk={sk}
                    quyen={quyen}
                    onThayDoi={thayThe}
                    onXoa={onLamMoi}
                    thuGonDuoc
                  />
                </div>
              ))}
            </section>
          );
        })
      )}
    </div>
  );
}

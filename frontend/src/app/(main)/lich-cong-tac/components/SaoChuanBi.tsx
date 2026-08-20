/**
 * Chấm sao công tác chuẩn bị một cuộc họp — G5.3.
 *
 * Người không có quyền chấm vẫn THẤY điểm đã có, chỉ là sao không bấm được —
 * giữ đúng hành vi `publicPrepRating` của hệ cũ. Điểm chuẩn bị là lời nhắc
 * cho đơn vị chuẩn bị chứ không phải hồ sơ kín.
 *
 * Khi chưa ai chấm và người xem cũng không có quyền, khối này biến mất hẳn
 * thay vì hiện 5 sao rỗng — 5 sao rỗng trông như "đã chấm 0 điểm".
 */

'use client';

import { useEffect, useState } from 'react';
import { Loader2, Star } from 'lucide-react';

import { danhGiaChuanBiApi } from '@/services/danh-gia-chuan-bi';
import { errApi } from '@/lib/hkg-error';
import type { IDanhGiaChuanBi } from '@/types/lich-cong-tac';

interface Props {
  cuocHopId: string;
}

export default function SaoChuanBi({ cuocHopId }: Props) {
  const [dl, setDl] = useState<IDanhGiaChuanBi | null>(null);
  const [ray, setRay] = useState<number | null>(null);
  const [dangLuu, setDangLuu] = useState(false);
  const [moGhiChu, setMoGhiChu] = useState(false);
  const [ghiChu, setGhiChu] = useState('');
  const [loi, setLoi] = useState<string | null>(null);

  useEffect(() => {
    danhGiaChuanBiApi
      .cuaCuocHop(cuocHopId)
      .then((d) => {
        setDl(d);
        setGhiChu(d.ghi_chu_cua_toi ?? '');
      })
      .catch((e) => setLoi(errApi(e, 'Không tải được đánh giá')));
  }, [cuocHopId]);

  const cham = async (diem: number, kemGhiChu = false) => {
    setDangLuu(true);
    setLoi(null);
    try {
      const d = await danhGiaChuanBiApi.cham(
        cuocHopId,
        diem,
        kemGhiChu ? ghiChu.trim() || null : (dl?.ghi_chu_cua_toi ?? null),
      );
      setDl(d);
      setGhiChu(d.ghi_chu_cua_toi ?? '');
      setMoGhiChu(false);
    } catch (e) {
      setLoi(errApi(e, 'Không ghi được đánh giá'));
    } finally {
      setDangLuu(false);
    }
  };

  const boCham = async () => {
    setDangLuu(true);
    setLoi(null);
    try {
      const d = await danhGiaChuanBiApi.boCham(cuocHopId);
      setDl(d);
      setGhiChu('');
      setMoGhiChu(false);
    } catch (e) {
      setLoi(errApi(e, 'Không rút lại được đánh giá'));
    } finally {
      setDangLuu(false);
    }
  };

  if (!dl) {
    return loi ? (
      <p className="text-sm text-red-700">{loi}</p>
    ) : (
      <span className="inline-flex items-center gap-1.5 text-sm text-gray-500">
        <Loader2 className="h-4 w-4 animate-spin" /> Đang tải đánh giá…
      </span>
    );
  }

  // Chưa ai chấm và mình cũng không được chấm → không hiện gì.
  if (!dl.duoc_cham && dl.so_luot === 0) return null;

  // Sao hiển thị: đang rê chuột → điểm mình đã chấm → điểm trung bình.
  const hien = ray ?? dl.diem_cua_toi ?? Math.round(dl.diem_tb ?? 0);

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <div
          className="flex items-center"
          onMouseLeave={() => setRay(null)}
        >
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              disabled={!dl.duoc_cham || dangLuu}
              onMouseEnter={() => dl.duoc_cham && setRay(n)}
              onClick={() => void cham(n)}
              title={dl.duoc_cham ? `Chấm ${n} sao` : undefined}
              className={`p-0.5 ${
                dl.duoc_cham ? 'cursor-pointer' : 'cursor-default'
              }`}
            >
              <Star
                className={`h-5 w-5 ${
                  n <= hien
                    ? 'fill-amber-400 text-amber-400'
                    : 'text-gray-300'
                }`}
              />
            </button>
          ))}
        </div>

        {dl.so_luot > 0 ? (
          <span className="text-sm text-gray-600">
            {dl.diem_tb?.toFixed(1)}/5 · {dl.so_luot} lượt chấm
          </span>
        ) : (
          <span className="text-sm text-gray-500">Chưa ai chấm</span>
        )}

        {dangLuu && <Loader2 className="h-4 w-4 animate-spin text-gray-500" />}
      </div>

      {dl.duoc_cham && dl.diem_cua_toi !== null && (
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <span className="text-gray-600">
            Bạn đã chấm {dl.diem_cua_toi} sao
          </span>
          <button
            type="button"
            onClick={() => setMoGhiChu((m) => !m)}
            className="text-blue-700 hover:underline"
          >
            {dl.ghi_chu_cua_toi ? 'Sửa nhận xét' : 'Thêm nhận xét'}
          </button>
          <button
            type="button"
            onClick={() => void boCham()}
            className="text-red-700 hover:underline"
          >
            Rút lại
          </button>
        </div>
      )}

      {moGhiChu && dl.diem_cua_toi !== null && (
        <div className="flex gap-2">
          <input
            className="flex-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
            value={ghiChu}
            onChange={(e) => setGhiChu(e.target.value)}
            maxLength={2000}
            placeholder="Nhận xét về công tác chuẩn bị…"
          />
          <button
            type="button"
            disabled={dangLuu}
            onClick={() => void cham(dl.diem_cua_toi as number, true)}
            className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
          >
            Lưu
          </button>
        </div>
      )}

      {dl.danh_sach.length > 0 && (
        <ul className="space-y-0.5 text-xs text-gray-600">
          {dl.danh_sach.map((c) => (
            <li key={c.id}>
              <span className="font-medium text-gray-800">{c.ho_ten}</span>
              {c.chuc_vu ? ` (${c.chuc_vu})` : ''} — {c.diem} sao
              {c.ghi_chu ? `: ${c.ghi_chu}` : ''}
            </li>
          ))}
        </ul>
      )}

      {loi && <p className="text-sm text-red-700">{loi}</p>}
    </div>
  );
}

/**
 * Chọn người để chia sẻ một ghi chú — G5.2.
 *
 * Chọn từ danh sách công chức chứ không gõ tên: chia sẻ nhầm người là lộ nội
 * dung, mà tên trùng trong cơ quan thì nhiều.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { Check, Loader2, X } from 'lucide-react';

import { ghiChuApi } from '@/services/ghi-chu';
import { errApi } from '@/lib/hkg-error';
import type { INguoiNhanGhiChu } from '@/types/lich-cong-tac';

interface Props {
  ghiChuId: string;
  tieuDe: string;
  /** Người đã được chia sẻ rồi — hiện mờ, không cho chọn lại. */
  daChiaSe: Set<string>;
  onDong: () => void;
  onXong: () => void;
}

const oCss =
  'w-full rounded-lg border border-gray-300 px-3 py-1.5 focus:border-blue-500 focus:outline-none';

export default function ModalChiaSe({
  ghiChuId,
  tieuDe,
  daChiaSe,
  onDong,
  onXong,
}: Props) {
  const [ds, setDs] = useState<INguoiNhanGhiChu[] | null>(null);
  const [tuKhoa, setTuKhoa] = useState('');
  const [chon, setChon] = useState<Set<string>>(new Set());
  const [loiNhan, setLoiNhan] = useState('');
  const [dangLuu, setDangLuu] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  useEffect(() => {
    ghiChuApi
      .nguoiNhan()
      .then(setDs)
      .catch((e) => {
        setDs([]);
        setLoi(errApi(e, 'Không tải được danh sách công chức'));
      });
  }, []);

  const loc = useMemo(() => {
    if (!ds) return [];
    const t = tuKhoa.trim().toLowerCase();
    if (!t) return ds.slice(0, 100);
    return ds
      .filter(
        (x) =>
          x.ho_ten.toLowerCase().includes(t) ||
          x.ma_cc.toLowerCase().includes(t) ||
          (x.chuc_vu ?? '').toLowerCase().includes(t),
      )
      .slice(0, 100);
  }, [ds, tuKhoa]);

  const bat = (id: string) => {
    setChon((truoc) => {
      const sau = new Set(truoc);
      if (sau.has(id)) sau.delete(id);
      else sau.add(id);
      return sau;
    });
  };

  const gui = async () => {
    if (chon.size === 0) return setLoi('Chưa chọn người nhận');
    setDangLuu(true);
    setLoi(null);
    try {
      await ghiChuApi.chiaSe(ghiChuId, [...chon], loiNhan.trim() || undefined);
      onXong();
    } catch (e) {
      setLoi(errApi(e, 'Không chia sẻ được'));
    } finally {
      setDangLuu(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4">
      <div className="my-12 w-full max-w-lg rounded-xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <div>
            <h2 className="font-semibold text-gray-900">Chia sẻ ghi chú</h2>
            <p className="max-w-md truncate text-xs text-gray-500">{tieuDe}</p>
          </div>
          <button
            type="button"
            onClick={onDong}
            className="rounded p-1 text-gray-500 hover:bg-gray-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-3 px-5 py-4">
          <input
            className={oCss}
            value={tuKhoa}
            onChange={(e) => setTuKhoa(e.target.value)}
            placeholder="Tìm theo tên, mã công chức hoặc chức vụ…"
            autoFocus
          />

          <div className="max-h-64 overflow-y-auto rounded-lg border border-gray-200">
            {ds === null ? (
              <div className="flex items-center gap-2 px-3 py-4 text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Đang tải…
              </div>
            ) : loc.length === 0 ? (
              <p className="px-3 py-4 text-sm text-gray-500">
                Không tìm thấy ai khớp từ khoá.
              </p>
            ) : (
              loc.map((x) => {
                const cu = daChiaSe.has(x.id);
                const dangChon = chon.has(x.id);
                return (
                  <button
                    key={x.id}
                    type="button"
                    disabled={cu}
                    onClick={() => bat(x.id)}
                    className={`flex w-full items-center justify-between gap-2 border-b border-gray-100 px-3 py-2 text-left text-sm last:border-b-0 ${
                      cu
                        ? 'cursor-not-allowed bg-gray-50 text-gray-400'
                        : dangChon
                          ? 'bg-blue-50 text-blue-900'
                          : 'hover:bg-gray-50'
                    }`}
                  >
                    <span>
                      <span className="font-medium">{x.ho_ten}</span>
                      {x.chuc_vu ? (
                        <span className="text-gray-500"> — {x.chuc_vu}</span>
                      ) : null}
                      <span className="block text-xs text-gray-400">
                        {x.ma_cc}
                      </span>
                    </span>
                    {cu ? (
                      <span className="text-xs">đã chia sẻ</span>
                    ) : dangChon ? (
                      <Check className="h-4 w-4 shrink-0" />
                    ) : null}
                  </button>
                );
              })
            )}
          </div>

          <label className="block text-sm">
            <span className="mb-1 block text-gray-600">Lời nhắn (không bắt buộc)</span>
            <input
              className={oCss}
              value={loiNhan}
              onChange={(e) => setLoiNhan(e.target.value)}
              maxLength={1000}
              placeholder="Anh/chị xem giúp em phần…"
            />
          </label>
        </div>

        {loi && (
          <div className="mx-5 mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {loi}
          </div>
        )}

        <div className="flex items-center justify-between border-t border-gray-200 px-5 py-3">
          <span className="text-xs text-gray-500">Đã chọn {chon.size} người</span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onDong}
              className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm hover:bg-gray-50"
            >
              Đóng
            </button>
            <button
              type="button"
              onClick={gui}
              disabled={dangLuu || chon.size === 0}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
            >
              {dangLuu && <Loader2 className="h-4 w-4 animate-spin" />}
              Chia sẻ
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

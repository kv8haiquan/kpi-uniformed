/**
 * Chọn lãnh đạo từ danh mục — dùng cho ô Chủ trì (một người) và ô Thành phần
 * (nhiều người) trong form lịch công tác.
 *
 * Vì sao chọn thay vì gõ tay: 283/498 sự kiện di trú có thành phần ghi tay,
 * mỗi người một kiểu — "Phó Chi cục trưởng Bùi Ngọc Lợi", "Đ/c Nguyễn Cảnh
 * Thắng - Phó Chi cục trưởng". Gõ tay thì không nối được sang chương trình
 * công tác của từng lãnh đạo, mà đó chính là màn hình người ta xem nhiều nhất.
 *
 * Chỉ có lãnh đạo trong danh mục, không có công chức thường: thành phần dự
 * họp cấp Chi cục là lãnh đạo, còn "toàn thể công chức Đội X" thì viết ở ô
 * ghi tay bên cạnh chứ không liệt kê từng người.
 */

'use client';

import { useMemo, useState } from 'react';
import { Check, Search, X } from 'lucide-react';

import type { ILanhDaoChon } from '@/types/lich-cong-tac';

interface Props {
  ds: ILanhDaoChon[];
  /** Id đang chọn. Chế độ một người thì mảng có 0 hoặc 1 phần tử. */
  chon: string[];
  onDoi: (chon: string[]) => void;
  nhieu?: boolean;
  /** Tên hiển thị cho người đã chọn nhưng không có trong danh mục (đã nghỉ). */
  tenDuPhong?: Record<string, string>;
  placeholder?: string;
}

/** Bỏ dấu để gõ "loi" cũng tìm ra "Lợi". */
function boDau(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase();
}

export default function ChonLanhDao({
  ds,
  chon,
  onDoi,
  nhieu = false,
  tenDuPhong = {},
  placeholder = 'Tìm theo tên, chức vụ hoặc đơn vị…',
}: Props) {
  const [tuKhoa, setTuKhoa] = useState('');
  const [moDs, setMoDs] = useState(false);

  const theoId = useMemo(
    () => new Map(ds.map((x) => [x.id, x])),
    [ds],
  );

  const loc = useMemo(() => {
    const t = boDau(tuKhoa.trim());
    if (!t) return ds;
    return ds.filter(
      (x) =>
        boDau(x.ho_ten).includes(t) ||
        boDau(x.chuc_vu ?? '').includes(t) ||
        boDau(x.ten_don_vi ?? '').includes(t) ||
        x.ma_cc.toLowerCase().includes(t),
    );
  }, [ds, tuKhoa]);

  const bat = (id: string) => {
    if (!nhieu) {
      onDoi(chon[0] === id ? [] : [id]);
      setMoDs(false);
      setTuKhoa('');
      return;
    }
    onDoi(chon.includes(id) ? chon.filter((x) => x !== id) : [...chon, id]);
  };

  const ten = (id: string) =>
    theoId.get(id)?.ho_ten ?? tenDuPhong[id] ?? 'Đã chọn';
  const chucVu = (id: string) => theoId.get(id)?.chuc_vu ?? null;

  return (
    <div className="space-y-1.5">
      {chon.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {chon.map((id) => (
            <span
              key={id}
              className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 py-1 pl-3 pr-1.5 text-sm text-blue-900"
            >
              <span className="truncate">
                {ten(id)}
                {chucVu(id) && (
                  <span className="text-blue-700/70"> — {chucVu(id)}</span>
                )}
              </span>
              <button
                type="button"
                onClick={() => onDoi(chon.filter((x) => x !== id))}
                className="shrink-0 rounded-full p-0.5 hover:bg-blue-200"
                title="Bỏ chọn"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </span>
          ))}
        </div>
      )}

      {(nhieu || chon.length === 0) && (
        <>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              className="w-full rounded-lg border border-gray-300 py-1.5 pl-9 pr-3 focus:border-blue-500 focus:outline-none"
              value={tuKhoa}
              onChange={(e) => {
                setTuKhoa(e.target.value);
                setMoDs(true);
              }}
              onFocus={() => setMoDs(true)}
              placeholder={placeholder}
            />
          </div>

          {(moDs || tuKhoa) && (
            <div className="max-h-56 overflow-y-auto rounded-lg border border-gray-200">
              {loc.length === 0 ? (
                <p className="px-3 py-3 text-sm text-gray-500">
                  Không có lãnh đạo nào khớp từ khoá.
                </p>
              ) : (
                loc.map((x) => {
                  const dangChon = chon.includes(x.id);
                  return (
                    <button
                      key={x.id}
                      type="button"
                      onClick={() => bat(x.id)}
                      className={`flex w-full items-center gap-2 border-b border-gray-100 px-3 py-2 text-left last:border-b-0 ${
                        dangChon ? 'bg-blue-50' : 'hover:bg-gray-50'
                      }`}
                    >
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium text-gray-900">
                          {x.ho_ten}
                        </span>
                        <span className="block truncate text-xs text-gray-500">
                          {x.chuc_vu || 'Lãnh đạo'}
                          {x.ten_don_vi ? ` · ${x.ten_don_vi}` : ''}
                        </span>
                      </span>
                      {dangChon && (
                        <Check className="h-4 w-4 shrink-0 text-blue-600" />
                      )}
                    </button>
                  );
                })
              )}
            </div>
          )}

          {moDs && (
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>
                {loc.length}/{ds.length} lãnh đạo · xếp theo chức vụ
              </span>
              <button
                type="button"
                onClick={() => {
                  setMoDs(false);
                  setTuKhoa('');
                }}
                className="text-gray-600 hover:underline"
              >
                Thu gọn
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

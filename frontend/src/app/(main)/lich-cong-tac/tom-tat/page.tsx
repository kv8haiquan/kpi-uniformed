/**
 * /lich-cong-tac/tom-tat — bản tóm tắt chương trình công tác.
 *
 * Mục đích chính là để copy dán sang Zalo hoặc email, nên backend trả sẵn
 * `van_ban_thuan` và trang này chỉ cần một nút sao chép. Sinh trực tiếp từ dữ
 * liệu lịch — sửa lịch thì tóm tắt tự đổi theo, không lưu bản riêng.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { Check, ClipboardCopy, Loader2, Printer } from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import { errMsg } from '@/lib/hkg-error';
import type { ITomTatLich } from '@/types/lich-cong-tac';

function homNayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`;
}

export default function TomTatLichPage() {
  const [tuNgay, setTuNgay] = useState(homNayISO);
  const [soNgay, setSoNgay] = useState(3);
  const [chiDaDang, setChiDaDang] = useState(true);
  const [kemTrucBan, setKemTrucBan] = useState(true);

  const [dl, setDl] = useState<ITomTatLich | null>(null);
  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState<string | null>(null);
  const [daChep, setDaChep] = useState(false);

  const tai = useCallback(async () => {
    setDangTai(true);
    setLoi(null);
    try {
      setDl(
        await lichCongTacApi.tomTat({
          'tu-ngay': tuNgay,
          'so-ngay': soNgay,
          'chi-da-dang': chiDaDang,
          'kem-truc-ban': kemTrucBan,
        }),
      );
    } catch (e) {
      setLoi(errMsg(e, 'Không tải được tóm tắt lịch'));
    } finally {
      setDangTai(false);
    }
  }, [tuNgay, soNgay, chiDaDang, kemTrucBan]);

  useEffect(() => {
    void tai();
  }, [tai]);

  const chep = async () => {
    if (!dl?.van_ban_thuan) return;
    try {
      await navigator.clipboard.writeText(dl.van_ban_thuan);
      setDaChep(true);
      setTimeout(() => setDaChep(false), 2000);
    } catch {
      setLoi('Trình duyệt không cho phép sao chép. Bôi đen rồi Ctrl+C.');
    }
  };

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex flex-wrap items-end gap-3 print:hidden">
        <label className="text-sm">
          <span className="block text-gray-600 mb-1">Từ ngày</span>
          <input
            type="date"
            value={tuNgay}
            onChange={(e) => setTuNgay(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-1.5"
          />
        </label>

        <label className="text-sm">
          <span className="block text-gray-600 mb-1">Số ngày</span>
          <select
            value={soNgay}
            onChange={(e) => setSoNgay(Number(e.target.value))}
            className="rounded-lg border border-gray-300 px-3 py-1.5"
          >
            {[1, 2, 3, 5, 7, 14, 30].map((n) => (
              <option key={n} value={n}>
                {n} ngày
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2 text-sm pb-1.5">
          <input
            type="checkbox"
            checked={chiDaDang}
            onChange={(e) => setChiDaDang(e.target.checked)}
          />
          Chỉ lịch đã đăng
        </label>

        <label className="flex items-center gap-2 text-sm pb-1.5">
          <input
            type="checkbox"
            checked={kemTrucBan}
            onChange={(e) => setKemTrucBan(e.target.checked)}
          />
          Kèm lịch trực
        </label>

        <div className="ml-auto flex gap-2">
          <button
            type="button"
            onClick={chep}
            disabled={!dl?.van_ban_thuan}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {daChep ? (
              <>
                <Check className="w-4 h-4" />
                Đã chép
              </>
            ) : (
              <>
                <ClipboardCopy className="w-4 h-4" />
                Sao chép
              </>
            )}
          </button>
          <button
            type="button"
            onClick={() => window.print()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
          >
            <Printer className="w-4 h-4" />
            In
          </button>
        </div>
      </div>

      {loi && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 print:hidden">
          {loi}
        </div>
      )}

      {dangTai ? (
        <div className="flex items-center justify-center py-16 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          Đang tải…
        </div>
      ) : !dl || dl.theo_ngay.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white py-16 text-center text-gray-500">
          Không có lịch nào trong khoảng đã chọn.
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 bg-white p-5 space-y-5">
          {dl.theo_ngay.map((ng) => (
            <div key={ng.ngay}>
              <h2 className="font-semibold text-gray-900 border-b border-gray-200 pb-1 mb-2">
                {ng.thu}, {ng.ngay.split('-').reverse().join('/')}
              </h2>

              {ng.su_kien.length === 0 && ng.truc_ban.length === 0 && (
                <p className="text-sm text-gray-400 italic">Không có lịch</p>
              )}

              <ul className="space-y-1.5">
                {ng.su_kien.map((sk) => (
                  <li key={sk.id} className="text-sm flex gap-2">
                    <span className="font-medium text-gray-700 w-12 shrink-0 tabular-nums">
                      {sk.gio_bat_dau.slice(0, 5)}
                    </span>
                    <span className="flex-1">
                      {sk.tieu_de}
                      {sk.dia_diem && (
                        <span className="text-gray-500"> ({sk.dia_diem})</span>
                      )}
                      {(sk.chu_toa?.ho_ten || sk.chu_tri_text) && (
                        <span className="text-gray-500">
                          {' '}
                          — {sk.chu_toa?.ho_ten ?? sk.chu_tri_text}
                        </span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>

              {ng.truc_ban.length > 0 && (
                <div className="mt-2 pl-2 border-l-2 border-amber-300 text-sm text-gray-600">
                  {ng.truc_ban.map((t) => (
                    <div key={t}>Trực ban: {t}</div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

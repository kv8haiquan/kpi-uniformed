/**
 * src/components/lms/XemTruocExcel.tsx
 * ====================================
 * Dựng nội dung file Excel (.xlsx / .xls) ngay trong trình duyệt để giảng viên
 * đọc bài nộp mà không phải tải về mở Excel.
 *
 * Khác với Word: SheetJS đọc được CẢ .xls nhị phân (BIFF) của Office 97-2003,
 * nên Excel không có khoảng trống "định dạng cũ phải tải về" như .doc.
 *
 * ── Vì sao dựng bảng bằng React chứ không dùng `XLSX.utils.sheet_to_html` ──
 * File này do HỌC VIÊN nộp lên, còn màn chấm bài do GIẢNG VIÊN / QUẢN TRỊ mở.
 * Nhét chuỗi HTML do file sinh ra vào `innerHTML` là mở đường cho ô tính chứa
 * thẻ độc hại chạy trong phiên của người chấm — leo thang đặc quyền, không chỉ
 * là lỗi hiển thị. Đọc ra mảng giá trị rồi để React tự escape thì không có cửa đó.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';

interface Props {
  /**
   * URL bài nộp, ví dụ /uploads/lms/bai-thuc-hanh/abc_bang-ke.xlsx
   *
   * Nơi gọi PHẢI truyền `key={url}` để đổi bài nộp là dựng lại từ đầu — cùng
   * lý do đã ghi ở XemTruocWord.
   */
  url: string;
  /** Tên file gốc — dùng cho nút tải về */
  tenFile?: string | null;
  /** Chiều cao khung xem, mặc định 50vh */
  chieuCao?: string;
}

type TrangThai = 'DANG_TAI' | 'XONG' | 'LOI';

/** Một bảng tính đã đọc xong, rút về dạng mảng ô để React tự dựng. */
interface BangTinh {
  ten: string;
  hang: string[][];
  /** Số hàng / cột thật của sheet trước khi cắt bớt để hiển thị */
  tongHang: number;
  tongCot: number;
}

// Trần hiển thị. Học viên có thể nộp sheet vài chục nghìn dòng; dựng hết ra DOM
// là treo trình duyệt người chấm. Quá trần thì cắt và mời tải bản gốc.
const TRAN_HANG = 200;
const TRAN_COT = 40;

export default function XemTruocExcel({ url, tenFile, chieuCao = '50vh' }: Props) {
  const [trangThai, setTrangThai] = useState<TrangThai>('DANG_TAI');
  const [loi, setLoi] = useState<string>('');
  const [cacSheet, setCacSheet] = useState<BangTinh[]>([]);
  const [sheetDangXem, setSheetDangXem] = useState(0);

  useEffect(() => {
    // Cờ huỷ: người chấm có thể đóng modal giữa chừng
    let daHuy = false;

    (async () => {
      try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`Máy chủ trả ${resp.status}`);
        const buf = await resp.arrayBuffer();
        if (daHuy) return;

        // Nạp SheetJS theo yêu cầu — người chấm bài trắc nghiệm không phải tải
        const XLSX = await import('xlsx');
        if (daHuy) return;

        // PHAI boc qua Uint8Array: dua thang ArrayBuffer thi SheetJS doc nham
        // byte ZIP thanh chu, ra mot o chua "PK\x03\x04..." thay vi bang tinh.
        const wb = XLSX.read(new Uint8Array(buf), { type: 'array' });
        const ketQua: BangTinh[] = wb.SheetNames.map((ten) => {
          const sheet = wb.Sheets[ten];
          // header:1 → mảng của mảng, giữ đúng vị trí ô; raw:false để ngày tháng
          // và số đã định dạng hiện ra đúng như người nộp nhìn thấy trong Excel
          const tatCa = XLSX.utils.sheet_to_json<unknown[]>(sheet, {
            header: 1,
            raw: false,
            defval: '',
            blankrows: false,
          });
          const tongHang = tatCa.length;
          const tongCot = tatCa.reduce((max, h) => Math.max(max, h.length), 0);
          const hang = tatCa
            .slice(0, TRAN_HANG)
            .map((h) => Array.from({ length: Math.min(tongCot, TRAN_COT) },
                                   (_, i) => String(h[i] ?? '')));
          return { ten, hang, tongHang, tongCot };
        });

        if (daHuy) return;
        setCacSheet(ketQua);
        setSheetDangXem(0);
        setTrangThai('XONG');
      } catch (e) {
        if (daHuy) return;
        setLoi(e instanceof Error ? e.message : 'Không đọc được file');
        setTrangThai('LOI');
      }
    })();

    return () => { daHuy = true; };
  }, [url]);

  const sheet = cacSheet[sheetDangXem];
  const biCat = useMemo(
    () => !!sheet && (sheet.tongHang > TRAN_HANG || sheet.tongCot > TRAN_COT),
    [sheet],
  );

  if (trangThai === 'LOI') {
    return (
      <div className="border border-dashed border-gray-300 rounded-lg p-6 text-center bg-gray-50">
        <div className="text-3xl mb-1">📗</div>
        <p className="text-sm text-gray-700">Không hiển thị được nội dung Excel</p>
        <p className="text-xs text-gray-500 mt-0.5">{loi}</p>
        <a
          href={url}
          download={tenFile || undefined}
          className="inline-block mt-2 px-3 py-1.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
        >
          Tải file về để chấm
        </a>
      </div>
    );
  }

  if (trangThai === 'DANG_TAI') {
    return (
      <div
        className="flex flex-col items-center justify-center bg-gray-50 rounded-lg border border-gray-200"
        style={{ height: chieuCao }}
      >
        <div className="w-6 h-6 border-2 border-green-600 border-t-transparent rounded-full animate-spin mb-2" />
        <p className="text-xs text-gray-500">Đang đọc bảng tính…</p>
      </div>
    );
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      {/* Thẻ chọn sheet — chỉ hiện khi file có nhiều hơn một bảng tính */}
      {cacSheet.length > 1 && (
        <div className="flex gap-1 px-2 pt-2 pb-1 border-b border-gray-200 bg-gray-50 overflow-x-auto">
          {cacSheet.map((s, i) => (
            <button
              key={s.ten}
              type="button"
              onClick={() => setSheetDangXem(i)}
              className={`px-2.5 py-1 rounded-t text-xs whitespace-nowrap ${
                i === sheetDangXem
                  ? 'bg-white border border-b-white border-gray-300 text-gray-900 font-medium'
                  : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              {s.ten}
            </button>
          ))}
        </div>
      )}

      <div className="overflow-auto" style={{ height: chieuCao }}>
        {sheet && sheet.hang.length > 0 ? (
          <table className="text-xs border-collapse">
            <tbody>
              {sheet.hang.map((hang, r) => (
                <tr key={r} className={r === 0 ? 'bg-gray-50 font-medium' : ''}>
                  <td className="sticky left-0 z-10 bg-gray-100 text-gray-400 text-right px-1.5 py-1 border border-gray-200 select-none">
                    {r + 1}
                  </td>
                  {hang.map((o, k) => (
                    <td
                      key={k}
                      className="px-2 py-1 border border-gray-200 text-gray-800 whitespace-pre-wrap align-top"
                      style={{ maxWidth: '22rem' }}
                    >
                      {o}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-6 text-center text-sm text-gray-500">Bảng tính trống</div>
        )}
      </div>

      {biCat && sheet && (
        <div className="px-3 py-1.5 border-t border-amber-200 bg-amber-50 text-xs text-amber-800">
          Bảng tính có {sheet.tongHang} hàng × {sheet.tongCot} cột — đang hiển thị{' '}
          {Math.min(sheet.tongHang, TRAN_HANG)} hàng đầu ×{' '}
          {Math.min(sheet.tongCot, TRAN_COT)} cột.{' '}
          <a href={url} download={tenFile || undefined} className="underline font-medium">
            Tải bản gốc
          </a>{' '}
          để xem đầy đủ.
        </div>
      )}
    </div>
  );
}

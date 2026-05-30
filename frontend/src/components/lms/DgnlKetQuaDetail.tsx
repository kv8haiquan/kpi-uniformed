/**
 * components/lms/DgnlKetQuaDetail.tsx
 * ====================================
 * Render chi tiet ket qua mot bai thi DGNL.
 * Dung cho ca trang thi sinh tu xem va admin xem bai lam tung thi sinh.
 */

'use client';

import Link from 'next/link';
import type { IDgnlKetQua } from '@/types/lms';

interface Props {
  ketQua: IDgnlKetQua;
  /** Link tro ve khi bam "Quay lai". */
  backHref: string;
  /** Label nut "Quay lai". Mac dinh "Quay lai". */
  backLabel?: string;
  /** Tieu de trang. Mac dinh "Ket qua ky thi". */
  title?: string;
  /** Hien banner thong bao admin dang xem bai cua thi sinh khac. */
  adminViewBanner?: boolean;
  /** So lan thi dang hien thi (1, 2, 3...). Optional — chi truyen khi drill-down. */
  lanHienThi?: number;
  /** True khi dang xem lan THI CU (khong phai lan moi nhat) -> hien badge canh bao. */
  isLanCu?: boolean;
  /** Slot tu do (vi du dropdown chon lan thi) ben canh title. */
  lanSelector?: React.ReactNode;
}

function formatAnswer(v: any): string {
  if (v === null || v === undefined) return 'Không trả lời';
  let raw: any = v;
  if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
    if ('dap_an' in raw) raw = raw.dap_an;
    else if ('dap_an_dung' in raw) raw = raw.dap_an_dung;
    else if ('goi_y' in raw) raw = raw.goi_y;
  }
  if (raw === null || raw === undefined || raw === '') return 'Không trả lời';
  if (Array.isArray(raw)) return raw.length ? raw.join(', ') : 'Không trả lời';
  if (typeof raw === 'boolean') return raw ? 'Đúng' : 'Sai';
  if (typeof raw === 'object') return JSON.stringify(raw);
  return String(raw);
}

export default function DgnlKetQuaDetail({
  ketQua,
  backHref,
  backLabel = 'Quay lại',
  title = 'Kết quả kỳ thi',
  adminViewBanner = false,
  lanHienThi,
  isLanCu = false,
  lanSelector,
}: Props) {
  const { ky_thi, thi_sinh, ket_qua, diem_theo_linh_vuc, lich_su_thi } = ketQua;
  const isDat = ket_qua.xep_loai === 'DAT';

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 flex-wrap">
            {title}
            {lanHienThi !== undefined && (
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  isLanCu
                    ? 'bg-amber-100 text-amber-700 border border-amber-200'
                    : 'bg-blue-100 text-blue-700 border border-blue-200'
                }`}
              >
                Lần {lanHienThi}
                {isLanCu && ' · lần cũ'}
              </span>
            )}
            {lanSelector}
          </h1>
          <p className="text-sm text-gray-500">{ky_thi.ten_ky_thi}</p>
        </div>
        <Link
          href={backHref}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          {backLabel}
        </Link>
      </div>

      {adminViewBanner && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
          <span className="font-medium">🔒 Chế độ quản trị viên:</span> Bạn đang xem bài làm của{' '}
          <span className="font-semibold">{thi_sinh.ho_ten}</span> ({thi_sinh.ma_cc}).
          {isLanCu && (
            <> Đây là <span className="font-semibold">lần thi cũ</span> (lần {lanHienThi}), không phải lần thi mới nhất.</>
          )}
        </div>
      )}

      {/* Score card */}
      <div className={`rounded-xl p-6 mb-6 ${isDat ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
        <div className="flex items-center gap-6">
          <div className={`text-6xl font-bold ${isDat ? 'text-green-600' : 'text-red-600'}`}>
            {ket_qua.diem_tong}%
          </div>
          <div>
            <div className={`text-2xl font-bold ${isDat ? 'text-green-700' : 'text-red-700'}`}>
              {isDat ? 'ĐẠT' : 'KHÔNG ĐẠT'}
            </div>
            <div className="text-sm text-gray-600 mt-1">
              Điểm đạt: {ky_thi.diem_dat}% | Lần thi: {ket_qua.lan_thi}
            </div>
          </div>
        </div>
      </div>

      {/* Info grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Thông tin thí sinh</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Họ tên</span>
              <span className="font-medium">{thi_sinh.ho_ten}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Mã CC</span>
              <span className="font-medium">{thi_sinh.ma_cc}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Đơn vị</span>
              <span className="font-medium">{thi_sinh.don_vi}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Vị trí thi</span>
              <span className="font-medium">{thi_sinh.vi_tri_thi}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Thống kê</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Số câu đúng</span>
              <span className="font-medium text-green-600">{ket_qua.so_cau_dung}/{ket_qua.tong_so_cau}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Số câu sai</span>
              <span className="font-medium text-red-600">{ket_qua.so_cau_sai}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Thời gian làm bài</span>
              <span className="font-medium">
                {Math.floor(ket_qua.thoi_gian_lam_giay / 60)} phút {ket_qua.thoi_gian_lam_giay % 60} giây
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Diem theo linh vuc */}
      {diem_theo_linh_vuc && diem_theo_linh_vuc.length > 0 && (
        <div className="bg-white rounded-xl border p-4 mb-6">
          <h3 className="font-semibold text-gray-700 mb-4">Điểm theo lĩnh vực</h3>
          <div className="space-y-3">
            {diem_theo_linh_vuc.map((lv, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-700">{lv.linh_vuc}</span>
                  <span className="font-medium">
                    {lv.so_cau_dung}/{lv.tong_cau} ({lv.phan_tram}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className={`h-2.5 rounded-full ${lv.phan_tram >= 50 ? 'bg-green-500' : 'bg-red-500'}`}
                    style={{ width: `${Math.min(lv.phan_tram, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chi tiet tung cau (chi hien khi ky_thi.hien_dap_an = true) */}
      {ketQua.chi_tiet && ketQua.chi_tiet.length > 0 && (
        <div className="bg-white rounded-xl border p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Chi tiết từng câu</h3>
          <div className="space-y-4">
            {ketQua.chi_tiet.map((ct, i) => {
              const isCorrect = ct.dung === true;
              const isWrong = ct.dung === false;

              return (
                <div
                  key={i}
                  className={`rounded-lg border p-4 ${
                    isCorrect
                      ? 'bg-green-50 border-green-200'
                      : isWrong
                      ? 'bg-red-50 border-red-200'
                      : 'bg-yellow-50 border-yellow-200'
                  }`}
                >
                  <div className="flex items-start gap-2 mb-2">
                    <span className="text-lg shrink-0">{isCorrect ? '✅' : isWrong ? '❌' : '⏳'}</span>
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-medium text-gray-500">Câu {i + 1}</span>
                      {ct.noi_dung && (
                        <p className="text-sm text-gray-900 mt-0.5 whitespace-pre-wrap">{ct.noi_dung}</p>
                      )}
                    </div>
                    {ct.diem_toi_da !== undefined && (
                      <span
                        className={`text-sm font-bold shrink-0 ${
                          isCorrect ? 'text-green-700' : isWrong ? 'text-red-700' : 'text-yellow-700'
                        }`}
                      >
                        {ct.diem_dat ?? 0}/{ct.diem_toi_da}đ
                      </span>
                    )}
                  </div>

                  <div
                    className={`mt-2 px-3 py-1.5 rounded text-xs ${
                      isCorrect ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}
                  >
                    <span className="font-medium">Bạn chọn:</span> {formatAnswer(ct.tra_loi)}
                  </div>

                  {isWrong && ct.dap_an_dung !== undefined && ct.dap_an_dung !== null && (
                    <div className="mt-1.5 px-3 py-1.5 rounded text-xs bg-green-100 text-green-800">
                      <span className="font-medium">Đáp án đúng:</span> {formatAnswer(ct.dap_an_dung)}
                    </div>
                  )}

                  {ct.giai_thich && (
                    <div className="mt-2 px-3 py-2 bg-blue-50 border border-blue-100 rounded text-xs text-blue-800">
                      <span className="font-medium">Giải thích:</span> {ct.giai_thich}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Lich su thi */}
      {lich_su_thi && lich_su_thi.length > 0 && (
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Lịch sử các lần thi</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-2 px-3">Lần</th>
                  <th className="py-2 px-3">Điểm</th>
                  <th className="py-2 px-3">Xếp loại</th>
                  <th className="py-2 px-3">Số câu đúng</th>
                  <th className="py-2 px-3">Thời gian nộp</th>
                </tr>
              </thead>
              <tbody>
                {lich_su_thi.map((ls, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3">{ls.lan}</td>
                    <td className="py-2 px-3 font-medium">{ls.diem}%</td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        ls.xep_loai === 'DAT' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                      }`}>
                        {ls.xep_loai === 'DAT' ? 'Đạt' : 'Không đạt'}
                      </span>
                    </td>
                    <td className="py-2 px-3">{ls.so_cau_dung}</td>
                    <td className="py-2 px-3 text-gray-500">
                      {ls.thoi_gian_nop ? new Date(ls.thoi_gian_nop).toLocaleString('vi-VN') : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

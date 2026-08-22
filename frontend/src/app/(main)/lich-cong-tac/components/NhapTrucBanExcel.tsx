/**
 * Nhập lịch trực ban từ Excel — G4.8.
 *
 * Hai bước: chọn file → **xem trước** → mới ghi. Hệ cũ ghi thẳng, sai một dòng
 * là hỏng cả bảng mà không biết hỏng ở đâu.
 *
 * Dòng hỏng không chặn phần còn lại: bảng xem trước nói rõ dòng nào sai vì sao,
 * người nhập tự quyết định ghi phần hợp lệ hay về sửa file rồi tải lại.
 */

'use client';

import { useState } from 'react';
import { AlertTriangle, CheckCircle2, Loader2, Upload, X } from 'lucide-react';

import { trucBanApi } from '@/services/truc-ban';
import { errMsg } from '@/lib/hkg-error';
import type { IKetQuaXemTruoc } from '@/types/lich-cong-tac';

interface Props {
  onDong: () => void;
  onXong: () => void;
}

export default function NhapTrucBanExcel({ onDong, onXong }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [xem, setXem] = useState<IKetQuaXemTruoc | null>(null);
  const [ghiDe, setGhiDe] = useState(false);
  const [dangChay, setDangChay] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  const doc = async (f: File) => {
    setFile(f);
    setXem(null);
    setLoi(null);
    setDangChay(true);
    try {
      setXem(await trucBanApi.xemTruoc(f));
    } catch (e) {
      setLoi(errMsg(e, 'Không đọc được file'));
    } finally {
      setDangChay(false);
    }
  };

  const ghi = async () => {
    if (!xem) return;
    setDangChay(true);
    setLoi(null);
    try {
      const kq = await trucBanApi.ghiNhap(
        xem.dong.filter((d) => d.hop_le),
        ghiDe,
      );
      window.alert(`Đã ghi ${kq.da_ghi} dòng vào ${kq.so_o} ô.`);
      onXong();
    } catch (e) {
      setLoi(errMsg(e, 'Không ghi được'));
    } finally {
      setDangChay(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 overflow-y-auto">
      <div className="w-full max-w-4xl rounded-xl bg-white shadow-xl my-8">
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <h2 className="font-semibold text-gray-900">
            Nhập lịch trực ban từ Excel
          </h2>
          <button
            type="button"
            onClick={onDong}
            className="rounded p-1 text-gray-500 hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="inline-flex items-center gap-2 rounded-lg border border-dashed border-gray-400 px-4 py-3 text-sm cursor-pointer hover:bg-gray-50">
              <Upload className="w-4 h-4" />
              {file ? file.name : 'Chọn file Excel (.xlsx)'}
              <input
                type="file"
                accept=".xlsx,.xlsm"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) void doc(f);
                }}
              />
            </label>
            <p className="mt-1.5 text-xs text-gray-500">
              Dùng được file mẫu của phần mềm lịch cũ. Tên cột nhận nhiều biến
              thể — <code>GHI_CHU</code>, <code>Ghi chú</code>,{' '}
              <code>NOTE</code> đều được hiểu là một cột.
            </p>
          </div>

          {loi && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {loi}
            </div>
          )}

          {dangChay && !xem && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              Đang đọc file…
            </div>
          )}

          {xem && (
            <>
              <div className="flex flex-wrap gap-3 text-sm">
                <span className="inline-flex items-center gap-1.5 rounded-lg bg-green-50 border border-green-200 px-3 py-1.5 text-green-800">
                  <CheckCircle2 className="w-4 h-4" />
                  {xem.so_hop_le} dòng dùng được
                </span>
                {xem.so_loi > 0 && (
                  <span className="inline-flex items-center gap-1.5 rounded-lg bg-red-50 border border-red-200 px-3 py-1.5 text-red-800">
                    <AlertTriangle className="w-4 h-4" />
                    {xem.so_loi} dòng có lỗi — sẽ bỏ qua
                  </span>
                )}
                <span className="px-3 py-1.5 text-gray-500">
                  Tổng {xem.tong_dong} dòng
                </span>
              </div>

              <div className="max-h-80 overflow-auto rounded-lg border border-gray-200">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium">Dòng</th>
                      <th className="px-3 py-2 text-left font-medium">Ngày</th>
                      <th className="px-3 py-2 text-left font-medium">Trụ sở</th>
                      <th className="px-3 py-2 text-left font-medium">Mã CC</th>
                      <th className="px-3 py-2 text-left font-medium">Họ tên</th>
                      <th className="px-3 py-2 text-left font-medium">Chức vụ</th>
                      <th className="px-3 py-2 text-left font-medium">
                        Điện thoại
                      </th>
                      <th className="px-3 py-2 text-left font-medium">Ghi nhận</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {xem.dong.map((d) => (
                      <tr
                        key={d.dong}
                        className={d.hop_le ? '' : 'bg-red-50/70'}
                      >
                        <td className="px-3 py-1.5 tabular-nums text-gray-500">
                          {d.dong}
                        </td>
                        <td className="px-3 py-1.5 tabular-nums">
                          {d.ngay_truc
                            ? d.ngay_truc.split('-').reverse().join('/')
                            : '—'}
                        </td>
                        <td className="px-3 py-1.5">
                          {d.ten_tru_so ?? d.ma_tru_so ?? '—'}
                        </td>
                        <td className="px-3 py-1.5 font-mono text-xs text-gray-600">
                          {d.ma_cc ?? '—'}
                        </td>
                        {/* Họ tên/chức vụ/SĐT do hệ thống tra từ mã — đây là
                            chỗ người duyệt đối chiếu trước khi bấm ghi. */}
                        <td className="px-3 py-1.5">{d.ho_ten ?? '—'}</td>
                        <td className="px-3 py-1.5 text-gray-600">
                          {d.chuc_vu ?? ''}
                        </td>
                        <td className="px-3 py-1.5 text-gray-600">
                          {d.so_dien_thoai ?? ''}
                        </td>
                        <td className="px-3 py-1.5">
                          {d.hop_le ? (
                            <span className="text-green-700">sẽ ghi</span>
                          ) : (
                            <span className="text-red-700">
                              {d.loi.join('; ')}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <label className="flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={ghiDe}
                  onChange={(e) => setGhiDe(e.target.checked)}
                  className="mt-0.5"
                />
                <span>
                  <b>Thay thế lịch cũ</b> của các ô có trong file.
                  <span className="block text-gray-500">
                    Bỏ trống thì dữ liệu trong file được <i>thêm vào</i> bên
                    cạnh những người đã có — dùng khi bổ sung thêm người trực.
                  </span>
                </span>
              </label>
            </>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t border-gray-200 px-5 py-3">
          <button
            type="button"
            onClick={onDong}
            className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm hover:bg-gray-50"
          >
            Đóng
          </button>
          <button
            type="button"
            onClick={ghi}
            disabled={dangChay || !xem || xem.so_hop_le === 0}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {dangChay && <Loader2 className="w-4 h-4 animate-spin" />}
            Ghi {xem?.so_hop_le ?? 0} dòng
          </button>
        </div>
      </div>
    </div>
  );
}

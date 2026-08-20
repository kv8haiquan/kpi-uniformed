/**
 * Thêm một người vào ô trực ban — G4.7.
 *
 * Một ô có thể có nhiều người (trụ sở Chi cục thường có một lãnh đạo và một
 * công chức), nên form này chỉ thêm từng người; sửa thì xoá rồi thêm lại.
 *
 * Chọn người từ danh sách công chức của đơn vị giữ trụ sở, không gõ tay: gõ
 * tay là mỗi người viết tên và chức vụ một kiểu, mà chức vụ lại quyết định
 * thứ tự hiển thị trong ô.
 *
 * Số điện thoại điền sẵn từ lượt trực gần nhất của chính người đó, KHÔNG lấy
 * từ `public.cong_chuc` — bảng đó chỉ có 6/544 người khai số. Vẫn sửa được
 * tại chỗ vì số có thể đã đổi.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { Check, Loader2, Search, X } from 'lucide-react';

import { trucBanApi } from '@/services/truc-ban';
import { errMsg } from '@/lib/hkg-error';
import type { INguoiGoiYTruc } from '@/types/lich-cong-tac';

interface Props {
  ngay: string;
  truSoId: string;
  tenTruSo: string;
  onDong: () => void;
  onXong: () => void;
}

const oCss =
  'w-full rounded-lg border border-gray-300 px-3 py-1.5 focus:border-blue-500 focus:outline-none';

/** Số điện thoại hợp lệ: 10 số bắt đầu bằng 0. */
function sdtHopLe(s: string): boolean {
  return s === '' || /^0\d{9}$/.test(s.replace(/\s/g, ''));
}

export default function FormNguoiTruc({
  ngay,
  truSoId,
  tenTruSo,
  onDong,
  onXong,
}: Props) {
  const [ds, setDs] = useState<INguoiGoiYTruc[] | null>(null);
  const [chon, setChon] = useState('');
  const [tuKhoa, setTuKhoa] = useState('');

  const [sdt, setSdt] = useState('');
  const [caTruc, setCaTruc] = useState('CA_NGAY');
  const [loaiTruc, setLoaiTruc] = useState('CUOI_TUAN');
  const [ghiChu, setGhiChu] = useState('');

  const [dangLuu, setDangLuu] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  useEffect(() => {
    trucBanApi
      .nguoiGoiY(truSoId)
      .then(setDs)
      .catch((e) => {
        setDs([]);
        setLoi(errMsg(e, 'Không tải được danh sách công chức'));
      });
  }, [truSoId]);

  const loc = useMemo(() => {
    if (!ds) return [];
    const t = tuKhoa.trim().toLowerCase();
    if (!t) return ds;
    return ds.filter(
      (x) =>
        x.ho_ten.toLowerCase().includes(t) ||
        x.ma_cc.toLowerCase().includes(t) ||
        (x.chuc_vu ?? '').toLowerCase().includes(t),
    );
  }, [ds, tuKhoa]);

  const nguoi = ds?.find((x) => x.cong_chuc_id === chon) ?? null;

  const chonNguoi = (id: string) => {
    setChon(id);
    const n = ds?.find((x) => x.cong_chuc_id === id);
    // Chỉ điền sẵn, không khoá — số điện thoại có thể đã đổi từ lần trực trước.
    setSdt(n?.so_dien_thoai ?? '');
  };

  const luu = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nguoi) return setLoi('Chưa chọn người trực');
    if (!sdtHopLe(sdt)) {
      return setLoi('Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0');
    }

    setDangLuu(true);
    setLoi(null);
    try {
      await trucBanApi.them({
        ngay_truc: ngay,
        tru_so_id: truSoId,
        cong_chuc_id: nguoi.cong_chuc_id,
        ho_ten: nguoi.ho_ten,
        chuc_vu: nguoi.chuc_vu,
        so_dien_thoai: sdt.replace(/\s/g, '') || null,
        ca_truc: caTruc,
        loai_truc: loaiTruc,
        ghi_chu: ghiChu.trim() || null,
      });
      onXong();
    } catch (e2) {
      setLoi(errMsg(e2, 'Không lưu được'));
    } finally {
      setDangLuu(false);
    }
  };

  const laCuoiTuan = [0, 6].includes(new Date(`${ngay}T00:00:00`).getDay());

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 overflow-y-auto">
      <form
        onSubmit={luu}
        className="w-full max-w-lg rounded-xl bg-white shadow-xl my-12"
      >
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <div>
            <h2 className="font-semibold text-gray-900">Thêm người trực</h2>
            <p className="text-xs text-gray-500">
              {ngay.split('-').reverse().join('/')} — {tenTruSo}
            </p>
          </div>
          <button
            type="button"
            onClick={onDong}
            className="rounded p-1 text-gray-500 hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-3 px-5 py-4">
          <div className="text-sm">
            <span className="mb-1 block text-gray-600">Người trực *</span>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                className="w-full rounded-lg border border-gray-300 py-1.5 pl-9 pr-3 focus:border-blue-500 focus:outline-none"
                value={tuKhoa}
                onChange={(e) => setTuKhoa(e.target.value)}
                placeholder="Tìm theo tên, mã công chức hoặc chức vụ…"
                autoFocus
              />
            </div>

            {ds === null ? (
              <div className="flex items-center gap-2 py-3 text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Đang tải danh sách…
              </div>
            ) : ds.length === 0 ? (
              <p className="py-2 text-sm text-amber-700">
                Đơn vị giữ trụ sở này chưa có công chức nào trong hệ thống.
              </p>
            ) : (
              <>
                <div className="mt-1.5 max-h-56 overflow-y-auto rounded-lg border border-gray-200">
                  {loc.length === 0 ? (
                    <p className="px-3 py-3 text-sm text-gray-500">
                      Không ai khớp từ khoá.
                    </p>
                  ) : (
                    loc.map((x) => {
                      const dangChon = chon === x.cong_chuc_id;
                      return (
                        <button
                          key={x.cong_chuc_id}
                          type="button"
                          onClick={() => chonNguoi(x.cong_chuc_id)}
                          className={`flex w-full items-center gap-2 border-b border-gray-100 px-3 py-2 text-left last:border-b-0 ${
                            dangChon ? 'bg-blue-50' : 'hover:bg-gray-50'
                          }`}
                        >
                          <span className="min-w-0 flex-1">
                            <span className="block truncate font-medium text-gray-900">
                              {x.ho_ten}
                            </span>
                            <span className="block truncate text-xs text-gray-500">
                              {x.chuc_vu || 'Công chức'}
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
                <span className="mt-1 block text-xs text-gray-500">
                  {loc.length}/{ds.length} người · xếp theo chức vụ, lãnh đạo
                  lên trước
                </span>
              </>
            )}
          </div>

          <label className="block text-sm">
            <span className="block text-gray-600 mb-1">Số điện thoại</span>
            <input
              className={`${oCss} ${
                sdtHopLe(sdt) ? '' : 'border-red-400 bg-red-50'
              }`}
              value={sdt}
              onChange={(e) => setSdt(e.target.value)}
              maxLength={15}
              placeholder="0912345678"
            />
            <span className="block text-xs text-gray-500 mt-1">
              {nguoi?.so_dien_thoai
                ? 'Điền sẵn từ lượt trực gần nhất — sửa được nếu đã đổi số.'
                : 'Người này chưa từng có số trong lịch trực, nhập tay.'}
            </span>
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="block text-sm">
              <span className="block text-gray-600 mb-1">Ca trực</span>
              <select
                className={oCss}
                value={caTruc}
                onChange={(e) => setCaTruc(e.target.value)}
              >
                <option value="CA_NGAY">Cả ngày</option>
                <option value="SANG">Buổi sáng</option>
                <option value="CHIEU">Buổi chiều</option>
                <option value="DEM">Ban đêm</option>
              </select>
            </label>

            <label className="block text-sm">
              <span className="block text-gray-600 mb-1">Loại trực</span>
              <select
                className={oCss}
                value={loaiTruc}
                onChange={(e) => setLoaiTruc(e.target.value)}
              >
                <option value="CUOI_TUAN">Cuối tuần</option>
                <option value="LE_TET">Lễ, Tết</option>
                <option value="NGAY_THUONG">Ngày thường</option>
              </select>
            </label>
          </div>

          {!laCuoiTuan && loaiTruc === 'CUOI_TUAN' && (
            <p className="text-xs text-amber-700">
              Ngày này không phải Thứ Bảy hay Chủ Nhật — cân nhắc chọn
              &ldquo;Lễ, Tết&rdquo; hoặc &ldquo;Ngày thường&rdquo;.
            </p>
          )}

          <label className="block text-sm">
            <span className="block text-gray-600 mb-1">Ghi chú</span>
            <input
              className={oCss}
              value={ghiChu}
              onChange={(e) => setGhiChu(e.target.value)}
            />
          </label>
        </div>

        {loi && (
          <div className="mx-5 mb-3 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
            {loi}
          </div>
        )}

        <div className="flex justify-end gap-2 border-t border-gray-200 px-5 py-3">
          <button
            type="button"
            onClick={onDong}
            className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm hover:bg-gray-50"
          >
            Đóng
          </button>
          <button
            type="submit"
            disabled={dangLuu || !chon}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {dangLuu && <Loader2 className="w-4 h-4 animate-spin" />}
            Thêm
          </button>
        </div>
      </form>
    </div>
  );
}

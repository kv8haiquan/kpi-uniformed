/**
 * Quản trị danh mục — G4.11.
 *
 * Thay màn hình "QUẢN TRỊ DANH MỤC" của lichkv8 (sheet `SETUP`). Yêu cầu
 * chuyển đổi mục II.15 đòi đơn vị tự quản lý được loại lịch, trạng thái và
 * các danh mục cấu hình; bảng nghiệm thu XI.9 kiểm lại điểm này.
 *
 * Trước màn hình này, thêm một loại lịch phải gọi người sửa mã nguồn.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  ArrowDown,
  ArrowUp,
  Check,
  Loader2,
  Lock,
  Pencil,
  Plus,
  Trash2,
  X,
} from 'lucide-react';

import { danhMucLichApi } from '@/services/danh-muc-lich';
import { errApi } from '@/lib/hkg-error';
import type {
  IMucDanhMuc,
  INhomDanhMuc,
  NhomDanhMuc,
} from '@/types/lich-cong-tac';

const oCss =
  'w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none';

/** Lời giải thích từng nhóm — người dùng cần biết sửa ở đây thì đâu đổi theo. */
const GIAI_THICH: Record<NhomDanhMuc, string> = {
  LOAI_LICH:
    'Ô "Loại lịch" khi thêm hoặc sửa lịch công tác, và bộ lọc trên trang Lịch.',
  TRANG_THAI_LICH:
    'Ô "Trạng thái" của lịch. Phần mềm chạy theo mã của các mục này nên chỉ đổi được tên hiển thị.',
  LOAI_TAI_LIEU:
    'Ô "Loại tài liệu" khi đính kèm file vào lịch. Nhãn này hiện cạnh tên file.',
  PHONG_HOP:
    'Gợi ý cho ô "Địa điểm". Là gợi ý để mọi người gõ giống nhau, không bắt buộc chọn.',
};

export default function QuanTriDanhMucPage() {
  const [nhomInfo, setNhomInfo] = useState<INhomDanhMuc | null>(null);
  const [nhom, setNhom] = useState<NhomDanhMuc>('LOAI_LICH');
  const [muc, setMuc] = useState<IMucDanhMuc[] | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [dangLuu, setDangLuu] = useState<string | null>(null);

  // Sửa tại chỗ: chỉ một dòng mở một lúc, đỡ phải mở hộp thoại cho một ô chữ.
  const [dangSua, setDangSua] = useState<string | null>(null);
  const [nhanSua, setNhanSua] = useState('');

  const [themMo, setThemMo] = useState(false);
  const [maMoi, setMaMoi] = useState('');
  const [nhanMoi, setNhanMoi] = useState('');

  const duocSua = nhomInfo?.duoc_sua ?? false;

  const tai = useCallback(async () => {
    setLoi(null);
    try {
      setMuc(
        await danhMucLichApi.danhSach({
          nhom,
          gomCaTat: true,
          demSuDung: true,
        }),
      );
    } catch (e) {
      setMuc([]);
      setLoi(errApi(e, 'Không tải được danh mục'));
    }
  }, [nhom]);

  useEffect(() => {
    danhMucLichApi.nhom().then(setNhomInfo).catch(() => setNhomInfo(null));
  }, []);

  useEffect(() => {
    void tai();
  }, [tai]);

  const chay = async (khoa: string, viec: () => Promise<unknown>) => {
    setDangLuu(khoa);
    setLoi(null);
    try {
      await viec();
      await tai();
      return true;
    } catch (e) {
      setLoi(errApi(e, 'Không thực hiện được'));
      return false;
    } finally {
      setDangLuu(null);
    }
  };

  const luuNhan = async (m: IMucDanhMuc) => {
    const nhanGon = nhanSua.trim();
    if (!nhanGon || nhanGon === m.nhan) return setDangSua(null);
    if (await chay(m.id, () => danhMucLichApi.sua(m.id, { nhan: nhanGon }))) {
      setDangSua(null);
    }
  };

  const doiCho = async (i: number, huong: -1 | 1) => {
    if (!muc) return;
    const j = i + huong;
    if (j < 0 || j >= muc.length) return;
    await chay('sap-xep', () =>
      danhMucLichApi.sapXep([
        { id: muc[i].id, thu_tu: muc[j].thu_tu },
        { id: muc[j].id, thu_tu: muc[i].thu_tu },
      ]),
    );
  };

  const them = async () => {
    if (!maMoi.trim() || !nhanMoi.trim()) {
      return setLoi('Nhập cả mã và tên hiển thị');
    }
    if (
      await chay('them', () =>
        danhMucLichApi.them({ nhom, ma: maMoi, nhan: nhanMoi }),
      )
    ) {
      setMaMoi('');
      setNhanMoi('');
      setThemMo(false);
    }
  };

  const xoa = async (m: IMucDanhMuc) => {
    if (!window.confirm(`Xoá “${m.nhan}” khỏi danh mục?`)) return;
    await chay(m.id, () => danhMucLichApi.xoa(m.id));
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <h2 className="font-semibold text-gray-900">Quản trị danh mục</h2>
        <p className="mt-1 text-sm text-gray-600">
          Sửa ở đây là các ô chọn trong toàn bộ module Lịch công tác đổi theo,
          không cần sửa phần mềm.
        </p>

        <div className="mt-3 flex flex-wrap gap-1 border-b border-gray-200">
          {(nhomInfo?.nhom ?? []).map((n) => (
            <button
              key={n.ma}
              type="button"
              onClick={() => {
                setNhom(n.ma);
                setDangSua(null);
                setThemMo(false);
              }}
              className={`-mb-px border-b-2 px-3 py-2 text-sm ${
                nhom === n.ma
                  ? 'border-blue-600 font-medium text-blue-700'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {n.ten}
            </button>
          ))}
        </div>

        <p className="mt-2 text-xs text-gray-500">{GIAI_THICH[nhom]}</p>
      </div>

      {!duocSua && nhomInfo && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Bạn xem được danh mục nhưng không sửa được — cần quyền quản trị Lịch
          công tác.
        </p>
      )}

      {loi && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {loi}
        </p>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Tên hiển thị</th>
              <th className="px-3 py-2 text-left font-medium">Mã</th>
              <th className="px-3 py-2 text-right font-medium">Đang dùng</th>
              <th className="px-3 py-2 text-left font-medium">Tình trạng</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {muc === null ? (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-gray-500">
                  <Loader2 className="mx-auto h-5 w-5 animate-spin" />
                </td>
              </tr>
            ) : muc.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-gray-400">
                  Nhóm này chưa có mục nào.
                </td>
              </tr>
            ) : (
              muc.map((m, i) => (
                <tr
                  key={m.id}
                  className={m.is_active ? '' : 'bg-gray-50 text-gray-400'}
                >
                  <td className="px-3 py-2">
                    {dangSua === m.id ? (
                      <div className="flex items-center gap-1">
                        <input
                          autoFocus
                          className={oCss}
                          value={nhanSua}
                          maxLength={150}
                          onChange={(e) => setNhanSua(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') void luuNhan(m);
                            if (e.key === 'Escape') setDangSua(null);
                          }}
                        />
                        <button
                          type="button"
                          title="Lưu"
                          onClick={() => void luuNhan(m)}
                          className="rounded p-1 text-green-700 hover:bg-green-50"
                        >
                          <Check className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          title="Bỏ qua"
                          onClick={() => setDangSua(null)}
                          className="rounded p-1 text-gray-500 hover:bg-gray-100"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <span className="flex items-center gap-1.5">
                        {m.nhan}
                        {m.he_thong && (
                          <Lock
                            className="h-3.5 w-3.5 text-gray-400"
                            aria-label="Mục hệ thống"
                          />
                        )}
                      </span>
                    )}
                    {m.mo_ta && (
                      <span className="mt-0.5 block text-xs text-gray-500">
                        {m.mo_ta}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-gray-500">
                    {m.ma}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-gray-600">
                    {m.dang_su_dung ?? 0}
                  </td>
                  <td className="px-3 py-2">
                    {m.he_thong ? (
                      <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                        Hệ thống
                      </span>
                    ) : m.is_active ? (
                      <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-800">
                        Đang dùng
                      </span>
                    ) : (
                      <span className="rounded bg-gray-200 px-1.5 py-0.5 text-xs text-gray-600">
                        Đã tắt
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {duocSua && (
                      <div className="flex items-center justify-end gap-0.5">
                        <button
                          type="button"
                          title="Lên trên"
                          disabled={i === 0 || dangLuu !== null}
                          onClick={() => void doiCho(i, -1)}
                          className="rounded p-1 text-gray-500 hover:bg-gray-100 disabled:opacity-30"
                        >
                          <ArrowUp className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          title="Xuống dưới"
                          disabled={i === muc.length - 1 || dangLuu !== null}
                          onClick={() => void doiCho(i, 1)}
                          className="rounded p-1 text-gray-500 hover:bg-gray-100 disabled:opacity-30"
                        >
                          <ArrowDown className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          title="Sửa tên hiển thị"
                          onClick={() => {
                            setDangSua(m.id);
                            setNhanSua(m.nhan);
                          }}
                          className="rounded p-1 text-gray-600 hover:bg-gray-100"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          title={
                            m.he_thong
                              ? 'Mục hệ thống — phần mềm chạy theo mã này'
                              : m.is_active
                                ? 'Tắt: dữ liệu cũ giữ nguyên, chỉ không chọn mới được nữa'
                                : 'Bật lại'
                          }
                          disabled={m.he_thong || dangLuu === m.id}
                          onClick={() =>
                            void chay(m.id, () =>
                              danhMucLichApi.sua(m.id, {
                                is_active: !m.is_active,
                              }),
                            )
                          }
                          className="rounded px-1.5 py-1 text-xs text-gray-600 hover:bg-gray-100 disabled:opacity-30"
                        >
                          {m.is_active ? 'Tắt' : 'Bật'}
                        </button>
                        <button
                          type="button"
                          title={
                            m.he_thong
                              ? 'Mục hệ thống — không xoá được'
                              : (m.dang_su_dung ?? 0) > 0
                                ? `Còn ${m.dang_su_dung} bản ghi đang dùng — hãy Tắt thay vì xoá`
                                : 'Xoá hẳn'
                          }
                          disabled={
                            m.he_thong ||
                            (m.dang_su_dung ?? 0) > 0 ||
                            dangLuu === m.id
                          }
                          onClick={() => void xoa(m)}
                          className="rounded p-1 text-red-600 hover:bg-red-50 disabled:opacity-30"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {duocSua && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          {themMo ? (
            <div className="space-y-2">
              <div className="grid gap-2 sm:grid-cols-2">
                <label className="text-sm">
                  <span className="mb-1 block text-gray-600">
                    Tên hiển thị *
                  </span>
                  <input
                    autoFocus
                    className={oCss}
                    value={nhanMoi}
                    maxLength={150}
                    onChange={(e) => setNhanMoi(e.target.value)}
                    placeholder="vd: Toạ đàm"
                  />
                </label>
                <label className="text-sm">
                  <span className="mb-1 block text-gray-600">Mã *</span>
                  <input
                    className={`${oCss} font-mono`}
                    value={maMoi}
                    maxLength={50}
                    onChange={(e) => setMaMoi(e.target.value.toUpperCase())}
                    placeholder="vd: TOA_DAM"
                  />
                </label>
              </div>
              <p className="text-xs text-gray-500">
                Mã chỉ gồm chữ không dấu, số và gạch dưới — dữ liệu sẽ ghi theo
                mã này và <strong>không đổi được về sau</strong>. Tên hiển thị
                có dấu thì sửa lúc nào cũng được.
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={dangLuu === 'them'}
                  onClick={() => void them()}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
                >
                  {dangLuu === 'them' && (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  )}
                  Thêm
                </button>
                <button
                  type="button"
                  onClick={() => setThemMo(false)}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
                >
                  Đóng
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setThemMo(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
            >
              <Plus className="h-4 w-4" />
              Thêm mục vào nhóm này
            </button>
          )}
        </div>
      )}
    </div>
  );
}

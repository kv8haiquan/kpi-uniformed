/**
 * Soạn / sửa một ghi chú — G5.2.
 *
 * Gắn cuộc họp là tuỳ chọn: phần lớn ghi chú của hệ cũ đứng độc lập (2/6 bản
 * ghi có gắn họp), nên ô chọn cuộc họp để trống mặc định và tìm theo từ khoá
 * chứ không đổ hết danh sách hơn 600 cuộc họp vào một thẻ select.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { Loader2, X } from 'lucide-react';

import { ghiChuApi, type IGhiChuGhi } from '@/services/ghi-chu';
import { lichCongTacApi } from '@/services/lich-cong-tac';
import { errApi } from '@/lib/hkg-error';
import type { IGhiChuChiTiet, ISuKienLich } from '@/types/lich-cong-tac';

interface Props {
  /** Có nghĩa là sửa; bỏ trống là tạo mới. */
  ghiChu?: IGhiChuChiTiet | null;
  onDong: () => void;
  onXong: (id: string) => void;
}

const oCss =
  'w-full rounded-lg border border-gray-300 px-3 py-1.5 focus:border-blue-500 focus:outline-none';

export default function FormGhiChu({ ghiChu, onDong, onXong }: Props) {
  const [tieuDe, setTieuDe] = useState(ghiChu?.tieu_de ?? '');
  const [noiDung, setNoiDung] = useState(ghiChu?.noi_dung ?? '');
  const [isGhim, setIsGhim] = useState(ghiChu?.is_ghim ?? false);

  const [cuocHopId, setCuocHopId] = useState(ghiChu?.cuoc_hop?.id ?? '');
  const [nhanHop, setNhanHop] = useState(
    ghiChu?.cuoc_hop
      ? `${ghiChu.cuoc_hop.ma_lich ?? ''} ${ghiChu.cuoc_hop.tieu_de}`.trim()
      : '',
  );
  const [timHop, setTimHop] = useState('');
  const [ungVien, setUngVien] = useState<ISuKienLich[]>([]);
  const [dangTim, setDangTim] = useState(false);

  const [dangLuu, setDangLuu] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  // Chỉ gọi backend khi người dùng gõ đủ 2 ký tự, và giãn 350ms — ô này nằm
  // trong form nên mỗi phím gõ đều re-render.
  useEffect(() => {
    const tu = timHop.trim();
    if (tu.length < 2) {
      setUngVien([]);
      return;
    }
    setDangTim(true);
    const h = setTimeout(() => {
      lichCongTacApi
        .danhSach({ 'tim-kiem': tu, 'so-dong': 10, 'moi-truoc': true })
        .then((r) => setUngVien(r.data.data))
        .catch(() => setUngVien([]))
        .finally(() => setDangTim(false));
    }, 350);
    return () => clearTimeout(h);
  }, [timHop]);

  const daChonHop = useMemo(() => Boolean(cuocHopId), [cuocHopId]);

  const luu = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tieuDe.trim()) return setLoi('Tiêu đề không được để trống');

    setDangLuu(true);
    setLoi(null);
    const du_lieu: IGhiChuGhi = {
      tieu_de: tieuDe.trim(),
      noi_dung: noiDung.trim() || null,
      cuoc_hop_id: cuocHopId || null,
      is_ghim: isGhim,
    };
    try {
      const kq = ghiChu
        ? await ghiChuApi.capNhat(ghiChu.id, du_lieu)
        : await ghiChuApi.tao(du_lieu);
      onXong(kq.id);
    } catch (e2) {
      setLoi(errApi(e2, 'Không lưu được ghi chú'));
    } finally {
      setDangLuu(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4">
      <form
        onSubmit={luu}
        className="my-12 w-full max-w-2xl rounded-xl bg-white shadow-xl"
      >
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <h2 className="font-semibold text-gray-900">
            {ghiChu ? 'Sửa ghi chú' : 'Ghi chú mới'}
          </h2>
          <button
            type="button"
            onClick={onDong}
            className="rounded p-1 text-gray-500 hover:bg-gray-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-3 px-5 py-4">
          <label className="block text-sm">
            <span className="mb-1 block text-gray-600">Tiêu đề *</span>
            <input
              className={oCss}
              value={tieuDe}
              onChange={(e) => setTieuDe(e.target.value)}
              maxLength={300}
              autoFocus
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block text-gray-600">Nội dung</span>
            <textarea
              className={`${oCss} min-h-[160px]`}
              value={noiDung}
              onChange={(e) => setNoiDung(e.target.value)}
            />
          </label>

          <div className="rounded-lg border border-gray-200 p-3">
            <span className="mb-1 block text-sm text-gray-600">
              Gắn vào cuộc họp / sự kiện (không bắt buộc)
            </span>
            {daChonHop ? (
              <div className="flex items-center justify-between gap-2 rounded-lg bg-blue-50 px-3 py-1.5 text-sm text-blue-900">
                <span className="truncate">{nhanHop}</span>
                <button
                  type="button"
                  onClick={() => {
                    setCuocHopId('');
                    setNhanHop('');
                  }}
                  className="shrink-0 text-xs text-blue-700 underline"
                >
                  Bỏ gắn
                </button>
              </div>
            ) : (
              <>
                <input
                  className={oCss}
                  value={timHop}
                  onChange={(e) => setTimHop(e.target.value)}
                  placeholder="Gõ ít nhất 2 ký tự để tìm…"
                />
                {dangTim && (
                  <p className="mt-1 flex items-center gap-1 text-xs text-gray-500">
                    <Loader2 className="h-3 w-3 animate-spin" /> Đang tìm…
                  </p>
                )}
                {ungVien.length > 0 && (
                  <div className="mt-2 max-h-44 overflow-y-auto rounded-lg border border-gray-200">
                    {ungVien.map((sk) => (
                      <button
                        key={sk.id}
                        type="button"
                        onClick={() => {
                          setCuocHopId(sk.id);
                          setNhanHop(
                            `${sk.ma_lich ?? ''} ${sk.tieu_de}`.trim(),
                          );
                          setTimHop('');
                        }}
                        className="block w-full border-b border-gray-100 px-3 py-2 text-left text-sm last:border-b-0 hover:bg-gray-50"
                      >
                        {sk.ma_lich && (
                          <span className="mr-1 rounded bg-gray-100 px-1 font-mono text-xs text-gray-600">
                            {sk.ma_lich}
                          </span>
                        )}
                        {sk.tieu_de}
                        <span className="block text-xs text-gray-500">
                          {(sk.ngay_hien_thi ?? sk.ngay_hop ?? '')
                            .split('-')
                            .reverse()
                            .join('/')}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={isGhim}
              onChange={(e) => setIsGhim(e.target.checked)}
            />
            Ghim lên đầu danh sách
          </label>
        </div>

        {loi && (
          <div className="mx-5 mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {loi}
          </div>
        )}

        <div className="flex justify-end gap-2 border-t border-gray-200 px-5 py-3">
          <button
            type="button"
            onClick={onDong}
            className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm hover:bg-gray-50"
          >
            Huỷ
          </button>
          <button
            type="submit"
            disabled={dangLuu}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {dangLuu && <Loader2 className="h-4 w-4 animate-spin" />}
            Lưu
          </button>
        </div>
      </form>
    </div>
  );
}

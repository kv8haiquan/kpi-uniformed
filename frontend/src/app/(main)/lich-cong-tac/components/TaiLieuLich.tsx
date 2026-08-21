/**
 * Tài liệu của một sự kiện lịch công tác — quản lý ngay trên trang lịch.
 *
 * Trước đây trang chi tiết chỉ có một đường dẫn sang màn hình tài liệu của
 * Họp Không Giấy. Đường đó hỏng với phần lớn người dùng: màn hình kia áp luật
 * quyền của cuộc họp (chỉ người được mời), mà sự kiện lịch thì không có danh
 * sách mời — nên công chức thường bấm vào là 403, còn Văn phòng thì không tải
 * tài liệu lên được vì không phải chủ toạ hay thư ký.
 *
 * Quyền dùng đúng luật của nút Sửa lịch: quản trị lịch hoặc người tạo sự kiện.
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Download, Eye, FileText, Loader2, Trash2, Upload } from 'lucide-react';

import { danhMucLichApi } from '@/services/danh-muc-lich';
import { taiLieuApi } from '@/services/hkg';
import { errApi } from '@/lib/hkg-error';
import {
  ACCEPT_FILE,
  LOAI_TAI_LIEU,
  coDaiFile,
  moTaFileHong,
  taiNhieuFile,
} from '@/lib/tai-lieu-upload';
import type {
  IMucPhanQuyen,
  ITaiLieuListItem,
  PhanQuyenTaiLieu,
} from '@/types/hkg';

interface Props {
  cuocHopId: string;
  /** Người đang xem có được tải lên / xoá không — cùng điều kiện với nút Sửa. */
  quanLyDuoc: boolean;
  /** Báo cho trang cha để cập nhật số tài liệu đang hiển thị. */
  onDoiSoLuong?: (n: number) => void;
}

export default function TaiLieuLich({
  cuocHopId,
  quanLyDuoc,
  onDoiSoLuong,
}: Props) {
  const [ds, setDs] = useState<ITaiLieuListItem[] | null>(null);
  const [muc, setMuc] = useState<IMucPhanQuyen[]>([]);
  const [mucUpload, setMucUpload] = useState<PhanQuyenTaiLieu>('CONG_KHAI');
  const [loaiTaiLieu, setLoaiTaiLieu] = useState(LOAI_TAI_LIEU[0]);
  const [dsLoai, setDsLoai] = useState<string[]>(LOAI_TAI_LIEU);
  const [dangTai, setDangTai] = useState<string[]>([]);
  const [conLai, setConLai] = useState(0);
  const [dangXoa, setDangXoa] = useState<string | null>(null);
  const [keoVao, setKeoVao] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  const oFile = useRef<HTMLInputElement>(null);
  const dangTaiLen = dangTai.length > 0 || conLai > 0;

  const tai = useCallback(async () => {
    try {
      const list = await taiLieuApi.listByCuocHop(cuocHopId);
      setDs(list);
      onDoiSoLuong?.(list.length);
    } catch (e) {
      setDs([]);
      setLoi(errApi(e, 'Không tải được danh sách tài liệu'));
    }
    // onDoiSoLuong do trang cha truyền vào, không đưa vào phụ thuộc để tránh
    // vòng lặp khi cha vẽ lại.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cuocHopId]);

  useEffect(() => {
    void tai();
  }, [tai]);

  useEffect(() => {
    if (!quanLyDuoc) return;
    taiLieuApi.mucPhanQuyen().then(setMuc).catch(() => setMuc([]));
    // Loại tài liệu do đơn vị tự quản trị (G4.11). Gọi hỏng thì giữ 7 mục
    // gieo sẵn — thà chọn được loại cũ còn hơn ô chọn rỗng.
    danhMucLichApi
      .danhSach({ nhom: 'LOAI_TAI_LIEU' })
      .then((ds) => {
        if (ds.length === 0) return;
        const nhan = ds.map((m) => m.nhan);
        setDsLoai(nhan);
        setLoaiTaiLieu(nhan[0]);
      })
      .catch(() => undefined);
  }, [quanLyDuoc]);

  /**
   * Nhận nhiều file một lượt — trước đây chỉ lấy `files[0]`, nên chọn 5 file
   * thì 4 file lặng lẽ rơi mất mà không báo gì.
   *
   * Phải chụp `FileList` thành mảng NGAY, đồng bộ: đây là danh sách sống, ô
   * chọn file bị đặt lại `value` là nó rỗng theo.
   */
  const themFile = async (ds: FileList | File[] | null) => {
    const files = Array.from(ds ?? []);
    if (files.length === 0) return;

    setLoi(null);
    setConLai(files.length);
    try {
      const hong = await taiNhieuFile({
        cuocHopId,
        files,
        moTa: loaiTaiLieu,
        phanQuyen: mucUpload,
        onDoiDangTai: setDangTai,
      });
      await tai();
      if (hong.length > 0) {
        setLoi(
          `${hong.length}/${files.length} file không tải lên được: ` +
            moTaFileHong(hong),
        );
      }
    } catch (e) {
      setLoi(errApi(e, 'Không tải được file lên'));
    } finally {
      setDangTai([]);
      setConLai(0);
    }
  };

  const moFile = async (id: string, taiVe: boolean) => {
    setLoi(null);
    try {
      const r = taiVe
        ? await taiLieuApi.taiUrl(id)
        : await taiLieuApi.xemUrl(id);
      window.open(r.url, '_blank', 'noopener');
    } catch (e) {
      setLoi(errApi(e, 'Không mở được tài liệu'));
    }
  };

  const xoaFile = async (id: string, ten: string) => {
    if (!window.confirm(`Xoá tài liệu "${ten}"?`)) return;
    setDangXoa(id);
    setLoi(null);
    try {
      await taiLieuApi.xoa(id);
      await tai();
    } catch (e) {
      setLoi(errApi(e, 'Không xoá được tài liệu'));
    } finally {
      setDangXoa(null);
    }
  };

  const mucDatDuoc = muc.filter((m) => m.dat_duoc);

  return (
    <div className="space-y-2">
      {quanLyDuoc && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setKeoVao(true);
          }}
          onDragLeave={() => setKeoVao(false)}
          onDrop={(e) => {
            e.preventDefault();
            setKeoVao(false);
            void themFile(e.dataTransfer.files);
          }}
          className={`flex flex-wrap items-center gap-2 rounded-lg border-2 border-dashed p-2 ${
            keoVao ? 'border-blue-400 bg-blue-50' : 'border-transparent'
          }`}
        >
          <select
            value={loaiTaiLieu}
            onChange={(e) => setLoaiTaiLieu(e.target.value)}
            className="rounded-lg border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          >
            {dsLoai.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>

          {mucDatDuoc.length > 1 && (
            <select
              value={mucUpload}
              onChange={(e) => setMucUpload(e.target.value as PhanQuyenTaiLieu)}
              title={muc.find((m) => m.ma === mucUpload)?.mo_ta}
              className="rounded-lg border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
            >
              {mucDatDuoc.map((m) => (
                <option key={m.ma} value={m.ma}>
                  {m.ten}
                </option>
              ))}
            </select>
          )}

          {/* Ô chọn file nằm trong nhãn — bấm nhãn là trình duyệt tự mở hộp
              thoại, khỏi phụ thuộc ref và khỏi lệ thuộc vào .click(). */}
          <label
            className={`inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 ${
              dangTaiLen ? 'pointer-events-none opacity-40' : 'cursor-pointer'
            }`}
          >
            <input
              ref={oFile}
              type="file"
              multiple
              accept={ACCEPT_FILE}
              disabled={dangTaiLen}
              className="hidden"
              onChange={(e) => {
                void themFile(e.target.files);
                // Dọn sau khi đã chụp mảng — để chọn lại đúng file vừa xoá
                // vẫn nổ `change`.
                e.target.value = '';
              }}
            />
            {dangTaiLen ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            {dangTaiLen
              ? `Đang tải ${conLai} file…`
              : 'Thêm tài liệu'}
          </label>

          <span className="text-xs text-gray-500">
            Chọn nhiều file một lúc, hoặc kéo thả vào đây
          </span>
        </div>
      )}

      {ds === null ? (
        <span className="inline-flex items-center gap-1.5 text-sm text-gray-500">
          <Loader2 className="h-4 w-4 animate-spin" /> Đang tải…
        </span>
      ) : ds.length === 0 ? (
        <p className="text-sm text-gray-400">
          {quanLyDuoc
            ? 'Chưa có tài liệu — bấm Thêm tài liệu để tải lên.'
            : 'Chưa có tài liệu.'}
        </p>
      ) : (
        <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
          {ds.map((t) => (
            <li key={t.id} className="flex items-center gap-2 px-3 py-2 text-sm">
              <FileText className="h-4 w-4 shrink-0 text-gray-400" />
              <span className="min-w-0 flex-1">
                <span className="block truncate">{t.ten_tai_lieu}</span>
                <span className="text-xs text-gray-500">
                  {coDaiFile(t.file_size)}
                  {t.mo_ta ? ` · ${t.mo_ta}` : ''}
                  {t.phan_quyen !== 'CONG_KHAI' && (
                    <span className="ml-1.5 rounded bg-amber-100 px-1.5 py-0.5 text-amber-900">
                      {muc.find((m) => m.ma === t.phan_quyen)?.ten ??
                        'Hạn chế người xem'}
                    </span>
                  )}
                </span>
              </span>
              <button
                type="button"
                title="Xem"
                onClick={() => void moFile(t.id, false)}
                className="rounded p-1 text-gray-600 hover:bg-gray-100"
              >
                <Eye className="h-4 w-4" />
              </button>
              {t.cho_phep_tai && (
                <button
                  type="button"
                  title="Tải về"
                  onClick={() => void moFile(t.id, true)}
                  className="rounded p-1 text-gray-600 hover:bg-gray-100"
                >
                  <Download className="h-4 w-4" />
                </button>
              )}
              {quanLyDuoc && (
                <button
                  type="button"
                  title="Xoá"
                  disabled={dangXoa === t.id}
                  onClick={() => void xoaFile(t.id, t.ten_tai_lieu)}
                  className="rounded p-1 text-red-600 hover:bg-red-50 disabled:opacity-40"
                >
                  {dangXoa === t.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {loi && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {loi}
        </p>
      )}
    </div>
  );
}

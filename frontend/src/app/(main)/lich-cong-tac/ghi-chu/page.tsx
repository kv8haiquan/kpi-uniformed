/**
 * /lich-cong-tac/ghi-chu — sổ tay cá nhân và chia sẻ (G5.2).
 *
 * Thay `MEETING_NOTE` của lichkv8. Hai điều màn hình phải nói rõ, vì đây là
 * dữ liệu riêng và người dùng cần tin được điều đó:
 *
 * 1. Ghi chú chỉ mình đọc cho tới khi tự tay chia sẻ — nhắc thẳng trên đầu
 *    trang, không giấu trong tài liệu hướng dẫn.
 * 2. Ghi chú người khác gửi cho mình thì CHỈ ĐỌC — nút Sửa/Xoá không hiện,
 *    chứ không hiện rồi báo lỗi khi bấm.
 */

'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Download,
  Eye,
  FileText,
  Loader2,
  Lock,
  Paperclip,
  Pencil,
  Pin,
  Plus,
  Share2,
  Trash2,
  UserMinus,
} from 'lucide-react';

import FormGhiChu from '../components/FormGhiChu';
import ModalChiaSe from '../components/ModalChiaSe';
import { ghiChuApi } from '@/services/ghi-chu';
import { errApi } from '@/lib/hkg-error';
import type {
  IGhiChuChiTiet,
  IGhiChuTomTat,
  PhamViGhiChu,
} from '@/types/lich-cong-tac';

const PHAM_VI: { ma: PhamViGhiChu; nhan: string }[] = [
  { ma: 'TAT_CA', nhan: 'Tất cả' },
  { ma: 'CUA_TOI', nhan: 'Của tôi' },
  { ma: 'DUOC_CHIA_SE', nhan: 'Được chia sẻ' },
];

const SO_DONG = 20;

function ngayVN(s?: string | null): string {
  if (!s) return '';
  return s.slice(0, 10).split('-').reverse().join('/');
}

function coDaiFile(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export default function GhiChuPage() {
  const qs = useSearchParams();
  const idTuUrl = qs.get('ghi_chu_id');

  const [phamVi, setPhamVi] = useState<PhamViGhiChu>('TAT_CA');
  const [tuKhoa, setTuKhoa] = useState('');
  const [tuKhoaGui, setTuKhoaGui] = useState('');
  const [chiChuaDoc, setChiChuaDoc] = useState(false);
  const [trang, setTrang] = useState(1);

  const [ds, setDs] = useState<IGhiChuTomTat[]>([]);
  const [tong, setTong] = useState(0);
  const [soChuaDoc, setSoChuaDoc] = useState(0);
  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState<string | null>(null);

  const [chon, setChon] = useState<string | null>(idTuUrl);
  const [chiTiet, setChiTiet] = useState<IGhiChuChiTiet | null>(null);
  const [dangTaiChiTiet, setDangTaiChiTiet] = useState(false);

  const [moForm, setMoForm] = useState(false);
  const [sua, setSua] = useState<IGhiChuChiTiet | null>(null);
  const [moChiaSe, setMoChiaSe] = useState(false);
  const [dangTaiLen, setDangTaiLen] = useState(false);

  const oFile = useRef<HTMLInputElement>(null);

  const taiDanhSach = useCallback(async () => {
    setDangTai(true);
    setLoi(null);
    try {
      const r = await ghiChuApi.danhSach({
        'pham-vi': phamVi,
        'tu-khoa': tuKhoaGui || undefined,
        'chi-chua-doc': chiChuaDoc || undefined,
        trang,
        'so-dong': SO_DONG,
      });
      setDs(r.data.data);
      setTong(r.data.pagination?.total_items ?? r.data.data.length);
    } catch (e) {
      setLoi(errApi(e, 'Không tải được danh sách ghi chú'));
    } finally {
      setDangTai(false);
    }
  }, [phamVi, tuKhoaGui, chiChuaDoc, trang]);

  const demChuaDoc = useCallback(() => {
    ghiChuApi.soChuaDoc().then(setSoChuaDoc).catch(() => setSoChuaDoc(0));
  }, []);

  useEffect(() => {
    void taiDanhSach();
  }, [taiDanhSach]);

  useEffect(() => {
    demChuaDoc();
  }, [demChuaDoc]);

  // Mở chi tiết. Ghi chú người khác gửi thì đánh dấu đã đọc luôn — mở ra xem
  // chính là đã đọc, bắt bấm thêm một nút nữa chỉ làm số đếm sai sự thật.
  const moChiTiet = useCallback(
    async (id: string) => {
      setChon(id);
      setDangTaiChiTiet(true);
      try {
        const ct = await ghiChuApi.chiTiet(id);
        setChiTiet(ct);
        if (ct.la_cua_toi === false && ct.da_doc === false) {
          await ghiChuApi.danhDauDaDoc(id);
          setChiTiet({ ...ct, da_doc: true });
          setDs((truoc) =>
            truoc.map((x) => (x.id === id ? { ...x, da_doc: true } : x)),
          );
          demChuaDoc();
        }
      } catch (e) {
        setLoi(errApi(e, 'Không mở được ghi chú'));
        setChiTiet(null);
      } finally {
        setDangTaiChiTiet(false);
      }
    },
    [demChuaDoc],
  );

  useEffect(() => {
    if (chon && !chiTiet) void moChiTiet(chon);
    // Chỉ chạy khi id đổi — moChiTiet tự ổn định qua useCallback.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chon]);

  const daChiaSe = useMemo(
    () => new Set((chiTiet?.chia_se ?? []).map((c) => c.nguoi_nhan_id)),
    [chiTiet],
  );

  const lamMoi = async (id?: string) => {
    await taiDanhSach();
    demChuaDoc();
    if (id) {
      setChiTiet(null);
      await moChiTiet(id);
    }
  };

  const xoaGhiChu = async (id: string) => {
    if (!confirm('Xoá ghi chú này? Thao tác không hoàn tác được.')) return;
    try {
      await ghiChuApi.xoa(id);
      setChon(null);
      setChiTiet(null);
      await lamMoi();
    } catch (e) {
      setLoi(errApi(e, 'Không xoá được ghi chú'));
    }
  };

  const dinhKem = async (f: File | null) => {
    if (!f || !chiTiet) return;
    setDangTaiLen(true);
    try {
      await ghiChuApi.themDinhKem(chiTiet.id, f);
      await lamMoi(chiTiet.id);
    } catch (e) {
      setLoi(errApi(e, 'Không tải được file lên'));
    } finally {
      setDangTaiLen(false);
      if (oFile.current) oFile.current.value = '';
    }
  };

  const moFile = async (taiLieuId: string, tai: boolean) => {
    try {
      const url = tai
        ? await ghiChuApi.urlTai(taiLieuId)
        : await ghiChuApi.urlXem(taiLieuId);
      window.open(url, '_blank', 'noopener');
    } catch (e) {
      setLoi(errApi(e, 'Không mở được file'));
    }
  };

  const soTrang = Math.max(1, Math.ceil(tong / SO_DONG));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-gray-200 bg-white p-3">
        <div className="flex gap-1">
          {PHAM_VI.map((p) => (
            <button
              key={p.ma}
              type="button"
              onClick={() => {
                setPhamVi(p.ma);
                setTrang(1);
              }}
              className={`rounded-lg px-3 py-1.5 text-sm ${
                phamVi === p.ma
                  ? 'bg-blue-600 text-white'
                  : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {p.nhan}
            </button>
          ))}
        </div>

        <form
          className="flex flex-1 gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            setTuKhoaGui(tuKhoa.trim());
            setTrang(1);
          }}
        >
          <input
            className="min-w-[180px] flex-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
            value={tuKhoa}
            onChange={(e) => setTuKhoa(e.target.value)}
            placeholder="Tìm trong tiêu đề và nội dung…"
          />
          <button
            type="submit"
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
          >
            Tìm
          </button>
        </form>

        <label className="flex items-center gap-1.5 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={chiChuaDoc}
            onChange={(e) => {
              setChiChuaDoc(e.target.checked);
              setTrang(1);
            }}
          />
          Chỉ chưa đọc
          {soChuaDoc > 0 && (
            <span className="rounded-full bg-red-100 px-1.5 text-xs text-red-700">
              {soChuaDoc}
            </span>
          )}
        </label>

        <button
          type="button"
          onClick={() => {
            setSua(null);
            setMoForm(true);
          }}
          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" /> Ghi chú mới
        </button>
      </div>

      <p className="flex items-center gap-1.5 text-xs text-gray-500">
        <Lock className="h-3.5 w-3.5" />
        Ghi chú chỉ mình bạn đọc được — kể cả quản trị hệ thống — cho tới khi
        bạn tự chia sẻ.
      </p>

      {loi && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {loi}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
        {/* ── danh sách ─────────────────────────────────────────── */}
        <div className="space-y-2">
          {dangTai ? (
            <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-6 text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" /> Đang tải…
            </div>
          ) : ds.length === 0 ? (
            <div className="rounded-lg border border-gray-200 bg-white py-12 text-center text-sm text-gray-500">
              Chưa có ghi chú nào.
            </div>
          ) : (
            ds.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => {
                  setChiTiet(null);
                  void moChiTiet(g.id);
                }}
                className={`block w-full rounded-lg border px-3 py-2 text-left ${
                  chon === g.id
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-200 bg-white hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start gap-1.5">
                  {g.is_ghim && (
                    <Pin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600" />
                  )}
                  <span className="flex-1 font-medium text-gray-900">
                    {g.tieu_de}
                  </span>
                  {g.da_doc === false && (
                    <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-red-500" />
                  )}
                </div>
                {g.trich_yeu && (
                  <p className="mt-0.5 line-clamp-2 text-xs text-gray-600">
                    {g.trich_yeu}
                  </p>
                )}
                <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-gray-500">
                  <span>{ngayVN(g.updated_at)}</span>
                  {!g.la_cua_toi && <span>· {g.nguoi_chia_se} gửi</span>}
                  {g.so_tai_lieu > 0 && (
                    <span className="inline-flex items-center gap-0.5">
                      <Paperclip className="h-3 w-3" />
                      {g.so_tai_lieu}
                    </span>
                  )}
                  {g.la_cua_toi && g.so_chia_se > 0 && (
                    <span className="inline-flex items-center gap-0.5">
                      <Share2 className="h-3 w-3" />
                      {g.so_chia_se}
                    </span>
                  )}
                  {g.ten_cuoc_hop && (
                    <span className="truncate text-blue-700">
                      {g.ma_lich ? `${g.ma_lich} · ` : ''}
                      {g.ten_cuoc_hop}
                    </span>
                  )}
                </div>
              </button>
            ))
          )}

          {soTrang > 1 && (
            <div className="flex items-center justify-between px-1 text-sm text-gray-600">
              <button
                type="button"
                disabled={trang <= 1}
                onClick={() => setTrang((t) => t - 1)}
                className="rounded border border-gray-300 px-2 py-1 disabled:opacity-40"
              >
                Trước
              </button>
              <span>
                Trang {trang}/{soTrang} · {tong} ghi chú
              </span>
              <button
                type="button"
                disabled={trang >= soTrang}
                onClick={() => setTrang((t) => t + 1)}
                className="rounded border border-gray-300 px-2 py-1 disabled:opacity-40"
              >
                Sau
              </button>
            </div>
          )}
        </div>

        {/* ── chi tiết ──────────────────────────────────────────── */}
        <div className="rounded-lg border border-gray-200 bg-white">
          {dangTaiChiTiet ? (
            <div className="flex items-center gap-2 px-5 py-16 text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" /> Đang mở…
            </div>
          ) : !chiTiet ? (
            <div className="px-5 py-16 text-center text-sm text-gray-500">
              Chọn một ghi chú để xem nội dung.
            </div>
          ) : (
            <>
              <div className="flex items-start justify-between gap-3 border-b border-gray-200 px-5 py-3">
                <div className="min-w-0">
                  <h2 className="flex items-center gap-1.5 font-semibold text-gray-900">
                    {chiTiet.is_ghim && (
                      <Pin className="h-4 w-4 text-amber-600" />
                    )}
                    {chiTiet.tieu_de}
                  </h2>
                  <p className="text-xs text-gray-500">
                    {chiTiet.la_cua_toi
                      ? `Của bạn · cập nhật ${ngayVN(chiTiet.updated_at)}`
                      : `${chiTiet.nguoi_tao} chia sẻ · ${ngayVN(chiTiet.created_at)}`}
                  </p>
                  {chiTiet.cuoc_hop && (
                    <p className="mt-1 text-xs text-blue-700">
                      {chiTiet.cuoc_hop.ma_lich && (
                        <span className="mr-1 rounded bg-gray-100 px-1 font-mono text-gray-600">
                          {chiTiet.cuoc_hop.ma_lich}
                        </span>
                      )}
                      {chiTiet.cuoc_hop.tieu_de} ·{' '}
                      {ngayVN(chiTiet.cuoc_hop.ngay_hop)}
                    </p>
                  )}
                </div>

                {chiTiet.la_cua_toi && (
                  <div className="flex shrink-0 gap-1">
                    <button
                      type="button"
                      title="Chia sẻ"
                      onClick={() => setMoChiaSe(true)}
                      className="rounded p-1.5 text-gray-600 hover:bg-gray-100"
                    >
                      <Share2 className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      title="Sửa"
                      onClick={() => {
                        setSua(chiTiet);
                        setMoForm(true);
                      }}
                      className="rounded p-1.5 text-gray-600 hover:bg-gray-100"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      title="Xoá"
                      onClick={() => void xoaGhiChu(chiTiet.id)}
                      className="rounded p-1.5 text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>

              <div className="space-y-4 px-5 py-4">
                {chiTiet.loi_nhan && (
                  <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
                    Lời nhắn: {chiTiet.loi_nhan}
                  </p>
                )}

                <p className="whitespace-pre-wrap text-sm text-gray-800">
                  {chiTiet.noi_dung || (
                    <span className="text-gray-400">(Không có nội dung)</span>
                  )}
                </p>

                {/* đính kèm */}
                <div>
                  <div className="mb-1 flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-700">
                      File đính kèm ({chiTiet.tai_lieu.length})
                    </h3>
                    {chiTiet.la_cua_toi && (
                      <>
                        <input
                          ref={oFile}
                          type="file"
                          className="hidden"
                          onChange={(e) =>
                            void dinhKem(e.target.files?.[0] ?? null)
                          }
                        />
                        <button
                          type="button"
                          disabled={dangTaiLen}
                          onClick={() => oFile.current?.click()}
                          className="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-2 py-1 text-xs hover:bg-gray-50 disabled:opacity-40"
                        >
                          {dangTaiLen ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Paperclip className="h-3 w-3" />
                          )}
                          Đính kèm
                        </button>
                      </>
                    )}
                  </div>
                  {chiTiet.tai_lieu.length === 0 ? (
                    <p className="text-xs text-gray-500">Chưa có file nào.</p>
                  ) : (
                    <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
                      {chiTiet.tai_lieu.map((t) => (
                        <li
                          key={t.id}
                          className="flex items-center gap-2 px-3 py-2 text-sm"
                        >
                          <FileText className="h-4 w-4 shrink-0 text-gray-400" />
                          <span className="flex-1 truncate">
                            {t.ten_tai_lieu}
                            <span className="ml-1 text-xs text-gray-500">
                              {coDaiFile(t.file_size)}
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
                          <button
                            type="button"
                            title="Tải về"
                            onClick={() => void moFile(t.id, true)}
                            className="rounded p-1 text-gray-600 hover:bg-gray-100"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                          {chiTiet.la_cua_toi && (
                            <button
                              type="button"
                              title="Xoá file"
                              onClick={async () => {
                                try {
                                  await ghiChuApi.xoaDinhKem(t.id);
                                  await lamMoi(chiTiet.id);
                                } catch (e) {
                                  setLoi(errApi(e, 'Không xoá được file'));
                                }
                              }}
                              className="rounded p-1 text-red-600 hover:bg-red-50"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* chia sẻ — chỉ chủ ghi chú thấy */}
                {chiTiet.la_cua_toi && (
                  <div>
                    <h3 className="mb-1 text-sm font-medium text-gray-700">
                      Đã chia sẻ cho ({chiTiet.chia_se.length})
                    </h3>
                    {chiTiet.chia_se.length === 0 ? (
                      <p className="text-xs text-gray-500">
                        Chưa chia sẻ cho ai — ghi chú này chỉ mình bạn đọc được.
                      </p>
                    ) : (
                      <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
                        {chiTiet.chia_se.map((c) => (
                          <li
                            key={c.id}
                            className="flex items-center gap-2 px-3 py-2 text-sm"
                          >
                            <span className="flex-1">
                              {c.ho_ten}
                              {c.chuc_vu && (
                                <span className="text-gray-500">
                                  {' '}
                                  — {c.chuc_vu}
                                </span>
                              )}
                            </span>
                            <span
                              className={`text-xs ${
                                c.da_doc ? 'text-green-700' : 'text-gray-500'
                              }`}
                            >
                              {c.da_doc
                                ? `đã đọc ${ngayVN(c.thoi_diem_doc)}`
                                : 'chưa đọc'}
                            </span>
                            <button
                              type="button"
                              title="Thu hồi"
                              onClick={async () => {
                                try {
                                  await ghiChuApi.thuHoi(chiTiet.id, c.id);
                                  await lamMoi(chiTiet.id);
                                } catch (e) {
                                  setLoi(errApi(e, 'Không thu hồi được'));
                                }
                              }}
                              className="rounded p-1 text-gray-600 hover:bg-gray-100"
                            >
                              <UserMinus className="h-4 w-4" />
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {moForm && (
        <FormGhiChu
          ghiChu={sua}
          onDong={() => setMoForm(false)}
          onXong={async (id) => {
            setMoForm(false);
            await lamMoi(id);
          }}
        />
      )}

      {moChiaSe && chiTiet && (
        <ModalChiaSe
          ghiChuId={chiTiet.id}
          tieuDe={chiTiet.tieu_de}
          daChiaSe={daChiaSe}
          onDong={() => setMoChiaSe(false)}
          onXong={async () => {
            setMoChiaSe(false);
            await lamMoi(chiTiet.id);
          }}
        />
      )}
    </div>
  );
}

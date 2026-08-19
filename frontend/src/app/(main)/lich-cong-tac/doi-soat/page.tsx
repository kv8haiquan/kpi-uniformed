/**
 * /lich-cong-tac/doi-soat — đối soát 412 file còn lại của đợt di trú (G4.9).
 *
 * Màn hình DÙNG MỘT LẦN. Xong việc thì bỏ mục này khỏi thanh tab.
 *
 * Điểm phải giữ đúng: đây là danh sách để NGƯỜI chọn, không phải nút xác nhận
 * một chạm. Ngày nào cũng có 2–8 cuộc họp — riêng "Chỉ đạo trực ban" lặp gần
 * như hằng ngày — nên không thư mục nào có ứng viên duy nhất. Khi máy không
 * thấy ứng viên nào nổi trội, màn hình nói thẳng ra thay vì để người dùng
 * tưởng dòng đầu bảng là đáp án.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Download,
  FileText,
  Loader2,
  RotateCcw,
} from 'lucide-react';

import { doiSoatApi } from '@/services/doi-soat';
import { errMsg } from '@/lib/hkg-error';
import type {
  IDanhSachDoiSoat,
  IGoiYDoiSoat,
  IThuMucDoiSoat,
  QuyetDinhDoiSoat,
} from '@/types/lich-cong-tac';

const MAU_QUYET_DINH: Record<QuyetDinhDoiSoat, string> = {
  GAN_CUOC_HOP: 'bg-green-100 text-green-800 border-green-200',
  TAO_CUOC_HOP_LICH_SU: 'bg-blue-100 text-blue-800 border-blue-200',
  KHO_LUU_TRU: 'bg-gray-100 text-gray-700 border-gray-200',
  KHONG_DI_TRU: 'bg-red-100 text-red-800 border-red-200',
};

export default function DoiSoatPage() {
  const [duocXem, setDuocXem] = useState<boolean | null>(null);
  const [dl, setDl] = useState<IDanhSachDoiSoat | null>(null);
  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState<string | null>(null);
  const [locNhom, setLocNhom] = useState<'' | 'D' | 'E'>('');
  const [chiConLai, setChiConLai] = useState(false);
  const [mo, setMo] = useState<string | null>(null);

  const tai = useCallback(async () => {
    setDangTai(true);
    setLoi(null);
    try {
      setDl(
        await doiSoatApi.danhSach({
          nhom: locNhom || undefined,
          'da-quyet-dinh': chiConLai ? false : undefined,
        }),
      );
    } catch (e) {
      setLoi(errMsg(e, 'Không tải được danh sách đối soát'));
    } finally {
      setDangTai(false);
    }
  }, [locNhom, chiConLai]);

  useEffect(() => {
    doiSoatApi
      .quyen()
      .then((q) => setDuocXem(q.duoc_xem))
      .catch(() => setDuocXem(false));
  }, []);

  useEffect(() => {
    if (duocXem) void tai();
  }, [duocXem, tai]);

  if (duocXem === false) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white py-16 text-center text-gray-500">
        Màn hình đối soát chỉ dành cho Chánh Văn phòng và Quản trị viên.
      </div>
    );
  }

  const th = dl?.tong_hop;

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
        <b>Màn hình dùng một lần.</b> 813 file đã tự gắn được vào cuộc họp nhờ
        khớp thư mục. Số còn lại nằm ở đây vì máy không đoán ra chúng thuộc
        cuộc họp nào — ngày nào cũng có vài cuộc họp nên không thư mục nào có
        ứng viên duy nhất. Mỗi quyết định được ghi kèm người và thời điểm; bản
        Excel xuất ra chính là biên bản đối chiếu nộp khi nghiệm thu.
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select
          value={locNhom}
          onChange={(e) => setLocNhom(e.target.value as '' | 'D' | 'E')}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value="">Tất cả nhóm</option>
          <option value="D">Nhóm D — có bản ghi cũ nhưng không khớp</option>
          <option value="E">Nhóm E — file up thẳng lên Drive</option>
        </select>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={chiConLai}
            onChange={(e) => setChiConLai(e.target.checked)}
          />
          Chỉ hiện thư mục chưa quyết định
        </label>

        <button
          type="button"
          onClick={() => doiSoatApi.xuatBienBan()}
          className="ml-auto inline-flex items-center gap-1.5 rounded-lg bg-green-700 px-3 py-1.5 text-sm text-white hover:bg-green-800"
        >
          <Download className="w-4 h-4" />
          Xuất biên bản
        </button>
      </div>

      {th && (
        <div className="flex flex-wrap gap-3 text-sm">
          <span className="rounded-lg border border-gray-200 bg-white px-4 py-2">
            <b className="text-lg tabular-nums">{th.tong_thu_muc}</b> thư mục ·{' '}
            <b className="tabular-nums">{th.tong_file}</b> file
          </span>
          <span className="rounded-lg border border-green-200 bg-green-50 px-4 py-2 text-green-800">
            Đã quyết định <b className="tabular-nums">{th.da_quyet_dinh}</b>
          </span>
          <span className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-amber-800">
            Còn lại <b className="tabular-nums">{th.con_lai}</b>
          </span>
        </div>
      )}

      {loi && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {loi}
        </div>
      )}

      {dangTai ? (
        <div className="flex items-center justify-center py-16 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          Đang tải…
        </div>
      ) : (
        <div className="space-y-2">
          {dl?.dong.map((tm) => (
            <ThuMuc
              key={tm.id}
              tm={tm}
              dangMo={mo === tm.id}
              onMo={() => setMo(mo === tm.id ? null : tm.id)}
              onXong={() => void tai()}
              onLoi={setLoi}
            />
          ))}
          {dl?.dong.length === 0 && (
            <div className="rounded-lg border border-gray-200 bg-white py-16 text-center text-gray-500">
              Không còn thư mục nào khớp bộ lọc.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/** Một thư mục: tóm tắt luôn hiện, danh sách file và ứng viên mở ra khi bấm. */
function ThuMuc({
  tm,
  dangMo,
  onMo,
  onXong,
  onLoi,
}: {
  tm: IThuMucDoiSoat;
  dangMo: boolean;
  onMo: () => void;
  onXong: () => void;
  onLoi: (s: string) => void;
}) {
  const [goiY, setGoiY] = useState<IGoiYDoiSoat | null>(null);
  const [dangTaiGoiY, setDangTaiGoiY] = useState(false);
  const [dangGhi, setDangGhi] = useState(false);

  useEffect(() => {
    if (!dangMo || goiY || tm.quyet_dinh) return;
    setDangTaiGoiY(true);
    doiSoatApi
      .ungVien(tm.id)
      .then(setGoiY)
      .catch((e) => onLoi(errMsg(e, 'Không tải được gợi ý')))
      .finally(() => setDangTaiGoiY(false));
  }, [dangMo, goiY, tm.id, tm.quyet_dinh, onLoi]);

  const ghi = async (
    quyet_dinh: QuyetDinhDoiSoat,
    cuoc_hop_id?: string,
  ) => {
    const ghi_chu =
      quyet_dinh === 'KHONG_DI_TRU' || quyet_dinh === 'KHO_LUU_TRU'
        ? window.prompt('Ghi chú (không bắt buộc):') ?? undefined
        : undefined;
    setDangGhi(true);
    try {
      await doiSoatApi.quyetDinh(tm.id, quyet_dinh, cuoc_hop_id, ghi_chu);
      onXong();
    } catch (e) {
      onLoi(errMsg(e, 'Không ghi được quyết định'));
    } finally {
      setDangGhi(false);
    }
  };

  const bo = async () => {
    if (!window.confirm('Bỏ quyết định của thư mục này để chọn lại?')) return;
    try {
      await doiSoatApi.boQuyetDinh(tm.id);
      onXong();
    } catch (e) {
      onLoi(errMsg(e, 'Không bỏ được quyết định'));
    }
  };

  const nut =
    'rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-40';

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <button
        type="button"
        onClick={onMo}
        className="flex w-full items-start gap-2 px-4 py-3 text-left"
      >
        {dangMo ? (
          <ChevronDown className="w-4 h-4 mt-0.5 shrink-0 text-gray-400" />
        ) : (
          <ChevronRight className="w-4 h-4 mt-0.5 shrink-0 text-gray-400" />
        )}

        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-900 break-all">
            {tm.ten_thu_muc}
          </div>
          <div className="text-xs text-gray-500 break-all">
            {tm.duong_dan_thu_muc}
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded bg-gray-100 px-2 py-0.5">
              Nhóm {tm.nhom}
            </span>
            <span className="text-gray-600">{tm.so_file} file</span>
            {tm.ngay_suy_ra && (
              <span className="text-gray-600">
                Ngày suy ra: {tm.ngay_suy_ra.split('-').reverse().join('/')}
              </span>
            )}
            {tm.so_gm_suy_ra && (
              <span className="text-gray-600">GM {tm.so_gm_suy_ra}</span>
            )}
          </div>
        </div>

        {tm.quyet_dinh && (
          <span
            className={`shrink-0 rounded border px-2 py-0.5 text-xs ${
              MAU_QUYET_DINH[tm.quyet_dinh]
            }`}
          >
            {tm.quyet_dinh_nhan}
          </span>
        )}
      </button>

      {dangMo && (
        <div className="border-t border-gray-200 px-4 py-3 space-y-4">
          {/* Danh sách file */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-1.5 flex items-center gap-1.5">
              <FileText className="w-4 h-4" />
              {tm.so_file} file trong thư mục
            </h3>
            <ul className="max-h-56 overflow-auto rounded border border-gray-200 divide-y divide-gray-100 text-sm">
              {tm.danh_sach_file.map((f) => (
                <li key={f.drive_file_id} className="px-3 py-1.5">
                  {f.thu_muc_con && (
                    <span className="text-xs text-gray-400">
                      {f.thu_muc_con}/
                    </span>
                  )}
                  {f.ten}
                </li>
              ))}
              {tm.danh_sach_file.length === 0 && (
                <li className="px-3 py-2 text-gray-400 italic">
                  Chưa nạp danh sách tên file
                </li>
              )}
            </ul>
          </div>

          {tm.quyet_dinh ? (
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span>
                Đã quyết định: <b>{tm.quyet_dinh_nhan}</b>
                {tm.nguoi_quyet_dinh && <> — {tm.nguoi_quyet_dinh}</>}
                {tm.thoi_diem_quyet_dinh && (
                  <>
                    {' '}
                    lúc{' '}
                    {new Date(tm.thoi_diem_quyet_dinh).toLocaleString('vi-VN')}
                  </>
                )}
              </span>
              {tm.ghi_chu && (
                <span className="text-gray-600">Ghi chú: {tm.ghi_chu}</span>
              )}
              <button
                type="button"
                onClick={bo}
                className="inline-flex items-center gap-1.5 text-blue-700 hover:underline"
              >
                <RotateCcw className="w-4 h-4" />
                Chọn lại
              </button>
            </div>
          ) : (
            <>
              {/* Ứng viên */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-1.5">
                  Cuộc họp có thể là chủ thư mục này
                </h3>

                {dangTaiGoiY ? (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Đang tìm…
                  </div>
                ) : !goiY || goiY.ung_vien.length === 0 ? (
                  <p className="text-sm text-gray-500">
                    Không tìm được cuộc họp nào gần khớp. Dùng
                    &ldquo;Tạo cuộc họp lịch sử&rdquo; hoặc đưa vào kho lưu trữ.
                  </p>
                ) : (
                  <>
                    {!goiY.co_ung_vien_noi_troi && (
                      <div className="mb-2 flex gap-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-900">
                        <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                        <span>
                          Không ứng viên nào vượt hẳn — các cuộc họp trong ngày
                          hoà điểm nhau. <b>Đừng chọn dòng đầu bảng theo phản
                          xạ</b>, hãy đối chiếu tên file ở trên trước.
                        </span>
                      </div>
                    )}

                    <ul className="divide-y divide-gray-100 rounded border border-gray-200">
                      {goiY.ung_vien.map((uv) => (
                        <li
                          key={uv.cuoc_hop_id}
                          className="flex items-start gap-3 px-3 py-2"
                        >
                          <div className="flex-1 min-w-0 text-sm">
                            <div className="flex items-start gap-2">
                              {/* Mã lịch đứng trước nội dung: người rà đối
                                  chiếu bằng mã, và mã là thứ tra ngược lại
                                  được trên màn hình Lịch. */}
                              {uv.ma_lich && (
                                <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 font-mono text-xs text-gray-700">
                                  {uv.ma_lich}
                                </span>
                              )}
                              <span className="font-medium">{uv.tieu_de}</span>
                            </div>
                            <div className="text-xs text-gray-500">
                              {uv.ngay?.split('-').reverse().join('/')}
                              {uv.gio_bat_dau && ` ${uv.gio_bat_dau.slice(0, 5)}`}
                              {uv.so_van_ban && ` · VB ${uv.so_van_ban}`}
                              {uv.don_vi_chuan_bi && ` · ${uv.don_vi_chuan_bi}`}
                            </div>
                            {uv.tu_trung.length > 0 && (
                              <div className="text-xs text-gray-500">
                                Trùng: {uv.tu_trung.join(', ')}
                              </div>
                            )}
                          </div>
                          <button
                            type="button"
                            disabled={dangGhi}
                            onClick={() => ghi('GAN_CUOC_HOP', uv.cuoc_hop_id)}
                            className="shrink-0 rounded-lg bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-40"
                          >
                            Gắn vào đây
                          </button>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>

              {/* Ba lựa chọn còn lại */}
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={dangGhi || !tm.ngay_suy_ra}
                  onClick={() => ghi('TAO_CUOC_HOP_LICH_SU')}
                  title={
                    tm.ngay_suy_ra
                      ? 'Dựng một cuộc họp từ chính tên thư mục này'
                      : 'Tên thư mục không cho biết ngày nên không dựng được'
                  }
                  className={`${nut} border-blue-300 text-blue-700`}
                >
                  Tạo cuộc họp lịch sử
                </button>
                <button
                  type="button"
                  disabled={dangGhi}
                  onClick={() => ghi('KHO_LUU_TRU')}
                  className={`${nut} border-gray-300`}
                >
                  Kho lưu trữ, không gắn
                </button>
                <button
                  type="button"
                  disabled={dangGhi}
                  onClick={() => ghi('KHONG_DI_TRU')}
                  className={`${nut} border-red-300 text-red-700`}
                >
                  Không di trú
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

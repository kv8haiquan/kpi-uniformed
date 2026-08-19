/**
 * Form tạo / sửa một sự kiện lịch công tác — G4.3.
 *
 * Dùng chung cho cả hai việc: truyền `banGhi` thì là sửa, không truyền là tạo.
 *
 * Khi sửa, chỉ gửi lên những trường thật sự đổi. Backend dùng PATCH và ghi
 * nhật ký từng trường, nên gửi thừa sẽ đẻ ra nhật ký rác — người đọc không
 * phân biệt được lần nào sửa thật.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { Loader2, X } from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import { congChucApi, type ICongChucSearchItem } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type {
  IDanhMucLoai,
  IDonVi,
  ILichCongTacGhi,
  ISuKienChiTiet,
  LoaiLich,
} from '@/types/lich-cong-tac';

interface Props {
  /** Có giá trị là đang sửa; bỏ trống là tạo mới. */
  banGhi?: ISuKienChiTiet | null;
  /** Ngày điền sẵn khi tạo mới từ ô ngày trên lịch tháng. */
  ngayMacDinh?: string;
  onDong: () => void;
  onXong: (sk: ISuKienChiTiet) => void;
}

type Truong = keyof ILichCongTacGhi;

const oCss =
  'w-full rounded-lg border border-gray-300 px-3 py-1.5 focus:border-blue-500 focus:outline-none';

/**
 * Một ô nhập kèm nhãn.
 *
 * Phải khai báo NGOÀI component cha: khai báo bên trong thì mỗi lần vẽ lại là
 * một kiểu component mới, React tháo input cũ và gắn input mới, gõ được một ký
 * tự là mất con trỏ.
 */
function O({
  nhan,
  children,
  rong,
}: {
  nhan: string;
  children: React.ReactNode;
  rong?: boolean;
}) {
  return (
    <label className={`text-sm ${rong ? 'sm:col-span-2' : ''}`}>
      <span className="block text-gray-600 mb-1">{nhan}</span>
      {children}
    </label>
  );
}

/** Giá trị rỗng trên form về `null` — để xoá được nội dung đã nhập trước đó. */
function chuanHoa(v: string): string | null {
  const t = v.trim();
  return t === '' ? null : t;
}

export default function FormLich({
  banGhi,
  ngayMacDinh,
  onDong,
  onXong,
}: Props) {
  const dangSua = Boolean(banGhi);

  const [loai, setLoai] = useState<IDanhMucLoai[]>([]);
  const [donVi, setDonVi] = useState<IDonVi[]>([]);
  const [dangLuu, setDangLuu] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  // Chủ trì: chọn công chức thì lưu vào `chu_toa_id` và liên kết được sang
  // chương trình công tác của người đó. Người ngoài Chi cục (lãnh đạo Tỉnh,
  // Tổng cục) không có trong danh bạ nên vẫn phải cho gõ tay — 8/498 sự kiện
  // di trú rơi vào trường hợp này.
  const [timChuTri, setTimChuTri] = useState('');
  const [ketQuaChuTri, setKetQuaChuTri] = useState<ICongChucSearchItem[]>([]);
  const [dangTimChuTri, setDangTimChuTri] = useState(false);

  const banDau = useMemo<Record<Truong, string>>(
    () => ({
      tieu_de: banGhi?.tieu_de ?? '',
      loai_lich: (banGhi?.loai_lich as LoaiLich) ?? 'HOP',
      ngay_hop: banGhi?.ngay_hop ?? ngayMacDinh ?? '',
      ngay_ket_thuc: banGhi?.ngay_ket_thuc ?? '',
      ngay_hien_thi: banGhi?.ngay_hien_thi ?? '',
      gio_bat_dau: (banGhi?.gio_bat_dau ?? '08:00:00').slice(0, 5),
      gio_ket_thuc: (banGhi?.gio_ket_thuc ?? '').slice(0, 5),
      dia_diem: banGhi?.dia_diem ?? '',
      mo_ta: banGhi?.mo_ta ?? '',
      chu_tri_text: banGhi?.chu_tri_text ?? '',
      thanh_phan_text: banGhi?.thanh_phan_text ?? '',
      don_vi_chuan_bi: banGhi?.don_vi_chuan_bi ?? '',
      so_van_ban: banGhi?.so_van_ban ?? '',
      trang_thai: banGhi?.trang_thai ?? 'LEN_KE_HOACH',
      chu_toa_id: banGhi?.chu_toa?.id ?? '',
      lanh_dao_lien_quan_ids: '',
    }),
    [banGhi, ngayMacDinh],
  );

  // Form được gắn mới mỗi lần mở (cha bật/tắt bằng cờ) nên lấy giá trị đầu
  // một lần là đủ — không cần useEffect đồng bộ lại.
  const [form, setForm] = useState(banDau);

  useEffect(() => {
    lichCongTacApi.danhMuc().then(setLoai).catch(() => setLoai([]));
    lichCongTacApi.danhMucDonVi().then(setDonVi).catch(() => setDonVi([]));
  }, []);

  // Tìm công chức khi gõ, hoãn 300ms để không gọi API mỗi phím.
  useEffect(() => {
    const tu = timChuTri.trim();
    // Dưới 2 ký tự thì không gọi API. Không xoá state ở đây — xoá đồng bộ
    // trong effect là một vòng vẽ lại thừa; lọc lúc hiển thị là đủ.
    if (tu.length < 2) return;
    // Đặt cờ "đang tìm" bên trong hẹn giờ: đặt ngay ở thân effect sẽ kích
    // hoạt một vòng vẽ lại thừa cho mỗi phím gõ.
    const h = setTimeout(() => {
      setDangTimChuTri(true);
      congChucApi
        .search({ q: tu, limit: 15 })
        .then(setKetQuaChuTri)
        .catch(() => setKetQuaChuTri([]))
        .finally(() => setDangTimChuTri(false));
    }, 300);
    return () => clearTimeout(h);
  }, [timChuTri]);

  const dat = (k: Truong, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const luu = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoi(null);

    if (!form.tieu_de.trim()) return setLoi('Chưa nhập nội dung');
    if (!form.ngay_hop) return setLoi('Chưa chọn ngày');
    if (
      form.ngay_ket_thuc &&
      form.ngay_ket_thuc < form.ngay_hop
    ) {
      return setLoi('Ngày kết thúc không được trước ngày bắt đầu');
    }

    // Chỉ những trường đổi so với lúc mở form.
    const goi: ILichCongTacGhi = {};
    (Object.keys(form) as Truong[]).forEach((k) => {
      if (k === 'lanh_dao_lien_quan_ids') return;
      if (dangSua && form[k] === banDau[k]) return;
      const v = form[k];
      if (k === 'tieu_de' || k === 'loai_lich' || k === 'ngay_hop') {
        (goi as Record<string, unknown>)[k] = v;
      } else if (k === 'gio_bat_dau') {
        goi.gio_bat_dau = `${v}:00`;
      } else if (k === 'gio_ket_thuc') {
        goi.gio_ket_thuc = v ? `${v}:00` : null;
      } else if (k === 'trang_thai') {
        (goi as Record<string, unknown>)[k] = v;
      } else if (k === 'chu_toa_id') {
        goi.chu_toa_id = v || null;
      } else {
        (goi as Record<string, unknown>)[k] = chuanHoa(v);
      }
    });

    if (dangSua && Object.keys(goi).length === 0) {
      onDong();
      return;
    }

    setDangLuu(true);
    try {
      const sk = dangSua
        ? await lichCongTacApi.capNhat(banGhi!.id, goi)
        : await lichCongTacApi.tao(goi);
      onXong(sk);
    } catch (e2) {
      setLoi(errMsg(e2, 'Không lưu được lịch'));
    } finally {
      setDangLuu(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 overflow-y-auto">
      <form
        onSubmit={luu}
        className="w-full max-w-3xl rounded-xl bg-white shadow-xl my-8"
      >
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <h2 className="font-semibold text-gray-900">
            {dangSua
              ? `Sửa lịch ${banGhi?.ma_lich ?? ''}`
              : 'Thêm lịch công tác'}
          </h2>
          <button
            type="button"
            onClick={onDong}
            className="rounded p-1 text-gray-500 hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid gap-3 px-5 py-4 sm:grid-cols-2">
          <O nhan="Nội dung *" rong>
            <input
              className={oCss}
              value={form.tieu_de}
              onChange={(e) => dat('tieu_de', e.target.value)}
              maxLength={500}
              autoFocus
            />
          </O>

          <O nhan="Loại lịch">
            <select
              className={oCss}
              value={form.loai_lich}
              onChange={(e) => dat('loai_lich', e.target.value)}
            >
              {loai.map((l) => (
                <option key={l.ma} value={l.ma}>
                  {l.ten}
                </option>
              ))}
            </select>
          </O>

          <O nhan="Trạng thái">
            <select
              className={oCss}
              value={form.trang_thai}
              onChange={(e) => dat('trang_thai', e.target.value)}
            >
              <option value="LEN_KE_HOACH">Dự kiến (chưa đăng)</option>
              <option value="DA_THONG_BAO">Đã đăng</option>
              <option value="HOAN_THANH">Đã diễn ra</option>
            </select>
          </O>

          <O nhan="Ngày *">
            <input
              type="date"
              className={oCss}
              value={form.ngay_hop}
              onChange={(e) => dat('ngay_hop', e.target.value)}
            />
          </O>

          <O nhan="Ngày kết thúc (nếu kéo dài nhiều ngày)">
            <input
              type="date"
              className={oCss}
              value={form.ngay_ket_thuc}
              onChange={(e) => dat('ngay_ket_thuc', e.target.value)}
            />
          </O>

          <O nhan="Giờ bắt đầu">
            <input
              type="time"
              className={oCss}
              value={form.gio_bat_dau}
              onChange={(e) => dat('gio_bat_dau', e.target.value)}
            />
          </O>

          <O nhan="Giờ kết thúc">
            <input
              type="time"
              className={oCss}
              value={form.gio_ket_thuc}
              onChange={(e) => dat('gio_ket_thuc', e.target.value)}
            />
          </O>

          <O nhan="Địa điểm" rong>
            <input
              className={oCss}
              value={form.dia_diem}
              onChange={(e) => dat('dia_diem', e.target.value)}
              maxLength={300}
            />
          </O>

          <O nhan="Chủ trì" rong>
            {form.chu_toa_id ? (
              <div className="flex items-center gap-2">
                <span className="flex-1 rounded-lg border border-green-300 bg-green-50 px-3 py-1.5">
                  {ketQuaChuTri.find((x) => x.id === form.chu_toa_id)?.ho_ten ??
                    banGhi?.chu_toa?.ho_ten ??
                    'Đã chọn'}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    dat('chu_toa_id', '');
                    setTimChuTri('');
                  }}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
                >
                  Bỏ chọn
                </button>
              </div>
            ) : (
              <>
                <input
                  className={oCss}
                  value={timChuTri}
                  onChange={(e) => setTimChuTri(e.target.value)}
                  placeholder="Gõ tên hoặc mã công chức để chọn…"
                />
                {dangTimChuTri && (
                  <span className="block text-xs text-gray-500 mt-1">
                    Đang tìm…
                  </span>
                )}
                {timChuTri.trim().length >= 2 && ketQuaChuTri.length > 0 && (
                  <ul className="mt-1 max-h-40 overflow-auto rounded-lg border border-gray-200 divide-y divide-gray-100">
                    {ketQuaChuTri.map((cc) => (
                      <li key={cc.id}>
                        <button
                          type="button"
                          onClick={() => {
                            dat('chu_toa_id', cc.id);
                            dat('chu_tri_text', '');
                          }}
                          className="w-full px-3 py-1.5 text-left text-sm hover:bg-gray-50"
                        >
                          {cc.ho_ten}
                          {cc.chuc_vu && (
                            <span className="text-gray-500"> — {cc.chuc_vu}</span>
                          )}
                          {cc.ten_don_vi && (
                            <span className="block text-xs text-gray-400">
                              {cc.ten_don_vi}
                            </span>
                          )}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </O>

          <O nhan="Hoặc ghi tay người chủ trì" rong>
            <input
              className={oCss}
              value={form.chu_tri_text}
              onChange={(e) => dat('chu_tri_text', e.target.value)}
              maxLength={300}
              disabled={Boolean(form.chu_toa_id)}
              placeholder="Dùng khi người chủ trì ngoài Chi cục — vd: đ/c Phó Chủ tịch UBND tỉnh"
            />
          </O>

          <O nhan="Đơn vị chuẩn bị" rong>
            <select
              className={oCss}
              value={
                donVi.some((d) => d.ten_don_vi === form.don_vi_chuan_bi)
                  ? form.don_vi_chuan_bi
                  : '__khac__'
              }
              onChange={(e) =>
                dat(
                  'don_vi_chuan_bi',
                  e.target.value === '__khac__' ? '' : e.target.value,
                )
              }
            >
              <option value="">— Chưa giao đơn vị nào —</option>
              {donVi.map((d) => (
                <option key={d.id} value={d.ten_don_vi}>
                  {d.ten_don_vi}
                </option>
              ))}
              <option value="__khac__">Khác (tự nhập bên dưới)…</option>
            </select>
            {!donVi.some((d) => d.ten_don_vi === form.don_vi_chuan_bi) && (
              <input
                className={`${oCss} mt-1.5`}
                value={form.don_vi_chuan_bi}
                onChange={(e) => dat('don_vi_chuan_bi', e.target.value)}
                maxLength={200}
                placeholder="Nhiều đơn vị hoặc tên khác — vd: Văn phòng, Đội NV1"
              />
            )}
          </O>

          <O nhan="Thành phần" rong>
            <textarea
              className={oCss}
              rows={2}
              value={form.thanh_phan_text}
              onChange={(e) => dat('thanh_phan_text', e.target.value)}
            />
          </O>

          <O nhan="Số văn bản">
            <input
              className={oCss}
              value={form.so_van_ban}
              onChange={(e) => dat('so_van_ban', e.target.value)}
              maxLength={100}
            />
          </O>

          <O nhan="Ngày hiển thị trên lịch">
            <input
              type="date"
              className={oCss}
              value={form.ngay_hien_thi}
              onChange={(e) => dat('ngay_hien_thi', e.target.value)}
              placeholder="mặc định lấy ngày bắt đầu"
            />
          </O>

          <O nhan="Ghi chú" rong>
            <textarea
              className={oCss}
              rows={2}
              value={form.mo_ta}
              onChange={(e) => dat('mo_ta', e.target.value)}
            />
          </O>
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
            disabled={dangLuu}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {dangLuu && <Loader2 className="w-4 h-4 animate-spin" />}
            {dangSua ? 'Lưu thay đổi' : 'Tạo lịch'}
          </button>
        </div>
      </form>
    </div>
  );
}

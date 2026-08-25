/**
 * Thẻ CHI TIẾT một sự kiện trên lịch — dùng chung cho hai chỗ:
 *
 *  - `/lich-cong-tac/[id]` — xem một cuộc họp;
 *  - chế độ "Lịch ngày" — xem TOÀN BỘ cuộc họp của một ngày, mỗi cuộc một thẻ
 *    y hệt thế này xếp nối nhau.
 *
 * Tách ra khỏi trang chi tiết chính vì yêu cầu đó: xem một ngày phải giống
 * hệt xem một cuộc họp, chỉ khác là có nhiều cuộc. Nhân đôi phần hiển thị thì
 * chỉ vài lần sửa là hai bên lệch nhau.
 *
 * Thẻ tự lo mọi thao tác của nó (sửa, huỷ, xoá, nhật ký) để trang cha chỉ việc
 * xếp thẻ. Sau khi sửa hoặc xoá, thẻ báo ngược lên bằng `onThayDoi`/`onXoa` —
 * cha quyết định nạp lại thế nào, vì sửa ngày là sự kiện có thể nhảy sang ngày
 * khác và biến mất khỏi màn hình đang xem.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Ban,
  Building2,
  CalendarDays,
  ChevronDown,
  ChevronUp,
  Clock,
  ExternalLink,
  FileText,
  History,
  MapPin,
  Pencil,
  Star,
  Trash2,
  User,
  Users,
} from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import { errMsg } from '@/lib/hkg-error';
import { gioNgan } from '@/lib/lich-ngay';
import {
  NHAN_TRANG_THAI,
  type IDongNhatKy,
  type IQuyenLich,
  type ISuKienChiTiet,
} from '@/types/lich-cong-tac';

import FormLich from './FormLich';
import SaoChuanBi from './SaoChuanBi';
import TaiLieuLich from './TaiLieuLich';
import { MAU_TRANG_THAI, mauLoai, suaDuocLich } from './lich-mau';

const NHAN_HANH_DONG: Record<string, string> = {
  TAO_LICH: 'Tạo lịch',
  SUA_LICH: 'Sửa lịch',
  HUY_LICH: 'Huỷ lịch',
  XOA_LICH: 'Xoá lịch',
};

function Dong({
  icon,
  nhan,
  children,
}: {
  icon: React.ReactNode;
  nhan: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-3 py-2">
      <div className="w-5 shrink-0 text-gray-400 pt-0.5">{icon}</div>
      <div className="w-40 shrink-0 text-sm text-gray-500">{nhan}</div>
      <div className="flex-1 text-sm text-gray-900">{children}</div>
    </div>
  );
}

interface Props {
  sk: ISuKienChiTiet;
  /** Quyền của người đang đăng nhập; null khi chưa hỏi xong. */
  quyen: IQuyenLich | null;
  /** Sự kiện vừa được sửa hoặc huỷ — cha tự quyết nạp lại hay thay tại chỗ. */
  onThayDoi: (moi: ISuKienChiTiet) => void;
  /** Sự kiện đã bị xoá. */
  onXoa: () => void;
  /**
   * Cho thu gọn phần thân. Lịch ngày bật cờ này vì một ngày có thể tới 8 cuộc
   * họp; trang chi tiết một cuộc thì không có gì để gấp lại.
   */
  thuGonDuoc?: boolean;
  /** Bắt đầu ở trạng thái thu gọn. */
  macDinhThuGon?: boolean;
}

export default function ChiTietSuKien({
  sk,
  quyen,
  onThayDoi,
  onXoa,
  thuGonDuoc = false,
  macDinhThuGon = false,
}: Props) {
  const [moForm, setMoForm] = useState(false);
  const [nhatKy, setNhatKy] = useState<IDongNhatKy[] | null>(null);
  const [dangXuLy, setDangXuLy] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [moThan, setMoThan] = useState(!macDinhThuGon);
  // Số tài liệu do khối Tài liệu tự đếm sau khi tải danh sách — `sk.so_tai_lieu`
  // là ảnh chụp lúc mở trang, tải thêm file xong sẽ lệch ngay.
  const [soTaiLieu, setSoTaiLieu] = useState(0);

  const suaDuoc = suaDuocLich(sk, quyen);

  const huyLich = async () => {
    const ly_do = window.prompt('Lý do huỷ lịch này?');
    if (!ly_do?.trim()) return;
    setDangXuLy(true);
    setLoi(null);
    try {
      onThayDoi(await lichCongTacApi.huy(sk.id, ly_do.trim()));
    } catch (e) {
      setLoi(errMsg(e, 'Không huỷ được lịch'));
    } finally {
      setDangXuLy(false);
    }
  };

  const xoaLich = async () => {
    if (
      !window.confirm(
        'Xoá lịch này khỏi danh sách?\n\n' +
          'Muốn giữ lại để tra cứu thì bấm Huỷ lịch thay vì Xoá.',
      )
    ) {
      return;
    }
    setDangXuLy(true);
    setLoi(null);
    try {
      await lichCongTacApi.xoa(sk.id);
      onXoa();
    } catch (e) {
      setLoi(errMsg(e, 'Không xoá được lịch'));
      setDangXuLy(false);
    }
  };

  const xemNhatKy = async () => {
    if (nhatKy) return setNhatKy(null);
    try {
      setNhatKy(await lichCongTacApi.nhatKy(sk.id));
    } catch (e) {
      setLoi(errMsg(e, 'Không tải được nhật ký'));
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="flex flex-wrap items-start justify-between gap-3 p-5 pb-0">
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className={`rounded border px-2 py-0.5 text-xs ${mauLoai(sk.loai_lich)}`}>
              {sk.loai_lich_nhan ?? 'Lịch khác'}
            </span>
            <span
              className={`rounded px-2 py-0.5 text-xs ${MAU_TRANG_THAI[sk.trang_thai]}`}
            >
              {NHAN_TRANG_THAI[sk.trang_thai]}
            </span>
            {sk.ma_lich && (
              <span className="font-mono text-xs text-gray-500">{sk.ma_lich}</span>
            )}
            {/* Giờ nằm ngay cạnh tiêu đề: xem cả ngày thì thứ tự giờ là thứ
                người đọc dò theo, không phải bới xuống dòng "Giờ" bên dưới. */}
            <span className="text-xs font-semibold text-gray-700">
              {gioNgan(sk.gio_bat_dau)}
              {sk.gio_ket_thuc && ` – ${gioNgan(sk.gio_ket_thuc)}`}
            </span>
          </div>

          <h2
            className={`text-xl font-semibold text-gray-900 ${
              sk.trang_thai === 'HUY' ? 'line-through' : ''
            }`}
          >
            {sk.tieu_de}
          </h2>
        </div>

        <div className="flex flex-wrap gap-2">
          {suaDuoc && (
            <>
              <button
                type="button"
                onClick={() => setMoForm(true)}
                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
              >
                <Pencil className="w-4 h-4" />
                Sửa
              </button>
              {sk.trang_thai !== 'HUY' && (
                <button
                  type="button"
                  onClick={huyLich}
                  disabled={dangXuLy}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 px-3 py-1.5 text-sm text-amber-800 hover:bg-amber-50 disabled:opacity-40"
                >
                  <Ban className="w-4 h-4" />
                  Huỷ lịch
                </button>
              )}
              <button
                type="button"
                onClick={xoaLich}
                disabled={dangXuLy}
                className="inline-flex items-center gap-1.5 rounded-lg border border-red-300 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50 disabled:opacity-40"
              >
                <Trash2 className="w-4 h-4" />
                Xoá
              </button>
            </>
          )}

          <button
            type="button"
            onClick={xemNhatKy}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
          >
            <History className="w-4 h-4" />
            Nhật ký
          </button>

          {sk.co_the_mo_hkg && (
            <Link
              href={`/hop-khong-giay/chi-tiet/${sk.id}`}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700"
            >
              <ExternalLink className="w-4 h-4" />
              Mở trong Họp Không Giấy
            </Link>
          )}

          {thuGonDuoc && (
            <button
              type="button"
              onClick={() => setMoThan(!moThan)}
              aria-expanded={moThan}
              title={moThan ? 'Thu gọn' : 'Xem đầy đủ'}
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
            >
              {moThan ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
              {moThan ? 'Thu gọn' : 'Xem đầy đủ'}
            </button>
          )}
        </div>
      </div>

      <div className="p-5 pt-3">
        {loi && (
          <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {loi}
          </div>
        )}

        {sk.trang_thai === 'HUY' && sk.ly_do_huy && (
          <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            <span className="font-medium">Lý do hủy:</span> {sk.ly_do_huy}
          </div>
        )}

        {!moThan ? (
          // Bản thu gọn vẫn phải trả lời được "họp ở đâu, ai chủ trì" — thu
          // gọn thành một dòng trắng thì bằng không có gì.
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
            {sk.dia_diem && (
              <span className="inline-flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" />
                {sk.dia_diem}
              </span>
            )}
            {(sk.chu_toa || sk.chu_tri_text) && (
              <span className="inline-flex items-center gap-1">
                <User className="w-3.5 h-3.5" />
                {sk.chu_toa?.ho_ten ?? sk.chu_tri_text}
              </span>
            )}
            {sk.so_tai_lieu > 0 && (
              <span className="inline-flex items-center gap-1">
                <FileText className="w-3.5 h-3.5" />
                {sk.so_tai_lieu} tài liệu
              </span>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            <Dong icon={<CalendarDays className="w-4 h-4" />} nhan="Ngày">
              {sk.ngay_hien_thi}
              {sk.ngay_ket_thuc && sk.ngay_ket_thuc !== sk.ngay_hien_thi && (
                <> → {sk.ngay_ket_thuc}</>
              )}
            </Dong>

            <Dong icon={<Clock className="w-4 h-4" />} nhan="Giờ">
              {gioNgan(sk.gio_bat_dau)}
              {sk.gio_ket_thuc && ` – ${gioNgan(sk.gio_ket_thuc)}`}
            </Dong>

            {sk.dia_diem && (
              <Dong icon={<MapPin className="w-4 h-4" />} nhan="Địa điểm">
                {sk.dia_diem}
              </Dong>
            )}

            {(sk.chu_toa || sk.chu_tri_text) && (
              <Dong icon={<User className="w-4 h-4" />} nhan="Chủ trì">
                {sk.chu_toa ? (
                  <>
                    {sk.chu_toa.ho_ten}
                    {sk.chu_toa.chuc_vu && (
                      <span className="text-gray-500"> — {sk.chu_toa.chuc_vu}</span>
                    )}
                  </>
                ) : (
                  sk.chu_tri_text
                )}
              </Dong>
            )}

            {sk.lanh_dao_lien_quan.length > 0 && (
              <Dong icon={<Users className="w-4 h-4" />} nhan="Thành phần tham dự">
                <div className="flex flex-wrap gap-1.5">
                  {sk.lanh_dao_lien_quan.map((ld) => (
                    <Link
                      key={ld.id}
                      href={`/lich-cong-tac/lanh-dao/${ld.id}`}
                      className="rounded bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
                      title="Xem chương trình công tác"
                    >
                      {ld.ho_ten}
                    </Link>
                  ))}
                </div>
              </Dong>
            )}

            {sk.thanh_phan_text && (
              <Dong icon={<Users className="w-4 h-4" />} nhan="Thành phần khác">
                <span className="whitespace-pre-line">{sk.thanh_phan_text}</span>
              </Dong>
            )}

            {sk.don_vi_chuan_bi && (
              <Dong icon={<Building2 className="w-4 h-4" />} nhan="Đơn vị chuẩn bị">
                {sk.don_vi_chuan_bi}
              </Dong>
            )}

            {sk.so_van_ban && (
              <Dong icon={<FileText className="w-4 h-4" />} nhan="Số văn bản">
                {sk.so_van_ban}
              </Dong>
            )}

            {sk.mo_ta && (
              <Dong icon={<FileText className="w-4 h-4" />} nhan="Ghi chú">
                <span className="whitespace-pre-line">{sk.mo_ta}</span>
              </Dong>
            )}

            <Dong icon={<FileText className="w-4 h-4" />} nhan="Tài liệu">
              <TaiLieuLich
                cuocHopId={sk.id}
                quanLyDuoc={suaDuoc}
                onDoiSoLuong={setSoTaiLieu}
              />
              {/*
                Không CHẶN tải tài liệu khi thiếu đơn vị chuẩn bị: 141/191 sự
                kiện lịch sử có tài liệu mà không ghi đơn vị, và cuộc họp Họp
                Không Giấy thì không dùng trường này. Nhưng phải nói rõ hậu quả,
                vì báo cáo Thống kê tài liệu phân loại theo đúng trường đó.
              */}
              {soTaiLieu > 0 && !sk.don_vi_chuan_bi && (
                <p className="mt-1.5 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-xs text-amber-900">
                  Có tài liệu nhưng chưa giao đơn vị chuẩn bị — báo cáo{' '}
                  <Link href="/lich-cong-tac/thong-ke-tai-lieu" className="underline">
                    Thống kê tài liệu
                  </Link>{' '}
                  sẽ xếp sự kiện này vào nhóm &ldquo;Chưa giao chuẩn bị&rdquo;.
                  {suaDuoc && ' Bấm Sửa để bổ sung đơn vị.'}
                </p>
              )}
            </Dong>

            <Dong icon={<Star className="w-4 h-4" />} nhan="Công tác chuẩn bị">
              <SaoChuanBi cuocHopId={sk.id} />
            </Dong>
          </div>
        )}

        {nhatKy && (
          <div className="mt-4 border-t border-gray-200 pt-4">
            <h3 className="mb-3 font-semibold text-gray-900">Nhật ký thay đổi</h3>
            {nhatKy.length === 0 ? (
              <p className="text-sm text-gray-500">
                Chưa có thay đổi nào được ghi nhận.
              </p>
            ) : (
              <ul className="space-y-3">
                {nhatKy.map((n, i) => (
                  <li key={i} className="border-l-2 border-gray-200 pl-3 text-sm">
                    <div className="text-gray-500">
                      {new Date(n.thoi_diem).toLocaleString('vi-VN')}
                      {n.nguoi_thuc_hien && <> — {n.nguoi_thuc_hien}</>}
                    </div>
                    <div className="font-medium text-gray-900">
                      {NHAN_HANH_DONG[n.hanh_dong] ?? n.hanh_dong}
                    </div>
                    {n.chi_tiet?.ly_do && (
                      <div className="text-gray-700">Lý do: {n.chi_tiet.ly_do}</div>
                    )}
                    {n.chi_tiet?.thay_doi?.map((t) => (
                      <div key={t.truong} className="text-gray-700">
                        {t.nhan}:{' '}
                        <span className="text-gray-400 line-through">
                          {t.cu || '(trống)'}
                        </span>{' '}
                        → <span>{t.moi || '(trống)'}</span>
                      </div>
                    ))}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {moForm && (
        <FormLich
          banGhi={sk}
          onDong={() => setMoForm(false)}
          onXong={(moi) => {
            setMoForm(false);
            setNhatKy(null);
            onThayDoi(moi);
          }}
        />
      )}
    </div>
  );
}

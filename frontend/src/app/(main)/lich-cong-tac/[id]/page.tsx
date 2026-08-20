/**
 * /lich-cong-tac/[id] — chi tiết một sự kiện trên lịch.
 *
 * Nếu sự kiện có nguồn HKG thì hiện nút mở thẳng sang chi tiết cuộc họp trong
 * Họp Không Giấy — tiêu chí 8.3 gạch 2 của yêu cầu chuyển đổi.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Ban,
  Building2,
  CalendarDays,
  Clock,
  ExternalLink,
  FileText,
  History,
  Loader2,
  MapPin,
  Pencil,
  Star,
  Trash2,
  User,
  Users,
} from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import { errMsg } from '@/lib/hkg-error';
import {
  NHAN_TRANG_THAI,
  type IDongNhatKy,
  type ISuKienChiTiet,
  type LoaiLich,
  type TrangThaiLich,
} from '@/types/lich-cong-tac';
import FormLich from '../components/FormLich';
import SaoChuanBi from '../components/SaoChuanBi';

const MAU_LOAI: Record<LoaiLich, string> = {
  HOP: 'bg-blue-100 text-blue-800',
  TRUC_BAN: 'bg-amber-100 text-amber-800',
  HOI_NGHI: 'bg-purple-100 text-purple-800',
  LAM_VIEC: 'bg-emerald-100 text-emerald-800',
  CONG_TAC: 'bg-cyan-100 text-cyan-800',
  LICH_KHAC: 'bg-gray-100 text-gray-700',
};

const MAU_TRANG_THAI: Record<TrangThaiLich, string> = {
  LEN_KE_HOACH: 'bg-gray-100 text-gray-700',
  DA_THONG_BAO: 'bg-blue-100 text-blue-800',
  DANG_DIEN_RA: 'bg-yellow-100 text-yellow-800',
  HOAN_THANH: 'bg-green-100 text-green-800',
  HUY: 'bg-red-100 text-red-800',
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

export default function ChiTietSuKienPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [sk, setSk] = useState<ISuKienChiTiet | null>(null);
  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState<string | null>(null);

  const [moForm, setMoForm] = useState(false);
  const [suaDuoc, setSuaDuoc] = useState(false);
  const [nhatKy, setNhatKy] = useState<IDongNhatKy[] | null>(null);
  const [dangXuLy, setDangXuLy] = useState(false);

  useEffect(() => {
    const chay = async () => {
      setDangTai(true);
      setLoi(null);
      try {
        setSk(await lichCongTacApi.chiTiet(id));
      } catch (e) {
        setLoi(errMsg(e, 'Không tải được sự kiện'));
      } finally {
        setDangTai(false);
      }
    };
    void chay();
  }, [id]);

  // Quyền sửa: quản trị lịch sửa được tất cả, người thường chỉ sửa lịch mình
  // tạo. Backend mới là nơi quyết định — chỗ này chỉ để ẩn nút cho đỡ rối.
  useEffect(() => {
    if (!sk || sk.nguon !== 'LICH_CONG_TAC') {
      setSuaDuoc(false);
      return;
    }
    lichCongTacApi
      .quyenCuaToi()
      .then((q) => setSuaDuoc(q.la_quan_tri_lich || q.cong_chuc_id === sk.created_by))
      .catch(() => setSuaDuoc(false));
  }, [sk]);

  const huyLich = async () => {
    const ly_do = window.prompt('Lý do huỷ lịch này?');
    if (!ly_do?.trim()) return;
    setDangXuLy(true);
    try {
      setSk(await lichCongTacApi.huy(id, ly_do.trim()));
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
    try {
      await lichCongTacApi.xoa(id);
      router.push('/lich-cong-tac');
    } catch (e) {
      setLoi(errMsg(e, 'Không xoá được lịch'));
      setDangXuLy(false);
    }
  };

  const xemNhatKy = async () => {
    if (nhatKy) return setNhatKy(null);
    try {
      setNhatKy(await lichCongTacApi.nhatKy(id));
    } catch (e) {
      setLoi(errMsg(e, 'Không tải được nhật ký'));
    }
  };

  if (dangTai) {
    return (
      <div className="flex items-center justify-center py-16 text-gray-500">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        Đang tải…
      </div>
    );
  }

  if (loi || !sk) {
    return (
      <div className="space-y-4">
        <button
          type="button"
          onClick={() => router.back()}
          className="inline-flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Quay lại
        </button>
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {loi ?? 'Không tìm thấy sự kiện'}
        </div>
      </div>
    );
  }

  const gio = (g?: string | null) => (g ? g.slice(0, 5) : '');

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex items-center justify-between">
        <Link
          href="/lich-cong-tac"
          className="inline-flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Lịch công tác
        </Link>

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
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-5">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <span
            className={`rounded px-2 py-0.5 text-xs ${
              MAU_LOAI[sk.loai_lich ?? 'LICH_KHAC']
            }`}
          >
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
        </div>

        <h1 className="text-xl font-semibold text-gray-900 mb-4">{sk.tieu_de}</h1>

        {sk.trang_thai === 'HUY' && sk.ly_do_huy && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
            <span className="font-medium">Lý do hủy:</span> {sk.ly_do_huy}
          </div>
        )}

        <div className="divide-y divide-gray-100">
          <Dong icon={<CalendarDays className="w-4 h-4" />} nhan="Ngày">
            {sk.ngay_hien_thi}
            {sk.ngay_ket_thuc && sk.ngay_ket_thuc !== sk.ngay_hien_thi && (
              <> → {sk.ngay_ket_thuc}</>
            )}
          </Dong>

          <Dong icon={<Clock className="w-4 h-4" />} nhan="Giờ">
            {gio(sk.gio_bat_dau)}
            {sk.gio_ket_thuc && ` – ${gio(sk.gio_ket_thuc)}`}
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
            {sk.so_tai_lieu > 0 ? (
              <Link
                href={`/hop-khong-giay/chi-tiet/${sk.id}/tai-lieu`}
                className="text-blue-700 hover:underline"
              >
                {sk.so_tai_lieu} tài liệu đính kèm
              </Link>
            ) : (
              <Link
                href={`/hop-khong-giay/chi-tiet/${sk.id}/tai-lieu`}
                className="text-gray-500 hover:underline"
              >
                Chưa có tài liệu — bấm để tải lên
              </Link>
            )}
            {/*
              Không CHẶN tải tài liệu khi thiếu đơn vị chuẩn bị: 141/191 sự
              kiện lịch sử có tài liệu mà không ghi đơn vị, và cuộc họp Họp
              Không Giấy thì không dùng trường này. Nhưng phải nói rõ hậu quả,
              vì báo cáo Thống kê tài liệu phân loại theo đúng trường đó.
            */}
            {sk.so_tai_lieu > 0 && !sk.don_vi_chuan_bi && (
              <p className="mt-1 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-xs text-amber-900">
                Có tài liệu nhưng chưa giao đơn vị chuẩn bị — báo cáo{' '}
                <Link
                  href="/lich-cong-tac/thong-ke-tai-lieu"
                  className="underline"
                >
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
      </div>

      {nhatKy && (
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h2 className="font-semibold text-gray-900 mb-3">Nhật ký thay đổi</h2>
          {nhatKy.length === 0 ? (
            <p className="text-sm text-gray-500">
              Chưa có thay đổi nào được ghi nhận.
            </p>
          ) : (
            <ul className="space-y-3">
              {nhatKy.map((n, i) => (
                <li key={i} className="text-sm border-l-2 border-gray-200 pl-3">
                  <div className="text-gray-500">
                    {new Date(n.thoi_diem).toLocaleString('vi-VN')}
                    {n.nguoi_thuc_hien && <> — {n.nguoi_thuc_hien}</>}
                  </div>
                  <div className="font-medium text-gray-900">
                    {{
                      TAO_LICH: 'Tạo lịch',
                      SUA_LICH: 'Sửa lịch',
                      HUY_LICH: 'Huỷ lịch',
                      XOA_LICH: 'Xoá lịch',
                    }[n.hanh_dong] ?? n.hanh_dong}
                  </div>
                  {n.chi_tiet?.ly_do && (
                    <div className="text-gray-700">Lý do: {n.chi_tiet.ly_do}</div>
                  )}
                  {n.chi_tiet?.thay_doi?.map((t) => (
                    <div key={t.truong} className="text-gray-700">
                      {t.nhan}:{' '}
                      <span className="line-through text-gray-400">
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

      {moForm && (
        <FormLich
          banGhi={sk}
          onDong={() => setMoForm(false)}
          onXong={(moi) => {
            setSk(moi);
            setMoForm(false);
            setNhatKy(null);
          }}
        />
      )}
    </div>
  );
}

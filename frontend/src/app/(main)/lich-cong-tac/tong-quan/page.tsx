/**
 * /lich-cong-tac/tong-quan — chỉ số nhanh của Lịch công tác (G4.10).
 *
 * Mọi con số tính từ dữ liệu thật, không có số nhập tay. Bấm vào thẻ là mở
 * thẳng danh sách lịch của đúng khoảng ngày đó — chỉ số mà không đi tiếp được
 * thì chỉ để nhìn cho vui.
 *
 * "Trong tháng" và "trong năm" đếm TRỌN kỳ chứ không cắt ở hôm nay: lịch là để
 * nhìn việc sắp tới, cắt ở hôm nay thì đầu tháng nào con số cũng gần bằng 0.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { CalendarDays, Loader2, Star, Users } from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import { danhGiaChuanBiApi } from '@/services/danh-gia-chuan-bi';
import { errMsg } from '@/lib/hkg-error';
import {
  NHAN_LOAI_LICH,
  type IThongKeLich,
  type ITongHopChuanBi,
  type LoaiLich,
} from '@/types/lich-cong-tac';

/** Đường dẫn tới danh sách lịch đã lọc sẵn theo khoảng ngày. */
function duongDan(tu: string, den: string): string {
  return `/lich-cong-tac?che-do=danh-sach&tu-ngay=${tu}&den-ngay=${den}`;
}

function The({
  nhan,
  so,
  href,
  mau,
  ghiChu,
}: {
  nhan: string;
  so: number;
  href: string;
  mau: string;
  ghiChu?: string;
}) {
  return (
    <Link
      href={href}
      className={`flex-1 min-w-[150px] rounded-lg border px-4 py-3 transition hover:brightness-95 ${mau}`}
    >
      <div className="text-3xl font-bold tabular-nums">{so}</div>
      <div className="text-sm mt-0.5">{nhan}</div>
      {ghiChu && <div className="text-xs opacity-70 mt-0.5">{ghiChu}</div>}
    </Link>
  );
}

export default function TongQuanLichPage() {
  const [dl, setDl] = useState<IThongKeLich | null>(null);
  const [chuanBi, setChuanBi] = useState<ITongHopChuanBi | null>(null);
  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState<string | null>(null);

  useEffect(() => {
    lichCongTacApi
      .thongKe()
      .then(setDl)
      .catch((e) => setLoi(errMsg(e, 'Không tải được chỉ số')))
      .finally(() => setDangTai(false));
  }, []);

  // Điểm chuẩn bị tải riêng: thiếu nó thì các chỉ số còn lại vẫn dùng được,
  // không nên để một truy vấn phụ làm hỏng cả trang.
  useEffect(() => {
    danhGiaChuanBiApi.tongHop().then(setChuanBi).catch(() => setChuanBi(null));
  }, []);

  if (dangTai) {
    return (
      <div className="flex items-center justify-center py-16 text-gray-500">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        Đang tải…
      </div>
    );
  }

  if (loi || !dl) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
        {loi ?? 'Không có dữ liệu'}
      </div>
    );
  }

  const m = dl.moc;
  const loai = Object.entries(dl.theo_loai_thang_nay).sort(
    (a, b) => b[1] - a[1],
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-3">
        <The
          nhan="Hôm nay"
          so={dl.hom_nay}
          href={duongDan(m.hom_nay, m.hom_nay)}
          mau="bg-blue-50 border-blue-200 text-blue-900"
        />
        <The
          nhan="Ngày mai"
          so={dl.ngay_mai}
          href={duongDan(m.ngay_mai, m.ngay_mai)}
          mau="bg-indigo-50 border-indigo-200 text-indigo-900"
        />
        <The
          nhan="Trong tuần"
          so={dl.trong_tuan}
          href={duongDan(m.dau_tuan, m.cuoi_tuan)}
          mau="bg-emerald-50 border-emerald-200 text-emerald-900"
          ghiChu={`${m.dau_tuan.slice(8)}/${m.dau_tuan.slice(5, 7)} – ${m.cuoi_tuan.slice(8)}/${m.cuoi_tuan.slice(5, 7)}`}
        />
        <The
          nhan="Trong tháng"
          so={dl.trong_thang}
          href={duongDan(m.dau_thang, m.cuoi_thang)}
          mau="bg-amber-50 border-amber-200 text-amber-900"
          ghiChu="trọn tháng"
        />
        <The
          nhan="Trong năm"
          so={dl.trong_nam}
          href={duongDan(m.dau_nam, m.cuoi_nam)}
          mau="bg-gray-50 border-gray-200 text-gray-900"
          ghiChu="trọn năm"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <CalendarDays className="w-4 h-4 text-gray-500" />
            Theo loại lịch — tháng này
          </h2>
          {loai.length === 0 ? (
            <p className="text-sm text-gray-500">Tháng này chưa có lịch nào.</p>
          ) : (
            <ul className="space-y-1.5">
              {loai.map(([ma, so]) => (
                <li key={ma}>
                  <Link
                    href={`/lich-cong-tac?che-do=danh-sach&loai-lich=${ma}&tu-ngay=${m.dau_thang}&den-ngay=${m.cuoi_thang}`}
                    className="flex items-center justify-between rounded px-2 py-1 text-sm hover:bg-gray-50"
                  >
                    <span>
                      {NHAN_LOAI_LICH[ma as LoaiLich] ?? ma}
                    </span>
                    <span className="tabular-nums font-medium">{so}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Users className="w-4 h-4 text-gray-500" />
            Theo lãnh đạo — tháng này
          </h2>
          {dl.theo_lanh_dao_thang_nay.length === 0 ? (
            <p className="text-sm text-gray-500">
              Tháng này chưa có lịch nào gắn lãnh đạo.
            </p>
          ) : (
            <ul className="space-y-1.5">
              {dl.theo_lanh_dao_thang_nay.map((ld) => (
                <li key={ld.cong_chuc_id}>
                  <Link
                    href={`/lich-cong-tac/lanh-dao/${ld.cong_chuc_id}`}
                    className="flex items-center justify-between rounded px-2 py-1 text-sm hover:bg-gray-50"
                    title="Xem chương trình công tác"
                  >
                    <span>
                      {ld.ho_ten}
                      {ld.chuc_vu && (
                        <span className="text-gray-500"> — {ld.chuc_vu}</span>
                      )}
                    </span>
                    <span className="tabular-nums font-medium">
                      {ld.so_su_kien}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {chuanBi && chuanBi.so_luot > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h2 className="mb-1 flex items-center gap-2 font-semibold text-gray-900">
            <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
            Công tác chuẩn bị — điểm trung bình theo đơn vị
          </h2>
          <p className="mb-3 text-xs text-gray-500">
            {chuanBi.so_luot} lượt chấm trên {chuanBi.so_cuoc_hop} cuộc họp
            {chuanBi.diem_tb !== null && ` · trung bình ${chuanBi.diem_tb}/5`}.
            Chỉ lãnh đạo Chi cục và quản trị chấm được điểm này.
          </p>
          <ul className="space-y-1.5">
            {chuanBi.theo_don_vi.slice(0, 12).map((d) => (
              <li
                key={d.don_vi}
                className="flex items-center justify-between rounded px-2 py-1 text-sm"
              >
                <span>{d.don_vi}</span>
                <span className="tabular-nums text-gray-700">
                  <span className="font-medium text-amber-700">
                    {d.diem_tb.toFixed(1)}
                  </span>
                  <span className="text-gray-400"> /5 · {d.so_cuoc_hop} cuộc họp</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-gray-500">
        Một cuộc họp có nhiều lãnh đạo thì được tính cho từng người, nên tổng ở
        bảng bên phải lớn hơn số cuộc họp. Người vừa chủ trì vừa nằm trong danh
        sách lãnh đạo liên quan chỉ tính một lần.
      </p>
    </div>
  );
}

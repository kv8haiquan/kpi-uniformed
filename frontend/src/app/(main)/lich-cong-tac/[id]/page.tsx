/**
 * /lich-cong-tac/[id] — chi tiết một sự kiện trên lịch.
 *
 * Phần hiển thị nằm ở `components/ChiTietSuKien` vì chế độ "Lịch ngày" xếp
 * nhiều bản của đúng thẻ đó để xem cả ngày một lượt — hai bên phải giống hệt
 * nhau, không chép lại.
 *
 * Nếu sự kiện có nguồn HKG thì thẻ hiện nút mở thẳng sang chi tiết cuộc họp
 * trong Họp Không Giấy — tiêu chí 8.3 gạch 2 của yêu cầu chuyển đổi.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, CalendarClock, Loader2 } from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import { errMsg } from '@/lib/hkg-error';
import type { IQuyenLich, ISuKienChiTiet } from '@/types/lich-cong-tac';
import ChiTietSuKien from '../components/ChiTietSuKien';

export default function ChiTietSuKienPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [sk, setSk] = useState<ISuKienChiTiet | null>(null);
  const [quyen, setQuyen] = useState<IQuyenLich | null>(null);
  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState<string | null>(null);

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

  useEffect(() => {
    lichCongTacApi.quyenCuaToi().then(setQuyen).catch(() => setQuyen(null));
  }, []);

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

  const ngay = sk.ngay_hien_thi ?? sk.ngay_hop;

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Link
          href="/lich-cong-tac"
          className="inline-flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Lịch công tác
        </Link>

        {/* Đường ra màn hình cả ngày: xem một cuộc xong thường là muốn biết
            hôm đó còn cuộc nào nữa, trước đây phải quay lại lưới tháng dò. */}
        {ngay && (
          <Link
            href={`/lich-cong-tac?che-do=ngay&ngay=${ngay}`}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
          >
            <CalendarClock className="w-4 h-4" />
            Xem cả ngày
          </Link>
        )}
      </div>

      <ChiTietSuKien
        sk={sk}
        quyen={quyen}
        onThayDoi={setSk}
        onXoa={() => router.push('/lich-cong-tac')}
      />
    </div>
  );
}

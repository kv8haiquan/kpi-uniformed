/**
 * /lich-cong-tac/lanh-dao/[id] — chương trình công tác của một lãnh đạo.
 *
 * Tương ứng "Leader Schedule Card" của lichkv8. Sự kiện lấy theo hai nguồn:
 * lãnh đạo là chủ trì, hoặc nằm trong danh sách lãnh đạo liên quan — đúng cách
 * hệ cũ xác định lịch của lãnh đạo.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Loader2, MapPin } from 'lucide-react';

import { lichCongTacApi } from '@/services/lich-cong-tac';
import { errMsg } from '@/lib/hkg-error';
import type { ILichLanhDao, LoaiLich } from '@/types/lich-cong-tac';

const MAU_LOAI: Record<LoaiLich, string> = {
  HOP: 'bg-blue-100 text-blue-800',
  TRUC_BAN: 'bg-amber-100 text-amber-800',
  HOI_NGHI: 'bg-purple-100 text-purple-800',
  LAM_VIEC: 'bg-emerald-100 text-emerald-800',
  CONG_TAC: 'bg-cyan-100 text-cyan-800',
  LICH_KHAC: 'bg-gray-100 text-gray-700',
};

function homNayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`;
}

export default function LichLanhDaoPage() {
  const { id } = useParams<{ id: string }>();
  const [tuNgay, setTuNgay] = useState(homNayISO);
  const [soNgay, setSoNgay] = useState(30);
  const [dl, setDl] = useState<ILichLanhDao | null>(null);
  const [dangTai, setDangTai] = useState(true);
  const [loi, setLoi] = useState<string | null>(null);

  const tai = useCallback(async () => {
    setDangTai(true);
    setLoi(null);
    try {
      setDl(
        await lichCongTacApi.lichLanhDao(id, {
          'tu-ngay': tuNgay,
          'so-ngay': soNgay,
        }),
      );
    } catch (e) {
      setLoi(errMsg(e, 'Không tải được chương trình công tác'));
    } finally {
      setDangTai(false);
    }
  }, [id, tuNgay, soNgay]);

  useEffect(() => {
    void tai();
  }, [tai]);

  return (
    <div className="space-y-4 max-w-4xl">
      <Link
        href="/lich-cong-tac"
        className="inline-flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="w-4 h-4" />
        Lịch công tác
      </Link>

      {dl && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h1 className="text-lg font-semibold text-gray-900">
            {dl.lanh_dao.ho_ten}
          </h1>
          {dl.lanh_dao.chuc_vu && (
            <p className="text-sm text-gray-500">{dl.lanh_dao.chuc_vu}</p>
          )}
          <p className="mt-1 text-sm text-gray-600">
            {dl.tong_su_kien} sự kiện trong {soNgay} ngày
          </p>
        </div>
      )}

      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm">
          <span className="block text-gray-600 mb-1">Từ ngày</span>
          <input
            type="date"
            value={tuNgay}
            onChange={(e) => setTuNgay(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-1.5"
          />
        </label>
        <label className="text-sm">
          <span className="block text-gray-600 mb-1">Khoảng</span>
          <select
            value={soNgay}
            onChange={(e) => setSoNgay(Number(e.target.value))}
            className="rounded-lg border border-gray-300 px-3 py-1.5"
          >
            {[7, 14, 30, 60, 90].map((n) => (
              <option key={n} value={n}>
                {n} ngày
              </option>
            ))}
          </select>
        </label>
      </div>

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
      ) : !dl || dl.theo_ngay.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white py-16 text-center text-gray-500">
          Không có sự kiện nào trong khoảng đã chọn.
        </div>
      ) : (
        <div className="space-y-3">
          {dl.theo_ngay.map((ng) => (
            <div
              key={ng.ngay}
              className="rounded-lg border border-gray-200 bg-white overflow-hidden"
            >
              <div className="bg-gray-50 px-4 py-2 text-sm font-semibold text-gray-700 border-b border-gray-200">
                {ng.ngay.split('-').reverse().join('/')}
              </div>
              <ul className="divide-y divide-gray-100">
                {ng.su_kien.map((sk) => (
                  <li key={sk.id} className="px-4 py-2.5">
                    <div className="flex items-start gap-3">
                      <span className="w-12 shrink-0 text-sm font-medium text-gray-700 tabular-nums pt-0.5">
                        {sk.gio_bat_dau.slice(0, 5)}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`rounded px-1.5 py-0.5 text-[11px] ${
                              MAU_LOAI[sk.loai_lich ?? 'LICH_KHAC']
                            }`}
                          >
                            {sk.loai_lich_nhan ?? 'Lịch khác'}
                          </span>
                          <Link
                            href={`/lich-cong-tac/${sk.id}`}
                            className="text-sm font-medium text-gray-900 hover:text-blue-700"
                          >
                            {sk.tieu_de}
                          </Link>
                        </div>
                        {sk.dia_diem && (
                          <p className="mt-0.5 inline-flex items-center gap-1 text-xs text-gray-500">
                            <MapPin className="w-3 h-3" />
                            {sk.dia_diem}
                          </p>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

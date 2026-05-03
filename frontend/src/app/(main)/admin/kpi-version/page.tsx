'use client';

/**
 * app/(main)/admin/kpi-version/page.tsx
 * =====================================
 * Trang admin pin phiên bản KPI cho CC / đơn vị (Phase E — 29/04/2026).
 *
 * Use case UAT:
 *   Admin chọn 1-2 đơn vị thử V2_PL3 trong tháng kiểm thử,
 *   các đơn vị khác giữ V1 → 2 phiên bản chạy song song.
 *
 * KHÔNG có UI "default hệ thống" theo decision Phase E (cutover qua SQL).
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Search, Users, User, Loader2, AlertCircle } from 'lucide-react';

import { isApiError } from '@/lib/axios';
import { adminPL3Service } from '@/services/admin-pl3.service';
import { adminService } from '@/services/admin.service';
import { KpiVersion } from '@/types/admin-pl3';

interface DonViLite {
  id: string;
  ma_don_vi?: string;
  ten_don_vi: string;
}

interface CongChucLite {
  id: string;
  ma_cc: string;
  ho_ten: string;
  don_vi_ten?: string | null;
  kpi_version_pinned?: KpiVersion | null;
}

// IDonViOption from admin.service trả về tối thiểu {id, ten_don_vi}
interface IDonViOptionShape extends DonViLite {}
// IUserResponse có các field mở rộng — chỉ pick fields cần
interface IUserResponseShape {
  id: string;
  ma_cc: string;
  ho_ten: string;
  don_vi_ten?: string | null;
  kpi_version_pinned?: KpiVersion | null;
}

const VERSION_OPTIONS: { value: KpiVersion | null; label: string }[] = [
  { value: null, label: 'Default hệ thống' },
  { value: 'V1', label: 'V1 (cũ)' },
  { value: 'V2_PL3', label: 'V2_PL3 (mới)' },
];

export default function AdminKpiVersionPage() {
  // Don vi pin
  const [donViList, setDonViList] = useState<DonViLite[]>([]);
  const [selectedDonVi, setSelectedDonVi] = useState<string>('');
  const [donViVersion, setDonViVersion] = useState<KpiVersion | null>(null);
  const [donViBusy, setDonViBusy] = useState(false);
  const [donViMsg, setDonViMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(
    null
  );

  // CC search + pin
  const [searchCC, setSearchCC] = useState('');
  const [ccList, setCcList] = useState<CongChucLite[]>([]);
  const [ccLoading, setCcLoading] = useState(false);
  const [ccBusy, setCcBusy] = useState<string | null>(null);

  // Load đơn vị
  useEffect(() => {
    adminService
      .getDonViList()
      .then((res) => setDonViList(res ?? []))
      .catch((err) => console.error('Load don vi error', err));
  }, []);

  const reloadCC = useCallback(async () => {
    if (!searchCC.trim() && !selectedDonVi) {
      setCcList([]);
      return;
    }
    setCcLoading(true);
    try {
      const res = await adminService.getUsers({
        search: searchCC.trim() || undefined,
        don_vi_id: selectedDonVi || undefined,
        page: 1,
        page_size: 50,
      });
      setCcList(
        (res.data ?? []).map((u: IUserResponseShape) => ({
          id: u.id,
          ma_cc: u.ma_cc,
          ho_ten: u.ho_ten,
          don_vi_ten: u.don_vi_ten,
          kpi_version_pinned: u.kpi_version_pinned ?? null,
        }))
      );
    } catch (err) {
      console.error(err);
    } finally {
      setCcLoading(false);
    }
  }, [searchCC, selectedDonVi]);

  useEffect(() => {
    const t = setTimeout(reloadCC, 400);
    return () => clearTimeout(t);
  }, [reloadCC]);

  const submitDonVi = async () => {
    if (!selectedDonVi) return;
    setDonViBusy(true);
    setDonViMsg(null);
    try {
      const res = await adminPL3Service.setDonViVersion(selectedDonVi, donViVersion);
      setDonViMsg({
        type: 'success',
        text: `Đã set ${res.updated}/${res.total_cc} CC trong "${res.ten_don_vi}" sang ${donViVersion ?? 'Default'}`,
      });
      reloadCC();
    } catch (err: unknown) {
      setDonViMsg({
        type: 'error',
        text: isApiError(err) ? err.message : 'Lỗi pin đơn vị',
      });
    } finally {
      setDonViBusy(false);
    }
  };

  const setCCVersion = async (cc: CongChucLite, version: KpiVersion | null) => {
    setCcBusy(cc.id);
    try {
      await adminPL3Service.setCongChucVersion(cc.id, version);
      setCcList((prev) =>
        prev.map((c) =>
          c.id === cc.id ? { ...c, kpi_version_pinned: version } : c
        )
      );
    } catch (err: unknown) {
      alert(isApiError(err) ? err.message : 'Lỗi pin CC');
    } finally {
      setCcBusy(null);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cấu hình phiên bản KPI</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Pin V1 / V2_PL3 / Default cho từng công chức hoặc cả đơn vị (UAT scenario)
        </p>
      </div>

      <div className="rounded-md bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-900 flex items-start gap-2">
        <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
        <div>
          <strong>Default hệ thống hiện tại: V2_PL3</strong> (cutover qua DB).
          Khi <code>kpi_version_pinned IS NULL</code>, hệ thống dùng default này.
          Cần đổi default? Liên hệ devops chạy SQL update <code>platform_config</code>.
        </div>
      </div>

      {/* SECTION 1: Pin theo đơn vị */}
      <section className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Pin theo đơn vị (bulk)</h2>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Đơn vị
            </label>
            <select
              value={selectedDonVi}
              onChange={(e) => setSelectedDonVi(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">— Chọn đơn vị —</option>
              {donViList.map((dv) => (
                <option key={dv.id} value={dv.id}>
                  {dv.ten_don_vi}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Phiên bản
            </label>
            <select
              value={donViVersion ?? ''}
              onChange={(e) =>
                setDonViVersion(e.target.value === '' ? null : (e.target.value as KpiVersion))
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              {VERSION_OPTIONS.map((opt) => (
                <option key={String(opt.value)} value={opt.value ?? ''}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={submitDonVi}
              disabled={!selectedDonVi || donViBusy}
              className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-60"
            >
              {donViBusy ? (
                <span className="inline-flex items-center gap-1 justify-center">
                  <Loader2 className="h-4 w-4 animate-spin" /> Đang xử lý…
                </span>
              ) : (
                'Áp dụng cho tất cả CC'
              )}
            </button>
          </div>
        </div>

        {donViMsg && (
          <div
            className={[
              'rounded-md px-4 py-2 text-sm',
              donViMsg.type === 'success'
                ? 'bg-green-50 border border-green-200 text-green-800'
                : 'bg-red-50 border border-red-200 text-red-800',
            ].join(' ')}
          >
            {donViMsg.text}
          </div>
        )}
      </section>

      {/* SECTION 2: Pin theo cá nhân */}
      <section className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
        <div className="flex items-center gap-2">
          <User className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Pin theo cá nhân</h2>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            value={searchCC}
            onChange={(e) => setSearchCC(e.target.value)}
            placeholder="Tìm theo mã CC hoặc họ tên… (lọc thêm theo đơn vị bên trên)"
            className="w-full rounded-md border border-gray-300 pl-9 pr-3 py-2 text-sm"
          />
        </div>

        <div className="border border-gray-200 rounded-md overflow-hidden">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Mã CC
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Họ tên
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Đơn vị
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Pinned
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                  Hành động
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {ccLoading && (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-gray-500">
                    Đang tải…
                  </td>
                </tr>
              )}
              {!ccLoading && ccList.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-gray-500">
                    {searchCC || selectedDonVi
                      ? 'Không tìm thấy CC.'
                      : 'Nhập từ khóa hoặc chọn đơn vị để tìm CC.'}
                  </td>
                </tr>
              )}
              {ccList.map((cc) => (
                <tr key={cc.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 font-mono text-xs">{cc.ma_cc}</td>
                  <td className="px-3 py-2">{cc.ho_ten}</td>
                  <td className="px-3 py-2 text-gray-600">{cc.don_vi_ten ?? '—'}</td>
                  <td className="px-3 py-2">
                    {cc.kpi_version_pinned ? (
                      <span
                        className={[
                          'inline-flex px-2 py-0.5 text-xs rounded',
                          cc.kpi_version_pinned === 'V2_PL3'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-700',
                        ].join(' ')}
                      >
                        {cc.kpi_version_pinned}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-500 italic">— Default —</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right space-x-1">
                    <select
                      value={cc.kpi_version_pinned ?? ''}
                      disabled={ccBusy === cc.id}
                      onChange={(e) =>
                        setCCVersion(
                          cc,
                          e.target.value === '' ? null : (e.target.value as KpiVersion)
                        )
                      }
                      className="rounded border border-gray-300 px-2 py-1 text-xs"
                    >
                      <option value="">Default</option>
                      <option value="V1">V1</option>
                      <option value="V2_PL3">V2_PL3</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

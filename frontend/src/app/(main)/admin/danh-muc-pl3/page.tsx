'use client';

/**
 * app/(main)/admin/danh-muc-pl3/page.tsx
 * ======================================
 * Trang admin quản lý danh mục PL3 (V2 — Phase E, 29/04/2026).
 *
 * Tách riêng với /admin/danh-muc-cv (V1 — giữ nguyên không động).
 *
 * Tính năng:
 * - List + filter (lĩnh vực, nhóm, search) + pagination.
 * - Modal tạo / sửa: nhập trực tiếp `diem_cham`, auto-compute he_so + khung.
 * - Modal Import Excel 3 bước (component riêng).
 * - Soft delete (is_active=FALSE).
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Plus,
  RefreshCw,
  Edit3,
  Power,
  Search,
  Upload,
  AlertCircle,
} from 'lucide-react';

import { isApiError } from '@/lib/axios';
import { adminPL3Service } from '@/services/admin-pl3.service';
import { kpiV2Service } from '@/services/kpi-v2.service';
import {
  IDanhMucPL3,
  IDanhMucPL3CreateRequest,
  IDanhMucPL3UpdateRequest,
} from '@/types/admin-pl3';
import { ILinhVuc } from '@/types/kpi-v2';

import { ImportPL3Modal } from '@/components/admin/ImportPL3Modal';

const NHOM_KHUNG_MAP: Record<number, number> = {
  1: 100,
  2: 200,
  3: 300,
  4: 400,
  5: 500,
};

interface FormState {
  ma_danh_muc: string;
  ten_cong_viec: string;
  linh_vuc: string;
  nhom_pl3: number;
  diem_cham: number;
  nhiem_vu: string;
  cong_viec_chi_tiet: string;
  san_pham_dau_ra: string;
  mo_ta: string;
  is_active: boolean;
}

const EMPTY_FORM: FormState = {
  ma_danh_muc: '',
  ten_cong_viec: '',
  linh_vuc: 'I',
  nhom_pl3: 1,
  diem_cham: 25,
  nhiem_vu: '',
  cong_viec_chi_tiet: '',
  san_pham_dau_ra: '',
  mo_ta: '',
  is_active: true,
};

export default function AdminDanhMucPL3Page() {
  const [list, setList] = useState<IDanhMucPL3[]>([]);
  const [total, setTotal] = useState(0);
  const [linhVucList, setLinhVucList] = useState<ILinhVuc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter
  const [filterLinhVuc, setFilterLinhVuc] = useState('');
  const [filterNhom, setFilterNhom] = useState<number | ''>('');
  const [filterSearch, setFilterSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 50;

  // Modal
  const [openImport, setOpenImport] = useState(false);
  const [openForm, setOpenForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminPL3Service.listPL3({
        linh_vuc: filterLinhVuc || undefined,
        nhom_pl3: filterNhom === '' ? undefined : filterNhom,
        search: filterSearch || undefined,
        page,
        page_size: pageSize,
      });
      setList(res.data);
      setTotal(res.pagination?.total_items ?? 0);
    } catch (err: unknown) {
      console.error(err);
      if (isApiError(err)) setError(err.message);
      else setError('Lỗi tải danh mục');
    } finally {
      setLoading(false);
    }
  }, [filterLinhVuc, filterNhom, filterSearch, page]);

  useEffect(() => {
    reload();
  }, [reload]);

  useEffect(() => {
    kpiV2Service.getLinhVuc().then(setLinhVucList).catch(console.error);
  }, []);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const handleDeactivate = async (item: IDanhMucPL3) => {
    if (
      !confirm(`Vô hiệu hóa "${item.ma_danh_muc}"? Mục sẽ không hiện cho CC kê khai mới.`)
    )
      return;
    try {
      await adminPL3Service.deactivatePL3(item.id);
      await reload();
    } catch (err: unknown) {
      alert(isApiError(err) ? err.message : 'Lỗi');
    }
  };

  const openCreate = () => {
    setEditingId(null);
    setOpenForm(true);
  };

  const openEdit = (item: IDanhMucPL3) => {
    setEditingId(item.id);
    setOpenForm(true);
  };

  return (
    <div className="p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Quản lý danh mục PL3 (V2)
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            2.812 mục công việc theo Phụ lục III của Bộ Nội vụ
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setOpenImport(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-300 rounded-md hover:bg-blue-100"
          >
            <Upload className="h-4 w-4" /> Import Excel
          </button>
          <button
            onClick={openCreate}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" /> Thêm mục
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Lĩnh vực</label>
            <select
              value={filterLinhVuc}
              onChange={(e) => {
                setFilterLinhVuc(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">— Tất cả 15 lĩnh vực —</option>
              {linhVucList.map((lv) => (
                <option key={lv.ma} value={lv.ma}>
                  {lv.ma}. {lv.ten}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Nhóm</label>
            <select
              value={filterNhom}
              onChange={(e) => {
                setFilterNhom(e.target.value === '' ? '' : Number(e.target.value));
                setPage(1);
              }}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">— Tất cả nhóm —</option>
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  Nhóm {n} (max {NHOM_KHUNG_MAP[n]})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Tìm kiếm</label>
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={filterSearch}
                onChange={(e) => {
                  setFilterSearch(e.target.value);
                  setPage(1);
                }}
                placeholder="Tên CV / mã / chi tiết…"
                className="w-full rounded-md border border-gray-300 pl-8 pr-3 py-2 text-sm"
              />
            </div>
          </div>
        </div>
        <div className="text-xs text-gray-500">
          Tổng: <strong>{total}</strong> mục • Trang {page}/{totalPages}
          <button
            onClick={reload}
            className="ml-2 inline-flex items-center gap-1 text-blue-600 hover:underline"
          >
            <RefreshCw className="h-3 w-3" /> Tải lại
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Mã
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Tên công việc
                </th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                  Lĩnh vực
                </th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                  Nhóm
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                  Điểm chấm
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                  Hệ số
                </th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                  Active
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                  Hành động
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading && (
                <tr>
                  <td colSpan={8} className="px-3 py-6 text-center text-gray-500">
                    Đang tải…
                  </td>
                </tr>
              )}
              {!loading && list.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-3 py-6 text-center text-gray-500">
                    Không có mục.
                  </td>
                </tr>
              )}
              {list.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 font-mono text-xs text-gray-700">
                    {item.ma_danh_muc}
                  </td>
                  <td className="px-3 py-2 text-gray-900 max-w-md">
                    <p className="line-clamp-2">{item.ten_cong_viec}</p>
                    {item.san_pham_dau_ra && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        SP: {item.san_pham_dau_ra}
                      </p>
                    )}
                  </td>
                  <td className="px-3 py-2 text-center">{item.linh_vuc}</td>
                  <td className="px-3 py-2 text-center">{item.nhom_pl3}</td>
                  <td className="px-3 py-2 text-right">{item.diem_cham}</td>
                  <td className="px-3 py-2 text-right font-mono text-blue-700">
                    {item.he_so_quy_doi?.toFixed(6).replace(/\.?0+$/, '')}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {item.is_active ? (
                      <span className="inline-flex px-2 py-0.5 text-xs rounded bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-600">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right space-x-1">
                    <button
                      onClick={() => openEdit(item)}
                      className="p-1 rounded text-blue-600 hover:bg-blue-50"
                      title="Sửa"
                    >
                      <Edit3 className="h-4 w-4" />
                    </button>
                    {item.is_active && (
                      <button
                        onClick={() => handleDeactivate(item)}
                        className="p-1 rounded text-red-500 hover:bg-red-50"
                        title="Vô hiệu hóa"
                      >
                        <Power className="h-4 w-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-3 py-2 border-t border-gray-200 flex justify-between items-center text-sm">
            <span className="text-gray-600">
              Trang {page}/{totalPages}
            </span>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-40"
              >
                ← Trước
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-40"
              >
                Sau →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <ImportPL3Modal
        open={openImport}
        onClose={() => setOpenImport(false)}
        onSuccess={reload}
      />

      <DanhMucPL3FormModal
        open={openForm}
        editingId={editingId}
        linhVucList={linhVucList}
        onClose={() => setOpenForm(false)}
        onSuccess={reload}
      />
    </div>
  );
}

// =============================================================================
// Form Modal
// =============================================================================

function DanhMucPL3FormModal({
  open,
  editingId,
  linhVucList,
  onClose,
  onSuccess,
}: {
  open: boolean;
  editingId: string | null;
  linhVucList: ILinhVuc[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Auto-compute
  const heSoQuyDoi = useMemo(() => form.diem_cham / 25, [form.diem_cham]);
  const khungDiemToiDa = useMemo(
    () => NHOM_KHUNG_MAP[form.nhom_pl3] ?? 100,
    [form.nhom_pl3]
  );
  const overflow = form.diem_cham > khungDiemToiDa;

  // Load data nếu edit
  useEffect(() => {
    if (!open) return;
    setErrorMsg(null);
    if (editingId) {
      adminPL3Service
        .detailPL3(editingId)
        .then((dm) => {
          setForm({
            ma_danh_muc: dm.ma_danh_muc,
            ten_cong_viec: dm.ten_cong_viec,
            linh_vuc: dm.linh_vuc ?? 'I',
            nhom_pl3: dm.nhom_pl3 ?? 1,
            diem_cham: dm.diem_cham ?? 25,
            nhiem_vu: dm.nhiem_vu ?? '',
            cong_viec_chi_tiet: dm.cong_viec_chi_tiet ?? '',
            san_pham_dau_ra: dm.san_pham_dau_ra ?? '',
            mo_ta: dm.mo_ta ?? '',
            is_active: dm.is_active,
          });
        })
        .catch((err) => setErrorMsg(isApiError(err) ? err.message : 'Lỗi load'));
    } else {
      setForm(EMPTY_FORM);
    }
  }, [open, editingId]);

  if (!open) return null;

  const submit = async () => {
    setErrorMsg(null);
    if (!form.ma_danh_muc.trim() || !form.ten_cong_viec.trim()) {
      setErrorMsg('Vui lòng nhập đầy đủ Mã và Tên');
      return;
    }
    if (overflow) {
      setErrorMsg(`Điểm chấm vượt khung Nhóm ${form.nhom_pl3} (max ${khungDiemToiDa})`);
      return;
    }

    setSubmitting(true);
    try {
      if (editingId) {
        const updateData: IDanhMucPL3UpdateRequest = {
          ten_cong_viec: form.ten_cong_viec,
          linh_vuc: form.linh_vuc,
          nhom_pl3: form.nhom_pl3,
          diem_cham: form.diem_cham,
          nhiem_vu: form.nhiem_vu || undefined,
          cong_viec_chi_tiet: form.cong_viec_chi_tiet || undefined,
          san_pham_dau_ra: form.san_pham_dau_ra || undefined,
          mo_ta: form.mo_ta || undefined,
          is_active: form.is_active,
        };
        await adminPL3Service.updatePL3(editingId, updateData);
      } else {
        const createData: IDanhMucPL3CreateRequest = {
          ma_danh_muc: form.ma_danh_muc.trim(),
          ten_cong_viec: form.ten_cong_viec.trim(),
          linh_vuc: form.linh_vuc,
          nhom_pl3: form.nhom_pl3,
          diem_cham: form.diem_cham,
          nhiem_vu: form.nhiem_vu || undefined,
          cong_viec_chi_tiet: form.cong_viec_chi_tiet || undefined,
          san_pham_dau_ra: form.san_pham_dau_ra || undefined,
          mo_ta: form.mo_ta || undefined,
          is_active: form.is_active,
        };
        await adminPL3Service.createPL3(createData);
      }
      onSuccess();
      onClose();
    } catch (err: unknown) {
      console.error(err);
      setErrorMsg(isApiError(err) ? err.message : 'Lỗi submit');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {editingId ? 'Sửa mục PL3' : 'Thêm mục PL3'}
          </h2>
        </div>

        <div className="px-6 py-4 space-y-4">
          <div>
            <label className="block text-sm text-gray-700 mb-1">
              Mã danh mục <span className="text-red-500">*</span>
            </label>
            <input
              value={form.ma_danh_muc}
              disabled={!!editingId}
              onChange={(e) => setForm({ ...form, ma_danh_muc: e.target.value })}
              placeholder="VD: PL3-I-CUSTOM-001"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono disabled:bg-gray-100"
            />
            <p className="mt-1 text-xs text-gray-500">
              Format: PL3-{'{lĩnh vực}'}-{'{stt}'}, max 30 ký tự
            </p>
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">
              Tên công việc <span className="text-red-500">*</span>
            </label>
            <input
              value={form.ten_cong_viec}
              onChange={(e) => setForm({ ...form, ten_cong_viec: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1">
                Lĩnh vực <span className="text-red-500">*</span>
              </label>
              <select
                value={form.linh_vuc}
                onChange={(e) => setForm({ ...form, linh_vuc: e.target.value })}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                {linhVucList.map((lv) => (
                  <option key={lv.ma} value={lv.ma}>
                    {lv.ma}. {lv.ten}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">
                Nhóm <span className="text-red-500">*</span>
              </label>
              <select
                value={form.nhom_pl3}
                onChange={(e) =>
                  setForm({ ...form, nhom_pl3: Number(e.target.value) })
                }
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    Nhóm {n} (max {NHOM_KHUNG_MAP[n]})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">
              Điểm chấm <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              min={1}
              max={500}
              step={1}
              value={form.diem_cham}
              onChange={(e) => setForm({ ...form, diem_cham: Number(e.target.value) })}
              className={[
                'w-full rounded-md border px-3 py-2 text-sm',
                overflow ? 'border-red-400 bg-red-50' : 'border-gray-300',
              ].join(' ')}
            />
            <p className="mt-1 text-xs text-gray-500">
              Số nguyên 1-{khungDiemToiDa} (theo Nhóm {form.nhom_pl3})
            </p>
          </div>

          {/* Tự tính */}
          <div className="rounded-md bg-blue-50 border border-blue-200 px-4 py-3 text-sm space-y-1">
            <div>
              Khung điểm tối đa Nhóm {form.nhom_pl3}:{' '}
              <strong className="text-blue-900">{khungDiemToiDa}</strong>
            </div>
            <div>
              Hệ số quy đổi (auto): <strong className="text-blue-900">{heSoQuyDoi.toFixed(4)}</strong>{' '}
              <span className="text-xs text-gray-500">(= điểm chấm / 25)</span>
            </div>
            {overflow && (
              <div className="flex items-center gap-1 text-red-700 mt-2">
                <AlertCircle className="h-4 w-4" />
                Điểm chấm vượt khung của Nhóm {form.nhom_pl3}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">
              Nhiệm vụ (tùy chọn)
            </label>
            <input
              value={form.nhiem_vu}
              onChange={(e) => setForm({ ...form, nhiem_vu: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">
              Công việc chi tiết (tùy chọn)
            </label>
            <textarea
              rows={2}
              value={form.cong_viec_chi_tiet}
              onChange={(e) =>
                setForm({ ...form, cong_viec_chi_tiet: e.target.value })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">
              Sản phẩm đầu ra (tùy chọn)
            </label>
            <input
              value={form.san_pham_dau_ra}
              onChange={(e) => setForm({ ...form, san_pham_dau_ra: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300"
            />
            <label htmlFor="is_active" className="text-sm text-gray-700">
              Active (hiện cho CC chọn khi kê khai)
            </label>
          </div>

          {errorMsg && (
            <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
              {errorMsg}
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-gray-50 px-6 py-3 border-t border-gray-200 flex justify-end gap-2">
          <button
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Hủy
          </button>
          <button
            onClick={submit}
            disabled={submitting || overflow}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-60"
          >
            {submitting ? 'Đang lưu…' : 'Lưu'}
          </button>
        </div>
      </div>
    </div>
  );
}

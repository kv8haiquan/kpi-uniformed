/**
 * src/app/(main)/admin/vinh-danh/page.tsx
 * =========================================
 * Trang admin quản lý vinh danh công chức tiêu biểu tháng.
 *
 * Quyền: System Admin (admin layout đã check).
 *
 * Phiên bản: 1.0 (10/05/2026)
 */

'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { vinhDanhApi } from '@/services/portal';
import { adminService } from '@/services/admin.service';
import type {
  IVinhDanhThang,
  IVinhDanhThangCreate,
  IVinhDanhThangUpdate,
  TrangThaiVinhDanh,
} from '@/types/vinh-danh';
import type { IUserResponse } from '@/types/admin';

const PORTAL_BASE =
  process.env.NEXT_PUBLIC_PORTAL_API_URL?.replace(/\/api\/v1$/, '') || '';

function buildAnhUrl(path?: string | null): string | null {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  return `${PORTAL_BASE}${path}`;
}

function getApiErrorMessage(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: { detail?: { error?: { message?: string } } } } };
  return e?.response?.data?.detail?.error?.message ?? fallback;
}

const VI_TRI_MAC_DINH = '50% 50%';

/** Parse chuỗi "50% 30%" → [50, 30]; fallback [50, 50]. */
function parseViTri(value?: string | null): [number, number] {
  if (!value) return [50, 50];
  const m = value.match(/(-?\d+(?:\.\d+)?)%?\s+(-?\d+(?:\.\d+)?)%?/);
  if (!m) return [50, 50];
  const x = Math.min(100, Math.max(0, Number(m[1])));
  const y = Math.min(100, Math.max(0, Number(m[2])));
  return [x, y];
}

const clamp = (n: number) => Math.min(100, Math.max(0, n));

/**
 * Editor kéo-thả để chỉnh vị trí ảnh trong khung tròn.
 * Người dùng giữ chuột và rê ảnh để canh khuôn mặt vào giữa.
 * Lưu kết quả dưới dạng CSS object-position "x% y%".
 */
function AnhViTriEditor({
  src,
  value,
  onChange,
}: {
  src: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const frameRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{ sx: number; sy: number; px: number; py: number } | null>(null);
  const [dragging, setDragging] = useState(false);
  const [px, py] = parseViTri(value);

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    const el = frameRef.current;
    if (!el) return;
    el.setPointerCapture(e.pointerId);
    drag.current = { sx: e.clientX, sy: e.clientY, px, py };
    setDragging(true);
  };

  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    const el = frameRef.current;
    if (!d || !el) return;
    const rect = el.getBoundingClientRect();
    // Rê ảnh sang phải → hiện phần bên trái → object-position-x giảm
    const nx = clamp(d.px - ((e.clientX - d.sx) / rect.width) * 100);
    const ny = clamp(d.py - ((e.clientY - d.sy) / rect.height) * 100);
    onChange(`${Math.round(nx)}% ${Math.round(ny)}%`);
  };

  const endDrag = (e: React.PointerEvent<HTMLDivElement>) => {
    drag.current = null;
    setDragging(false);
    try {
      frameRef.current?.releasePointerCapture(e.pointerId);
    } catch {
      /* noop */
    }
  };

  return (
    <div className="flex items-center gap-4">
      <div className="flex flex-col items-center gap-2">
        <div
          ref={frameRef}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={endDrag}
          onPointerCancel={endDrag}
          className={`relative w-36 h-36 rounded-full overflow-hidden border-4 shadow select-none touch-none ${
            dragging ? 'border-amber-500 cursor-grabbing' : 'border-amber-300 cursor-grab'
          }`}
          title="Giữ chuột và rê để chỉnh vị trí ảnh"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={src}
            alt="Chỉnh vị trí ảnh"
            draggable={false}
            className="w-full h-full object-cover pointer-events-none"
            style={{ objectPosition: value || VI_TRI_MAC_DINH }}
          />
          {/* Vòng ngắm ở giữa để canh mặt */}
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <div className="w-16 h-16 rounded-full border border-white/70 shadow-[0_0_0_9999px_rgba(0,0,0,0.04)]" />
          </div>
        </div>
        <button
          type="button"
          onClick={() => onChange(VI_TRI_MAC_DINH)}
          className="text-xs text-amber-700 hover:text-amber-900 hover:underline"
        >
          ↺ Về giữa
        </button>
      </div>
      <div className="text-xs text-gray-500 leading-relaxed">
        <p className="font-medium text-gray-700 mb-1">Chỉnh vị trí khuôn mặt</p>
        <p>Giữ chuột và <strong>rê ảnh</strong> trong khung tròn để canh khuôn mặt vào giữa.</p>
        <p className="mt-1 text-gray-400">Đây chính là khung tròn hiển thị trên trang tổng quan.</p>
      </div>
    </div>
  );
}

interface FormState {
  thang: number;
  nam: number;
  cong_chuc_id: string;
  tieu_de: string;
  ly_do: string;
  anh_chan_dung: string;
  anh_vi_tri: string;
  loi_tuyen_duong: string;
}

const NOW = new Date();

const EMPTY_FORM: FormState = {
  thang: NOW.getMonth() + 1,
  nam: NOW.getFullYear(),
  cong_chuc_id: '',
  tieu_de: `Công chức tiêu biểu tháng ${NOW.getMonth() + 1}/${NOW.getFullYear()}`,
  ly_do: '',
  anh_chan_dung: '',
  anh_vi_tri: VI_TRI_MAC_DINH,
  loi_tuyen_duong: '',
};

export default function VinhDanhAdminPage() {
  const [items, setItems] = useState<IVinhDanhThang[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterNam, setFilterNam] = useState<number | ''>('');
  const [filterTrangThai, setFilterTrangThai] = useState<TrangThaiVinhDanh | ''>('');
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<IVinhDanhThang | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  // Công chức search
  const [searchUser, setSearchUser] = useState('');
  const [userOptions, setUserOptions] = useState<IUserResponse[]>([]);
  const [searchingUser, setSearchingUser] = useState(false);
  const [selectedUser, setSelectedUser] = useState<IUserResponse | null>(null);

  // Upload ảnh
  const [uploadingAnh, setUploadingAnh] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page: 1, page_size: 100 };
      if (filterNam) params.nam = filterNam;
      if (filterTrangThai) params.trang_thai = filterTrangThai;
      const res = await vinhDanhApi.danhSach(params);
      setItems(res.data?.data ?? []);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Không tải được danh sách'));
    } finally {
      setLoading(false);
    }
  }, [filterNam, filterTrangThai]);

  useEffect(() => {
    loadList();
  }, [loadList]);

  // Search công chức với debounce
  useEffect(() => {
    if (!searchUser.trim() || searchUser.trim().length < 2) {
      setUserOptions([]);
      return;
    }
    const t = setTimeout(async () => {
      setSearchingUser(true);
      try {
        const res = await adminService.getUsers({
          search: searchUser.trim(),
          page: 1,
          page_size: 20,
          is_active: true,
        });
        setUserOptions(res.data ?? []);
      } catch {
        setUserOptions([]);
      } finally {
        setSearchingUser(false);
      }
    }, 350);
    return () => clearTimeout(t);
  }, [searchUser]);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setSelectedUser(null);
    setSearchUser('');
    setUserOptions([]);
    setShowForm(true);
  };

  const openEdit = (vd: IVinhDanhThang) => {
    setEditing(vd);
    setForm({
      thang: vd.thang,
      nam: vd.nam,
      cong_chuc_id: vd.cong_chuc?.id || '',
      tieu_de: vd.tieu_de,
      ly_do: vd.ly_do,
      anh_chan_dung: vd.anh_chan_dung || '',
      anh_vi_tri: vd.anh_vi_tri || VI_TRI_MAC_DINH,
      loi_tuyen_duong: vd.loi_tuyen_duong || '',
    });
    if (vd.cong_chuc) {
      setSelectedUser({
        id: vd.cong_chuc.id,
        ma_cc: vd.cong_chuc.ma_cc,
        ho_ten: vd.cong_chuc.ho_ten,
        chuc_vu: vd.cong_chuc.chuc_vu ?? null,
      } as IUserResponse);
    } else {
      setSelectedUser(null);
    }
    setSearchUser('');
    setUserOptions([]);
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditing(null);
    setForm(EMPTY_FORM);
    setSelectedUser(null);
  };

  const handleUploadAnh = async (file: File) => {
    setUploadingAnh(true);
    try {
      const res = await vinhDanhApi.uploadAnh(file);
      const url = res.data?.data?.url;
      if (url) setForm((f) => ({ ...f, anh_chan_dung: url }));
    } catch (err) {
      alert(getApiErrorMessage(err, 'Upload ảnh thất bại'));
    } finally {
      setUploadingAnh(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.cong_chuc_id) {
      alert('Vui lòng chọn công chức');
      return;
    }
    if (!form.tieu_de.trim() || !form.ly_do.trim()) {
      alert('Vui lòng nhập tiêu đề và lý do');
      return;
    }

    setSubmitting(true);
    try {
      if (editing) {
        const update: IVinhDanhThangUpdate = {
          thang: form.thang,
          nam: form.nam,
          cong_chuc_id: form.cong_chuc_id,
          tieu_de: form.tieu_de.trim(),
          ly_do: form.ly_do.trim(),
          anh_chan_dung: form.anh_chan_dung || null,
          anh_vi_tri: form.anh_vi_tri || VI_TRI_MAC_DINH,
          loi_tuyen_duong: form.loi_tuyen_duong || null,
        };
        await vinhDanhApi.capNhat(editing.id, update);
      } else {
        const create: IVinhDanhThangCreate = {
          thang: form.thang,
          nam: form.nam,
          cong_chuc_id: form.cong_chuc_id,
          tieu_de: form.tieu_de.trim(),
          ly_do: form.ly_do.trim(),
          anh_chan_dung: form.anh_chan_dung || null,
          anh_vi_tri: form.anh_vi_tri || VI_TRI_MAC_DINH,
          loi_tuyen_duong: form.loi_tuyen_duong || null,
        };
        await vinhDanhApi.taoMoi(create);
      }
      closeForm();
      await loadList();
    } catch (err) {
      alert(getApiErrorMessage(err, 'Lưu không thành công'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCongBo = async (vd: IVinhDanhThang) => {
    if (!confirm(`Công bố vinh danh tháng ${vd.thang}/${vd.nam}?`)) return;
    try {
      await vinhDanhApi.congBo(vd.id);
      await loadList();
    } catch (err) {
      alert(getApiErrorMessage(err, 'Công bố thất bại'));
    }
  };

  const handleGoCongBo = async (vd: IVinhDanhThang) => {
    if (!confirm(`Gỡ công bố vinh danh tháng ${vd.thang}/${vd.nam}?`)) return;
    try {
      await vinhDanhApi.goCongBo(vd.id);
      await loadList();
    } catch (err) {
      alert(getApiErrorMessage(err, 'Gỡ công bố thất bại'));
    }
  };

  const handleXoa = async (vd: IVinhDanhThang) => {
    if (!confirm('Xóa bản ghi này? Không thể hoàn tác.')) return;
    try {
      await vinhDanhApi.xoa(vd.id);
      await loadList();
    } catch (err) {
      alert(getApiErrorMessage(err, 'Xóa thất bại'));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span>🏆</span>
              Vinh danh công chức tiêu biểu
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Quản lý công chức tiêu biểu hàng tháng. Mỗi tháng chỉ có 1 người
              ở trạng thái PUBLISHED.
            </p>
          </div>
          <button
            type="button"
            onClick={openCreate}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 font-medium shadow-sm"
          >
            + Tạo mới
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Năm
            </label>
            <select
              value={filterNam}
              onChange={(e) =>
                setFilterNam(e.target.value ? Number(e.target.value) : '')
              }
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
            >
              <option value="">Tất cả</option>
              {Array.from({ length: 5 }, (_, i) => NOW.getFullYear() - i).map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Trạng thái
            </label>
            <select
              value={filterTrangThai}
              onChange={(e) =>
                setFilterTrangThai(e.target.value as TrangThaiVinhDanh | '')
              }
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
            >
              <option value="">Tất cả</option>
              <option value="DRAFT">DRAFT</option>
              <option value="PUBLISHED">PUBLISHED</option>
            </select>
          </div>
          <div className="ml-auto text-xs text-gray-500">
            Tổng: {items.length} bản ghi
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* List */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Đang tải...</div>
          ) : items.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Chưa có bản ghi vinh danh nào.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-700 text-left text-xs uppercase tracking-wide">
                <tr>
                  <th className="px-4 py-3">Tháng/Năm</th>
                  <th className="px-4 py-3">Công chức</th>
                  <th className="px-4 py-3">Tiêu đề</th>
                  <th className="px-4 py-3">Trạng thái</th>
                  <th className="px-4 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((vd) => (
                  <tr key={vd.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">
                      {vd.thang}/{vd.nam}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {vd.anh_chan_dung && (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={buildAnhUrl(vd.anh_chan_dung) || ''}
                            alt=""
                            className="w-8 h-8 rounded-full object-cover border"
                          />
                        )}
                        <div>
                          <div className="font-medium text-gray-900">
                            {vd.cong_chuc?.ho_ten || '—'}
                          </div>
                          <div className="text-xs text-gray-500">
                            {vd.cong_chuc?.ma_cc}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 max-w-xs truncate">{vd.tieu_de}</td>
                    <td className="px-4 py-3">
                      {vd.trang_thai === 'PUBLISHED' ? (
                        <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                          PUBLISHED
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
                          DRAFT
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right space-x-1">
                      <button
                        type="button"
                        onClick={() => openEdit(vd)}
                        className="px-2 py-1 text-xs text-blue-700 hover:bg-blue-50 rounded"
                      >
                        Sửa
                      </button>
                      {vd.trang_thai === 'DRAFT' ? (
                        <>
                          <button
                            type="button"
                            onClick={() => handleCongBo(vd)}
                            className="px-2 py-1 text-xs text-green-700 hover:bg-green-50 rounded"
                          >
                            Công bố
                          </button>
                          <button
                            type="button"
                            onClick={() => handleXoa(vd)}
                            className="px-2 py-1 text-xs text-red-700 hover:bg-red-50 rounded"
                          >
                            Xóa
                          </button>
                        </>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleGoCongBo(vd)}
                          className="px-2 py-1 text-xs text-orange-700 hover:bg-orange-50 rounded"
                        >
                          Gỡ công bố
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* FORM MODAL */}
      {showForm && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
              <h3 className="font-semibold text-gray-900">
                {editing ? 'Sửa vinh danh' : 'Tạo mới vinh danh'}
              </h3>
              <button
                type="button"
                onClick={closeForm}
                className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* Tháng/Năm */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tháng <span className="text-red-500">*</span>
                  </label>
                  <select
                    required
                    value={form.thang}
                    onChange={(e) =>
                      setForm({ ...form, thang: Number(e.target.value) })
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                      <option key={m} value={m}>
                        Tháng {m}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Năm <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    required
                    min={2020}
                    max={2100}
                    value={form.nam}
                    onChange={(e) =>
                      setForm({ ...form, nam: Number(e.target.value) })
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>
              </div>

              {/* Chọn công chức */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Công chức <span className="text-red-500">*</span>
                </label>
                {selectedUser ? (
                  <div className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-amber-200 flex items-center justify-center text-lg flex-shrink-0">
                        👤
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{selectedUser.ho_ten}</div>
                        <div className="text-xs text-gray-600">
                          {selectedUser.ma_cc}
                          {selectedUser.chuc_vu && ` • ${selectedUser.chuc_vu}`}
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedUser(null);
                        setForm({ ...form, cong_chuc_id: '' });
                      }}
                      className="text-xs text-red-600 hover:underline whitespace-nowrap"
                    >
                      Đổi người khác
                    </button>
                  </div>
                ) : (
                  <div className="relative">
                    {/* Search input có icon kính lúp + nút clear */}
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
                        </svg>
                      </div>
                      <input
                        type="text"
                        value={searchUser}
                        onChange={(e) => setSearchUser(e.target.value)}
                        placeholder="Tìm theo tên hoặc mã công chức (tối thiểu 2 ký tự)..."
                        className="w-full border border-gray-300 rounded-lg pl-10 pr-10 py-2.5 focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none transition"
                        autoFocus
                      />
                      {searchUser && (
                        <button
                          type="button"
                          onClick={() => {
                            setSearchUser('');
                            setUserOptions([]);
                          }}
                          className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                          aria-label="Xóa tìm kiếm"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      )}
                    </div>

                    {/* Dropdown kết quả */}
                    {(searchingUser || userOptions.length > 0 || (searchUser.trim().length >= 2 && !searchingUser)) && (
                      <div className="absolute z-10 mt-1 w-full border border-gray-200 rounded-lg max-h-72 overflow-y-auto bg-white shadow-lg">
                        {searchingUser ? (
                          <div className="px-3 py-3 text-sm text-gray-500 flex items-center gap-2">
                            <div className="animate-spin w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full" />
                            Đang tìm kiếm...
                          </div>
                        ) : userOptions.length === 0 ? (
                          <div className="px-3 py-4 text-sm text-gray-500 text-center">
                            Không tìm thấy công chức nào khớp với &ldquo;{searchUser}&rdquo;
                          </div>
                        ) : (
                          userOptions.map((u) => (
                            <button
                              key={u.id}
                              type="button"
                              onClick={() => {
                                setSelectedUser(u);
                                setForm({ ...form, cong_chuc_id: u.id });
                                setSearchUser('');
                                setUserOptions([]);
                              }}
                              className="w-full text-left px-3 py-2.5 hover:bg-amber-50 text-sm border-b border-gray-100 last:border-b-0 flex items-center gap-3"
                            >
                              <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm flex-shrink-0">
                                👤
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-gray-900 truncate">{u.ho_ten}</div>
                                <div className="text-xs text-gray-500 truncate">
                                  {u.ma_cc}
                                  {u.chuc_vu && ` • ${u.chuc_vu}`}
                                </div>
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    )}

                    {/* Hint khi chưa nhập đủ */}
                    {searchUser.trim().length > 0 && searchUser.trim().length < 2 && (
                      <p className="text-xs text-gray-500 mt-1">Nhập thêm ký tự để tìm kiếm...</p>
                    )}
                  </div>
                )}
              </div>

              {/* Tiêu đề */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tiêu đề <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  maxLength={200}
                  value={form.tieu_de}
                  onChange={(e) => setForm({ ...form, tieu_de: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>

              {/* Ảnh chân dung — upload box dạng dashed */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ảnh chân dung
                </label>

                {form.anh_chan_dung ? (
                  // Đã có ảnh — hiển thị preview lớn + nút thay/xóa
                  <div className="border-2 border-amber-300 rounded-xl p-4 bg-amber-50/50 space-y-4">
                    {/* Editor kéo-thả chỉnh vị trí ảnh trong khung tròn */}
                    <AnhViTriEditor
                      src={buildAnhUrl(form.anh_chan_dung) || ''}
                      value={form.anh_vi_tri}
                      onChange={(v) => setForm((f) => ({ ...f, anh_vi_tri: v }))}
                    />
                    <div className="flex-1 border-t border-amber-200 pt-3">
                      <div className="flex gap-2">
                        <label className="px-3 py-1.5 bg-white border border-amber-400 text-amber-700 hover:bg-amber-100 rounded-lg cursor-pointer text-sm font-medium transition">
                          🔄 Thay ảnh khác
                          <input
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={(e) => {
                              const f = e.target.files?.[0];
                              if (f) handleUploadAnh(f);
                            }}
                            disabled={uploadingAnh}
                          />
                        </label>
                        <button
                          type="button"
                          onClick={() => setForm({ ...form, anh_chan_dung: '' })}
                          className="px-3 py-1.5 bg-white border border-red-300 text-red-600 hover:bg-red-50 rounded-lg text-sm font-medium transition"
                        >
                          🗑️ Xóa ảnh
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  // Chưa có ảnh — upload box dashed clickable + drag & drop
                  <label
                    onDragOver={(e) => {
                      e.preventDefault();
                      setDragOver(true);
                    }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={(e) => {
                      e.preventDefault();
                      setDragOver(false);
                      const f = e.dataTransfer.files?.[0];
                      if (f && f.type.startsWith('image/')) {
                        handleUploadAnh(f);
                      }
                    }}
                    className={`flex flex-col items-center justify-center w-full py-8 px-4 border-2 border-dashed rounded-xl cursor-pointer transition ${
                      dragOver
                        ? 'border-amber-500 bg-amber-100'
                        : uploadingAnh
                        ? 'border-amber-300 bg-amber-50 cursor-wait'
                        : 'border-gray-300 bg-gray-50 hover:border-amber-400 hover:bg-amber-50'
                    }`}
                  >
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleUploadAnh(f);
                      }}
                      disabled={uploadingAnh}
                    />

                    {uploadingAnh ? (
                      <>
                        <div className="animate-spin w-10 h-10 border-4 border-amber-500 border-t-transparent rounded-full mb-3" />
                        <p className="text-sm font-medium text-amber-700">
                          Đang tải ảnh lên...
                        </p>
                      </>
                    ) : (
                      <>
                        <div className="w-14 h-14 rounded-full bg-amber-100 flex items-center justify-center mb-3">
                          <svg className="w-7 h-7 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 0115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                        </div>
                        <p className="text-sm font-medium text-gray-700 mb-1">
                          <span className="text-amber-700 underline">Bấm để chọn ảnh</span>{' '}
                          hoặc kéo thả vào đây
                        </p>
                        <p className="text-xs text-gray-500">
                          JPG, PNG, WEBP — tối đa 5MB
                        </p>
                      </>
                    )}
                  </label>
                )}
              </div>

              {/* Lời tuyên dương */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lời tuyên dương (hiển thị trên banner)
                </label>
                <textarea
                  rows={2}
                  value={form.loi_tuyen_duong}
                  onChange={(e) =>
                    setForm({ ...form, loi_tuyen_duong: e.target.value })
                  }
                  placeholder="VD: Hoàn thành xuất sắc nhiệm vụ, lập nhiều thành tích..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>

              {/* Lý do */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lý do vinh danh <span className="text-red-500">*</span>
                </label>
                <textarea
                  required
                  rows={6}
                  value={form.ly_do}
                  onChange={(e) => setForm({ ...form, ly_do: e.target.value })}
                  placeholder="Mô tả cụ thể thành tích, đóng góp, câu chuyện..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={closeForm}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 font-medium"
                >
                  {submitting ? 'Đang lưu...' : editing ? 'Cập nhật' : 'Tạo mới'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

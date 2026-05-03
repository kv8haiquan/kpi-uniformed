/**
 * NhomDetailModal — modal chi tiết 1 nhóm + CRUD thành viên.
 *
 * Layout thêm thành viên (giống form tạo cuộc họp):
 * - vai_tro + loai_tham_du dropdowns (apply cho tất cả CBCC trong lần Thêm)
 * - Đơn vị dropdown → CongChucCheckboxList
 *   • CBCC đã có trong nhóm: tick + disabled, suffix "(đã trong nhóm)"
 * - CrossUnitPicker cho CBCC đơn vị khác
 * - Submit gọi batch endpoint (skip trùng, không 409)
 *
 * Sau khi thêm, user có thể sửa vai_tro/loai_tham_du từng row trong bảng dưới.
 */

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Loader2, Plus, Trash2, X } from 'lucide-react';
import { nhomThanhPhanApi, type ICongChucSearchItem } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import CongChucCheckboxList from '@/components/hkg/CongChucCheckboxList';
import CrossUnitPicker from '@/components/hkg/CrossUnitPicker';
import type {
  INhom,
  INhomChiTiet,
  INhomChiTietInput,
  LoaiThamDu,
  VaiTroNhom,
} from '@/types/hkg';

const LMS_API = process.env.NEXT_PUBLIC_LMS_API_URL || '/api/v1/lms';

interface IDonVi {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
}

interface Props {
  nhomId: string;
  onClose: () => void;
}

const VAI_TRO_LABEL: Record<VaiTroNhom, string> = {
  CHU_TRI: 'Chủ trì',
  THU_KY: 'Thư ký',
  THANH_VIEN: 'Thành viên',
};

const VAI_TRO_BADGE: Record<VaiTroNhom, string> = {
  CHU_TRI: 'bg-purple-100 text-purple-800',
  THU_KY: 'bg-blue-100 text-blue-800',
  THANH_VIEN: 'bg-gray-100 text-gray-700',
};

export default function NhomDetailModal({ nhomId, onClose }: Props) {
  const [nhom, setNhom] = useState<INhom | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form bulk add
  const [donViList, setDonViList] = useState<IDonVi[]>([]);
  const [donViId, setDonViId] = useState<string>('');
  const [inDonViIds, setInDonViIds] = useState<string[]>([]);
  const [outsideEntries, setOutsideEntries] = useState<ICongChucSearchItem[]>([]);
  const [vaiTro, setVaiTro] = useState<VaiTroNhom>('THANH_VIEN');
  const [loaiThamDu, setLoaiThamDu] = useState<LoaiThamDu>('BAT_BUOC');
  const [adding, setAdding] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const detail = await nhomThanhPhanApi.chiTiet(nhomId);
      setNhom(detail);
    } catch (e: unknown) {
      setError(errMsg(e, 'Không tải được chi tiết nhóm'));
    } finally {
      setLoading(false);
    }
  }, [nhomId]);

  useEffect(() => {
    reload();
  }, [reload]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  // Load đơn vị list 1 lần
  useEffect(() => {
    const load = async () => {
      try {
        const token =
          typeof window !== 'undefined'
            ? localStorage.getItem('kpi_access_token')
            : null;
        const resp = await axios.get(`${LMS_API}/don-vi`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        setDonViList(resp.data?.data || []);
      } catch {
        // Silent — picker vẫn dùng được
      }
    };
    load();
  }, []);

  // Set UUIDs CBCC đã có sẵn trong nhóm — để khoá trong checkbox list
  const existingMemberIds = useMemo(
    () => new Set((nhom?.chi_tiet ?? []).map((ct) => ct.cong_chuc_id)),
    [nhom],
  );

  // Đổi đơn vị → reset selection trong đơn vị (giữ outside)
  useEffect(() => {
    setInDonViIds([]);
  }, [donViId]);

  // Tổng số CBCC sắp thêm (loại trừ trùng giữa 2 nguồn + đã có sẵn)
  const candidateIds = useMemo(() => {
    const s = new Set<string>(inDonViIds);
    outsideEntries.forEach((e) => s.add(e.id));
    existingMemberIds.forEach((id) => s.delete(id));
    return s;
  }, [inDonViIds, outsideEntries, existingMemberIds]);

  const handleAdd = async () => {
    if (candidateIds.size === 0) return;
    setAdding(true);
    try {
      const items: INhomChiTietInput[] = Array.from(candidateIds).map((cong_chuc_id) => ({
        cong_chuc_id,
        vai_tro: vaiTro,
        loai_tham_du: loaiThamDu,
      }));
      const result = await nhomThanhPhanApi.themThanhVienBatch(nhomId, items);
      setInDonViIds([]);
      setOutsideEntries([]);
      setVaiTro('THANH_VIEN');
      setLoaiThamDu('BAT_BUOC');
      await reload();
      const msgs = [`Đã thêm ${result.so_them} thành viên`];
      if (result.so_bo_qua_trung > 0) {
        msgs.push(`bỏ qua ${result.so_bo_qua_trung} người trùng`);
      }
      alert(msgs.join('. '));
    } catch (e: unknown) {
      alert(errMsg(e, 'Thêm thành viên thất bại'));
    } finally {
      setAdding(false);
    }
  };

  const handleUpdate = async (
    ct: INhomChiTiet,
    patch: { vai_tro?: VaiTroNhom; loai_tham_du?: LoaiThamDu },
  ) => {
    try {
      await nhomThanhPhanApi.suaThanhVien(nhomId, ct.cong_chuc_id, patch);
      await reload();
    } catch (e: unknown) {
      alert(errMsg(e, 'Cập nhật thất bại'));
    }
  };

  const handleRemove = async (ct: INhomChiTiet) => {
    if (!confirm(`Gỡ ${ct.ho_ten || ct.cong_chuc_id} khỏi nhóm?`)) return;
    try {
      await nhomThanhPhanApi.xoaThanhVien(nhomId, ct.cong_chuc_id);
      await reload();
    } catch (e: unknown) {
      alert(errMsg(e, 'Xoá thất bại'));
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <div>
            <h2 className="text-lg font-semibold">
              {nhom?.ten_nhom || 'Đang tải...'}
            </h2>
            {nhom?.loai_nhom && (
              <span className="inline-block text-xs px-2 py-0.5 bg-gray-100 text-gray-700 rounded">
                {nhom.loai_nhom}
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-5 py-4 overflow-y-auto flex-1">
          {nhom?.mo_ta && (
            <p className="text-sm text-gray-600 mb-4">{nhom.mo_ta}</p>
          )}

          {error && (
            <div className="p-2 mb-3 bg-red-50 text-red-700 border border-red-200 rounded text-sm">
              {error}
            </div>
          )}

          {loading && !nhom ? (
            <div className="flex items-center gap-2 p-4 text-gray-600">
              <Loader2 className="w-4 h-4 animate-spin" /> Đang tải...
            </div>
          ) : (
            <>
              {/* Form bulk add */}
              <div className="bg-gray-50 border border-gray-200 rounded p-3 mb-4 space-y-3">
                <div className="text-sm font-medium text-gray-700">
                  Thêm thành viên
                </div>

                {/* Default vai_tro + loai_tham_du */}
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="text-gray-600">Áp dụng cho lần thêm này:</span>
                  <select
                    value={vaiTro}
                    onChange={(e) => setVaiTro(e.target.value as VaiTroNhom)}
                    className="px-3 py-1.5 border border-gray-300 rounded text-sm bg-white"
                  >
                    <option value="THANH_VIEN">Thành viên</option>
                    <option value="CHU_TRI">Chủ trì</option>
                    <option value="THU_KY">Thư ký</option>
                  </select>
                  <select
                    value={loaiThamDu}
                    onChange={(e) => setLoaiThamDu(e.target.value as LoaiThamDu)}
                    className="px-3 py-1.5 border border-gray-300 rounded text-sm bg-white"
                  >
                    <option value="BAT_BUOC">Bắt buộc</option>
                    <option value="THAM_KHAO">Tham khảo</option>
                  </select>
                  <span className="text-xs text-gray-500">
                    (sửa lại từng người trong bảng dưới sau khi thêm)
                  </span>
                </div>

                {/* Đơn vị dropdown */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Chọn theo đơn vị
                  </label>
                  <select
                    value={donViId}
                    onChange={(e) => setDonViId(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
                  >
                    <option value="">— Chọn đơn vị —</option>
                    {donViList.map((dv) => (
                      <option key={dv.id} value={dv.id}>
                        {dv.ten_don_vi} ({dv.ma_don_vi})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Checkbox list trong đơn vị — locked với CBCC đã có */}
                <CongChucCheckboxList
                  donViId={donViId || null}
                  value={inDonViIds}
                  onChange={setInDonViIds}
                  lockedIds={existingMemberIds}
                  lockedLabel="(đã trong nhóm)"
                />

                {/* Cross-unit picker */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Hoặc tìm CBCC từ đơn vị khác
                  </label>
                  <CrossUnitPicker
                    donViList={donViList}
                    excludeDonViId={donViId || null}
                    entries={outsideEntries}
                    onChange={setOutsideEntries}
                  />
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                  <span className="text-sm text-gray-600">
                    Sẽ thêm <strong>{candidateIds.size}</strong> người
                    {existingMemberIds.size > 0 && (
                      <span className="text-xs text-gray-500 ml-1">
                        (CBCC đã trong nhóm sẽ bị bỏ qua)
                      </span>
                    )}
                  </span>
                  <button
                    onClick={handleAdd}
                    disabled={candidateIds.size === 0 || adding}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    {adding ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Plus className="w-4 h-4" />
                    )}
                    Thêm vào nhóm
                  </button>
                </div>
              </div>

              {/* Danh sách thành viên hiện có */}
              <div className="text-sm font-medium text-gray-700 mb-2">
                Thành viên hiện tại ({nhom?.chi_tiet.length ?? 0})
              </div>
              {nhom && nhom.chi_tiet.length === 0 ? (
                <div className="p-6 text-center text-gray-500 bg-white border border-dashed rounded">
                  Chưa có thành viên nào. Dùng form ở trên để thêm.
                </div>
              ) : (
                <div className="border border-gray-200 rounded overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-700 text-left">
                      <tr>
                        <th className="px-3 py-2 font-medium">Họ tên</th>
                        <th className="px-3 py-2 font-medium">Mã CBCC</th>
                        <th className="px-3 py-2 font-medium">Đơn vị</th>
                        <th className="px-3 py-2 font-medium">Vai trò</th>
                        <th className="px-3 py-2 font-medium">Tham dự</th>
                        <th className="px-3 py-2 font-medium text-right"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {nhom?.chi_tiet.map((ct) => (
                        <tr key={ct.id} className="border-t border-gray-100">
                          <td className="px-3 py-2">{ct.ho_ten || '—'}</td>
                          <td className="px-3 py-2 text-gray-600">{ct.ma_cc || '—'}</td>
                          <td className="px-3 py-2 text-gray-600 text-xs">
                            {ct.ten_don_vi || '—'}
                          </td>
                          <td className="px-3 py-2">
                            <select
                              value={ct.vai_tro}
                              onChange={(e) =>
                                handleUpdate(ct, {
                                  vai_tro: e.target.value as VaiTroNhom,
                                })
                              }
                              className={`px-2 py-1 text-xs rounded border-0 ${VAI_TRO_BADGE[ct.vai_tro]}`}
                            >
                              <option value="THANH_VIEN">{VAI_TRO_LABEL.THANH_VIEN}</option>
                              <option value="CHU_TRI">{VAI_TRO_LABEL.CHU_TRI}</option>
                              <option value="THU_KY">{VAI_TRO_LABEL.THU_KY}</option>
                            </select>
                          </td>
                          <td className="px-3 py-2">
                            <select
                              value={ct.loai_tham_du}
                              onChange={(e) =>
                                handleUpdate(ct, {
                                  loai_tham_du: e.target.value as LoaiThamDu,
                                })
                              }
                              className="px-2 py-1 text-xs rounded border border-gray-300 bg-white"
                            >
                              <option value="BAT_BUOC">Bắt buộc</option>
                              <option value="THAM_KHAO">Tham khảo</option>
                            </select>
                          </td>
                          <td className="px-3 py-2 text-right">
                            <button
                              onClick={() => handleRemove(ct)}
                              className="inline-flex items-center gap-1 px-2 py-1 text-xs text-red-700 border border-red-300 rounded hover:bg-red-50"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>

        <div className="px-5 py-3 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-100"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}

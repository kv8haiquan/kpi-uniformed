/**
 * NhomDetailModal — modal chi tiết 1 nhóm + CRUD thành viên.
 *
 * Hiển thị:
 * - Header: tên nhóm + loại + mô tả
 * - Danh sách thành viên (sorted CHU_TRI > THU_KY > THANH_VIEN)
 * - Form thêm thành viên (CongChucPicker + chọn vai_tro + loai_tham_du)
 * - Mỗi row: dropdown sửa vai_tro/loai_tham_du + nút xoá
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { Loader2, Plus, Trash2, X } from 'lucide-react';
import { nhomThanhPhanApi } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import CongChucPicker from '@/components/hkg/CongChucPicker';
import type {
  INhom,
  INhomChiTiet,
  LoaiThamDu,
  VaiTroNhom,
} from '@/types/hkg';

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

  const [pickedCcId, setPickedCcId] = useState<string | null>(null);
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

  const handleAdd = async () => {
    if (!pickedCcId) return;
    setAdding(true);
    try {
      await nhomThanhPhanApi.themThanhVien(nhomId, {
        cong_chuc_id: pickedCcId,
        vai_tro: vaiTro,
        loai_tham_du: loaiThamDu,
      });
      setPickedCcId(null);
      setVaiTro('THANH_VIEN');
      setLoaiThamDu('BAT_BUOC');
      await reload();
    } catch (e: unknown) {
      alert(errMsg(e, 'Thêm thất bại'));
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
        className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col"
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
              {/* Form thêm thành viên */}
              <div className="bg-gray-50 border border-gray-200 rounded p-3 mb-4">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  Thêm thành viên
                </div>
                <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto_auto] gap-2 items-end">
                  <CongChucPicker
                    value={pickedCcId}
                    onChange={(id) => setPickedCcId(id)}
                    placeholder="Tìm CBCC theo tên/mã (≥2 ký tự)"
                  />
                  <select
                    value={vaiTro}
                    onChange={(e) => setVaiTro(e.target.value as VaiTroNhom)}
                    className="px-3 py-2 border border-gray-300 rounded text-sm bg-white"
                  >
                    <option value="THANH_VIEN">Thành viên</option>
                    <option value="CHU_TRI">Chủ trì</option>
                    <option value="THU_KY">Thư ký</option>
                  </select>
                  <select
                    value={loaiThamDu}
                    onChange={(e) => setLoaiThamDu(e.target.value as LoaiThamDu)}
                    className="px-3 py-2 border border-gray-300 rounded text-sm bg-white"
                  >
                    <option value="BAT_BUOC">Bắt buộc</option>
                    <option value="THAM_KHAO">Tham khảo</option>
                  </select>
                  <button
                    onClick={handleAdd}
                    disabled={!pickedCcId || adding}
                    className="inline-flex items-center gap-1 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    {adding ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Plus className="w-4 h-4" />
                    )}
                    Thêm
                  </button>
                </div>
              </div>

              {/* Danh sách thành viên */}
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

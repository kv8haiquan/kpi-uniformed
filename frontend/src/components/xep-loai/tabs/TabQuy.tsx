/**
 * src/components/xep-loai/tabs/TabQuy.tsx
 * =========================================
 * Tab "Xếp loại quý" - Workflow phê duyệt báo cáo xếp loại quý.
 *
 * Version: 5.0.0 (16/04/2026)
 * - Bỏ view Tổng hợp, chỉ giữ workflow
 * - Thêm xem chi tiết 3 tháng cho từng CC trong workflow
 */

'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuthStore } from '@/stores/useAuthStore';
import { xepLoaiQuyService } from '@/services/xepLoaiQuyService';
import { exportService } from '@/services/export.service';
import type {
  ChiTietQuyResponse,
  BaoCaoXepLoaiQuy,
  ChiTietXepLoaiQuy,
  MucXepLoaiQuy,
  TrangThaiBaoCaoQuy,
} from '@/types/xep-loai-quy';
import { ITabProps } from '@/types/xep-loai';
import {
  LoadingSpinner,
  EmptyState,
  ErrorMessage,
} from '../shared';

// =============================================================================
// CONSTANTS
// =============================================================================

const TRANG_THAI_MAP: Record<string, { label: string; color: string }> = {
  NHAP: { label: 'Nháp', color: 'bg-gray-100 text-gray-700' },
  CHO_PHE_DUYET: { label: 'Chờ duyệt', color: 'bg-amber-100 text-amber-700' },
  DA_PHE_DUYET: { label: 'Đã duyệt', color: 'bg-green-100 text-green-700' },
  TU_CHOI: { label: 'Từ chối', color: 'bg-red-100 text-red-700' },
};

const XEP_LOAI_COLORS: Record<string, string> = {
  A: 'bg-green-100 text-green-700 border-green-300',
  B: 'bg-blue-100 text-blue-700 border-blue-300',
  C: 'bg-amber-100 text-amber-700 border-amber-300',
  D: 'bg-orange-100 text-orange-700 border-orange-300',
  E: 'bg-red-100 text-red-700 border-red-300',
};

const XEP_LOAI_BADGE_CLASS: Record<string, string> = {
  A: 'bg-green-100 text-green-800',
  B: 'bg-blue-100 text-blue-800',
  C: 'bg-yellow-100 text-yellow-800',
  D: 'bg-red-100 text-red-800',
};

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

function StatusBadge({ trangThai }: { trangThai: string }) {
  const info = TRANG_THAI_MAP[trangThai] || { label: trangThai, color: 'bg-gray-100 text-gray-600' };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${info.color}`}>
      {info.label}
    </span>
  );
}

function XepLoaiBadge({ xepLoai }: { xepLoai?: string | null }) {
  if (!xepLoai) return <span className="text-gray-400 text-xs">-</span>;
  return (
    <span className={`px-2 py-0.5 text-xs font-bold rounded border ${XEP_LOAI_COLORS[xepLoai] || 'bg-gray-100 text-gray-700 border-gray-300'}`}>
      {xepLoai}
    </span>
  );
}

function StatsSummary({ baoCao }: { baoCao: BaoCaoXepLoaiQuy }) {
  const stats = [
    { label: 'A', value: baoCao.so_loai_a, color: 'bg-green-500' },
    { label: 'B', value: baoCao.so_loai_b, color: 'bg-blue-500' },
    { label: 'C', value: baoCao.so_loai_c, color: 'bg-amber-500' },
    { label: 'D', value: baoCao.so_loai_d, color: 'bg-orange-500' },
    { label: 'E', value: baoCao.so_loai_e || 0, color: 'bg-red-500' },
  ];
  const total = baoCao.tong_cong_chuc || stats.reduce((sum, s) => sum + s.value, 0);
  const tongAB = baoCao.so_loai_a + baoCao.so_loai_b;
  const tyLeA = tongAB > 0 ? ((baoCao.so_loai_a / tongAB) * 100) : 0;
  const isVuotNguong = baoCao.canh_bao_ty_le_a || (tongAB > 0 && tyLeA > 20);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-4">
        {stats.map((s) => (
          <div key={s.label} className="flex items-center gap-1.5">
            <div className={`w-3 h-3 rounded ${s.color}`} />
            <span className="text-sm font-medium text-gray-700">{s.label}:</span>
            <span className="text-sm font-bold text-gray-900">{s.value}</span>
          </div>
        ))}
        <div className="border-l border-gray-300 pl-4 ml-2">
          <span className="text-sm text-gray-500">Tổng:</span>
          <span className="text-sm font-bold text-gray-900 ml-1">{total}</span>
        </div>
      </div>
      {isVuotNguong && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.27 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span className="text-xs text-red-700 font-medium">
            Tỷ lệ A/(A+B) = {tyLeA.toFixed(0)}% (vượt ngưỡng 20%)
          </span>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MODAL CHI TIẾT 3 THÁNG
// =============================================================================

function ChiTietModal({
  chiTiet,
  quy,
  nam,
  onClose,
}: {
  chiTiet: ChiTietXepLoaiQuy;
  quy: number;
  nam: number;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<ChiTietQuyResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await xepLoaiQuyService.getChiTietQuy(chiTiet.cong_chuc_id, quy, nam);
        setDetail(data);
      } catch {
        // Fallback: hiển thị thông tin cơ bản từ chiTiet
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [chiTiet.cong_chuc_id, quy, nam]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Chi tiết Quý {quy}/{nam}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {chiTiet.cong_chuc?.ho_ten} ({chiTiet.cong_chuc?.ma_cc})
              {chiTiet.is_lanh_dao && <span className="ml-1 text-blue-600 font-semibold">(Lãnh đạo)</span>}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tổng quan điểm quý */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-xs text-gray-600 mb-1">Điểm KPI quý</div>
            <div className="text-lg font-bold text-blue-600">
              {Number(chiTiet.diem_kpi).toFixed(2)}
            </div>
          </div>
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="text-xs text-gray-600 mb-1">Điểm TC quý</div>
            <div className="text-lg font-bold text-green-600">
              {Number(chiTiet.diem_tieu_chi_chung).toFixed(2)}
            </div>
          </div>
          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="text-xs text-gray-600 mb-1">Điểm tổng quý</div>
            <div className="text-lg font-bold text-purple-600">
              {Number(chiTiet.diem_tong).toFixed(2)}
            </div>
          </div>
          <div className="bg-yellow-50 p-3 rounded-lg">
            <div className="text-xs text-gray-600 mb-1">Xếp loại quý</div>
            <div className="text-lg font-bold text-yellow-600">
              {chiTiet.xep_loai_quyet_dinh || chiTiet.xep_loai_de_xuat || chiTiet.xep_loai_he_thong || 'N/A'}
            </div>
          </div>
        </div>

        {/* Chi tiết 3 tháng */}
        {loading ? (
          <div className="text-center py-8"><LoadingSpinner /></div>
        ) : detail ? (
          <>
            <h3 className="text-lg font-semibold mb-2 text-gray-900">Chi tiết 3 tháng</h3>
            <div className="overflow-x-auto mb-6">
              <table className="min-w-full border border-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700">Tháng</th>
                    <th className="border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700">Điểm KPI</th>
                    <th className="border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700">Điểm TC</th>
                    <th className="border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700">Điểm tổng</th>
                    <th className="border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700">Xếp loại</th>
                    <th className="border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700">Nguồn</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.cac_thang.map((t) => (
                    <tr key={t.thang} className={!t.co_du_lieu ? 'bg-yellow-50' : 'hover:bg-gray-50'}>
                      <td className="border border-gray-200 px-3 py-2 text-center font-medium">Tháng {t.thang}</td>
                      <td className="border border-gray-200 px-3 py-2 text-right">
                        <span className={t.co_du_lieu ? 'font-medium' : 'text-red-600'}>
                          {t.diem_kpi?.toFixed(2) ?? '0.00'}
                        </span>
                      </td>
                      <td className="border border-gray-200 px-3 py-2 text-right">
                        {t.diem_tc !== null ? t.diem_tc.toFixed(2) : '-'}
                      </td>
                      <td className="border border-gray-200 px-3 py-2 text-right font-semibold">
                        {t.diem_tong !== null ? t.diem_tong.toFixed(2) : '-'}
                      </td>
                      <td className="border border-gray-200 px-3 py-2 text-center">
                        {t.xep_loai_thang ? (
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${XEP_LOAI_BADGE_CLASS[t.xep_loai_thang] || 'bg-gray-100 text-gray-800'}`}>
                            {t.xep_loai_thang}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="border border-gray-200 px-3 py-2 text-center text-xs text-gray-500">
                        {t.nguon === 'DA_PHE_DUYET' ? 'Đã duyệt' : t.nguon === 'CHO_PHE_DUYET' ? 'Chờ duyệt' : t.nguon === 'real_time' ? 'Tạm tính' : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {detail.ghi_chu && (
              <p className="text-sm text-amber-700 bg-amber-50 p-2 rounded mb-4">{detail.ghi_chu}</p>
            )}
          </>
        ) : (
          <p className="text-sm text-gray-500 mb-4">Không tải được chi tiết 3 tháng.</p>
        )}

        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// WORKFLOW VIEW: TDV
// =============================================================================

interface WorkflowViewTDVProps {
  quy: number;
  nam: number;
}

function WorkflowViewTDV({ quy, nam }: WorkflowViewTDVProps) {
  const [baoCao, setBaoCao] = useState<BaoCaoXepLoaiQuy | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [canhBao, setCanhBao] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<{
    xep_loai_de_xuat: MucXepLoaiQuy;
    ly_do_dieu_chinh: string;
  }>({ xep_loai_de_xuat: 'B', ly_do_dieu_chinh: '' });
  const [selectedChiTiet, setSelectedChiTiet] = useState<ChiTietXepLoaiQuy | null>(null);

  const loadBaoCao = async () => {
    setLoading(true);
    setError(null);
    setCanhBao(null);
    try {
      const data = await xepLoaiQuyService.getBaoCaoQuy(quy, nam);
      if (data.canh_bao) {
        setCanhBao(data.canh_bao);
      }
      setBaoCao(data);
    } catch (err: any) {
      setError(err.message || 'Lỗi tải báo cáo quý');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadBaoCao(); }, [quy, nam]);

  const handleEdit = (ct: ChiTietXepLoaiQuy) => {
    setEditingId(ct.id);
    setEditForm({
      xep_loai_de_xuat: ct.xep_loai_de_xuat || ct.xep_loai_he_thong || 'B',
      ly_do_dieu_chinh: ct.ly_do_dieu_chinh_dt || '',
    });
  };

  const handleSaveEdit = async (chiTietId: string) => {
    try {
      await xepLoaiQuyService.deXuatXepLoai(chiTietId, editForm);
      setEditingId(null);
      await loadBaoCao();
    } catch (err: any) {
      alert('Lỗi lưu: ' + err.message);
    }
  };

  const handleGuiDuyet = async () => {
    if (!baoCao) return;
    if (!confirm('Gửi báo cáo quý lên CCT để phê duyệt?')) return;
    try {
      await xepLoaiQuyService.guiDuyet(baoCao.id);
      alert('Gửi duyệt thành công');
      await loadBaoCao();
    } catch (err: any) {
      alert('Lỗi gửi duyệt: ' + err.message);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!baoCao) return <EmptyState title="Không có báo cáo quý" />;

  const canEdit = baoCao.trang_thai === 'NHAP' || baoCao.trang_thai === 'TU_CHOI';

  return (
    <div className="space-y-4">
      {canhBao && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
          <span className="text-yellow-600 text-xl flex-shrink-0">&#9888;</span>
          <div>
            <p className="font-semibold text-yellow-800">Lưu ý</p>
            <p className="text-sm text-yellow-700">{canhBao}</p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Báo cáo xếp loại Quý {quy}/{nam}</h3>
            <p className="text-sm text-gray-600">Đơn vị: {baoCao.don_vi?.ten_don_vi || 'N/A'}</p>
          </div>
          <StatusBadge trangThai={baoCao.trang_thai} />
        </div>
        <StatsSummary baoCao={baoCao} />
        <div className="mt-3 flex flex-wrap gap-2">
          {canEdit && (
            <button onClick={handleGuiDuyet} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm font-medium">
              Gửi duyệt
            </button>
          )}
          <button
            onClick={async () => {
              try {
                await exportService.exportDonViQuy({
                  quy: baoCao.quy,
                  nam: baoCao.nam,
                  donViId: baoCao.don_vi_id,
                });
              } catch (err: any) {
                alert('Lỗi tải Mẫu 03: ' + (err?.response?.data?.detail?.message || err.message || 'Unknown'));
              }
            }}
            className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition-colors text-sm font-medium"
            title="Tải Mẫu 03 cho đơn vị mình"
          >
            📄 Tải Mẫu 03
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">STT</th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mã CC</th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Họ tên</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Điểm TC</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Điểm KPI</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Tổng</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase">XL HT</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase">XL ĐX</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {baoCao.chi_tiets.map((ct, idx) => {
              const isEditing = editingId === ct.id;
              return (
                <tr key={ct.id} className={`hover:bg-gray-50 ${ct.bi_tu_choi ? 'bg-red-50' : ''}`}>
                  <td className="px-3 py-2 text-gray-500">{idx + 1}</td>
                  <td className="px-3 py-2 font-medium text-gray-900">{ct.cong_chuc?.ma_cc}</td>
                  <td className="px-3 py-2 text-gray-900">
                    {ct.cong_chuc?.ho_ten}
                    {ct.is_lanh_dao && <span className="ml-1 text-xs text-blue-600 font-semibold">(LĐ)</span>}
                  </td>
                  <td className="px-3 py-2 text-right font-medium">{Number(ct.diem_tieu_chi_chung).toFixed(1)}</td>
                  <td className="px-3 py-2 text-right font-medium">{Number(ct.diem_kpi).toFixed(1)}</td>
                  <td className="px-3 py-2 text-right font-semibold text-gray-900">{Number(ct.diem_tong).toFixed(1)}</td>
                  <td className="px-3 py-2 text-center"><XepLoaiBadge xepLoai={ct.xep_loai_he_thong} /></td>
                  <td className="px-3 py-2 text-center">
                    {isEditing ? (
                      <select
                        className="border border-gray-300 rounded px-2 py-1 text-xs"
                        value={editForm.xep_loai_de_xuat}
                        onChange={(e) => setEditForm({ ...editForm, xep_loai_de_xuat: e.target.value as MucXepLoaiQuy })}
                      >
                        {['A','B','C','D','E'].map(v => <option key={v} value={v}>{v}</option>)}
                      </select>
                    ) : (
                      <XepLoaiBadge xepLoai={ct.xep_loai_de_xuat || ct.xep_loai_he_thong} />
                    )}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {isEditing ? (
                      <div className="flex gap-1">
                        <input type="text" className="border border-gray-300 rounded px-2 py-1 text-xs w-24" placeholder="Lý do..."
                          value={editForm.ly_do_dieu_chinh} onChange={(e) => setEditForm({ ...editForm, ly_do_dieu_chinh: e.target.value })} />
                        <button onClick={() => handleSaveEdit(ct.id)} className="bg-green-600 text-white px-2 py-1 rounded text-xs hover:bg-green-700">Lưu</button>
                        <button onClick={() => setEditingId(null)} className="bg-gray-400 text-white px-2 py-1 rounded text-xs hover:bg-gray-500">Hủy</button>
                      </div>
                    ) : (
                      <div className="flex gap-2 justify-center">
                        <button onClick={() => setSelectedChiTiet(ct)} className="text-blue-600 hover:text-blue-800 text-xs font-medium">Chi tiết</button>
                        {canEdit && (
                          <button onClick={() => handleEdit(ct)} className="text-amber-600 hover:text-amber-800 text-xs font-medium">Sửa XL</button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Metadata */}
      <div className="bg-gray-50 p-3 rounded-lg text-sm text-gray-600 space-y-1">
        <p>Người lập: <strong>{baoCao.nguoi_lap?.ho_ten || 'N/A'}</strong></p>
        {baoCao.ngay_gui_duyet && <p>Ngày gửi: {new Date(baoCao.ngay_gui_duyet).toLocaleString('vi-VN')}</p>}
        {baoCao.nguoi_phe_duyet?.ho_ten && <p>Người duyệt: <strong>{baoCao.nguoi_phe_duyet.ho_ten}</strong></p>}
        {baoCao.ngay_phe_duyet && <p>Ngày duyệt: {new Date(baoCao.ngay_phe_duyet).toLocaleString('vi-VN')}</p>}
        {baoCao.y_kien_phe_duyet && <p className="text-blue-700">Ý kiến: <em>{baoCao.y_kien_phe_duyet}</em></p>}
      </div>

      {/* Modal chi tiết */}
      {selectedChiTiet && (
        <ChiTietModal chiTiet={selectedChiTiet} quy={quy} nam={nam} onClose={() => setSelectedChiTiet(null)} />
      )}
    </div>
  );
}

// =============================================================================
// WORKFLOW VIEW: CCT / PCCT / TCCB
// =============================================================================
// - CCT/PCCT: xem + phê duyệt mọi đơn vị.
// - TCCB (can_view_all_units): chỉ xem (không phê duyệt).

interface WorkflowViewCCTProps {
  quy: number;
  nam: number;
  canApprove: boolean; // CCT/PCCT → true; TCCB view-only → false
}

const TRANG_THAI_FILTER_OPTIONS: { value: '' | TrangThaiBaoCaoQuy; label: string }[] = [
  { value: '', label: 'Tất cả' },
  { value: 'NHAP', label: 'Nháp' },
  { value: 'CHO_PHE_DUYET', label: 'Chờ duyệt' },
  { value: 'DA_PHE_DUYET', label: 'Đã duyệt' },
  { value: 'TU_CHOI', label: 'Từ chối' },
];

function WorkflowViewCCT({ quy, nam, canApprove }: WorkflowViewCCTProps) {
  const [danhSach, setDanhSach] = useState<BaoCaoXepLoaiQuy[]>([]);
  const [selectedBaoCao, setSelectedBaoCao] = useState<BaoCaoXepLoaiQuy | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [yKien, setYKien] = useState('');
  const [selectedChiTiet, setSelectedChiTiet] = useState<ChiTietXepLoaiQuy | null>(null);
  const [filterTrangThai, setFilterTrangThai] = useState<'' | TrangThaiBaoCaoQuy>('');
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const loadDanhSach = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { items } = await xepLoaiQuyService.getDanhSachQuy({
        quy,
        nam,
        trang_thai: filterTrangThai || undefined,
        page_size: 100,
      });
      setDanhSach(items);
    } catch (err: any) {
      setError(err.message || 'Lỗi tải danh sách');
    } finally {
      setLoading(false);
    }
  }, [quy, nam, filterTrangThai]);

  useEffect(() => { loadDanhSach(); }, [loadDanhSach]);

  const handleSelectBaoCao = async (baoCaoId: string) => {
    setLoadingDetail(true);
    try {
      const bc = await xepLoaiQuyService.getChiTietBaoCaoQuyById(baoCaoId);
      setSelectedBaoCao(bc);
    } catch (err: any) {
      alert('Lỗi tải chi tiết: ' + (err.message || 'Unknown error'));
    } finally {
      setLoadingDetail(false);
    }
  };

  const handlePheDuyet = async (baoCaoId: string, hanhDong: 'phe_duyet' | 'tu_choi') => {
    const msg = hanhDong === 'phe_duyet' ? 'Phê duyệt báo cáo này?' : 'Từ chối báo cáo này?';
    if (!confirm(msg)) return;
    try {
      await xepLoaiQuyService.pheDuyet(baoCaoId, { hanh_dong: hanhDong, y_kien: yKien });
      alert(hanhDong === 'phe_duyet' ? 'Phê duyệt thành công' : 'Từ chối thành công');
      setSelectedBaoCao(null);
      setYKien('');
      await loadDanhSach();
    } catch (err: any) {
      alert('Lỗi: ' + err.message);
    }
  };

  const handleDownloadMau03 = async (bc: BaoCaoXepLoaiQuy) => {
    setDownloadingId(bc.id);
    try {
      await exportService.exportDonViQuy({
        quy: bc.quy,
        nam: bc.nam,
        donViId: bc.don_vi_id,
      });
    } catch (err: any) {
      alert('Lỗi tải Mẫu 03: ' + (err?.response?.data?.detail?.message || err.message || 'Unknown'));
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDownloadTongHop = async () => {
    setDownloadingId('ALL');
    try {
      await exportService.exportDonViTongHopQuy({ quy, nam });
    } catch (err: any) {
      alert('Lỗi tải tổng hợp: ' + (err?.response?.data?.detail?.message || err.message || 'Unknown'));
    } finally {
      setDownloadingId(null);
    }
  };

  // Thống kê nhanh theo trạng thái
  const thongKeTrangThai = useMemo(() => {
    const base = { NHAP: 0, CHO_PHE_DUYET: 0, DA_PHE_DUYET: 0, TU_CHOI: 0 };
    for (const bc of danhSach) {
      if (bc.trang_thai in base) base[bc.trang_thai as keyof typeof base] += 1;
    }
    return base;
  }, [danhSach]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  // -------------------------------------------------------------------------
  // CHI TIẾT 1 BÁO CÁO
  // -------------------------------------------------------------------------
  if (selectedBaoCao) {
    const isChoDuyet = selectedBaoCao.trang_thai === 'CHO_PHE_DUYET';
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <button onClick={() => setSelectedBaoCao(null)} className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            &larr; Quay lại
          </button>
          <h3 className="text-lg font-semibold">Chi tiết báo cáo - {selectedBaoCao.don_vi?.ten_don_vi || 'N/A'}</h3>
          <StatusBadge trangThai={selectedBaoCao.trang_thai} />
        </div>

        <div className="bg-white p-4 rounded-lg shadow flex items-start justify-between gap-3">
          <StatsSummary baoCao={selectedBaoCao} />
          <button
            onClick={() => handleDownloadMau03(selectedBaoCao)}
            disabled={downloadingId === selectedBaoCao.id}
            className="shrink-0 bg-purple-600 text-white px-3 py-2 rounded-md hover:bg-purple-700 text-sm font-medium disabled:opacity-50"
            title="Tải Mẫu 03 cho đơn vị này"
          >
            {downloadingId === selectedBaoCao.id ? 'Đang tải...' : '📄 Tải Mẫu 03'}
          </button>
        </div>

        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">STT</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mã CC</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Họ tên</th>
                <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Điểm TC</th>
                <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Điểm KPI</th>
                <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Tổng</th>
                <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase">XL HT</th>
                <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase">XL ĐX</th>
                <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {selectedBaoCao.chi_tiets.map((ct, idx) => (
                <tr key={ct.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 text-gray-500">{idx + 1}</td>
                  <td className="px-3 py-2 font-medium text-gray-900">{ct.cong_chuc?.ma_cc}</td>
                  <td className="px-3 py-2 text-gray-900">
                    {ct.cong_chuc?.ho_ten}
                    {ct.is_lanh_dao && <span className="ml-1 text-xs text-blue-600 font-semibold">(LĐ)</span>}
                  </td>
                  <td className="px-3 py-2 text-right font-medium">{Number(ct.diem_tieu_chi_chung).toFixed(1)}</td>
                  <td className="px-3 py-2 text-right font-medium">{Number(ct.diem_kpi).toFixed(1)}</td>
                  <td className="px-3 py-2 text-right font-semibold text-gray-900">{Number(ct.diem_tong).toFixed(1)}</td>
                  <td className="px-3 py-2 text-center"><XepLoaiBadge xepLoai={ct.xep_loai_he_thong} /></td>
                  <td className="px-3 py-2 text-center"><XepLoaiBadge xepLoai={ct.xep_loai_de_xuat || ct.xep_loai_he_thong} /></td>
                  <td className="px-3 py-2 text-center">
                    <button onClick={() => setSelectedChiTiet(ct)} className="text-blue-600 hover:text-blue-800 text-xs font-medium">
                      Chi tiết
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Ý kiến + nút duyệt (chỉ khi CHO_PHE_DUYET và canApprove) */}
        {canApprove && isChoDuyet && (
          <div className="bg-white p-4 rounded-lg shadow">
            <label className="block text-sm font-medium text-gray-700 mb-2">Ý kiến phê duyệt</label>
            <textarea className="w-full border border-gray-300 rounded-md p-2 text-sm" rows={3} placeholder="Nhập ý kiến (nếu có)..."
              value={yKien} onChange={(e) => setYKien(e.target.value)} />
            <div className="mt-3 flex gap-2">
              <button onClick={() => handlePheDuyet(selectedBaoCao.id, 'phe_duyet')} className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 text-sm font-medium">Phê duyệt</button>
              <button onClick={() => handlePheDuyet(selectedBaoCao.id, 'tu_choi')} className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 text-sm font-medium">Từ chối</button>
            </div>
          </div>
        )}
        {!canApprove && isChoDuyet && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
            Bạn có quyền xem báo cáo nhưng không có quyền phê duyệt.
          </div>
        )}

        {selectedChiTiet && (
          <ChiTietModal chiTiet={selectedChiTiet} quy={quy} nam={nam} onClose={() => setSelectedChiTiet(null)} />
        )}
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // DANH SÁCH TẤT CẢ ĐƠN VỊ
  // -------------------------------------------------------------------------
  return (
    <div className="space-y-4">
      {/* Header: filter + tổng hợp */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Lọc trạng thái</label>
            <select
              value={filterTrangThai}
              onChange={(e) => setFilterTrangThai(e.target.value as '' | TrangThaiBaoCaoQuy)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
            >
              {TRANG_THAI_FILTER_OPTIONS.map((o) => (
                <option key={o.value || 'all'} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <button
            onClick={loadDanhSach}
            className="px-3 py-2 text-sm text-blue-600 border border-blue-200 rounded-md hover:bg-blue-50"
          >
            🔄 Tải lại
          </button>

          <button
            onClick={handleDownloadTongHop}
            disabled={danhSach.length === 0 || downloadingId === 'ALL'}
            className="ml-auto px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm font-medium disabled:opacity-50"
            title="Tải Mẫu 03 tổng hợp tất cả đơn vị (mỗi đơn vị 1 trang)"
          >
            {downloadingId === 'ALL' ? 'Đang tải...' : '📥 Tải tổng hợp tất cả đơn vị'}
          </button>
        </div>

        {/* Thống kê nhanh */}
        <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <div className="bg-gray-50 border border-gray-200 rounded px-3 py-2">
            <div className="text-gray-500">Nháp</div>
            <div className="font-bold text-gray-800">{thongKeTrangThai.NHAP}</div>
          </div>
          <div className="bg-amber-50 border border-amber-200 rounded px-3 py-2">
            <div className="text-amber-700">Chờ duyệt</div>
            <div className="font-bold text-amber-800">{thongKeTrangThai.CHO_PHE_DUYET}</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded px-3 py-2">
            <div className="text-green-700">Đã duyệt</div>
            <div className="font-bold text-green-800">{thongKeTrangThai.DA_PHE_DUYET}</div>
          </div>
          <div className="bg-red-50 border border-red-200 rounded px-3 py-2">
            <div className="text-red-700">Từ chối</div>
            <div className="font-bold text-red-800">{thongKeTrangThai.TU_CHOI}</div>
          </div>
        </div>
      </div>

      {/* Bảng danh sách */}
      {loadingDetail && <LoadingSpinner />}
      {danhSach.length === 0 ? (
        <EmptyState title={`Không có báo cáo quý ${quy}/${nam} nào${filterTrangThai ? ` ở trạng thái "${TRANG_THAI_MAP[filterTrangThai]?.label}"` : ''}`} />
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Đơn vị</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Trạng thái</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Tổng CC</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">A / B / C / D</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Người lập</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ngày gửi</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {danhSach.map((bc) => (
                <tr key={bc.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{bc.don_vi?.ten_don_vi || 'N/A'}</td>
                  <td className="px-4 py-3 text-center"><StatusBadge trangThai={bc.trang_thai} /></td>
                  <td className="px-4 py-3 text-sm text-center font-medium">{bc.tong_cong_chuc}</td>
                  <td className="px-4 py-3 text-sm text-center">
                    <span className="text-green-700 font-semibold">{bc.so_loai_a}</span>{' / '}
                    <span className="text-blue-700 font-semibold">{bc.so_loai_b}</span>{' / '}
                    <span className="text-amber-700 font-semibold">{bc.so_loai_c}</span>{' / '}
                    <span className="text-orange-700 font-semibold">{bc.so_loai_d}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{bc.nguoi_lap?.ho_ten || 'N/A'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{bc.ngay_gui_duyet ? new Date(bc.ngay_gui_duyet).toLocaleDateString('vi-VN') : '-'}</td>
                  <td className="px-4 py-3 text-center whitespace-nowrap">
                    <button
                      onClick={() => handleSelectBaoCao(bc.id)}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium hover:underline mr-3"
                    >
                      Xem chi tiết
                    </button>
                    <button
                      onClick={() => handleDownloadMau03(bc)}
                      disabled={downloadingId === bc.id}
                      className="text-purple-600 hover:text-purple-800 text-sm font-medium hover:underline disabled:opacity-50"
                      title="Tải Mẫu 03 của đơn vị này"
                    >
                      {downloadingId === bc.id ? 'Đang tải...' : '📄 Mẫu 03'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TabQuy({ nam }: ITabProps) {
  const { user } = useAuthStore();
  const [quy, setQuy] = useState<number>(Math.ceil((new Date().getMonth() + 1) / 3));

  const maVaiTro = user?.vai_tro?.ma_vai_tro || '';
  const isTDV = maVaiTro === 'TDV' || maVaiTro === 'PDV';
  const isCCT = ['CCT', 'PCCT', 'SUPER_ADMIN'].includes(maVaiTro);
  // TCCB (hoặc user có can_view_all_units): xem tất cả đơn vị nhưng không phê duyệt
  const hasViewAll = user?.can_view_all_units === true;
  const isBigViewer = isCCT || hasViewAll;

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Báo cáo xếp loại quý</h2>
        <div className="flex items-center gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Quý</label>
            <select
              className="border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={quy}
              onChange={(e) => setQuy(Number(e.target.value))}
            >
              <option value={1}>Quý 1 (Tháng 1-3)</option>
              <option value={2}>Quý 2 (Tháng 4-6)</option>
              <option value={3}>Quý 3 (Tháng 7-9)</option>
              <option value={4}>Quý 4 (Tháng 10-12)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Năm</label>
            <input type="text" className="border border-gray-300 rounded-md p-2 bg-gray-50" value={nam} readOnly />
          </div>
        </div>
      </div>

      {/* Content */}
      {isTDV ? (
        <WorkflowViewTDV quy={quy} nam={nam} />
      ) : isBigViewer ? (
        <WorkflowViewCCT quy={quy} nam={nam} canApprove={isCCT} />
      ) : (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <p className="text-gray-600">Bạn không có quyền truy cập báo cáo quý.</p>
        </div>
      )}
    </div>
  );
}

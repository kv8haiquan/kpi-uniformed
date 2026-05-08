/**
 * src/components/ke-khai/LeaderKeKhaiView.tsx
 * ============================================
 * Component view kê khai cho Lãnh đạo.
 * Bao gồm 2 tabs: Kê khai công việc + Đánh giá d, đ, e
 * 
 * Version: 2.7.0 (31/01/2026)
 * UPDATE v2.7.0:
 * - Thêm cột Mô tả riêng (giống Công chức)
 * - Wrap text thay vì truncate
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { leaderKPIService } from '@/services/leader-kpi.service';
import {
  IKeKhaiLanhDaoResponse,
  IThongKeKeKhaiLanhDao,
  IDanhGiaDDEResponse,
  TrangThaiKeKhaiLD,
  TrangThaiCongViecLD,
  tinhDiemKPILanhDao,
  INguoiPheDuyetLanhDao,
} from '@/types/leader-kpi';
import LeaderDeclarationForm from './LeaderDeclarationForm';
import LeaderAssessmentDDE from './LeaderAssessmentDDE';

// =============================================================================
// TYPES
// =============================================================================

type TabType = 'ke-khai' | 'danh-gia-dde';

interface LeaderKeKhaiViewProps {
  thang: number;
  nam: number;
  /** Phase 3 (29/04/2026): nếu user là HĐ 111 → ẩn tab "Đánh giá d, đ, e",
   *  hiển thị summary 3 chỉ số (a, b, c) thay vì 6, đổi label/màu phù hợp. */
  isHd111?: boolean;
}

// =============================================================================
// SUB COMPONENTS
// =============================================================================

function TabHeader({
  activeTab,
  onTabChange,
  hideAssessmentTab = false,
}: {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  hideAssessmentTab?: boolean;
}) {
  return (
    <div className="border-b border-gray-200 bg-white rounded-t-xl">
      <nav className="flex -mb-px" aria-label="Tabs">
        <button
          onClick={() => onTabChange('ke-khai')}
          className={`py-4 px-6 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'ke-khai'
              ? 'border-indigo-500 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <span className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Kê khai công việc
          </span>
        </button>
        {!hideAssessmentTab && (
          <button
            onClick={() => onTabChange('danh-gia-dde')}
            className={`py-4 px-6 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'danh-gia-dde'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <span className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Đánh giá d, đ, e
            </span>
          </button>
        )}
      </nav>
    </div>
  );
}

// Format tỷ lệ % tối đa 6 chữ số thập phân (strip trailing zeros). Chặn nhảy
// lên 100% khi v < 1 (làm tròn floating-point).
function pctSafe(v: number, _digits = 6): string {
  const value = v * 100;
  if (v < 1 && value >= 100) {
    const truncated = Math.floor(value * 1e6) / 1e6;
    return truncated.toFixed(6).replace(/\.?0+$/, '');
  }
  return value.toFixed(6).replace(/\.?0+$/, '');
}

function SummaryCard({ thongKe, dde }: { thongKe: IThongKeKeKhaiLanhDao | null; dde: IDanhGiaDDEResponse | null }) {
  if (!thongKe) return null;

  const diemKPI = tinhDiemKPILanhDao(thongKe, dde);

  return (
    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-5 border border-indigo-200 mb-6">
      <h3 className="font-semibold text-gray-900 mb-4">📊 Tóm tắt KPI Lãnh đạo</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="text-center">
          <p className="text-xs text-gray-500">Target (CV đã duyệt)</p>
          <p className="text-2xl font-bold text-indigo-600">{diemKPI.target_cong_viec}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">a. Số lượng</p>
          <p className="text-xl font-bold text-blue-600">{pctSafe(diemKPI.a_so_luong)}%</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">b. Chất lượng</p>
          <p className="text-xl font-bold text-green-600">{pctSafe(diemKPI.b_chat_luong)}%</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">c. Tiến độ</p>
          <p className="text-xl font-bold text-amber-600">{pctSafe(diemKPI.c_tien_do)}%</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4 pt-4 border-t border-indigo-200">
        <div className="text-center">
          <p className="text-xs text-gray-500">d. Kết quả ĐV</p>
          <p className={`text-lg font-bold ${diemKPI.d_ket_qua_don_vi === 100 ? 'text-green-600' : 'text-yellow-600'}`}>
            {diemKPI.d_ket_qua_don_vi}%
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">đ. Tổ chức TK</p>
          <p className={`text-lg font-bold ${diemKPI.dd_to_chuc_trien_khai === 100 ? 'text-green-600' : 'text-yellow-600'}`}>
            {diemKPI.dd_to_chuc_trien_khai}%
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">e. Đoàn kết NB</p>
          <p className={`text-lg font-bold ${diemKPI.e_doan_ket_noi_bo === 100 ? 'text-green-600' : 'text-yellow-600'}`}>
            {diemKPI.e_doan_ket_noi_bo}%
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg p-4 border border-indigo-200">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">Công thức: (a + b + c + d + đ + e) / 6 × 70</p>
          <div className="text-right">
            <p className="text-sm text-gray-500">Điểm KPI:</p>
            <p className="text-3xl font-bold text-indigo-700">{diemKPI.diem_kpi_quy_doi.toFixed(6).replace(/\.?0+$/, '')}<span className="text-sm text-gray-500">/70</span></p>
          </div>
        </div>
      </div>
    </div>
  );
}

function DeclarationTable({
  items,
  onEdit,
  onDelete,
  isLoading,
}: {
  items: IKeKhaiLanhDaoResponse[];
  onEdit: (item: IKeKhaiLanhDaoResponse) => void;
  onDelete: (id: string, name: string) => void;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="font-medium">Chưa có công việc nào được kê khai.</p>
        <p className="text-sm mt-1">Bấm "Thêm công việc" để bắt đầu.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">STT</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Công việc</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase min-w-[200px]">Mô tả</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ngày</th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">SL</th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Hoàn thành</th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Trạng thái</th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Thao tác</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {items.map((item, index) => {
            const canEdit = item.trang_thai === TrangThaiKeKhaiLD.NHAP || item.trang_thai === TrangThaiKeKhaiLD.TU_CHOI;
            const isCompleted = item.trang_thai_hoan_thanh === TrangThaiCongViecLD.DA_HOAN_THANH;

            return (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-500">{index + 1}</td>
                <td className="px-4 py-3">
                  <div className="text-sm font-medium text-gray-900">{item.ten_cong_viec}</div>
                </td>
                {/* v2.7.0: Cột mô tả riêng - wrap text */}
                <td className="px-4 py-3 max-w-[300px]">
                  <p className="text-sm text-gray-600 whitespace-pre-wrap break-words">
                    {item.mo_ta || '-'}
                  </p>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {new Date(item.ngay_thuc_hien).toLocaleDateString('vi-VN')}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 text-center font-medium">{item.so_luong}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    isCompleted ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {isCompleted ? '✓ Hoàn thành' : '○ Chưa'}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    item.trang_thai === TrangThaiKeKhaiLD.DA_PHE_DUYET ? 'bg-green-100 text-green-800' :
                    item.trang_thai === TrangThaiKeKhaiLD.CHO_PHE_DUYET ? 'bg-blue-100 text-blue-800' :
                    item.trang_thai === TrangThaiKeKhaiLD.TU_CHOI ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {item.trang_thai === TrangThaiKeKhaiLD.DA_PHE_DUYET ? 'Đã duyệt' :
                     item.trang_thai === TrangThaiKeKhaiLD.CHO_PHE_DUYET ? 'Chờ duyệt' :
                     item.trang_thai === TrangThaiKeKhaiLD.TU_CHOI ? 'Từ chối' : 'Nháp'}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  {canEdit ? (
                    <div className="flex items-center justify-center gap-2">
                      <button onClick={() => onEdit(item)} className="text-indigo-600 hover:text-indigo-800" title="Sửa">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button onClick={() => onDelete(item.id, item.ten_cong_viec)} className="text-red-600 hover:text-red-800" title="Xóa">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LeaderKeKhaiView({ thang, nam, isHd111 = false }: LeaderKeKhaiViewProps) {
  const [activeTab, setActiveTab] = useState<TabType>('ke-khai');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [keKhaiList, setKeKhaiList] = useState<IKeKhaiLanhDaoResponse[]>([]);
  const [thongKe, setThongKe] = useState<IThongKeKeKhaiLanhDao | null>(null);
  const [dde, setDDE] = useState<IDanhGiaDDEResponse | null>(null);

  // Form states
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<IKeKhaiLanhDaoResponse | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Submit states
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Người phê duyệt states
  const [nguoiPheDuyetList, setNguoiPheDuyetList] = useState<INguoiPheDuyetLanhDao[]>([]);
  const [showGuiDuyetModal, setShowGuiDuyetModal] = useState(false);
  const [selectedNguoiPheDuyet, setSelectedNguoiPheDuyet] = useState<string>('');

  // Load data
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [list, stats, ddeData, nguoiPD] = await Promise.all([
        leaderKPIService.getKeKhaiList(thang, nam),
        leaderKPIService.getThongKe(thang, nam),
        leaderKPIService.getDanhGiaDDE(thang, nam),
        leaderKPIService.getNguoiPheDuyet(),
      ]);

      setKeKhaiList(list);
      setThongKe(stats);
      setDDE(ddeData);
      setNguoiPheDuyetList(nguoiPD);
      
      // Tự động chọn người phê duyệt đầu tiên nếu có
      if (nguoiPD.length > 0 && !selectedNguoiPheDuyet) {
        setSelectedNguoiPheDuyet(nguoiPD[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Không thể tải dữ liệu');
    } finally {
      setIsLoading(false);
    }
  }, [thang, nam]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handlers
  const handleEdit = (item: IKeKhaiLanhDaoResponse) => {
    setEditingItem(item);
    setShowForm(true);
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setIsDeleting(true);

    try {
      await leaderKPIService.deleteKeKhai(deleteConfirm.id);
      setDeleteConfirm(null);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Không thể xóa');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingItem(null);
    loadData();
  };

  // Mở modal gửi duyệt
  const handleOpenGuiDuyet = () => {
    const draftItems = keKhaiList.filter(k => k.trang_thai === TrangThaiKeKhaiLD.NHAP);
    if (draftItems.length === 0) {
      alert('Không có bản kê khai nháp nào để gửi duyệt.');
      return;
    }
    
    if (nguoiPheDuyetList.length === 0) {
      alert('Không tìm thấy người phê duyệt. Vui lòng liên hệ quản trị viên.');
      return;
    }
    
    setShowGuiDuyetModal(true);
  };

  // Xác nhận gửi duyệt
  const handleConfirmGuiDuyet = async () => {
    if (!selectedNguoiPheDuyet) {
      alert('Vui lòng chọn người phê duyệt.');
      return;
    }
    
    const draftItems = keKhaiList.filter(k => k.trang_thai === TrangThaiKeKhaiLD.NHAP);

    setIsSubmitting(true);
    try {
      const result = await leaderKPIService.guiDuyetNhieu(
        draftItems.map(k => k.id),
        selectedNguoiPheDuyet  // Truyền người phê duyệt
      );
      
      setShowGuiDuyetModal(false);
      
      if (result.failed.length > 0) {
        alert(`Đã gửi ${result.success.length} bản. ${result.failed.length} bản thất bại.`);
      } else {
        alert(`Đã gửi ${result.success.length} bản kê khai đi phê duyệt!`);
      }
      loadData();
    } catch (err: any) {
      alert(err.message || 'Có lỗi xảy ra khi gửi duyệt');
    } finally {
      setIsSubmitting(false);
    }
  };

  const draftCount = keKhaiList.filter(k => k.trang_thai === TrangThaiKeKhaiLD.NHAP).length;

  return (
    <div className="space-y-6">
      {/* Summary */}
      {/* Phase 3: Tóm tắt KPI hiện đang dùng công thức 6 chỉ số (LĐ).
          HĐ 111 không có d/đ/e → ẩn để tránh hiển thị sai; xem điểm chi tiết ở /danh-gia. */}
      {!isHd111 && <SummaryCard thongKe={thongKe} dde={dde} />}

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <TabHeader
          activeTab={activeTab}
          onTabChange={setActiveTab}
          hideAssessmentTab={isHd111}
        />

        <div className="p-6">
          {activeTab === 'ke-khai' && (
            <>
              {/* Actions */}
              <div className="flex justify-between items-center mb-4">
                <div className="text-sm text-gray-600">
                  Tổng: <span className="font-medium">{keKhaiList.length}</span> công việc
                  {draftCount > 0 && (
                    <span className="ml-2 text-yellow-600">({draftCount} nháp)</span>
                  )}
                </div>
                <div className="flex gap-3">
                  {draftCount > 0 && (
                    <button
                      onClick={handleOpenGuiDuyet}
                      disabled={isSubmitting}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm flex items-center gap-2"
                    >
                      {isSubmitting ? (
                        <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                      ) : (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                      Gửi duyệt ({draftCount})
                    </button>
                  )}
                  <button
                    onClick={() => { setEditingItem(null); setShowForm(true); }}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Thêm công việc
                  </button>
                </div>
              </div>

              {/* Form or Table */}
              {showForm ? (
                <LeaderDeclarationForm
                  thang={thang}
                  nam={nam}
                  editItem={editingItem}
                  onSuccess={handleFormSuccess}
                  onCancel={() => { setShowForm(false); setEditingItem(null); }}
                />
              ) : (
                <DeclarationTable
                  items={keKhaiList}
                  onEdit={handleEdit}
                  onDelete={(id, name) => setDeleteConfirm({ id, name })}
                  isLoading={isLoading}
                />
              )}
            </>
          )}

          {activeTab === 'danh-gia-dde' && (
            <LeaderAssessmentDDE thang={thang} nam={nam} onSaveSuccess={loadData} />
          )}
        </div>
      </div>

      {/* Delete Confirm Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Xác nhận xóa</h3>
            <p className="text-gray-600 mb-4">
              Bạn có chắc muốn xóa công việc "<strong>{deleteConfirm.name}</strong>"?
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Hủy
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {isDeleting ? 'Đang xóa...' : 'Xóa'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Chọn Người Phê Duyệt */}
      {showGuiDuyetModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Gửi kê khai phê duyệt</h3>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-3">
                Bạn có <strong className="text-green-600">{keKhaiList.filter(k => k.trang_thai === TrangThaiKeKhaiLD.NHAP).length}</strong> bản kê khai nháp sẽ được gửi.
              </p>
              
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Chọn người phê duyệt <span className="text-red-500">*</span>
              </label>
              <select
                value={selectedNguoiPheDuyet}
                onChange={(e) => setSelectedNguoiPheDuyet(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              >
                <option value="">-- Chọn người phê duyệt --</option>
                {nguoiPheDuyetList.map((nguoi) => (
                  <option key={nguoi.id} value={nguoi.id}>
                    {nguoi.ho_ten} ({nguoi.chuc_vu || nguoi.ma_cc})
                  </option>
                ))}
              </select>
              
              {nguoiPheDuyetList.length === 1 && (
                <p className="text-xs text-gray-500 mt-1">
                  Theo quy định, kê khai của bạn sẽ do <strong>{nguoiPheDuyetList[0].ho_ten}</strong> phê duyệt.
                </p>
              )}
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowGuiDuyetModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                disabled={isSubmitting}
              >
                Hủy
              </button>
              <button
                onClick={handleConfirmGuiDuyet}
                disabled={isSubmitting || !selectedNguoiPheDuyet}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    Đang gửi...
                  </>
                ) : (
                  'Xác nhận gửi'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
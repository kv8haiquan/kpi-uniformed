/**
 * src/app/(main)/xep-loai/thong-ke/page.tsx
 * ==========================================
 * Trang Thống kê Xếp loại Chất lượng Công chức toàn Chi cục.
 * 
 * Chức năng:
 * - Xem thống kê xếp loại theo tháng/năm
 * - Bảng tổng hợp theo đơn vị
 * - Bảng số liệu chi tiết (không có biểu đồ)
 * - Xuất báo cáo Mẫu 04 (danh sách phê duyệt kết quả xếp loại)
 * 
 * Quyền: Chi cục trưởng, Phó Chi cục trưởng
 * 
 * Version: 1.1.0 (11/02/2026) - Thêm nút xuất báo cáo Mẫu 04
 * Version: 1.0.0 (28/01/2026)
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { baoCaoXepLoaiService } from '@/services/bao-cao-xep-loai.service';
import ExportButton, { ExportFormat } from '@/components/common/ExportButton';
import { exportService } from '@/services/export.service';
import {
  IThongKeXepLoai,
  TrangThaiBaoCao,
  getXepLoaiColor,
  getTrangThaiTen,
  getTrangThaiColor,
} from '@/types/bao-cao-xep-loai';

// =============================================================================
// SUB COMPONENTS
// =============================================================================

/**
 * Card thống kê tổng quan.
 */
function TongQuanCard({ thongKe }: { thongKe: IThongKeXepLoai }) {
  const items = [
    { label: 'Loại A', value: thongKe.theo_xep_loai.A, color: 'bg-green-500', textColor: 'text-green-600' },
    { label: 'Loại B', value: thongKe.theo_xep_loai.B, color: 'bg-blue-500', textColor: 'text-blue-600' },
    { label: 'Loại C', value: thongKe.theo_xep_loai.C, color: 'bg-yellow-500', textColor: 'text-yellow-600' },
    { label: 'Loại D', value: thongKe.theo_xep_loai.D, color: 'bg-orange-500', textColor: 'text-orange-600' },
    { label: 'Loại E', value: thongKe.theo_xep_loai.E, color: 'bg-red-500', textColor: 'text-red-600' },
  ];

  const total = thongKe.tong_cong_chuc;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Tổng quan toàn Chi cục</h3>
      
      <div className="text-center mb-6">
        <p className="text-4xl font-bold text-gray-900">{total}</p>
        <p className="text-gray-500">Tổng số công chức</p>
      </div>

      {/* Progress bar */}
      <div className="h-4 rounded-full overflow-hidden flex mb-4 bg-gray-100">
        {items.map((item) => {
          const percent = total > 0 ? (item.value / total) * 100 : 0;
          if (percent === 0) return null;
          return (
            <div 
              key={item.label}
              className={`${item.color} h-full`}
              style={{ width: `${percent}%` }}
              title={`${item.label}: ${item.value} (${percent.toFixed(1)}%)`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-5 gap-2">
        {items.map((item) => {
          const percent = total > 0 ? (item.value / total) * 100 : 0;
          return (
            <div key={item.label} className="text-center">
              <div className={`w-3 h-3 ${item.color} rounded-full mx-auto mb-1`} />
              <p className={`text-2xl font-bold ${item.textColor}`}>{item.value}</p>
              <p className="text-xs text-gray-500">{item.label}</p>
              <p className="text-xs text-gray-400">{percent.toFixed(1)}%</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Bảng thống kê theo đơn vị.
 */
function BangTheoDonVi({ thongKe }: { thongKe: IThongKeXepLoai }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600">
        <h3 className="text-lg font-semibold text-white">Thống kê theo đơn vị</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Đơn vị</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Tổng</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-green-600 uppercase">A</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-blue-600 uppercase">B</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-yellow-600 uppercase">C</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-orange-600 uppercase">D</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-red-600 uppercase">E</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Trạng thái</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {thongKe.theo_don_vi.map((dv) => {
              // Kiểm tra tỷ lệ A
              const tyLeA = dv.B > 0 ? (dv.A / dv.B) * 100 : (dv.A > 0 ? 100 : 0);
              const canhBaoA = tyLeA > 20;

              return (
                <tr key={dv.don_vi.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{dv.don_vi.ten_don_vi}</span>
                      {canhBaoA && (
                        <span className="text-amber-500" title="Tỷ lệ A vượt 20%">⚠️</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center font-semibold text-gray-900">{dv.tong}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded ${dv.A > 0 ? 'bg-green-100 text-green-700 font-semibold' : 'text-gray-400'}`}>
                      {dv.A}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded ${dv.B > 0 ? 'bg-blue-100 text-blue-700 font-semibold' : 'text-gray-400'}`}>
                      {dv.B}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded ${dv.C > 0 ? 'bg-yellow-100 text-yellow-700 font-semibold' : 'text-gray-400'}`}>
                      {dv.C}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded ${dv.D > 0 ? 'bg-orange-100 text-orange-700 font-semibold' : 'text-gray-400'}`}>
                      {dv.D}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded ${dv.E > 0 ? 'bg-red-100 text-red-700 font-semibold' : 'text-gray-400'}`}>
                      {dv.E}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {dv.trang_thai ? (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTrangThaiColor(dv.trang_thai)}`}>
                        {getTrangThaiTen(dv.trang_thai)}
                      </span>
                    ) : (
                      <span className="text-gray-400 text-xs">Chưa có</span>
                    )}
                  </td>
                </tr>
              );
            })}

            {/* Tổng cộng */}
            <tr className="bg-gray-100 font-semibold">
              <td className="px-4 py-3 text-gray-900">TỔNG CỘNG</td>
              <td className="px-4 py-3 text-center text-gray-900">{thongKe.tong_cong_chuc}</td>
              <td className="px-4 py-3 text-center text-green-700">{thongKe.theo_xep_loai.A}</td>
              <td className="px-4 py-3 text-center text-blue-700">{thongKe.theo_xep_loai.B}</td>
              <td className="px-4 py-3 text-center text-yellow-700">{thongKe.theo_xep_loai.C}</td>
              <td className="px-4 py-3 text-center text-orange-700">{thongKe.theo_xep_loai.D}</td>
              <td className="px-4 py-3 text-center text-red-700">{thongKe.theo_xep_loai.E}</td>
              <td className="px-4 py-3"></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Bảng thang điểm xếp loại.
 */
function ThangDiemCard() {
  const items = [
    { loai: 'A', diem: '≥ 90', moTa: 'Hoàn thành xuất sắc nhiệm vụ', color: getXepLoaiColor('A') },
    { loai: 'B', diem: '70 - 89', moTa: 'Hoàn thành tốt nhiệm vụ', color: getXepLoaiColor('B') },
    { loai: 'C', diem: '50 - 69', moTa: 'Hoàn thành nhiệm vụ', color: getXepLoaiColor('C') },
    { loai: 'D', diem: '< 50', moTa: 'Không hoàn thành nhiệm vụ', color: getXepLoaiColor('D') },
    { loai: 'E', diem: '0', moTa: 'Không đánh giá (nghỉ cả tháng)', color: getXepLoaiColor('E') },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Thang điểm xếp loại</h3>
      
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.loai} className="flex items-center gap-4">
            <div className={`w-10 h-10 ${item.color.bg} ${item.color.text} ${item.color.border} border rounded-lg flex items-center justify-center font-bold`}>
              {item.loai}
            </div>
            <div className="flex-1">
              <p className="font-medium text-gray-900">{item.moTa}</p>
              <p className="text-sm text-gray-500">Điểm: {item.diem}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          <strong>Lưu ý:</strong> Số công chức xếp loại A không được vượt quá 20% số công chức xếp loại B trong cùng đơn vị.
        </p>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function ThongKeXepLoaiPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  // State
  const [thongKe, setThongKe] = useState<IThongKeXepLoai | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Month/Year selector
  const currentDate = new Date();
  const [selectedThang, setSelectedThang] = useState(currentDate.getMonth() + 1);
  const [selectedNam, setSelectedNam] = useState(currentDate.getFullYear());

  // Auth check
  useEffect(() => {
    if (!isAuthenticated) router.push('/login');
  }, [isAuthenticated, router]);

  // Check quyền CCT hoặc Phó CCT
  const hasAccess = user?.vai_tro?.cap_bac === 'CHI_CUC_TRUONG' || user?.vai_tro?.cap_bac === 'PHO_CHI_CUC_TRUONG' || user?.can_view_all_units === true;

  // Load data
  const loadData = useCallback(async () => {
    if (!hasAccess) return;
    
    setIsLoading(true);
    setError(null);

    try {
      const data = await baoCaoXepLoaiService.getThongKe(selectedThang, selectedNam);
      setThongKe(data);
    } catch (err: any) {
      setError(err.message || 'Có lỗi xảy ra');
    } finally {
      setIsLoading(false);
    }
  }, [selectedThang, selectedNam, hasAccess]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Không có quyền
  if (!hasAccess) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Không có quyền truy cập</h2>
          <p className="text-gray-600 mb-4">Chỉ Chi cục trưởng và Phó Chi cục trưởng mới có quyền xem thống kê.</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Về Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/dashboard')}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📊 Thống kê Xếp loại Chất lượng</h1>
              <p className="text-gray-600 mt-1">Tổng hợp kết quả đánh giá toàn Chi cục</p>
            </div>
          </div>

          {/* Month/Year Selector */}
          <div className="flex items-center gap-3">
            <select
              value={selectedThang}
              onChange={(e) => setSelectedThang(parseInt(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>
              ))}
            </select>
            <select
              value={selectedNam}
              onChange={(e) => setSelectedNam(parseInt(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              {[currentDate.getFullYear() - 1, currentDate.getFullYear(), currentDate.getFullYear() + 1].map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
            
            {/* Nút xuất báo cáo Mẫu 04 */}
            {thongKe && (
            <>
              <ExportButton
                label="Xuất Mẫu 03 (Tất cả ĐV)"
                size="sm"
                onExport={async (format: ExportFormat) => {
                  await exportService.exportDonViTongHop({
                    thang: selectedThang,
                    nam: selectedNam,
                    format,
                  });
                }}
              />
              <ExportButton
                label="Xuất Mẫu 04"
                size="sm"
                onExport={async (format: ExportFormat) => {
                  await exportService.exportTongHop({
                    thang: selectedThang,
                    nam: selectedNam,
                    format,
                  });
                }}
              />
              <ExportButton
                label="Xuất Mẫu 05 (Đổi mới)"
                size="sm"
                onExport={async (format: ExportFormat) => {
                  await exportService.exportMau05DoiMoi({
                    thang: selectedThang,
                    nam: selectedNam,
                    format,
                  });
                }}
              />
            </>
          )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
        ) : thongKe ? (
          <div className="space-y-6">
            {/* Row 1: Tổng quan + Thang điểm */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <TongQuanCard thongKe={thongKe} />
              </div>
              <div>
                <ThangDiemCard />
              </div>
            </div>

            {/* Row 2: Bảng theo đơn vị */}
            <BangTheoDonVi thongKe={thongKe} />

            {/* Ghi chú */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <h4 className="font-medium text-gray-900 mb-2">Ghi chú</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• ⚠️ Cảnh báo: Đơn vị có tỷ lệ loại A vượt quá 20% số loại B</li>
                <li>• Số liệu được tính từ các báo cáo đã được phê duyệt</li>
                <li>• Đơn vị chưa gửi báo cáo sẽ hiển thị trạng thái "Chưa có"</li>
              </ul>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="text-gray-500">Chưa có dữ liệu thống kê cho tháng {selectedThang}/{selectedNam}</p>
          </div>
        )}
      </main>
    </div>
  );
}
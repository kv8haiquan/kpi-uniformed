/**
 * src/app/(main)/in-bang-ke/page.tsx
 * ====================================
 * Trang in bảng kê cá nhân.
 *
 * Cho phép user chọn tháng/năm hoặc quý/năm và in:
 * 1. Phiếu đánh giá (PL-01A hoặc PL-01B - auto detect is_lanh_dao)
 * 2. Bảng kê công việc (PL-02)
 *
 * Version: 1.1.0 (16/04/2026) - Thêm tab Quý
 */

'use client';

import React, { useState } from 'react';
import { useAuthStore } from '@/stores/useAuthStore';
import apiClient from '@/lib/axios';

export default function InBangKePage() {
  const { user } = useAuthStore();

  const currentDate = new Date();
  const [loaiKy, setLoaiKy] = useState<'thang' | 'quy'>('thang');
  const [thang, setThang] = useState(currentDate.getMonth() + 1);
  const [quy, setQuy] = useState(Math.ceil((currentDate.getMonth() + 1) / 3));
  const [nam, setNam] = useState(currentDate.getFullYear());
  const [loading, setLoading] = useState(false);

  // Download file helper
  const downloadFile = async (endpoint: string, filename: string) => {
    try {
      setLoading(true);
      const response = await apiClient.get(endpoint, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Lỗi tải file:', error);
      let errorMessage = 'Không thể tải file. Vui lòng thử lại.';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handler in phiếu đánh giá
  const handleInPhieuDanhGia = async () => {
    const ma_cc = user?.ma_cc?.replace('/', '-') || 'user';

    if (loaiKy === 'thang') {
      const filename = `PhieuDanhGia_${ma_cc}_T${thang}_${nam}.docx`;
      await downloadFile(`/in-bang-ke/phieu-danh-gia/${thang}/${nam}`, filename);
    } else {
      const filename = `PhieuDanhGia_${ma_cc}_Q${quy}_${nam}.docx`;
      await downloadFile(`/in-bang-ke/phieu-danh-gia-quy/${quy}/${nam}`, filename);
    }
  };

  // Handler in bảng kê công việc
  const handleInBangKeCongViec = async () => {
    const ma_cc = user?.ma_cc?.replace('/', '-') || 'user';

    if (loaiKy === 'thang') {
      const filename = `BangKeCongViec_${ma_cc}_T${thang}_${nam}.docx`;
      await downloadFile(`/in-bang-ke/bang-ke-cong-viec/${thang}/${nam}`, filename);
    } else {
      const filename = `BangKeCongViec_${ma_cc}_Q${quy}_${nam}.docx`;
      await downloadFile(`/in-bang-ke/bang-ke-cong-viec-quy/${quy}/${nam}`, filename);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 mb-6 p-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
              <span className="text-2xl text-white">📋</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">In Bảng kê</h1>
              <p className="text-sm text-gray-600 mt-1">Xuất phiếu đánh giá và bảng kê công việc</p>
            </div>
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
          {/* Chọn kỳ đánh giá */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-xl">📅</span>
              Chọn kỳ đánh giá
            </h2>

            {/* Tab chọn loại kỳ */}
            <div className="flex gap-2 mb-6 bg-gray-100 p-1.5 rounded-xl">
              <button
                onClick={() => setLoaiKy('thang')}
                className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
                  loaiKy === 'thang'
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Theo Tháng
              </button>
              <button
                onClick={() => setLoaiKy('quy')}
                className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
                  loaiKy === 'quy'
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Theo Quý
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Tháng hoặc Quý */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {loaiKy === 'thang' ? 'Tháng' : 'Quý'}
                </label>
                {loaiKy === 'thang' ? (
                  <select
                    value={thang}
                    onChange={(e) => setThang(Number(e.target.value))}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  >
                    {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                      <option key={m} value={m}>
                        Tháng {m}
                      </option>
                    ))}
                  </select>
                ) : (
                  <select
                    value={quy}
                    onChange={(e) => setQuy(Number(e.target.value))}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  >
                    {Array.from({ length: 4 }, (_, i) => i + 1).map((q) => (
                      <option key={q} value={q}>
                        Quý {q}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Năm */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Năm
                </label>
                <select
                  value={nam}
                  onChange={(e) => setNam(Number(e.target.value))}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                  {Array.from({ length: 10 }, (_, i) => currentDate.getFullYear() - 5 + i).map((y) => (
                    <option key={y} value={y}>
                      {y}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Thông tin kỳ đánh giá hiện tại */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 mb-8 border border-blue-100">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">📊</span>
              <h3 className="text-lg font-semibold text-gray-900">Kỳ đánh giá đã chọn</h3>
            </div>
            <p className="text-2xl font-bold text-blue-600">
              {loaiKy === 'thang' ? `Tháng ${thang}/${nam}` : `Quý ${quy}/${nam}`}
            </p>
            <p className="text-sm text-gray-600 mt-2">
              Họ tên: <span className="font-medium text-gray-900">{user?.ho_ten || 'N/A'}</span>
            </p>
            <p className="text-sm text-gray-600">
              Đơn vị: <span className="font-medium text-gray-900">{user?.don_vi?.ten_don_vi || 'N/A'}</span>
            </p>
          </div>

          {/* Nút in */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-xl">🖨️</span>
              Chọn loại báo cáo
            </h2>

            {/* Nút 1: In Phiếu đánh giá */}
            <button
              onClick={handleInPhieuDanhGia}
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-semibold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
            >
              <span className="text-2xl">📝</span>
              <span>In Phiếu đánh giá (PL-01A/01B)</span>
              {loading && <span className="ml-2 animate-spin">⏳</span>}
            </button>

            {/* Nút 2: In Bảng kê công việc */}
            <button
              onClick={handleInBangKeCongViec}
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white font-semibold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
            >
              <span className="text-2xl">📑</span>
              <span>In Bảng kê công việc (PL-02)</span>
              {loading && <span className="ml-2 animate-spin">⏳</span>}
            </button>
          </div>

          {/* Hướng dẫn */}
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <span className="text-2xl flex-shrink-0">💡</span>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Hướng dẫn sử dụng</h3>
                <ul className="text-sm text-gray-700 space-y-1.5 list-disc list-inside">
                  <li>
                    <strong>Phiếu đánh giá:</strong> Hệ thống tự động chọn mẫu PL-01A (công chức) hoặc PL-01B (lãnh đạo) dựa trên vai trò của bạn
                  </li>
                  <li>
                    <strong>Bảng kê công việc:</strong> Xuất chi tiết các công việc đã kê khai trong {loaiKy === 'thang' ? 'tháng' : 'quý (gộp 3 tháng)'}
                  </li>
                  <li>
                    <strong>Định dạng:</strong> Tất cả file xuất dưới dạng DOCX, bạn có thể chỉnh sửa trước khi in
                  </li>
                  <li>
                    <strong>Lưu ý:</strong> Nếu chưa có dữ liệu trong {loaiKy === 'thang' ? 'tháng' : 'quý'} đã chọn, file sẽ chứa thông tin cơ bản và các trường trống
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

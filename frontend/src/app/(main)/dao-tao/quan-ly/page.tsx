/**
 * src/app/(main)/dao-tao/quan-ly/page.tsx
 * ========================================
 * Quan ly dao tao — cho GIANG_VIEN va QT_DAO_TAO.
 * Tabs: Khoa hoc cua toi | Tao khoa hoc | Giao bai.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { khoaHocApi, chuyenDeApi } from '@/services/lms';
import type { IKhoaHoc, IChuyenDe, IPagination } from '@/types/lms';
import ChuyenDeManager from '@/components/lms/ChuyenDeManager';
import KhoaHocEditor from '@/components/lms/KhoaHocEditor';
import CauHoiManager from '@/components/lms/CauHoiManager';
import GiaoBaiForm from '@/components/lms/GiaoBaiForm';
import BaoCaoPanel from '@/components/lms/BaoCaoPanel';

const TT_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  NHAP: { label: 'Nháp', bg: 'bg-gray-100', text: 'text-gray-600' },
  CHO_DUYET: { label: 'Chờ duyệt', bg: 'bg-yellow-100', text: 'text-yellow-700' },
  DA_XUAT_BAN: { label: 'Đang mở', bg: 'bg-green-100', text: 'text-green-700' },
  TAM_DUNG: { label: 'Tạm dừng', bg: 'bg-orange-100', text: 'text-orange-700' },
  DA_DONG: { label: 'Đã đóng', bg: 'bg-red-100', text: 'text-red-700' },
};

type Tab = 'khoa-hoc' | 'tao-moi' | 'giao-bai' | 'chuyen-de' | 'cau-hoi' | 'bao-cao';

export default function QuanLyPage() {
  const [tab, setTab] = useState<Tab>('khoa-hoc');
  const [khoaHocs, setKhoaHocs] = useState<IKhoaHoc[]>([]);
  const [chuyenDes, setChuyenDes] = useState<IChuyenDe[]>([]);
  const [pagination, setPagination] = useState<IPagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterTT, setFilterTT] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  // ID khóa học đang sửa (null = chế độ tạo mới)
  const [editKhoaHocId, setEditKhoaHocId] = useState<string | null>(null);

  // Modal từ chối duyệt — yêu cầu ghi_chu bắt buộc
  const [rejectTarget, setRejectTarget] = useState<{ id: string; ten: string } | null>(null);
  const [rejectNote, setRejectNote] = useState('');

  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = { page, page_size: 15 };
      if (filterTT) params.trang_thai = filterTT;
      if (search) params.search = search;
      const [khRes, cdRes] = await Promise.all([
        khoaHocApi.quanLy(params),
        chuyenDes.length === 0 ? chuyenDeApi.danhSach({ is_active: true }) : null,
      ]);
      setKhoaHocs(khRes.data.data || []);
      setPagination(khRes.data.pagination || null);
      if (cdRes) setChuyenDes(cdRes.data.data || []);
    } catch (err: any) {
      const code = err?.response?.status;
      if (code === 403) {
        setError('Bạn không có quyền truy cập trang quản lý. Cần vai trò GIANG_VIEN hoặc QT_DAO_TAO.');
      } else {
        setError('Không thể tải dữ liệu. Kiểm tra LMS backend (port 8001).');
      }
    } finally {
      setLoading(false);
    }
  }, [page, filterTT, search]);

  useEffect(() => { loadList(); }, [loadList]);

  const handleWorkflow = async (id: string, trangThai: string, ghiChu?: string) => {
    try {
      await khoaHocApi.chuyenTrangThai(id, { trang_thai: trangThai, ghi_chu: ghiChu });
      loadList();
    } catch (err: any) {
      alert(err?.response?.data?.detail?.error?.message || 'Lỗi chuyển trạng thái');
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <span className="text-3xl">🔒</span>
          <p className="mt-2 text-red-700 font-medium">{error}</p>
          <Link href="/dao-tao" className="text-blue-600 hover:underline mt-3 inline-block text-sm">Quay lại Đào tạo</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
          <Link href="/dao-tao" className="hover:text-blue-600">Đào tạo</Link>
          <span>/</span><span className="text-gray-900">Quản lý</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Quản lý đào tạo</h1>

        {/* Tabs — label của tao-moi thay đổi tuỳ theo chế độ tạo/sửa */}
        <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1">
          {([
            ['khoa-hoc',  '📚 Khóa học'],
            ['tao-moi',   editKhoaHocId ? '✏️ Sửa khóa học' : '➕ Tạo mới'],
            ['giao-bai',  '📋 Giao bài'],
            ['chuyen-de', '📂 Chuyên đề'],
            ['cau-hoi',   '📚 Ngân hàng đề'],
            ['bao-cao',   '📊 Báo cáo'],
          ] as [Tab, string][]).map(([k, label]) => (
            <button key={k}
              onClick={() => {
                setTab(k as Tab);
                // Khi click thẳng vào "Tạo mới" → reset về chế độ tạo mới
                if (k === 'tao-moi') setEditKhoaHocId(null);
              }}
              className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                tab === k ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
              }`}>{label}</button>
          ))}
        </div>

        {/* Tab: Khoa hoc */}
        {tab === 'khoa-hoc' && (
          <>
            <div className="flex gap-3 mb-4">
              <input type="text" placeholder="Tìm kiếm..." value={search}
                onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && setPage(1)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm" />
              <select value={filterTT} onChange={(e) => { setFilterTT(e.target.value); setPage(1); }}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
                <option value="">Tất cả</option>
                {Object.entries(TT_CONFIG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
            </div>

            {loading ? (
              <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-14 bg-gray-100 rounded-lg animate-pulse" />)}</div>
            ) : khoaHocs.length === 0 ? (
              <div className="text-center py-12 text-gray-500">Chưa có khóa học nào</div>
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-gray-500">Mã</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-500">Tên khóa học</th>
                      <th className="px-4 py-3 text-center font-medium text-gray-500">Trạng thái</th>
                      <th className="px-4 py-3 text-center font-medium text-gray-500">Bài</th>
                      <th className="px-4 py-3 text-center font-medium text-gray-500">HV</th>
                      <th className="px-4 py-3 text-right font-medium text-gray-500">Hành động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {khoaHocs.map((kh) => {
                      const tt = TT_CONFIG[kh.trang_thai] || TT_CONFIG.NHAP;
                      return (
                        <tr key={kh.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-mono text-xs text-gray-500">{kh.ma_khoa_hoc}</td>
                          <td className="px-4 py-3">
                            <Link href={`/dao-tao/khoa-hoc/${kh.id}`} className="text-blue-600 hover:underline font-medium">{kh.ten_khoa_hoc}</Link>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${tt.bg} ${tt.text}`}>{tt.label}</span>
                          </td>
                          <td className="px-4 py-3 text-center text-gray-600">{kh.so_bai_hoc}</td>
                          <td className="px-4 py-3 text-center text-gray-600">{kh.so_hoc_vien}</td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex justify-end gap-1">
                              {/* Nút Sửa — mở KhoaHocEditor với khóa học này */}
                              <button
                                onClick={() => { setEditKhoaHocId(kh.id); setTab('tao-moi'); }}
                                className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200"
                              >Sửa</button>
                              {kh.trang_thai === 'NHAP' && (
                                <button onClick={() => handleWorkflow(kh.id, 'CHO_DUYET')}
                                  className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs hover:bg-yellow-200">Gửi duyệt</button>
                              )}
                              {kh.trang_thai === 'CHO_DUYET' && (
                                <>
                                  <button onClick={() => handleWorkflow(kh.id, 'DA_XUAT_BAN')}
                                    className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs hover:bg-green-200">Duyệt</button>
                                  <button
                                    onClick={() => { setRejectTarget({ id: kh.id, ten: kh.ten_khoa_hoc }); setRejectNote(''); }}
                                    className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200"
                                  >Từ chối</button>
                                </>
                              )}
                              {kh.trang_thai === 'DA_XUAT_BAN' && (
                                <>
                                  <button onClick={() => handleWorkflow(kh.id, 'TAM_DUNG')}
                                    className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs hover:bg-orange-200">Tạm dừng</button>
                                  <button onClick={() => { if (confirm('Đóng khóa học này? Học viên sẽ không thể truy cập.')) handleWorkflow(kh.id, 'DA_DONG'); }}
                                    className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200">Đóng</button>
                                </>
                              )}
                              {kh.trang_thai === 'TAM_DUNG' && (
                                <>
                                  <button onClick={() => handleWorkflow(kh.id, 'DA_XUAT_BAN')}
                                    className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs hover:bg-green-200">Mở lại</button>
                                  <button onClick={() => { if (confirm('Đóng hẳn khóa học này?')) handleWorkflow(kh.id, 'DA_DONG'); }}
                                    className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200">Đóng</button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
            {pagination && pagination.total_pages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-4">
                <button onClick={() => setPage(Math.max(1, page-1))} disabled={page<=1} className="px-3 py-1 border rounded text-sm disabled:opacity-50">Trước</button>
                <span className="text-sm text-gray-500">{page}/{pagination.total_pages}</span>
                <button onClick={() => setPage(Math.min(pagination.total_pages, page+1))} disabled={page>=pagination.total_pages} className="px-3 py-1 border rounded text-sm disabled:opacity-50">Sau</button>
              </div>
            )}
          </>
        )}

        {/* Tab: Tạo / Sửa khóa học — dùng KhoaHocEditor multi-step */}
        {tab === 'tao-moi' && (
          <KhoaHocEditor
            key={editKhoaHocId ?? 'new'}
            khoaHocId={editKhoaHocId}
            chuyenDes={chuyenDes}
            onSuccess={() => {
              setEditKhoaHocId(null);
              setTab('khoa-hoc');
              loadList();
            }}
            onBack={() => {
              setEditKhoaHocId(null);
              setTab('khoa-hoc');
            }}
          />
        )}

        {/* Tab: Chuyen de — dùng component ChuyenDeManager */}
        {tab === 'chuyen-de' && <ChuyenDeManager />}

        {/* Tab: Câu hỏi — Ngân hàng câu hỏi */}
        {tab === 'cau-hoi' && <CauHoiManager />}

        {/* Tab: Giao bai — dùng GiaoBaiForm thân thiện (combobox + CBCC search) */}
        {tab === 'giao-bai' && <GiaoBaiForm />}

        {/* Tab: Báo cáo — BaoCaoPanel với 3 sub-tabs */}
        {tab === 'bao-cao' && <BaoCaoPanel />}
      </div>

      {/* Modal từ chối duyệt — ghi_chu bắt buộc */}
      {rejectTarget && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="font-semibold text-gray-900">Từ chối khóa học</h3>
              <p className="text-sm text-gray-500 mt-0.5 truncate">{rejectTarget.ten}</p>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lý do từ chối <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={rejectNote}
                  onChange={(e) => setRejectNote(e.target.value)}
                  rows={4}
                  placeholder="Nhập lý do để giảng viên biết cần chỉnh sửa gì..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-400 resize-none"
                  autoFocus
                />
                {rejectNote.trim() === '' && (
                  <p className="text-xs text-red-500 mt-1">Bắt buộc phải nhập lý do từ chối.</p>
                )}
              </div>
            </div>
            <div className="px-6 pb-5 flex justify-end gap-3">
              <button
                onClick={() => { setRejectTarget(null); setRejectNote(''); }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50"
              >
                Hủy
              </button>
              <button
                disabled={!rejectNote.trim()}
                onClick={async () => {
                  await handleWorkflow(rejectTarget.id, 'NHAP', rejectNote.trim());
                  setRejectTarget(null);
                  setRejectNote('');
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50"
              >
                Xác nhận từ chối
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

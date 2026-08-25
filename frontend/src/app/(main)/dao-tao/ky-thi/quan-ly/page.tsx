/**
 * src/app/(main)/dao-tao/ky-thi/quan-ly/page.tsx
 * ===============================================
 * Trang quan ly ky thi DGNL — QT_DAO_TAO.
 * Tabs: Danh sach ky thi | Ngan hang de | Linh vuc | Mau cau truc de | Tao moi.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { kyThiApi, linhVucApi, viTriApi, nganHangDgnlApi, cbccApi, cauTrucDeTemplateApi } from '@/services/lms';
import { useAuthStore } from '@/stores/useAuthStore';
import type { IKyThi, ILinhVuc, IViTriViecLam, ICauTrucDeByViTri, IDgnlValidateResponse, ICauHoiDgnl, IThongKeNganHang, ICauTrucDeTemplate } from '@/types/lms';
import DonViCongChucPicker from '@/components/lms/DonViCongChucPicker';
import MauCauTrucDeManager, { SoCauInput, useTonKhoNganHang } from '@/components/lms/MauCauTrucDeManager';

const TRANG_THAI_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  NHAP: { label: 'Nháp', bg: 'bg-gray-100', text: 'text-gray-600' },
  CHO_DUYET: { label: 'Chờ duyệt', bg: 'bg-yellow-100', text: 'text-yellow-700' },
  DANG_MO: { label: 'Đang mở', bg: 'bg-green-100', text: 'text-green-700' },
  DA_DONG: { label: 'Đã đóng', bg: 'bg-red-100', text: 'text-red-600' },
};

type Tab = 'danh-sach' | 'ngan-hang' | 'linh-vuc' | 'mau-cau-truc' | 'tao-moi';

export default function QuanLyKyThiPage() {
  const { user } = useAuthStore();
  const platformRoles: string[] = (user as any)?.platform_roles ?? [];
  const isQT = user?.is_system_admin === true || platformRoles.includes('QT_DAO_TAO');
  const [tab, setTab] = useState<Tab>('danh-sach');
  const [kyThiList, setKyThiList] = useState<IKyThi[]>([]);
  const [linhVucList, setLinhVucList] = useState<ILinhVuc[]>([]);
  const [viTriList, setViTriList] = useState<IViTriViecLam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form tao moi
  const [form, setForm] = useState({
    ma_ky_thi: '', ten_ky_thi: '', mo_ta: '',
    ngay_bat_dau: '', ngay_ket_thuc: '',
    thoi_gian_lam_bai_phut: 60, diem_dat: 50,
    so_lan_thi_toi_da: 1,
    hien_dap_an: false,
  });
  const [creating, setCreating] = useState(false);

  // Cau truc de modal
  const [selectedKyThi, setSelectedKyThi] = useState<IKyThi | null>(null);
  const [showCauTrucModal, setShowCauTrucModal] = useState(false);
  const [cauTrucDe, setCauTrucDe] = useState<ICauTrucDeByViTri[]>([]);
  const [validateResult, setValidateResult] = useState<IDgnlValidateResponse | null>(null);

  // Giao thi sinh modal
  const [showGiaoThiSinh, setShowGiaoThiSinh] = useState(false);
  const [giaoKyThi, setGiaoKyThi] = useState<IKyThi | null>(null);

  // Sua ky thi modal
  const [editKyThi, setEditKyThi] = useState<IKyThi | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [ktRes, lvRes, vtRes] = await Promise.all([
        kyThiApi.danhSach({ page_size: 100 }),
        linhVucApi.danhSach({ page_size: 100 }),
        viTriApi.danhSach({ page_size: 100 }),
      ]);
      setKyThiList(ktRes.data.data || []);
      setLinhVucList(lvRes.data.data || []);
      setViTriList(vtRes.data.data || []);
    } catch (err: any) {
      setError('Không thể tải dữ liệu');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const clearMessages = () => { setError(null); setSuccess(null); };

  // Tao ky thi
  const handleCreate = async () => {
    clearMessages();
    if (!form.ma_ky_thi || !form.ten_ky_thi || !form.ngay_bat_dau || !form.ngay_ket_thuc) {
      setError('Vui lòng điền đầy đủ thông tin bắt buộc');
      return;
    }
    setCreating(true);
    try {
      await kyThiApi.taoMoi(form);
      setSuccess('Tạo kỳ thi thành công!');
      setForm({ ma_ky_thi: '', ten_ky_thi: '', mo_ta: '', ngay_bat_dau: '', ngay_ket_thuc: '', thoi_gian_lam_bai_phut: 60, diem_dat: 50, so_lan_thi_toi_da: 1, hien_dap_an: false });
      setTab('danh-sach');
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi tạo kỳ thi');
    } finally {
      setCreating(false);
    }
  };

  // Chuyen trang thai
  const handleChuyenTrangThai = async (kt: IKyThi, newState: string) => {
    clearMessages();
    try {
      await kyThiApi.chuyenTrangThai(kt.id, newState);
      setSuccess(`Chuyển trạng thái thành ${TRANG_THAI_CONFIG[newState]?.label} thành công`);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi chuyển trạng thái');
    }
  };

  // Xoa ky thi
  const handleXoa = async (kt: IKyThi) => {
    if (!confirm(`Bạn có chắc muốn xóa kỳ thi "${kt.ten_ky_thi}"?`)) return;
    clearMessages();
    try {
      await kyThiApi.xoa(kt.id);
      setSuccess('Đã xóa kỳ thi');
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi xóa kỳ thi');
    }
  };

  // Validate
  const handleValidate = async (kt: IKyThi) => {
    clearMessages();
    try {
      const res = await kyThiApi.validate(kt.id);
      setValidateResult(res.data.data);
      setSelectedKyThi(kt);
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi validate');
    }
  };

  // Mo cau truc de modal
  const handleOpenCauTruc = async (kt: IKyThi) => {
    clearMessages();
    setSelectedKyThi(kt);
    try {
      const res = await kyThiApi.layCauTrucDe(kt.id);
      setCauTrucDe(res.data.data || []);
      setShowCauTrucModal(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi lấy cấu trúc đề');
    }
  };

  if (!isQT) {
    return (
      <div className="max-w-3xl mx-auto p-8 text-center">
        <div className="text-4xl mb-3">🔒</div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Không có quyền truy cập</h2>
        <p className="text-gray-600">Chỉ Quản trị đào tạo (QT_DAO_TAO) được quản lý kỳ thi đánh giá năng lực.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
        <Link href="/dao-tao" className="hover:text-blue-600">Đào tạo</Link>
        <span>/</span>
        <Link href="/dao-tao/quan-ly" className="hover:text-blue-600">Quản lý</Link>
        <span>/</span>
        <span className="text-gray-900">Kỳ thi ĐGNL</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý kỳ thi ĐGNL</h1>
          <p className="text-sm text-gray-500">Tạo, cấu hình và quản lý kỳ thi đánh giá năng lực</p>
        </div>
        <div className="flex gap-2">
          <Link href="/dao-tao/ky-thi" className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
            Xem danh sách (CBCC)
          </Link>
          <Link href="/dao-tao/quan-ly" className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
            Quay lại quản lý
          </Link>
        </div>
      </div>

      {/* Messages */}
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      {success && <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{success}</div>}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b">
        {[
          { key: 'danh-sach' as Tab, label: 'Danh sách kỳ thi' },
          { key: 'ngan-hang' as Tab, label: 'Ngân hàng đề' },
          { key: 'linh-vuc' as Tab, label: 'Lĩnh vực' },
          { key: 'mau-cau-truc' as Tab, label: 'Mẫu cấu trúc đề' },
          { key: 'tao-moi' as Tab, label: 'Tạo kỳ thi mới' },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); clearMessages(); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* TAB: Danh sach */}
      {tab === 'danh-sach' && (
        <div className="bg-white rounded-xl border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b text-left text-gray-500">
                  <th className="py-3 px-4">Mã</th>
                  <th className="py-3 px-4">Tên kỳ thi</th>
                  <th className="py-3 px-4 text-center">Trạng thái</th>
                  <th className="py-3 px-4 text-center">Thí sinh</th>
                  <th className="py-3 px-4 text-center">Vị trí</th>
                  <th className="py-3 px-4">Thời gian</th>
                  <th className="py-3 px-4 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {kyThiList.length === 0 ? (
                  <tr><td colSpan={7} className="py-8 text-center text-gray-400">Chưa có kỳ thi nào</td></tr>
                ) : kyThiList.map(kt => {
                  const cfg = TRANG_THAI_CONFIG[kt.trang_thai] || TRANG_THAI_CONFIG.NHAP;
                  return (
                    <tr key={kt.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 font-mono text-xs">{kt.ma_ky_thi}</td>
                      <td className="py-3 px-4 font-medium">{kt.ten_ky_thi}</td>
                      <td className="py-3 px-4 text-center">
                        <span className={`${cfg.bg} ${cfg.text} px-2 py-0.5 rounded-full text-xs`}>{cfg.label}</span>
                      </td>
                      <td className="py-3 px-4 text-center">{kt.tong_thi_sinh}</td>
                      <td className="py-3 px-4 text-center">{kt.so_vi_tri}</td>
                      <td className="py-3 px-4 text-xs text-gray-500">
                        {new Date(kt.ngay_bat_dau).toLocaleDateString('vi-VN')} - {new Date(kt.ngay_ket_thuc).toLocaleDateString('vi-VN')}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex gap-1 justify-end flex-wrap">
                          {/* Sua — moi trang thai */}
                          <button onClick={() => setEditKyThi(kt)} className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded hover:bg-orange-200">Sửa</button>
                          {/* Cau truc de + Giao thi sinh — NHAP, CHO_DUYET, DANG_MO */}
                          {kt.trang_thai !== 'DA_DONG' && (
                            <>
                              <button onClick={() => handleOpenCauTruc(kt)} className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200">Cấu trúc đề</button>
                              <button onClick={() => { setGiaoKyThi(kt); setShowGiaoThiSinh(true); }} className="px-2 py-1 text-xs bg-teal-100 text-teal-700 rounded hover:bg-teal-200">Giao thí sinh</button>
                            </>
                          )}
                          {kt.trang_thai === 'NHAP' && (
                            <>
                              <button onClick={() => handleValidate(kt)} className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200">Validate</button>
                              <button onClick={() => handleChuyenTrangThai(kt, 'CHO_DUYET')} className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200">Gửi duyệt</button>
                              <button onClick={() => handleXoa(kt)} className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200">Xóa</button>
                            </>
                          )}
                          {kt.trang_thai === 'CHO_DUYET' && (
                            <>
                              <button onClick={() => handleChuyenTrangThai(kt, 'DANG_MO')} className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200">Duyệt</button>
                              <button onClick={() => handleChuyenTrangThai(kt, 'NHAP')} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200">Trả lại</button>
                            </>
                          )}
                          {kt.trang_thai === 'DANG_MO' && (
                            <>
                              <Link href={`/dao-tao/ky-thi/${kt.id}/giam-sat`} className="px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded hover:bg-amber-200">Giám sát</Link>
                              <button onClick={() => handleChuyenTrangThai(kt, 'DA_DONG')} className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200">Đóng</button>
                            </>
                          )}
                          {kt.trang_thai === 'DA_DONG' && (
                            <>
                              <button onClick={() => handleChuyenTrangThai(kt, 'DANG_MO')} className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200">Mở lại</button>
                              <button onClick={() => handleChuyenTrangThai(kt, 'NHAP')} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200">Về nháp</button>
                            </>
                          )}
                          {(kt.trang_thai === 'DANG_MO' || kt.trang_thai === 'DA_DONG') && (
                            <Link href={`/dao-tao/ky-thi/${kt.id}/thong-ke`} className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200">Thống kê</Link>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB: Tao moi */}
      {/* TAB: Ngan hang de */}
      {tab === 'ngan-hang' && (
        <NganHangDeTab linhVucList={linhVucList} />
      )}

      {/* TAB: Linh vuc */}
      {tab === 'linh-vuc' && (
        <LinhVucTab linhVucList={linhVucList} onReload={loadData} />
      )}

      {/* TAB: Mau cau truc de */}
      {tab === 'mau-cau-truc' && (
        <MauCauTrucDeManager linhVucList={linhVucList} viTriList={viTriList} />
      )}

      {tab === 'tao-moi' && (
        <div className="bg-white rounded-xl border p-6 max-w-2xl">
          <h3 className="font-semibold text-gray-700 mb-4">Thông tin kỳ thi</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mã kỳ thi *</label>
                <input value={form.ma_ky_thi} onChange={e => setForm({...form, ma_ky_thi: e.target.value})}
                  placeholder="VD: KT-Q2-2026" className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Điểm đạt (%)</label>
                <input type="number" value={form.diem_dat} onChange={e => setForm({...form, diem_dat: +e.target.value})}
                  className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tên kỳ thi *</label>
              <input value={form.ten_ky_thi} onChange={e => setForm({...form, ten_ky_thi: e.target.value})}
                placeholder="VD: Kỳ thi ĐGNL Quý 2/2026" className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả</label>
              <textarea value={form.mo_ta} onChange={e => setForm({...form, mo_ta: e.target.value})}
                rows={2} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ngày bắt đầu *</label>
                <input type="datetime-local" value={form.ngay_bat_dau}
                  onChange={e => setForm({...form, ngay_bat_dau: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ngày kết thúc *</label>
                <input type="datetime-local" value={form.ngay_ket_thuc}
                  onChange={e => setForm({...form, ngay_ket_thuc: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Thời gian làm bài (phút)</label>
                <input type="number" value={form.thoi_gian_lam_bai_phut}
                  onChange={e => setForm({...form, thoi_gian_lam_bai_phut: +e.target.value})}
                  className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Số lần thi tối đa</label>
                <input type="number" value={form.so_lan_thi_toi_da}
                  onChange={e => setForm({...form, so_lan_thi_toi_da: +e.target.value})}
                  className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={form.hien_dap_an}
                onChange={e => setForm({...form, hien_dap_an: e.target.checked})}
                className="w-4 h-4"
              />
              <span>Cho phép thí sinh xem chi tiết câu sai sau khi nộp bài</span>
            </label>
            <button
              onClick={handleCreate}
              disabled={creating}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {creating ? 'Đang tạo...' : 'Tạo kỳ thi'}
            </button>
          </div>
        </div>
      )}

      {/* Validate result modal */}
      {validateResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg">
                Kết quả Validate — {selectedKyThi?.ma_ky_thi}
              </h3>
              <button onClick={() => setValidateResult(null)} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div className={`p-3 rounded-lg mb-4 text-sm font-medium ${
              validateResult.tat_ca_du ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
            }`}>
              {validateResult.tat_ca_du ? 'Ngân hàng câu hỏi ĐỦ cho tất cả vị trí' : 'Ngân hàng câu hỏi CHƯA ĐỦ — xem chi tiết bên dưới'}
            </div>
            {validateResult.theo_vi_tri.map((vt, idx) => (
              <div key={idx} className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`w-2 h-2 rounded-full ${vt.du_cau_hoi ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="font-semibold text-sm">{vt.vi_tri_ten}</span>
                </div>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-gray-500 border-b">
                      <th className="py-1 px-2 text-left">Lĩnh vực</th>
                      <th className="py-1 px-2 text-center">Độ khó</th>
                      <th className="py-1 px-2 text-center">Yêu cầu</th>
                      <th className="py-1 px-2 text-center">Có sẵn</th>
                      <th className="py-1 px-2 text-center">Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vt.chi_tiet.map((ct, j) => (
                      <tr key={j} className="border-b">
                        <td className="py-1 px-2">{ct.linh_vuc_ten}</td>
                        <td className="py-1 px-2 text-center">{ct.do_kho}</td>
                        <td className="py-1 px-2 text-center">{ct.yeu_cau}</td>
                        <td className="py-1 px-2 text-center">{ct.co_san}</td>
                        <td className="py-1 px-2 text-center">
                          {ct.du ? <span className="text-green-600">OK</span> : <span className="text-red-600 font-bold">Thiếu {ct.yeu_cau - ct.co_san}</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cau truc de modal */}
      {showCauTrucModal && selectedKyThi && (
        <CauTrucDeModal
          kyThi={selectedKyThi}
          linhVucList={linhVucList}
          viTriList={viTriList}
          cauTrucDe={cauTrucDe}
          onClose={() => { setShowCauTrucModal(false); loadData(); }}
        />
      )}

      {/* Sua ky thi modal */}
      {editKyThi && (
        <SuaKyThiModal
          kyThi={editKyThi}
          onClose={() => { setEditKyThi(null); loadData(); }}
        />
      )}

      {/* Giao thi sinh modal */}
      {showGiaoThiSinh && giaoKyThi && (
        <GiaoThiSinhModal
          kyThi={giaoKyThi}
          viTriList={viTriList}
          onClose={() => { setShowGiaoThiSinh(false); setGiaoKyThi(null); loadData(); }}
        />
      )}
    </div>
  );
}

// =============================================================================
// CauTrucDeModal
// =============================================================================

function CauTrucDeModal({ kyThi, linhVucList, viTriList, cauTrucDe, onClose }: {
  kyThi: IKyThi;
  linhVucList: ILinhVuc[];
  viTriList: IViTriViecLam[];
  cauTrucDe: ICauTrucDeByViTri[];
  onClose: () => void;
}) {
  const [data, setData] = useState(cauTrucDe);
  const [selectedViTri, setSelectedViTri] = useState('');
  const [items, setItems] = useState<{ linh_vuc_id: string; so_cau_de: number; so_cau_trung_binh: number; so_cau_kho: number }[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Mẫu cấu trúc đề: danh sách mẫu + thao tác lưu/áp dụng
  const [templates, setTemplates] = useState<ICauTrucDeTemplate[]>([]);
  const [selectedTpl, setSelectedTpl] = useState('');
  const [tenMau, setTenMau] = useState('');
  const [tplBusy, setTplBusy] = useState(false);
  const [tplMsg, setTplMsg] = useState<string | null>(null);
  // Tồn kho ngân hàng câu hỏi — hiện ngay cạnh ô nhập
  const tonKho = useTonKhoNganHang();

  useEffect(() => {
    cauTrucDeTemplateApi.danhSach({ page_size: 100 })
      .then(res => setTemplates(res.data.data || []))
      .catch(() => { /* khong co quyen / loi mang — an phan mau */ });
  }, []);

  /** Nạp cấu trúc HIỆN CÓ của vị trí vào form khi chọn.
   *
   *  BE upsert coi payload là ảnh chụp đầy đủ: dòng không gửi lên bị xóa. Trước
   *  đây form luôn rỗng nên sửa 1 lĩnh vực là mất sạch các lĩnh vực còn lại —
   *  đó là lý do người dùng phải đi đường vòng "lưu thành mẫu rồi áp dụng".
   */
  const handleChonViTri = (viTriId: string) => {
    setSelectedViTri(viTriId);
    setError(null);
    const hienCo = data.find(d => d.vi_tri_id === viTriId);
    setItems((hienCo?.chi_tiet || []).map(ct => ({
      linh_vuc_id: ct.linh_vuc_id,
      so_cau_de: ct.so_cau_de || 0,
      so_cau_trung_binh: ct.so_cau_trung_binh || 0,
      so_cau_kho: ct.so_cau_kho || 0,
    })));
  };

  // Luu toan bo cau truc hien tai (moi vi tri x linh vuc) thanh mau
  const handleLuuThanhMau = async () => {
    if (!tenMau.trim() || data.length === 0) return;
    setTplBusy(true); setTplMsg(null); setError(null);
    try {
      const cauTruc = data.flatMap(vt => vt.chi_tiet.map(ct => ({
        vi_tri_id: vt.vi_tri_id,
        linh_vuc_id: ct.linh_vuc_id,
        so_cau_de: ct.so_cau_de,
        so_cau_trung_binh: ct.so_cau_trung_binh,
        so_cau_kho: ct.so_cau_kho,
      })));
      await cauTrucDeTemplateApi.taoMoi({
        ten_template: tenMau.trim(),
        mo_ta: `Lưu từ kỳ thi ${kyThi.ma_ky_thi}`,
        cau_truc: cauTruc,
      });
      setTenMau('');
      setTplMsg('✅ Đã lưu cấu trúc hiện tại thành mẫu');
      const res = await cauTrucDeTemplateApi.danhSach({ page_size: 100 });
      setTemplates(res.data.data || []);
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi lưu mẫu');
    } finally { setTplBusy(false); }
  };

  /** Áp dụng mẫu — 1 request nguyên tử, BE validate hết rồi ghi trong 1 transaction. */
  const handleApDungMau = async () => {
    const tpl = templates.find(t => t.id === selectedTpl);
    if (!tpl) return;
    if (!confirm(`Áp dụng mẫu "${tpl.ten_template}"? Cấu trúc của các vị trí trong mẫu sẽ được GHI ĐÈ.`)) return;
    setTplBusy(true); setTplMsg(null); setError(null);
    try {
      const res = await kyThiApi.apDungMauCauTruc(kyThi.id, { template_id: tpl.id });
      setData(res.data.data || []);
      setSelectedViTri(''); setItems([]);
      setTplMsg(`✅ Đã áp dụng mẫu "${tpl.ten_template}"`);
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi áp dụng mẫu');
    } finally { setTplBusy(false); }
  };

  const handleAddLinhVuc = () => {
    setItems([...items, { linh_vuc_id: '', so_cau_de: 0, so_cau_trung_binh: 0, so_cau_kho: 0 }]);
  };

  const handleSave = async () => {
    if (!selectedViTri || items.length === 0) {
      setError('Vui lòng chọn vị trí và thêm ít nhất 1 lĩnh vực');
      return;
    }
    const validItems = items.filter(i => i.linh_vuc_id);
    if (validItems.length === 0) {
      setError('Vui lòng chọn lĩnh vực');
      return;
    }
    const khoa = validItems.map(i => i.linh_vuc_id);
    if (new Set(khoa).size !== khoa.length) {
      setError('Có lĩnh vực bị lặp — vui lòng gộp lại thành 1 dòng');
      return;
    }
    // Payload là ảnh chụp đầy đủ: cảnh báo khi số dòng ít hơn cấu trúc đang có
    const hienCo = data.find(d => d.vi_tri_id === selectedViTri);
    const soDongCu = hienCo?.chi_tiet.length || 0;
    if (soDongCu > validItems.length) {
      const ok = confirm(
        `Vị trí này đang có ${soDongCu} lĩnh vực, bạn chỉ giữ lại ${validItems.length}.\n\n`
        + `${soDongCu - validItems.length} lĩnh vực còn lại sẽ bị XÓA khỏi cấu trúc đề. Tiếp tục?`
      );
      if (!ok) return;
    }

    setSaving(true);
    setError(null);
    try {
      const res = await kyThiApi.upsertCauTrucDe(kyThi.id, {
        vi_tri_id: selectedViTri,
        cau_truc: validItems,
      });
      setData(res.data.data || []);
      setSelectedViTri('');
      setItems([]);
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi lưu cấu trúc đề');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteViTri = async (viTriId: string, viTriTen: string, soCau: number) => {
    if (!confirm(`Xóa toàn bộ cấu trúc đề của "${viTriTen}" (${soCau} câu)?`)) return;
    try {
      await kyThiApi.xoaCauTrucDe(kyThi.id, viTriId);
      setData(data.filter(d => d.vi_tri_id !== viTriId));
      if (selectedViTri === viTriId) { setSelectedViTri(''); setItems([]); }
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi xóa');
    }
  };

  const soOVuot = items.filter(i => i.linh_vuc_id).reduce((n, i) => {
    const cap: ['de' | 'trung_binh' | 'kho', number][] = [
      ['de', i.so_cau_de], ['trung_binh', i.so_cau_trung_binh], ['kho', i.so_cau_kho],
    ];
    return n + cap.filter(([dk, v]) => {
      const co = tonKho.lay(i.linh_vuc_id, dk);
      return co !== null && v > co;
    }).length;
  }, 0);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-3xl w-full max-h-[85vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-lg">Cấu trúc đề — {kyThi.ma_ky_thi}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        {error && <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">{error}</div>}
        {tplMsg && <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded text-green-700 text-sm">{tplMsg}</div>}

        {kyThi.trang_thai === 'DANG_MO' && (
          <div className="mb-3 p-2 bg-amber-50 border border-amber-200 rounded text-amber-800 text-sm">
            ⚠️ Kỳ thi <strong>đang mở</strong>. Chỉ sửa được cấu trúc của các vị trí <strong>chưa có thí sinh làm bài</strong> —
            vị trí đã có người thi sẽ bị hệ thống từ chối.
          </div>
        )}

        {/* Mau cau truc de: ap dung mau co san / luu cau truc hien tai thanh mau */}
        <div className="mb-4 p-3 bg-indigo-50/60 border border-indigo-100 rounded-lg">
          <div className="text-xs font-semibold text-gray-600 mb-2">📋 Mẫu cấu trúc đề</div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={selectedTpl}
              onChange={e => setSelectedTpl(e.target.value)}
              className="border rounded-lg px-2 py-1.5 text-sm min-w-[220px]"
            >
              <option value="">-- Chọn mẫu có sẵn --</option>
              {templates.map(t => (
                <option key={t.id} value={t.id}>
                  {t.ten_template} ({t.cau_truc.length} dòng)
                </option>
              ))}
            </select>
            <button
              onClick={handleApDungMau}
              disabled={!selectedTpl || tplBusy}
              className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {tplBusy ? 'Đang xử lý...' : 'Áp dụng mẫu'}
            </button>
            <span className="mx-1 text-gray-300">|</span>
            <input
              value={tenMau}
              onChange={e => setTenMau(e.target.value)}
              placeholder="Tên mẫu mới..."
              className="border rounded-lg px-2 py-1.5 text-sm w-44"
            />
            <button
              onClick={handleLuuThanhMau}
              disabled={!tenMau.trim() || data.length === 0 || tplBusy}
              className="px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              title={data.length === 0 ? 'Kỳ thi chưa có cấu trúc đề để lưu' : 'Lưu cấu trúc hiện tại thành mẫu'}
            >
              💾 Lưu thành mẫu
            </button>
          </div>
          <div className="mt-2 text-[11px] text-gray-500">
            Sửa/xóa mẫu tại tab <strong>Mẫu cấu trúc đề</strong>.
          </div>
        </div>

        {/* Cau truc hien tai */}
        {data.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-600 mb-2">Cấu trúc hiện tại:</h4>
            {data.map(vt => (
              <div
                key={vt.vi_tri_id}
                className={`border rounded-lg p-3 mb-2 ${selectedViTri === vt.vi_tri_id ? 'border-blue-400 bg-blue-50/40' : ''}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm">{vt.vi_tri_ten} — {vt.tong_cau} câu</span>
                  <div className="flex gap-3">
                    <button
                      onClick={() => handleChonViTri(vt.vi_tri_id)}
                      className="text-blue-600 text-xs hover:underline"
                    >
                      Sửa
                    </button>
                    <button
                      onClick={() => handleDeleteViTri(vt.vi_tri_id, vt.vi_tri_ten, vt.tong_cau)}
                      className="text-red-500 text-xs hover:underline"
                    >
                      Xóa
                    </button>
                  </div>
                </div>
                <div className="text-xs text-gray-500 space-y-1">
                  {vt.chi_tiet.map(ct => (
                    <div key={ct.id} className="flex gap-4">
                      <span className="w-40">{ct.linh_vuc_ten}</span>
                      <span>Dễ: {ct.so_cau_de}</span>
                      <span>TB: {ct.so_cau_trung_binh}</span>
                      <span>Khó: {ct.so_cau_kho}</span>
                      <span className="font-medium">= {(ct.so_cau_de || 0) + (ct.so_cau_trung_binh || 0) + (ct.so_cau_kho || 0)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Them cau truc */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-semibold text-gray-600 mb-3">Thêm/Cập nhật cấu trúc cho vị trí:</h4>
          <div className="mb-3">
            <select
              value={selectedViTri}
              onChange={e => handleChonViTri(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            >
              <option value="">-- Chọn vị trí --</option>
              {viTriList.map(vt => (
                <option key={vt.id} value={vt.id}>
                  {vt.ten_vi_tri}
                  {data.some(d => d.vi_tri_id === vt.id) ? ' (đã có cấu trúc)' : ''}
                </option>
              ))}
            </select>
          </div>

          {soOVuot > 0 && (
            <div className="mb-3 p-2 bg-amber-50 border border-amber-200 rounded text-amber-800 text-xs">
              ⚠️ {soOVuot} ô vượt quá số câu sẵn có trong ngân hàng (ô tô đỏ). Thí sinh sẽ không bắt đầu thi được
              cho tới khi bổ sung câu hỏi.
            </div>
          )}

          {items.map((item, idx) => (
            <div key={idx} className="grid grid-cols-5 gap-2 mb-2 items-end">
              <div>
                <label className="text-xs text-gray-500">Lĩnh vực</label>
                <select value={item.linh_vuc_id}
                  onChange={e => { const n = [...items]; n[idx].linh_vuc_id = e.target.value; setItems(n); }}
                  className="w-full border rounded px-2 py-1 text-sm">
                  <option value="">-- Chọn --</option>
                  {linhVucList.map(lv => (
                    <option
                      key={lv.id}
                      value={lv.id}
                      disabled={lv.id !== item.linh_vuc_id && items.some(x => x.linh_vuc_id === lv.id)}
                    >
                      {lv.ten_linh_vuc}
                    </option>
                  ))}
                </select>
              </div>
              <SoCauInput
                nhan="Dễ"
                value={item.so_cau_de}
                onChange={v => { const n = [...items]; n[idx].so_cau_de = v; setItems(n); }}
                tonKho={tonKho.lay(item.linh_vuc_id, 'de')}
              />
              <SoCauInput
                nhan="TB"
                value={item.so_cau_trung_binh}
                onChange={v => { const n = [...items]; n[idx].so_cau_trung_binh = v; setItems(n); }}
                tonKho={tonKho.lay(item.linh_vuc_id, 'trung_binh')}
              />
              <SoCauInput
                nhan="Khó"
                value={item.so_cau_kho}
                onChange={v => { const n = [...items]; n[idx].so_cau_kho = v; setItems(n); }}
                tonKho={tonKho.lay(item.linh_vuc_id, 'kho')}
              />
              <button onClick={() => setItems(items.filter((_, i) => i !== idx))} className="text-red-500 text-sm pb-1">Xóa</button>
            </div>
          ))}

          <div className="flex gap-2 mt-3">
            <button onClick={handleAddLinhVuc} className="px-3 py-1.5 text-xs border border-dashed border-gray-300 rounded-lg hover:bg-gray-50">
              + Thêm lĩnh vực
            </button>
            {items.length > 0 && (
              <>
                <button onClick={handleSave} disabled={saving}
                  className="px-4 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  {saving ? 'Đang lưu...' : 'Lưu cấu trúc'}
                </button>
                <button onClick={() => { setSelectedViTri(''); setItems([]); setError(null); }}
                  className="px-3 py-1.5 text-xs border rounded-lg hover:bg-gray-50">
                  Hủy
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// SuaKyThiModal — Sua thong tin ky thi
// =============================================================================

function SuaKyThiModal({ kyThi, onClose }: { kyThi: IKyThi; onClose: () => void }) {
  const toLocalDatetime = (iso: string) => {
    if (!iso) return '';
    const d = new Date(iso);
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  const [form, setForm] = useState({
    ma_ky_thi: kyThi.ma_ky_thi,
    ten_ky_thi: kyThi.ten_ky_thi,
    mo_ta: kyThi.mo_ta || '',
    ngay_bat_dau: toLocalDatetime(kyThi.ngay_bat_dau),
    ngay_ket_thuc: toLocalDatetime(kyThi.ngay_ket_thuc),
    thoi_gian_lam_bai_phut: kyThi.thoi_gian_lam_bai_phut,
    diem_dat: kyThi.diem_dat,
    so_lan_thi_toi_da: kyThi.so_lan_thi_toi_da,
    hien_dap_an: kyThi.hien_dap_an ?? false,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    if (!form.ten_ky_thi.trim() || !form.ngay_bat_dau || !form.ngay_ket_thuc) {
      setError('Vui lòng điền đầy đủ thông tin bắt buộc');
      return;
    }
    setSaving(true); setError(null);
    try {
      await kyThiApi.capNhat(kyThi.id, form);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi cập nhật kỳ thi');
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-lg">Sửa kỳ thi — {kyThi.ma_ky_thi}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        {error && <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">{error}</div>}

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mã kỳ thi</label>
              <input value={form.ma_ky_thi} onChange={e => setForm({...form, ma_ky_thi: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Điểm đạt (%)</label>
              <input type="number" value={form.diem_dat} onChange={e => setForm({...form, diem_dat: +e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tên kỳ thi *</label>
            <input value={form.ten_ky_thi} onChange={e => setForm({...form, ten_ky_thi: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả</label>
            <textarea value={form.mo_ta} onChange={e => setForm({...form, mo_ta: e.target.value})}
              rows={2} className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ngày bắt đầu *</label>
              <input type="datetime-local" value={form.ngay_bat_dau}
                onChange={e => setForm({...form, ngay_bat_dau: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ngày kết thúc *</label>
              <input type="datetime-local" value={form.ngay_ket_thuc}
                onChange={e => setForm({...form, ngay_ket_thuc: e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Thời gian làm bài (phút)</label>
              <input type="number" value={form.thoi_gian_lam_bai_phut}
                onChange={e => setForm({...form, thoi_gian_lam_bai_phut: +e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Số lần thi tối đa</label>
              <input type="number" value={form.so_lan_thi_toi_da}
                onChange={e => setForm({...form, so_lan_thi_toi_da: +e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={form.hien_dap_an}
              onChange={e => setForm({...form, hien_dap_an: e.target.checked})}
              className="w-4 h-4"
            />
            <span>Cho phép thí sinh xem chi tiết câu sai sau khi nộp bài</span>
          </label>
          <div className="flex gap-2 pt-2 border-t">
            <button onClick={handleSave} disabled={saving}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
            <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">Hủy</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// LinhVucTab — CRUD linh vuc
// =============================================================================

function LinhVucTab({ linhVucList, onReload }: { linhVucList: ILinhVuc[]; onReload: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState({ ma_linh_vuc: '', ten_linh_vuc: '', mo_ta: '', thu_tu: 0 });
  const [saving, setSaving] = useState(false);

  const resetForm = () => {
    setForm({ ma_linh_vuc: '', ten_linh_vuc: '', mo_ta: '', thu_tu: 0 });
    setEditId(null);
  };

  const handleEdit = (lv: ILinhVuc) => {
    setEditId(lv.id);
    setForm({ ma_linh_vuc: lv.ma_linh_vuc, ten_linh_vuc: lv.ten_linh_vuc, mo_ta: lv.mo_ta || '', thu_tu: lv.thu_tu });
    setError(null); setSuccess(null);
  };

  const handleSave = async () => {
    if (!form.ma_linh_vuc.trim() || !form.ten_linh_vuc.trim()) {
      setError('Mã và tên lĩnh vực không được để trống');
      return;
    }
    setSaving(true); setError(null); setSuccess(null);
    try {
      if (editId) {
        await linhVucApi.capNhat(editId, {
          ma_linh_vuc: form.ma_linh_vuc.trim(),
          ten_linh_vuc: form.ten_linh_vuc.trim(),
          mo_ta: form.mo_ta.trim() || null,
          thu_tu: form.thu_tu,
        });
        setSuccess('Cập nhật lĩnh vực thành công');
      } else {
        await linhVucApi.taoMoi({
          ma_linh_vuc: form.ma_linh_vuc.trim(),
          ten_linh_vuc: form.ten_linh_vuc.trim(),
          mo_ta: form.mo_ta.trim() || null,
          thu_tu: form.thu_tu,
        });
        setSuccess('Tạo lĩnh vực thành công');
      }
      resetForm();
      onReload();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi lưu lĩnh vực');
    } finally { setSaving(false); }
  };

  const handleDelete = async (lv: ILinhVuc) => {
    if (!confirm(`Xóa lĩnh vực "${lv.ten_linh_vuc}"?`)) return;
    setError(null); setSuccess(null);
    try {
      await linhVucApi.xoa(lv.id);
      setSuccess('Đã xóa lĩnh vực');
      onReload();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi xóa lĩnh vực');
    }
  };

  return (
    <div>
      {error && <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      {success && <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{success}</div>}

      {/* Form them/sua */}
      <div className="bg-white rounded-xl border p-4 mb-4">
        <h3 className="font-semibold text-gray-700 mb-3">
          {editId ? 'Sửa lĩnh vực' : 'Thêm lĩnh vực mới'}
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div>
            <label className="text-xs font-medium text-gray-600">Mã lĩnh vực *</label>
            <input value={form.ma_linh_vuc} onChange={e => setForm({...form, ma_linh_vuc: e.target.value})}
              placeholder="VD: CNTT" className="w-full border rounded-lg px-3 py-2 text-sm mt-1" />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600">Tên lĩnh vực *</label>
            <input value={form.ten_linh_vuc} onChange={e => setForm({...form, ten_linh_vuc: e.target.value})}
              placeholder="VD: Công nghệ thông tin" className="w-full border rounded-lg px-3 py-2 text-sm mt-1" />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600">Mô tả</label>
            <input value={form.mo_ta} onChange={e => setForm({...form, mo_ta: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm mt-1" />
          </div>
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <label className="text-xs font-medium text-gray-600">Thứ tự</label>
              <input type="number" value={form.thu_tu} onChange={e => setForm({...form, thu_tu: +e.target.value})}
                className="w-full border rounded-lg px-3 py-2 text-sm mt-1" />
            </div>
            <button onClick={handleSave} disabled={saving}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 disabled:opacity-50 whitespace-nowrap">
              {saving ? '...' : editId ? 'Cập nhật' : 'Thêm'}
            </button>
            {editId && (
              <button onClick={resetForm} className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">Hủy</button>
            )}
          </div>
        </div>
      </div>

      {/* Danh sach */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b text-left text-gray-500">
              <th className="py-2 px-3 w-12">TT</th>
              <th className="py-2 px-3">Mã</th>
              <th className="py-2 px-3">Tên lĩnh vực</th>
              <th className="py-2 px-3">Mô tả</th>
              <th className="py-2 px-3 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {linhVucList.length === 0 ? (
              <tr><td colSpan={5} className="py-8 text-center text-gray-400">Chưa có lĩnh vực nào</td></tr>
            ) : linhVucList.map(lv => (
              <tr key={lv.id} className={`border-b hover:bg-gray-50 ${editId === lv.id ? 'bg-purple-50' : ''}`}>
                <td className="py-2 px-3 text-gray-400">{lv.thu_tu}</td>
                <td className="py-2 px-3 font-mono text-xs">{lv.ma_linh_vuc}</td>
                <td className="py-2 px-3 font-medium">{lv.ten_linh_vuc}</td>
                <td className="py-2 px-3 text-gray-500 text-xs">{lv.mo_ta || '—'}</td>
                <td className="py-2 px-3 text-right">
                  <div className="flex gap-1 justify-end">
                    <button onClick={() => handleEdit(lv)}
                      className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200">Sửa</button>
                    <button onClick={() => handleDelete(lv)}
                      className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200">Xóa</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// =============================================================================
// GiaoThiSinhModal — Giao thi sinh cho ky thi
// =============================================================================

function GiaoThiSinhModal({ kyThi, viTriList, onClose }: {
  kyThi: IKyThi;
  viTriList: IViTriViecLam[];
  onClose: () => void;
}) {
  const [mode, setMode] = useState<'don-vi' | 'ca-nhan' | 'import-excel'>('don-vi');
  // Mode "Import Excel": file + ket qua import (loi tung dong)
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<any>(null);
  const [donViList, setDonViList] = useState<{ id: string; ten_don_vi: string }[]>([]);
  // Mode "Theo đơn vị": cong_chuc_ids cuối cùng (đã trừ người bỏ chọn) do picker tính.
  const [donViCongChucIds, setDonViCongChucIds] = useState<string[]>([]);
  const [donViPickerKey, setDonViPickerKey] = useState(0);
  const handleDonViChange = useCallback((ids: string[]) => setDonViCongChucIds(ids), []);
  const [selectedViTri, setSelectedViTri] = useState('');
  const [searchText, setSearchText] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [danhSach, setDanhSach] = useState<{ cong_chuc_id: string; vi_tri_id: string; ho_ten: string }[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  // Load existing thi sinh
  const [existingTS, setExistingTS] = useState<any[]>([]);
  const [loadingTS, setLoadingTS] = useState(true);

  useEffect(() => {
    const load = async () => {
      const [dvRes, tsRes] = await Promise.allSettled([
        cbccApi.getDonVi(),
        kyThiApi.danhSachThiSinhTatCa(kyThi.id),
      ]);
      if (dvRes.status === 'fulfilled') {
        setDonViList(dvRes.value.data.data || []);
      } else {
        console.error('getDonVi error:', dvRes.reason);
        setError('Không thể tải danh sách đơn vị');
      }
      if (tsRes.status === 'fulfilled') {
        setExistingTS(tsRes.value || []);
      }
      setLoadingTS(false);
    };
    load();
  }, [kyThi.id]);

  // Search CBCC
  const handleSearch = async () => {
    if (!searchText.trim()) return;
    try {
      const res = await cbccApi.searchCBCC({ q: searchText, page_size: 20 });
      setSearchResults(res.data.data || []);
    } catch { /* ignore */ }
  };

  const handleAddCBCC = (cc: any) => {
    if (danhSach.find(d => d.cong_chuc_id === cc.id)) return;
    if (!selectedViTri) { setError('Vui lòng chọn vị trí thi trước'); return; }
    setDanhSach([...danhSach, { cong_chuc_id: cc.id, vi_tri_id: selectedViTri, ho_ten: cc.ho_ten || cc.ma_cc }]);
    setError(null);
  };

  const handleRemove = (ccId: string) => {
    setDanhSach(danhSach.filter(d => d.cong_chuc_id !== ccId));
  };

  // Tai file Excel mau import thi sinh
  const handleDownloadMauImport = async () => {
    try {
      const res = await kyThiApi.downloadMauImportThiSinh(kyThi.id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'mau_import_thi_sinh.xlsx';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      setError('Lỗi tải file mẫu');
    }
  };

  const handleSubmit = async () => {
    setSaving(true); setError(null); setResult(null); setImportResult(null);
    try {
      // Mode Import Excel: upload file, vi tri chon chung tren form
      if (mode === 'import-excel') {
        if (!selectedViTri) { setError('Vui lòng chọn vị trí thi'); setSaving(false); return; }
        if (!importFile) { setError('Vui lòng chọn file Excel (.xlsx)'); setSaving(false); return; }
        const res = await kyThiApi.importThiSinhExcel(kyThi.id, selectedViTri, importFile);
        setImportResult(res.data.data);
        setImportFile(null);
        try {
          const tsAll = await kyThiApi.danhSachThiSinhTatCa(kyThi.id);
          setExistingTS(tsAll);
        } catch { /* reload fail khong anh huong */ }
        setSaving(false);
        return;
      }

      let body: any;
      if (mode === 'don-vi') {
        if (!selectedViTri || donViCongChucIds.length === 0) {
          setError('Vui lòng chọn vị trí thi và ít nhất 1 thí sinh');
          setSaving(false);
          return;
        }
        // Gửi danh_sach (đã trừ người bỏ chọn) thay vì don_vi_ids
        body = { danh_sach: donViCongChucIds.map(id => ({ cong_chuc_id: id, vi_tri_id: selectedViTri })) };
      } else {
        if (danhSach.length === 0) {
          setError('Vui lòng thêm ít nhất 1 thí sinh');
          setSaving(false);
          return;
        }
        body = { danh_sach: danhSach.map(d => ({ cong_chuc_id: d.cong_chuc_id, vi_tri_id: d.vi_tri_id })) };
      }
      const res = await kyThiApi.giaoThiSinh(kyThi.id, body);
      setResult(res.data.data);
      setDanhSach([]);
      setDonViCongChucIds([]);
      setDonViPickerKey(k => k + 1); // remount picker → xoá lựa chọn
      // Reload existing — tach rieng de khong ghi de ket qua thanh cong
      try {
        const tsAll = await kyThiApi.danhSachThiSinhTatCa(kyThi.id);
        setExistingTS(tsAll);
      } catch { /* reload fail khong anh huong */ }
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi giao thí sinh');
    } finally { setSaving(false); }
  };

  // Xoa thi sinh
  const handleDeleteTS = async (ccId: string) => {
    try {
      await kyThiApi.xoaThiSinh(kyThi.id, ccId);
      setExistingTS(existingTS.filter(t => t.cong_chuc_id !== ccId));
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Không thể xóa thí sinh');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-lg">Giao thí sinh — {kyThi.ten_ky_thi}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        {error && <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">{error}</div>}
        {result && (
          <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
            Thành công: {result.thanh_cong} | Bỏ qua (trùng): {result.bo_qua} | Tổng: {result.tong}
          </div>
        )}

        {/* Danh sach thi sinh hien tai */}
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">
            Thí sinh hiện tại ({existingTS.length})
          </h4>
          {loadingTS ? (
            <div className="text-xs text-gray-400">Đang tải...</div>
          ) : existingTS.length === 0 ? (
            <div className="text-xs text-gray-400 py-2">Chưa có thí sinh nào</div>
          ) : (
            <div className="max-h-40 overflow-y-auto border rounded-lg">
              <table className="w-full text-xs">
                <thead className="bg-gray-50 sticky top-0">
                  <tr className="text-gray-500">
                    <th className="py-1 px-2 text-left">Mã CC</th>
                    <th className="py-1 px-2 text-left">Họ tên</th>
                    <th className="py-1 px-2 text-left">Đơn vị</th>
                    <th className="py-1 px-2 text-left">Vị trí</th>
                    <th className="py-1 px-2 text-center">Trạng thái</th>
                    <th className="py-1 px-2 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {existingTS.map(ts => (
                    <tr key={ts.id} className="border-t">
                      <td className="py-1 px-2 font-mono">{ts.ma_cc}</td>
                      <td className="py-1 px-2">{ts.ho_ten}</td>
                      <td className="py-1 px-2 text-gray-500">{ts.don_vi_ten}</td>
                      <td className="py-1 px-2">{ts.vi_tri_ten}</td>
                      <td className="py-1 px-2 text-center">{ts.trang_thai}</td>
                      <td className="py-1 px-2 text-center">
                        {ts.trang_thai === 'CHUA_THI' && (
                          <button onClick={() => handleDeleteTS(ts.cong_chuc_id)} className="text-red-500 hover:underline">Xóa</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <hr className="mb-4" />

        {/* Mode switch */}
        <div className="flex gap-2 mb-4">
          <button onClick={() => setMode('don-vi')}
            className={`px-4 py-2 text-sm rounded-lg ${mode === 'don-vi' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
            Giao theo đơn vị
          </button>
          <button onClick={() => setMode('ca-nhan')}
            className={`px-4 py-2 text-sm rounded-lg ${mode === 'ca-nhan' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
            Giao từng người
          </button>
          <button onClick={() => setMode('import-excel')}
            className={`px-4 py-2 text-sm rounded-lg ${mode === 'import-excel' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
            📥 Import Excel
          </button>
        </div>

        {/* Vi tri chung */}
        <div className="mb-4">
          <label className="text-xs font-medium text-gray-600">Vị trí thi *</label>
          <select value={selectedViTri} onChange={e => setSelectedViTri(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm mt-1">
            <option value="">-- Chọn vị trí --</option>
            {viTriList.map(vt => <option key={vt.id} value={vt.id}>{vt.ten_vi_tri}</option>)}
          </select>
        </div>

        {/* Mode: don vi (accordion — bo chon tung nguoi) */}
        {mode === 'don-vi' && (
          <div className="mb-4">
            <label className="text-xs font-medium text-gray-600 block mb-1">
              Chọn đơn vị — tick để chọn sẵn toàn bộ, mở rộng để bỏ chọn từng người
            </label>
            <DonViCongChucPicker
              key={donViPickerKey}
              donVis={donViList}
              donViLoading={loadingTS}
              onChange={handleDonViChange}
            />
            <p className="text-[11px] text-gray-400 mt-1">
              Tất cả thí sinh đã chọn sẽ được giao vào vị trí thi chọn ở trên.
            </p>
          </div>
        )}

        {/* Mode: ca nhan */}
        {mode === 'ca-nhan' && (
          <div className="mb-4">
            <label className="text-xs font-medium text-gray-600">Tìm kiếm CBCC</label>
            <div className="flex gap-2 mt-1">
              <input value={searchText} onChange={e => setSearchText(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
                placeholder="Nhập tên hoặc mã CC..."
                className="flex-1 border rounded-lg px-3 py-2 text-sm" />
              <button onClick={handleSearch} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">Tìm</button>
            </div>

            {/* Search results */}
            {searchResults.length > 0 && (
              <div className="mt-2 border rounded-lg max-h-32 overflow-y-auto">
                {searchResults.map(cc => (
                  <div key={cc.id} className="flex items-center justify-between px-3 py-1.5 text-sm hover:bg-gray-50 border-b last:border-b-0">
                    <span>{cc.ma_cc} — {cc.ho_ten} ({cc.don_vi_ten || ''})</span>
                    <button onClick={() => handleAddCBCC(cc)} className="text-blue-600 text-xs hover:underline">Thêm</button>
                  </div>
                ))}
              </div>
            )}

            {/* Danh sach da chon */}
            {danhSach.length > 0 && (
              <div className="mt-3">
                <div className="text-xs font-medium text-gray-600 mb-1">Đã chọn ({danhSach.length}):</div>
                <div className="flex flex-wrap gap-1">
                  {danhSach.map(d => (
                    <span key={d.cong_chuc_id} className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                      {d.ho_ten}
                      <button onClick={() => handleRemove(d.cong_chuc_id)} className="text-blue-500 hover:text-red-500">&times;</button>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Mode: import Excel (file chi co cot ma_cc, vi tri chon chung o tren) */}
        {mode === 'import-excel' && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-gray-600">
                File Excel danh sách mã công chức (cột <code className="bg-gray-100 px-1 rounded">ma_cc</code>)
              </label>
              <button type="button" onClick={handleDownloadMauImport}
                className="text-xs text-blue-600 hover:underline">
                ⬇️ Tải file mẫu
              </button>
            </div>
            <input
              type="file"
              accept=".xlsx"
              onChange={e => { setImportFile(e.target.files?.[0] || null); setImportResult(null); }}
              className="w-full border rounded-lg px-3 py-2 text-sm file:mr-3 file:px-3 file:py-1 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700"
            />
            <p className="text-[11px] text-gray-400 mt-1">
              Tất cả mã CC trong file sẽ được giao vào vị trí thi chọn ở trên. Muốn giao nhiều
              vị trí khác nhau, hãy import nhiều lần (mỗi lần 1 vị trí).
            </p>

            {importResult && (
              <div className="mt-3">
                <div className={`p-2 rounded text-sm border ${importResult.that_bai > 0
                  ? 'bg-amber-50 border-amber-200 text-amber-800'
                  : 'bg-green-50 border-green-200 text-green-700'}`}>
                  Import xong: thành công <strong>{importResult.thanh_cong}</strong>/{importResult.tong}
                  {importResult.that_bai > 0 && <> — lỗi <strong>{importResult.that_bai}</strong> dòng</>}
                </div>
                {(importResult.loi_chi_tiet || []).length > 0 && (
                  <div className="mt-2 max-h-40 overflow-y-auto border rounded-lg">
                    <table className="w-full text-xs">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr className="text-gray-500">
                          <th className="py-1 px-2 text-left">Dòng</th>
                          <th className="py-1 px-2 text-left">Mã CC</th>
                          <th className="py-1 px-2 text-left">Lỗi</th>
                        </tr>
                      </thead>
                      <tbody>
                        {importResult.loi_chi_tiet.map((e: any, i: number) => (
                          <tr key={i} className="border-t">
                            <td className="py-1 px-2 text-gray-400">{e.dong}</td>
                            <td className="py-1 px-2 font-mono">{e.ma_cc}</td>
                            <td className="py-1 px-2 text-red-600">{e.loi}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-2 border-t">
          <button onClick={handleSubmit} disabled={saving}
            className="px-6 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 text-sm">
            {saving ? 'Đang xử lý...' : mode === 'import-excel' ? 'Import thí sinh' : 'Giao thí sinh'}
          </button>
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// NganHangDeTab — Quan ly ngan hang cau hoi DGNL
// =============================================================================

const DO_KHO_LABEL: Record<string, string> = { DE: 'Dễ', TRUNG_BINH: 'Trung bình', KHO: 'Khó' };
const LOAI_LABEL: Record<string, string> = { TRAC_NGHIEM_1: 'Trắc nghiệm 1', TRAC_NGHIEM_NHIEU: 'Trắc nghiệm nhiều', DUNG_SAI: 'Đúng/Sai', TU_LUAN: 'Tự luận' };

function NganHangDeTab({ linhVucList }: { linhVucList: ILinhVuc[] }) {
  const [thongKe, setThongKe] = useState<IThongKeNganHang[]>([]);
  const [cauHoiList, setCauHoiList] = useState<ICauHoiDgnl[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterLV, setFilterLV] = useState('');
  const [filterDK, setFilterDK] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [totalItems, setTotalItems] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Chon nhieu cau hoi de xoa hang loat
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);

  // Form tao cau hoi
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ linh_vuc_id: '', noi_dung: '', loai: 'TRAC_NGHIEM_1', do_kho: 'TRUNG_BINH', diem: '1', giai_thich: '',
    dap_an_a: '', dap_an_b: '', dap_an_c: '', dap_an_d: '', dap_an_dung: '' });
  const [saving, setSaving] = useState(false);

  // Import
  const [importing, setImporting] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [tkRes, chRes] = await Promise.all([
        nganHangDgnlApi.thongKe(),
        nganHangDgnlApi.danhSach({ linh_vuc_id: filterLV || undefined, do_kho: filterDK || undefined, page, page_size: 20 }),
      ]);
      setThongKe(tkRes.data.data || []);
      setCauHoiList(chRes.data.data || []);
      setTotalPages(chRes.data.pagination?.total_pages || 0);
      setTotalItems(chRes.data.pagination?.total_items || 0);
      setSelectedIds(new Set()); // reset lua chon moi khi tai lai danh sach
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [filterLV, filterDK, page]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleCreateCauHoi = async () => {
    if (!form.linh_vuc_id || !form.noi_dung.trim()) { setError('Vui lòng chọn lĩnh vực và nhập nội dung'); return; }
    setSaving(true); setError(null);
    try {
      const lua_chon = [
        form.dap_an_a && { key: 'A', noi_dung: form.dap_an_a },
        form.dap_an_b && { key: 'B', noi_dung: form.dap_an_b },
        form.dap_an_c && { key: 'C', noi_dung: form.dap_an_c },
        form.dap_an_d && { key: 'D', noi_dung: form.dap_an_d },
      ].filter(Boolean);

      let dap_an: any = {};
      if (form.loai === 'TRAC_NGHIEM_1') {
        dap_an = { lua_chon, dap_an_dung: form.dap_an_dung.trim().toUpperCase() };
      } else if (form.loai === 'TRAC_NGHIEM_NHIEU') {
        dap_an = { lua_chon, dap_an_dung: form.dap_an_dung.split(',').map(s => s.trim().toUpperCase()) };
      } else if (form.loai === 'DUNG_SAI') {
        dap_an = { lua_chon: [{ key: 'A', noi_dung: 'Đúng' }, { key: 'B', noi_dung: 'Sai' }], dap_an_dung: form.dap_an_dung.trim().toUpperCase() };
      } else {
        dap_an = { goi_y: form.dap_an_dung };
      }

      await nganHangDgnlApi.taoMoi({
        linh_vuc_id: form.linh_vuc_id,
        noi_dung: form.noi_dung.trim(),
        loai: form.loai, do_kho: form.do_kho,
        diem: Number(form.diem) || 1,
        dap_an,
        ...(form.giai_thich.trim() && { giai_thich: form.giai_thich.trim() }),
      });
      setSuccess('Tạo câu hỏi thành công!');
      setForm({ linh_vuc_id: '', noi_dung: '', loai: 'TRAC_NGHIEM_1', do_kho: 'TRUNG_BINH', diem: '1', giai_thich: '', dap_an_a: '', dap_an_b: '', dap_an_c: '', dap_an_d: '', dap_an_dung: '' });
      setShowForm(false);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi tạo câu hỏi');
    } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Xóa câu hỏi này?')) return;
    try {
      await nganHangDgnlApi.xoa(id);
      await loadData();
    } catch (err: any) { setError(err?.response?.data?.detail?.error?.message || 'Lỗi xóa'); }
  };

  // --- Chon nhieu ---
  const toggleOne = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const allPageSelected = cauHoiList.length > 0 && cauHoiList.every(ch => selectedIds.has(ch.id));

  const toggleAllPage = () => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (allPageSelected) {
        cauHoiList.forEach(ch => next.delete(ch.id));
      } else {
        cauHoiList.forEach(ch => next.add(ch.id));
      }
      return next;
    });
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`Xóa ${selectedIds.size} câu hỏi đã chọn?`)) return;
    setBulkDeleting(true); setError(null);
    try {
      const res = await nganHangDgnlApi.xoaNhieu({ ids: Array.from(selectedIds) });
      setSuccess(`Đã xóa ${res.data.data?.so_xoa ?? selectedIds.size} câu hỏi`);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi xóa hàng loạt');
    } finally { setBulkDeleting(false); }
  };

  const handleDeleteAllMatching = async () => {
    if (!filterLV && !filterDK) {
      setError('Vui lòng chọn Lĩnh vực hoặc Độ khó trước khi xóa tất cả câu khớp bộ lọc');
      return;
    }
    const tenLV = linhVucList.find(lv => lv.id === filterLV)?.ten_linh_vuc;
    const mota = [tenLV && `lĩnh vực "${tenLV}"`, filterDK && `độ khó ${DO_KHO_LABEL[filterDK]}`]
      .filter(Boolean).join(', ');
    if (!confirm(`Xóa TẤT CẢ ${totalItems} câu hỏi thuộc ${mota} (toàn bộ các trang)?\n\nThao tác này xóa mềm — không ảnh hưởng các bài thi đã diễn ra.`)) return;
    setBulkDeleting(true); setError(null);
    try {
      const res = await nganHangDgnlApi.xoaNhieu({
        tat_ca_theo_bo_loc: true,
        linh_vuc_id: filterLV || undefined,
        do_kho: filterDK || undefined,
      });
      setSuccess(`Đã xóa ${res.data.data?.so_xoa ?? 0} câu hỏi`);
      setPage(1);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi xóa hàng loạt');
    } finally { setBulkDeleting(false); }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true); setError(null);
    try {
      const res = await nganHangDgnlApi.importFile(file);
      const data = res.data.data;
      setSuccess(`Import hoàn tất: ${data.thanh_cong}/${data.tong} câu thành công`);
      if (data.loi_chi_tiet?.length > 0) {
        setError(`${data.that_bai} lỗi: ${data.loi_chi_tiet.map((l: any) => `Dòng ${l.dong}: ${l.loi}`).join('; ')}`);
      }
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail?.error?.message || 'Lỗi import');
    } finally { setImporting(false); e.target.value = ''; }
  };

  const handleDownloadMau = async () => {
    try {
      const res = await nganHangDgnlApi.downloadMau();
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url; a.download = 'mau_import_cau_hoi_dgnl.xlsx'; a.click();
      window.URL.revokeObjectURL(url);
    } catch { setError('Lỗi tải file mẫu'); }
  };

  if (loading) return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" /></div>;

  return (
    <div>
      {error && <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      {success && <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{success}</div>}

      {/* Thong ke */}
      <div className="bg-white rounded-xl border p-4 mb-4">
        <h3 className="font-semibold text-gray-700 mb-3">Thống kê ngân hàng câu hỏi</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="py-2 px-3">Lĩnh vực</th>
                <th className="py-2 px-3 text-center">Dễ</th>
                <th className="py-2 px-3 text-center">TB</th>
                <th className="py-2 px-3 text-center">Khó</th>
                <th className="py-2 px-3 text-center font-bold">Tổng</th>
              </tr>
            </thead>
            <tbody>
              {thongKe.map(tk => (
                <tr key={tk.linh_vuc_id} className="border-b hover:bg-gray-50">
                  <td className="py-2 px-3 font-medium">{tk.linh_vuc_ten}</td>
                  <td className="py-2 px-3 text-center">{tk.so_cau_de}</td>
                  <td className="py-2 px-3 text-center">{tk.so_cau_trung_binh}</td>
                  <td className="py-2 px-3 text-center">{tk.so_cau_kho}</td>
                  <td className="py-2 px-3 text-center font-bold">{tk.tong}</td>
                </tr>
              ))}
              <tr className="bg-gray-50 font-bold">
                <td className="py-2 px-3">Tổng cộng</td>
                <td className="py-2 px-3 text-center">{thongKe.reduce((s, t) => s + t.so_cau_de, 0)}</td>
                <td className="py-2 px-3 text-center">{thongKe.reduce((s, t) => s + t.so_cau_trung_binh, 0)}</td>
                <td className="py-2 px-3 text-center">{thongKe.reduce((s, t) => s + t.so_cau_kho, 0)}</td>
                <td className="py-2 px-3 text-center">{thongKe.reduce((s, t) => s + t.tong, 0)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex gap-2">
          <select value={filterLV} onChange={e => { setFilterLV(e.target.value); setPage(1); }}
            className="border rounded-lg px-3 py-2 text-sm">
            <option value="">Tất cả lĩnh vực</option>
            {linhVucList.map(lv => <option key={lv.id} value={lv.id}>{lv.ten_linh_vuc}</option>)}
          </select>
          <select value={filterDK} onChange={e => { setFilterDK(e.target.value); setPage(1); }}
            className="border rounded-lg px-3 py-2 text-sm">
            <option value="">Tất cả độ khó</option>
            <option value="DE">Dễ</option>
            <option value="TRUNG_BINH">Trung bình</option>
            <option value="KHO">Khó</option>
          </select>
        </div>
        <div className="flex gap-2">
          <button onClick={handleDownloadMau} className="px-3 py-2 text-xs border border-gray-300 rounded-lg hover:bg-gray-50">
            Tải file mẫu
          </button>
          <label className={`px-3 py-2 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 cursor-pointer ${importing ? 'opacity-50' : ''}`}>
            {importing ? 'Đang import...' : 'Import Excel'}
            <input type="file" accept=".xlsx,.csv" className="hidden" onChange={handleImport} disabled={importing} />
          </label>
          <button onClick={() => setShowForm(true)} className="px-3 py-2 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700">
            + Tạo câu hỏi
          </button>
        </div>
      </div>

      {/* Thanh thao tac hang loat */}
      {(selectedIds.size > 0 || ((filterLV || filterDK) && totalItems > 0)) && (
        <div className="flex items-center justify-between mb-3 p-2.5 bg-amber-50 border border-amber-200 rounded-lg flex-wrap gap-2">
          <span className="text-sm text-amber-800">
            {selectedIds.size > 0
              ? <>Đã chọn <b>{selectedIds.size}</b> câu hỏi</>
              : <>Đang lọc: <b>{totalItems}</b> câu hỏi khớp bộ lọc</>}
          </span>
          <div className="flex gap-2">
            {selectedIds.size > 0 && (
              <button onClick={handleDeleteSelected} disabled={bulkDeleting}
                className="px-3 py-1.5 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50">
                {bulkDeleting ? 'Đang xóa...' : `Xóa ${selectedIds.size} câu đã chọn`}
              </button>
            )}
            {(filterLV || filterDK) && totalItems > 0 && (
              <button onClick={handleDeleteAllMatching} disabled={bulkDeleting}
                className="px-3 py-1.5 text-xs border border-red-500 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50">
                Xóa tất cả {totalItems} câu khớp bộ lọc
              </button>
            )}
            {selectedIds.size > 0 && (
              <button onClick={() => setSelectedIds(new Set())} disabled={bulkDeleting}
                className="px-3 py-1.5 text-xs border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50">
                Bỏ chọn
              </button>
            )}
          </div>
        </div>
      )}

      {/* Danh sach cau hoi */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b text-left text-gray-500">
              <th className="py-2 px-3 w-8 text-center">
                <input type="checkbox" checked={allPageSelected} onChange={toggleAllPage}
                  title="Chọn tất cả câu hỏi trong trang" className="cursor-pointer" />
              </th>
              <th className="py-2 px-3 w-8">STT</th>
              <th className="py-2 px-3">Nội dung</th>
              <th className="py-2 px-3">Lĩnh vực</th>
              <th className="py-2 px-3 text-center">Loại</th>
              <th className="py-2 px-3 text-center">Độ khó</th>
              <th className="py-2 px-3 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {cauHoiList.length === 0 ? (
              <tr><td colSpan={7} className="py-8 text-center text-gray-400">Chưa có câu hỏi nào</td></tr>
            ) : cauHoiList.map((ch, idx) => (
              <tr key={ch.id} className={`border-b hover:bg-gray-50 ${selectedIds.has(ch.id) ? 'bg-amber-50' : ''}`}>
                <td className="py-2 px-3 text-center">
                  <input type="checkbox" checked={selectedIds.has(ch.id)} onChange={() => toggleOne(ch.id)}
                    className="cursor-pointer" />
                </td>
                <td className="py-2 px-3 text-gray-400">{(page - 1) * 20 + idx + 1}</td>
                <td className="py-2 px-3 max-w-xs truncate" dangerouslySetInnerHTML={{ __html: ch.noi_dung }} />
                <td className="py-2 px-3 text-xs">{ch.linh_vuc_ten}</td>
                <td className="py-2 px-3 text-center text-xs">{LOAI_LABEL[ch.loai] || ch.loai}</td>
                <td className="py-2 px-3 text-center">
                  <span className={`px-2 py-0.5 rounded-full text-xs ${
                    ch.do_kho === 'DE' ? 'bg-green-100 text-green-700' :
                    ch.do_kho === 'KHO' ? 'bg-red-100 text-red-600' : 'bg-yellow-100 text-yellow-700'
                  }`}>{DO_KHO_LABEL[ch.do_kho] || ch.do_kho}</span>
                </td>
                <td className="py-2 px-3 text-right">
                  <button onClick={() => handleDelete(ch.id)} className="text-red-500 text-xs hover:underline">Xóa</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 p-3 border-t">
            <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
              className="px-3 py-1 text-xs border rounded hover:bg-gray-50 disabled:opacity-30">Trước</button>
            <span className="text-xs text-gray-500">Trang {page}/{totalPages}</span>
            <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages}
              className="px-3 py-1 text-xs border rounded hover:bg-gray-50 disabled:opacity-30">Tiếp</button>
          </div>
        )}
      </div>

      {/* Form tao cau hoi modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg">Tạo câu hỏi ĐGNL</h3>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-600">Lĩnh vực *</label>
                  <select value={form.linh_vuc_id} onChange={e => setForm({...form, linh_vuc_id: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2 text-sm">
                    <option value="">-- Chọn --</option>
                    {linhVucList.map(lv => <option key={lv.id} value={lv.id}>{lv.ten_linh_vuc}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-xs font-medium text-gray-600">Loại</label>
                    <select value={form.loai} onChange={e => setForm({...form, loai: e.target.value})}
                      className="w-full border rounded px-2 py-2 text-sm">
                      {Object.entries(LOAI_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600">Độ khó</label>
                    <select value={form.do_kho} onChange={e => setForm({...form, do_kho: e.target.value})}
                      className="w-full border rounded px-2 py-2 text-sm">
                      {Object.entries(DO_KHO_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600">Điểm</label>
                    <input type="number" value={form.diem} onChange={e => setForm({...form, diem: e.target.value})}
                      className="w-full border rounded px-2 py-2 text-sm" />
                  </div>
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600">Nội dung câu hỏi *</label>
                <textarea value={form.noi_dung} onChange={e => setForm({...form, noi_dung: e.target.value})}
                  rows={3} className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
              {(form.loai === 'TRAC_NGHIEM_1' || form.loai === 'TRAC_NGHIEM_NHIEU') && (
                <div className="grid grid-cols-2 gap-2">
                  {['A', 'B', 'C', 'D'].map(k => (
                    <div key={k}>
                      <label className="text-xs text-gray-500">Đáp án {k}</label>
                      <input value={(form as any)[`dap_an_${k.toLowerCase()}`]}
                        onChange={e => setForm({...form, [`dap_an_${k.toLowerCase()}`]: e.target.value})}
                        className="w-full border rounded px-2 py-1.5 text-sm" />
                    </div>
                  ))}
                </div>
              )}
              <div>
                <label className="text-xs font-medium text-gray-600">
                  Đáp án đúng * {form.loai === 'TRAC_NGHIEM_NHIEU' ? '(VD: A,C)' : '(VD: A)'}
                </label>
                <input value={form.dap_an_dung} onChange={e => setForm({...form, dap_an_dung: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600">Giải thích</label>
                <textarea value={form.giai_thich} onChange={e => setForm({...form, giai_thich: e.target.value})}
                  rows={2} className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
              <button onClick={handleCreateCauHoi} disabled={saving}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50">
                {saving ? 'Đang tạo...' : 'Tạo câu hỏi'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

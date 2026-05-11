/**
 * src/app/(main)/danh-gia/tu-cham-diem/page.tsx
 * ==============================================
 * Trang Tự đánh giá Tiêu chí chung (30 điểm).
 * 
 * ĐỒNG BỘ VỚI BACKEND v2.5.0
 * 
 * ⚠️ FIX v2.5.4:
 * - Master Data trả về { nhom_1, nhom_2, nhom_3 } - đã merge trong service
 * - Form state dùng ma_tieu_chi làm key
 * - POST dùng ma_tieu_chi, KHÔNG phải tieu_chi_id
 *
 * Version: 2.5.4 (27/01/2026)
 */

'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { tieuChiChungService, INguoiPheDuyet } from '@/services/tieu-chi-chung.service';
import { isApiError } from '@/lib/axios';
import {
  ITieuChiChungMaster,
  IKetQuaTieuChiChungResponse,
  ITieuChiFormState,
  ITieuChiGhiChu,
  TrangThaiTieuChiChung,
  getTrangThaiLabel,
  getTrangThaiBadgeClass,
  tinhDiemTuFormState,
  initFormStateFromResponse,
  initGhiChuFromResponse,
  convertFormToPayload,
} from '@/types/tieu-chi-chung';

import { formatScore } from '@/lib/format';
export default function TuChamDiemPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  const [masterData, setMasterData] = useState<ITieuChiChungMaster[]>([]);
  const [ketQua, setKetQua] = useState<IKetQuaTieuChiChungResponse | null>(null);
  const [nguoiPheDuyetList, setNguoiPheDuyetList] = useState<INguoiPheDuyet[]>([]);
  const [autoApprove, setAutoApprove] = useState(false);
  const [ghiChuNguoiPheDuyet, setGhiChuNguoiPheDuyet] = useState<string | null>(null);
  
  const currentDate = new Date();
  const [selectedThang, setSelectedThang] = useState(currentDate.getMonth() + 1);
  const [selectedNam, setSelectedNam] = useState(currentDate.getFullYear());
  
  const [formState, setFormState] = useState<ITieuChiFormState>({});
  const [ghiChu, setGhiChu] = useState<ITieuChiGhiChu>({});
  const [selectedNguoiPheDuyet, setSelectedNguoiPheDuyet] = useState<string>('');
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) router.push('/login');
  }, [isAuthenticated, router]);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    
    console.log('==========================================');
    console.log('[TuChamDiem] Starting loadData');
    console.log('==========================================');

    // 1. Load Master Data (10 tiêu chí lớn, merged từ nhom_1 + nhom_2 + nhom_3)
    let master: ITieuChiChungMaster[] = [];
    try {
      console.log('[TuChamDiem] Step 1: Calling getMasterData...');
      master = await tieuChiChungService.getMasterData();
      console.log('[TuChamDiem] getMasterData returned:', master.length, 'items');
      
      if (master.length === 0) {
        setLoadError('Không tải được danh mục tiêu chí. Vui lòng thử lại.');
      }
      
      setMasterData(master);
    } catch (err: unknown) {
      console.error('[TuChamDiem] getMasterData ERROR:', err);
      setLoadError('Lỗi khi tải danh mục tiêu chí.');
    }

    // 2. Load kết quả tháng (Virtual Record support)
    let response: IKetQuaTieuChiChungResponse | null = null;
    try {
      console.log('[TuChamDiem] Step 2: Calling getKetQuaThang...');
      response = await tieuChiChungService.getKetQuaThang(selectedThang, selectedNam);
      console.log('[TuChamDiem] getKetQuaThang returned:', response);
      setKetQua(response);
    } catch (err: unknown) {
      console.warn('[TuChamDiem] getKetQuaThang error:', err);
    }

    // 3. Init form state
    console.log('[TuChamDiem] Step 3: Initializing form state...');
    if (master.length > 0) {
      const newFormState = initFormStateFromResponse(response, master);
      const newGhiChu = initGhiChuFromResponse(response);
      console.log('[TuChamDiem] Form state initialized:', newFormState);
      setFormState(newFormState);
      setGhiChu(newGhiChu);
      if (response?.nguoi_phe_duyet_id) {
        setSelectedNguoiPheDuyet(response.nguoi_phe_duyet_id);
      }
    }

    // 4. Load người phê duyệt
    try {
      console.log('[TuChamDiem] Step 4: Calling getNguoiPheDuyet...');
      const result = await tieuChiChungService.getNguoiPheDuyet();
      console.log('[TuChamDiem] getNguoiPheDuyet returned:', result);
      setNguoiPheDuyetList(result.nguoiPheDuyet);
      setAutoApprove(result.autoApprove);
      setGhiChuNguoiPheDuyet(result.ghiChu);
      if (result.nguoiPheDuyet.length === 1) {
        setSelectedNguoiPheDuyet(result.nguoiPheDuyet[0].id);
      }
    } catch (err: unknown) {
      console.error('[TuChamDiem] getNguoiPheDuyet ERROR:', err);
    }

    console.log('==========================================');
    console.log('[TuChamDiem] loadData COMPLETED');
    console.log('==========================================');
    setIsLoading(false);
  }, [selectedThang, selectedNam]);

  useEffect(() => { loadData(); }, [loadData]);

  // Tính điểm preview
  const diemPreview = useMemo(() => {
    if (masterData.length === 0) {
      return { nhom_1_diem: 0, nhom_2_diem: 0, nhom_3_diem: 0, tong_diem: 0 };
    }
    return tinhDiemTuFormState(masterData, formState);
  }, [masterData, formState]);

  const trangThai = ketQua?.trang_thai || TrangThaiTieuChiChung.CHUA_DANH_GIA;
  const isNewRecord = ketQua?.is_new_record ?? true;
  
  // Check if deadline has passed for this month
  const isDeadlinePassed = useMemo(() => {
    const today = new Date();
    const todayMonth = today.getMonth() + 1;
    const todayYear = today.getFullYear();
    const todayDay = today.getDate();

    // NỚI HẠN TẠM THỜI (2026-04-21): cho phép mọi tháng ≥ 2026-01 đến hết
    // 2026-05-31 để CC bổ sung các tháng còn thiếu. Đồng bộ với backend
    // kiem_tra_thoi_han_tu_danh_gia.
    const HAN_MO_RONG_TAM_THOI_DEN = new Date(2026, 4, 31); // tháng 5 index = 4
    const MO_RONG_TU_NAM = 2026;
    const MO_RONG_TU_THANG = 1;
    if (today <= HAN_MO_RONG_TAM_THOI_DEN) {
      const afterStart =
        selectedNam > MO_RONG_TU_NAM ||
        (selectedNam === MO_RONG_TU_NAM && selectedThang >= MO_RONG_TU_THANG);
      const notFuture =
        selectedNam < todayYear ||
        (selectedNam === todayYear && selectedThang <= todayMonth);
      if (afterStart && notFuture) return false;
    }

    // Current month: always OK
    if (selectedThang === todayMonth && selectedNam === todayYear) return false;

    // Previous month: OK if day <= 10 (business rule: trước ngày 10 tháng sau)
    let prevMonth = todayMonth === 1 ? 12 : todayMonth - 1;
    let prevYear = todayMonth === 1 ? todayYear - 1 : todayYear;
    if (selectedThang === prevMonth && selectedNam === prevYear && todayDay <= 30) return false;

    // All other months: deadline passed
    return true;
  }, [selectedThang, selectedNam]);
  
  const isStatusLocked = trangThai === TrangThaiTieuChiChung.CHO_PHE_DUYET 
    || trangThai === TrangThaiTieuChiChung.DA_PHE_DUYET
    || trangThai === 'CHO_CAP2' as TrangThaiTieuChiChung;
  const isDisabled = isStatusLocked || isDeadlinePassed;

  const handleDiemChange = (maTieuChi: string, diem: number) => {
    setFormState((prev: ITieuChiFormState) => ({
      ...prev,
      [maTieuChi]: diem,
    }));
  };

  // Sanitize input → cap 0..max, làm tròn về bội số 0.5.
  const sanitizeDiem = (raw: string, max: number): number => {
    if (raw === '') return 0;
    let n = Number(raw);
    if (!Number.isFinite(n)) return 0;
    if (n < 0) n = 0;
    if (n > max) n = max;
    return Math.round(n * 2) / 2;
  };

  const handleGhiChuChange = (maTieuChi: string, value: string) => {
    setGhiChu((prev: ITieuChiGhiChu) => ({
      ...prev,
      [maTieuChi]: value,
    }));
  };

  const handleSaveDraft = async () => {
    if (isDisabled || masterData.length === 0) return;
    
    setIsSaving(true);
    try {
      const payload = convertFormToPayload(masterData, formState, ghiChu);
      console.log('[TuChamDiem] Save draft payload:', payload);
      
      await tieuChiChungService.luuNhap({ 
        thang: selectedThang, 
        nam: selectedNam, 
        tieu_chi: payload 
      });
      setSuccessMessage('Đã lưu nháp thành công!');
      setShowSuccessModal(true);
      loadData();
    } catch (err: unknown) {
      console.error('[TuChamDiem] Save draft error:', err);
      if (isApiError(err)) {
        const errMsg = err.message || '';
        if (errMsg.includes('BIZ_004') || errMsg.includes('hết hạn')) {
          alert('Đã hết hạn tự đánh giá tháng này. Thời hạn: trước ngày 10 tháng sau.');
        } else {
          alert('Lỗi: ' + errMsg);
        }
      } else {
        alert('Có lỗi xảy ra');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleSubmitForApproval = async () => {
    if (isDisabled || masterData.length === 0) return;
    
    if (!autoApprove && !selectedNguoiPheDuyet) {
      alert('Vui lòng chọn người phê duyệt!');
      return;
    }
    
    // Validate Nhóm 3: cần có ghi chú nếu CC chấm điểm > 0
    const nhom3 = masterData.filter((tc: ITieuChiChungMaster) => tc.nhom_tieu_chi === 3);
    for (const tc of nhom3) {
      const diem = formState[tc.ma_tieu_chi] ?? 0;
      if (diem > 0 && !ghiChu[tc.ma_tieu_chi]?.trim()) {
        alert(`Tiêu chí ${tc.ma_tieu_chi} (${tc.ten_tieu_chi}) đã chấm ${diem} điểm nhưng chưa có minh chứng!`);
        return;
      }
    }
    
    setIsSubmitting(true);
    try {
      const payload = convertFormToPayload(masterData, formState, ghiChu);
      console.log('[TuChamDiem] Submit payload:', payload);
      
      await tieuChiChungService.luuVaGuiPheDuyet({
        thang: selectedThang, 
        nam: selectedNam,
        tieu_chi: payload,
        nguoi_phe_duyet_id: autoApprove ? user?.id || '' : selectedNguoiPheDuyet,
      });
      setSuccessMessage(autoApprove ? 'Đã tự động phê duyệt!' : 'Đã gửi phê duyệt!');
      setShowSuccessModal(true);
      loadData();
    } catch (err: unknown) {
      console.error('[TuChamDiem] Submit error:', err);
      if (isApiError(err)) {
        const errMsg = err.message || '';
        if (errMsg.includes('BIZ_004') || errMsg.includes('hết hạn')) {
          alert('Đã hết hạn tự đánh giá tháng này. Thời hạn: trước ngày 10 tháng sau.');
        } else {
          alert('Lỗi: ' + errMsg);
        }
      } else {
        alert('Có lỗi xảy ra');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Group master data by nhom
  const nhom1 = masterData.filter((tc: ITieuChiChungMaster) => tc.nhom_tieu_chi === 1);
  const nhom2 = masterData.filter((tc: ITieuChiChungMaster) => tc.nhom_tieu_chi === 2);
  const nhom3 = masterData.filter((tc: ITieuChiChungMaster) => tc.nhom_tieu_chi === 3);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Đang tải dữ liệu...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
      {/* Header với nút Quay lại */}
      <div className="mb-6">
        <button
          onClick={() => router.push('/dashboard')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 group"
        >
          <svg className="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Quay lại Dashboard</span>
        </button>
        
        <h1 className="text-2xl font-bold text-gray-900">Tự chấm điểm Tiêu chí chung</h1>
        <p className="text-gray-600 mt-1">Đánh giá 30 điểm tiêu chí chung hàng tháng</p>
      </div>

      {/* Error Banner */}
      {loadError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2">
            <span className="text-red-600">⚠️</span>
            <span className="text-red-800">{loadError}</span>
            <button onClick={loadData} className="ml-auto text-red-600 hover:text-red-800 underline text-sm">
              Thử lại
            </button>
          </div>
        </div>
      )}

      {/* Filter & Status */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tháng</label>
              <select value={selectedThang} onChange={(e) => setSelectedThang(Number(e.target.value))}
                className="border border-gray-300 rounded-md px-3 py-2">
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m: number) => (
                  <option key={m} value={m}>Tháng {m}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Năm</label>
              <select value={selectedNam} onChange={(e) => setSelectedNam(Number(e.target.value))}
                className="border border-gray-300 rounded-md px-3 py-2">
                {[2025, 2026, 2027].map((y: number) => (<option key={y} value={y}>{y}</option>))}
              </select>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="text-sm text-gray-500">Trạng thái:</span>
              <span className={`ml-2 px-3 py-1 rounded-full text-sm font-medium border ${getTrangThaiBadgeClass(trangThai)}`}>
                {getTrangThaiLabel(trangThai)}
              </span>
            </div>
            <div className="text-right">
              <span className="text-sm text-gray-500">Điểm:</span>
              <span className="ml-2 text-2xl font-bold text-blue-600">{formatScore(diemPreview.tong_diem)}/30</span>
            </div>
          </div>
        </div>

        {ketQua && (
          <div className="mt-4 pt-4 border-t border-gray-200 flex flex-wrap gap-4 text-sm text-gray-600">
            <span>📅 Ngày trong tháng: <strong>{ketQua.so_ngay_trong_thang}</strong></span>
            <span>🏖️ Nghỉ phép: <strong>{ketQua.so_ngay_nghi_phep}</strong></span>
            <span>💼 Làm việc: <strong>{ketQua.so_ngay_lam_viec}</strong></span>
            <span>🎯 Target: <strong>{ketQua.target_kpi}</strong> điểm</span>
          </div>
        )}

        {isNewRecord && !isDeadlinePassed && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-800">
              📝 <strong>Chưa có đánh giá.</strong> Điền form và nhấn Lưu nháp hoặc Gửi phê duyệt.
            </p>
          </div>
        )}

        {isDeadlinePassed && !isStatusLocked && (
          <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-md">
            <p className="text-sm text-orange-800">
              ⏰ <strong>Đã hết hạn tự đánh giá tháng {selectedThang}/{selectedNam}.</strong> Thời hạn: trước ngày 10 tháng sau. Vui lòng liên hệ lãnh đạo nếu cần điều chỉnh.
            </p>
          </div>
        )}

        {/* Banner LĐ TỪ CHỐI / TRẢ LẠI — hiển thị rõ lý do để CC biết phải sửa gì */}
        {ketQua?.ly_do_tu_choi_tc && (() => {
          const raw = ketQua.ly_do_tu_choi_tc;
          const isTraLai = raw.startsWith('[TRẢ LẠI]');
          const noiDung = raw.replace(/^\[TRẢ LẠI\]\s*/, '');
          return (
            <div className={`mt-4 rounded-lg border-l-4 p-4 ${
              isTraLai
                ? 'bg-orange-50 border-orange-500'
                : 'bg-red-50 border-red-500'
            }`}>
              <div className="flex items-start gap-3">
                <span className={`text-2xl leading-none ${isTraLai ? 'text-orange-600' : 'text-red-600'}`}>
                  {isTraLai ? '↩' : '✕'}
                </span>
                <div className="flex-1 min-w-0">
                  <p className={`font-semibold mb-1 ${isTraLai ? 'text-orange-800' : 'text-red-800'}`}>
                    {isTraLai
                      ? 'Lãnh đạo đã trả lại bản tự chấm điểm — vui lòng chỉnh sửa và gửi duyệt lại'
                      : 'Lãnh đạo đã từ chối bản tự chấm điểm — vui lòng kê khai lại'}
                  </p>
                  <p className={`text-sm whitespace-pre-wrap ${isTraLai ? 'text-orange-700' : 'text-red-700'}`}>
                    <strong>Lý do:</strong> {noiDung}
                  </p>
                  {ketQua.ngay_tu_choi_tc && (
                    <p className={`text-xs mt-1 ${isTraLai ? 'text-orange-600' : 'text-red-600'}`}>
                      Ngày: {new Date(ketQua.ngay_tu_choi_tc).toLocaleString('vi-VN')}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })()}
      </div>

      {/* Score Preview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-emerald-500">
          <div className="text-sm text-gray-500">Nhóm 1 - Phẩm chất chính trị</div>
          <div className="text-xl font-bold text-emerald-600">{formatScore(diemPreview.nhom_1_diem)}/10</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-sky-500">
          <div className="text-sm text-gray-500">Nhóm 2 - Năng lực chuyên môn</div>
          <div className="text-xl font-bold text-sky-600">{formatScore(diemPreview.nhom_2_diem)}/10</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-amber-500">
          <div className="text-sm text-gray-500">Nhóm 3 - Năng lực đổi mới</div>
          <div className="text-xl font-bold text-amber-600">{formatScore(diemPreview.nhom_3_diem)}/10</div>
        </div>
      </div>

      {/* Form - Nhóm 1 */}
      {nhom1.length > 0 && (
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="p-4 bg-emerald-50 border-b border-emerald-200 rounded-t-lg">
            <h3 className="font-semibold text-emerald-800">
              Nhóm I: Phẩm chất chính trị, đạo đức
              <span className="ml-2 text-sm font-normal">(Mặc định full điểm, giảm khi vi phạm — bội số 0.5)</span>
            </h3>
          </div>
          <div className="p-4 space-y-4">
            {nhom1.map((tc: ITieuChiChungMaster) => {
              const diem = formState[tc.ma_tieu_chi] ?? (tc.gia_tri_mac_dinh ? tc.diem_toi_da : 0);
              return (
                <div key={tc.ma_tieu_chi} className="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg">
                  <div className="flex flex-col items-center pt-0.5">
                    <input
                      type="number"
                      id={tc.ma_tieu_chi}
                      min={0}
                      max={tc.diem_toi_da}
                      step={0.5}
                      value={Number.isFinite(diem) ? diem : 0}
                      onChange={(e) => handleDiemChange(tc.ma_tieu_chi, sanitizeDiem(e.target.value, tc.diem_toi_da))}
                      disabled={isDisabled}
                      className="w-20 px-2 py-1.5 text-center font-semibold border-2 border-emerald-300 rounded focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-gray-50"
                    />
                    <span className="text-[11px] text-gray-500 mt-0.5">/ {tc.diem_toi_da}</span>
                  </div>
                  <label htmlFor={tc.ma_tieu_chi} className="flex-1 cursor-pointer">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">TC {tc.ma_tieu_chi}</span>
                      <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">
                        Tối đa {tc.diem_toi_da} điểm
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{tc.ten_tieu_chi}</p>
                  </label>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Form - Nhóm 2 */}
      {nhom2.length > 0 && (
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="p-4 bg-sky-50 border-b border-sky-200 rounded-t-lg">
            <h3 className="font-semibold text-sky-800">
              Nhóm II: Năng lực chuyên môn, nghiệp vụ
              <span className="ml-2 text-sm font-normal">(Mặc định full điểm, giảm khi vi phạm — bội số 0.5)</span>
            </h3>
          </div>
          <div className="p-4 space-y-4">
            {nhom2.map((tc: ITieuChiChungMaster) => {
              const diem = formState[tc.ma_tieu_chi] ?? (tc.gia_tri_mac_dinh ? tc.diem_toi_da : 0);
              return (
                <div key={tc.ma_tieu_chi} className="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg">
                  <div className="flex flex-col items-center pt-0.5">
                    <input
                      type="number"
                      id={tc.ma_tieu_chi}
                      min={0}
                      max={tc.diem_toi_da}
                      step={0.5}
                      value={Number.isFinite(diem) ? diem : 0}
                      onChange={(e) => handleDiemChange(tc.ma_tieu_chi, sanitizeDiem(e.target.value, tc.diem_toi_da))}
                      disabled={isDisabled}
                      className="w-20 px-2 py-1.5 text-center font-semibold border-2 border-sky-300 rounded focus:outline-none focus:ring-2 focus:ring-sky-500 disabled:bg-gray-50"
                    />
                    <span className="text-[11px] text-gray-500 mt-0.5">/ {tc.diem_toi_da}</span>
                  </div>
                  <label htmlFor={tc.ma_tieu_chi} className="flex-1 cursor-pointer">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">TC {tc.ma_tieu_chi}</span>
                      <span className="text-xs bg-sky-100 text-sky-700 px-2 py-0.5 rounded">
                        Tối đa {tc.diem_toi_da} điểm
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{tc.ten_tieu_chi}</p>
                  </label>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Form - Nhóm 3 */}
      {nhom3.length > 0 && (
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="p-4 bg-amber-50 border-b border-amber-200 rounded-t-lg">
            <h3 className="font-semibold text-amber-800">
              Nhóm III: Năng lực đổi mới, sáng tạo
              <span className="ml-2 text-sm font-normal">(Mặc định 0 — nhập điểm khi có thành tích, cần minh chứng)</span>
            </h3>
          </div>
          <div className="p-4 space-y-4">
            {nhom3.map((tc: ITieuChiChungMaster) => {
              const diem = formState[tc.ma_tieu_chi] ?? (tc.gia_tri_mac_dinh ? tc.diem_toi_da : 0);
              return (
                <div key={tc.ma_tieu_chi} className="p-3 hover:bg-gray-50 rounded-lg">
                  <div className="flex items-start gap-3">
                    <div className="flex flex-col items-center pt-0.5">
                      <input
                        type="number"
                        id={tc.ma_tieu_chi}
                        min={0}
                        max={tc.diem_toi_da}
                        step={0.5}
                        value={Number.isFinite(diem) ? diem : 0}
                        onChange={(e) => handleDiemChange(tc.ma_tieu_chi, sanitizeDiem(e.target.value, tc.diem_toi_da))}
                        disabled={isDisabled}
                        className="w-20 px-2 py-1.5 text-center font-semibold border-2 border-amber-300 rounded focus:outline-none focus:ring-2 focus:ring-amber-500 disabled:bg-gray-50"
                      />
                      <span className="text-[11px] text-gray-500 mt-0.5">/ {tc.diem_toi_da}</span>
                    </div>
                    <label htmlFor={tc.ma_tieu_chi} className="flex-1 cursor-pointer">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">TC {tc.ma_tieu_chi}</span>
                        <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded">
                          Tối đa {tc.diem_toi_da} điểm
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{tc.ten_tieu_chi}</p>
                    </label>
                  </div>
                  {diem > 0 && (
                    <div className="mt-3 ml-[5.25rem]">
                      <textarea
                        placeholder="Nhập minh chứng thành tích..."
                        value={ghiChu[tc.ma_tieu_chi] || ''}
                        onChange={(e) => {
                          if (e.target.value.length <= 2000) {
                            handleGhiChuChange(tc.ma_tieu_chi, e.target.value);
                          }
                        }}
                        disabled={isDisabled}
                        rows={2}
                        maxLength={2000}
                        className={`w-full border rounded-md px-3 py-2 text-sm focus:ring-amber-500 focus:border-amber-500 ${
                          (ghiChu[tc.ma_tieu_chi]?.length || 0) > 1800 ? 'border-red-300' : 'border-amber-300'
                        }`}
                      />
                      <div className="flex justify-end mt-1">
                        <span className={`text-xs ${
                          (ghiChu[tc.ma_tieu_chi]?.length || 0) > 1800
                            ? 'text-red-500 font-medium'
                            : 'text-gray-400'
                        }`}>
                          {ghiChu[tc.ma_tieu_chi]?.length || 0}/2000
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Empty state */}
      {masterData.length === 0 && !loadError && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <p className="text-yellow-800">⚠️ Không có dữ liệu tiêu chí để hiển thị.</p>
          <button onClick={loadData} className="mt-3 px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700">
            Tải lại dữ liệu
          </button>
        </div>
      )}

      {/* Approval Section */}
      {!isDisabled && masterData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4 mt-6">
          <h3 className="font-medium text-gray-900 mb-4">Gửi phê duyệt</h3>
          
          {!autoApprove && nguoiPheDuyetList.length > 0 && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Chọn người phê duyệt</label>
              <select value={selectedNguoiPheDuyet} onChange={(e) => setSelectedNguoiPheDuyet(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2">
                <option value="">-- Chọn người phê duyệt --</option>
                {nguoiPheDuyetList.map((nguoi: INguoiPheDuyet) => (
                  <option key={nguoi.id} value={nguoi.id}>
                    {nguoi.ho_ten} {nguoi.chuc_vu ? `(${nguoi.chuc_vu})` : ''}
                  </option>
                ))}
              </select>
              {ghiChuNguoiPheDuyet && <p className="text-xs text-blue-600 mt-1 font-medium">💡 {ghiChuNguoiPheDuyet}</p>}
            </div>
          )}
          
          {autoApprove && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
              <p className="text-sm text-green-800">✅ Chi cục trưởng - Tự động phê duyệt.</p>
            </div>
          )}
          
          {nguoiPheDuyetList.length === 0 && !autoApprove && (
            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-sm text-yellow-800">⚠️ Chưa có người phê duyệt. Liên hệ Admin.</p>
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            <button onClick={handleSaveDraft} disabled={isSaving || isSubmitting}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50">
              {isSaving ? '⏳ Đang lưu...' : '💾 Lưu nháp'}
            </button>
            <button onClick={handleSubmitForApproval} disabled={isSaving || isSubmitting || (!autoApprove && !selectedNguoiPheDuyet)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
              {isSubmitting ? '⏳ Đang gửi...' : '📤 Gửi phê duyệt'}
            </button>
          </div>
        </div>
      )}

      {/* Disabled State */}
      {isDisabled && (
        <div className="bg-gray-100 rounded-lg p-4 mt-6">
          <p className="text-gray-600">
            {trangThai === TrangThaiTieuChiChung.CHO_PHE_DUYET && (() => {
              const cap1 = (ketQua as unknown as Record<string, unknown>)?.nguoi_phe_duyet_tc_cap1 as { ho_ten?: string } | null;
              const cap2 = (ketQua as unknown as Record<string, unknown>)?.nguoi_phe_duyet_tc_cap2 as { ho_ten?: string } | null;
              if (cap2?.ho_ten) {
                return `⏳ Đang chờ ${cap1?.ho_ten || 'Phó Đội trưởng'} phê duyệt cấp 1. Bạn không thể sửa đổi.`;
              }
              return `⏳ Đang chờ ${cap1?.ho_ten || 'Đội trưởng'} phê duyệt. Bạn không thể sửa đổi.`;
            })()}
            {trangThai === ('CHO_CAP2' as TrangThaiTieuChiChung) && (() => {
              const cap2 = (ketQua as unknown as Record<string, unknown>)?.nguoi_phe_duyet_tc_cap2 as { ho_ten?: string } | null;
              return `⏳ Phó ĐT đã duyệt cấp 1. Đang chờ ${cap2?.ho_ten || 'Đội trưởng'} phê duyệt cấp 2. Bạn không thể sửa đổi.`;
            })()}
            {trangThai === TrangThaiTieuChiChung.DA_PHE_DUYET && (() => {
              const cap2 = (ketQua as unknown as Record<string, unknown>)?.nguoi_phe_duyet_tc_cap2 as { ho_ten?: string } | null;
              const cap1 = (ketQua as unknown as Record<string, unknown>)?.nguoi_phe_duyet_tc_cap1 as { ho_ten?: string } | null;
              const nguoiDuyet = cap2?.ho_ten || cap1?.ho_ten;
              return nguoiDuyet ? `✅ Đã được phê duyệt bởi ${nguoiDuyet}.` : '✅ Đã được phê duyệt.';
            })()}
            {!isStatusLocked && isDeadlinePassed && `⏰ Đã hết hạn tự đánh giá tháng ${selectedThang}/${selectedNam}.`}
          </p>
        </div>
      )}

      {/* Success Modal */}
      {showSuccessModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4 text-center">
            <div className="text-4xl mb-4">✅</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Thành công!</h3>
            <p className="text-gray-600 mb-4">{successMessage}</p>
            <button onClick={() => setShowSuccessModal(false)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Đóng</button>
          </div>
        </div>
      )}
    </div>
  );
}
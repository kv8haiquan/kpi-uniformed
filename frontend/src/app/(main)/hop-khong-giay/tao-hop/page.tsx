/**
 * /hop-khong-giay/tao-hop — Form tạo cuộc họp.
 *
 * G4-fix-3 (01/05/2026):
 * - Đơn vị tổ chức (dropdown) — đổi → reset chu_toa + thu_ky
 * - Chu_toa/Thu_ky: toggle radio "Trong đơn vị" / "Toàn Chi cục" → CongChucPicker
 *   với donViId hoặc null (tương ứng)
 * - Thành phần: CongChucCheckboxList trong đơn vị + CongChucPicker thêm ngoài
 *   chu_toa + thu_ky tự auto-check vào thành phần (disabled, không bỏ được)
 *
 * G4-fix-7 (03/05/2026):
 * - Mở quyền cho công chức tự tạo cuộc họp (BE đã bỏ ACL).
 * - Tách CBCC thành 2 nhóm:
 *   • inDonViIds — ticked qua CongChucCheckboxList (đơn vị tổ chức)
 *   • outsideEntries — chọn qua CrossUnitPicker (đơn vị khác, hydrated)
 * - CrossUnitPicker: dropdown đơn vị + search + checkbox list, hiển thị tên +
 *   mã CBCC thay vì UUID.
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import axios from 'axios';
import { Loader2, Save, Users, UsersRound } from 'lucide-react';
import { cuocHopApi, nhomThanhPhanApi, type ICongChucSearchItem } from '@/services/hkg';
import { errMsg } from '@/lib/hkg-error';
import type { ICuocHopCreate } from '@/types/hkg';
import CongChucPicker from '@/components/hkg/CongChucPicker';
import CongChucCheckboxList from '@/components/hkg/CongChucCheckboxList';
import CrossUnitPicker from '@/components/hkg/CrossUnitPicker';
import ChonNhomModal from '@/components/hkg/ChonNhomModal';

const LMS_API = process.env.NEXT_PUBLIC_LMS_API_URL || '/api/v1/lms';

interface IDonVi {
  id: string;
  ma_don_vi: string;
  ten_don_vi: string;
}

type Scope = 'don_vi' | 'toan_cc';

interface FormData {
  tieu_de: string;
  mo_ta: string;
  khoi: 'DANG' | 'CHUYEN_MON' | 'HANH_CHINH' | 'BAN_NHOM';
  hinh_thuc: 'TRUC_TIEP' | 'TRUC_TUYEN' | 'HYBRID';
  ngay_hop: string;
  gio_bat_dau: string;
  gio_ket_thuc: string;
  dia_diem: string;
  don_vi_to_chuc_id: string;
  chu_toa_id: string;
  thu_ky_id: string;
}

export default function TaoHopPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [donViList, setDonViList] = useState<IDonVi[]>([]);

  // Tách thành 2 nhóm:
  // - inDonViIds: ID CBCC được tick trong đơn vị tổ chức (CongChucCheckboxList)
  // - outsideEntries: hydrated CBCC từ đơn vị khác (CrossUnitPicker)
  const [inDonViIds, setInDonViIds] = useState<string[]>([]);
  const [outsideEntries, setOutsideEntries] = useState<ICongChucSearchItem[]>([]);

  // Item của chu_toa/thu_ky để biết don_vi_id của họ → autoinclude đúng nhóm.
  const [chuToaDonViId, setChuToaDonViId] = useState<string | null>(null);
  const [thuKyDonViId, setThuKyDonViId] = useState<string | null>(null);

  // Scope toggle riêng cho chu_toa và thu_ky
  const [chuToaScope, setChuToaScope] = useState<Scope>('don_vi');
  const [thuKyScope, setThuKyScope] = useState<Scope>('don_vi');

  // Modal "Thêm từ nhóm"
  const [showNhomPicker, setShowNhomPicker] = useState(false);
  const [mergingNhom, setMergingNhom] = useState(false);

  // Default ngày họp = hôm nay (local timezone), giờ bắt đầu = 08:30 (giao ban thường)
  const todayIso = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD theo local

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      khoi: 'CHUYEN_MON',
      hinh_thuc: 'TRUC_TIEP',
      chu_toa_id: '',
      thu_ky_id: '',
      don_vi_to_chuc_id: '',
      ngay_hop: todayIso,
      gio_bat_dau: '08:30',
    },
  });

  const donViId = watch('don_vi_to_chuc_id');
  const chuToaId = watch('chu_toa_id');
  const thuKyId = watch('thu_ky_id');

  // Đổi đơn vị → reset chu_toa + thu_ky + danh sách thành phần
  const [prevDonViId, setPrevDonViId] = useState<string>('');
  useEffect(() => {
    if (prevDonViId && donViId !== prevDonViId) {
      setValue('chu_toa_id', '');
      setValue('thu_ky_id', '');
      setChuToaDonViId(null);
      setThuKyDonViId(null);
      setInDonViIds([]);
      setOutsideEntries([]);
    }
    setPrevDonViId(donViId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [donViId]);

  // Load danh sách đơn vị 1 lần
  useEffect(() => {
    const load = async () => {
      try {
        const token =
          typeof window !== 'undefined' ? localStorage.getItem('kpi_access_token') : null;
        const resp = await axios.get(`${LMS_API}/don-vi`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        setDonViList(resp.data?.data || []);
      } catch {
        // Silent — user nhập UUID trực tiếp nếu cần
      }
    };
    load();
  }, []);

  // Chu_toa/thu_ky chỉ auto-tick vào CongChucCheckboxList khi họ thuộc đơn vị tổ chức
  const chuToaInHomeDv = chuToaDonViId && chuToaDonViId === donViId ? chuToaId : null;
  const thuKyInHomeDv = thuKyDonViId && thuKyDonViId === donViId ? thuKyId : null;

  // Gộp thành viên từ 1+ nhóm vào form state. Skip người đã có (theo cong_chuc_id).
  // Auto-fill thu_ky_id nếu form chưa có thu_ky và nhóm có vai_tro=THU_KY.
  // Chu_toa_id KHÔNG auto-fill (form yêu cầu user tự chọn để giữ rõ trách nhiệm).
  const handleMergeNhom = async (nhomIds: string[]) => {
    setMergingNhom(true);
    try {
      const detais = await Promise.all(
        nhomIds.map((id) => nhomThanhPhanApi.chiTiet(id)),
      );
      const existingIds = new Set<string>(inDonViIds);
      outsideEntries.forEach((e) => existingIds.add(e.id));
      if (chuToaId) existingIds.add(chuToaId);
      if (thuKyId) existingIds.add(thuKyId);

      let soThem = 0;
      let soBoQua = 0;
      let candidateThuKy: { id: string; ho_ten: string; don_vi_id: string | null } | null = null;
      const newOutside: ICongChucSearchItem[] = [...outsideEntries];
      const newIn: string[] = [...inDonViIds];

      for (const nhom of detais) {
        for (const ct of nhom.chi_tiet) {
          if (!candidateThuKy && ct.vai_tro === 'THU_KY') {
            candidateThuKy = {
              id: ct.cong_chuc_id,
              ho_ten: ct.ho_ten || '',
              don_vi_id: ct.don_vi_id || null,
            };
          }
          if (existingIds.has(ct.cong_chuc_id)) {
            soBoQua += 1;
            continue;
          }
          existingIds.add(ct.cong_chuc_id);
          if (donViId && ct.don_vi_id === donViId) {
            newIn.push(ct.cong_chuc_id);
          } else {
            newOutside.push({
              id: ct.cong_chuc_id,
              ho_ten: ct.ho_ten || '(Không rõ tên)',
              ma_cc: ct.ma_cc || '',
              email: null,
              chuc_vu: ct.chuc_vu || null,
              don_vi_id: ct.don_vi_id || null,
              ten_don_vi: ct.ten_don_vi || null,
              ma_vai_tro: null,
              is_lanh_dao: false,
            });
          }
          soThem += 1;
        }
      }

      setInDonViIds(newIn);
      setOutsideEntries(newOutside);

      // Auto-fill thu_ky nếu form chưa có
      let thuKyFilled = false;
      if (!thuKyId && candidateThuKy) {
        setValue('thu_ky_id', candidateThuKy.id);
        setThuKyDonViId(candidateThuKy.don_vi_id);
        if (donViId && candidateThuKy.don_vi_id !== donViId) {
          setThuKyScope('toan_cc');
        }
        thuKyFilled = true;
      }

      setShowNhomPicker(false);

      const msgs: string[] = [`Đã thêm ${soThem} thành viên từ ${nhomIds.length} nhóm`];
      if (soBoQua > 0) msgs.push(`bỏ qua ${soBoQua} người đã có`);
      if (thuKyFilled) msgs.push('tự động điền Thư ký');
      alert(msgs.join('. '));
    } catch (e: unknown) {
      alert(errMsg(e, 'Thêm từ nhóm thất bại'));
    } finally {
      setMergingNhom(false);
    }
  };

  const onSubmit = async (data: FormData) => {
    setSubmitting(true);
    setError(null);
    try {
      if (!data.chu_toa_id) {
        setError('Phải chọn chủ tọa');
        setSubmitting(false);
        return;
      }
      if (!data.don_vi_to_chuc_id) {
        setError('Phải chọn đơn vị tổ chức');
        setSubmitting(false);
        return;
      }

      // Gộp tất cả ID: trong đơn vị + ngoài đơn vị + chu_toa + thu_ky (dedup)
      const finalIds = new Set<string>(inDonViIds);
      outsideEntries.forEach((e) => finalIds.add(e.id));
      finalIds.add(data.chu_toa_id);
      if (data.thu_ky_id) finalIds.add(data.thu_ky_id);

      const thanh_phan = Array.from(finalIds).map((cong_chuc_id) => ({
        cong_chuc_id,
        loai_tham_du: 'BAT_BUOC' as const,
      }));

      const payload: ICuocHopCreate = {
        tieu_de: data.tieu_de,
        mo_ta: data.mo_ta || null,
        khoi: data.khoi,
        hinh_thuc: data.hinh_thuc,
        ngay_hop: data.ngay_hop,
        gio_bat_dau: data.gio_bat_dau,
        gio_ket_thuc: data.gio_ket_thuc || null,
        dia_diem: data.dia_diem || null,
        don_vi_to_chuc_id: data.don_vi_to_chuc_id,
        chu_toa_id: data.chu_toa_id,
        thu_ky_id: data.thu_ky_id || null,
        thanh_phan,
      };

      const res = await cuocHopApi.taoMoi(payload);
      router.push(`/hop-khong-giay/chi-tiet/${res.id}`);
    } catch (e: unknown) {
      setError(errMsg(e, 'Lỗi tạo cuộc họp'));
    } finally {
      setSubmitting(false);
    }
  };

  // Tổng số CBCC sẽ submit (preview, đã dedup)
  const totalCount = (() => {
    const s = new Set<string>(inDonViIds);
    outsideEntries.forEach((e) => s.add(e.id));
    if (chuToaId) s.add(chuToaId);
    if (thuKyId) s.add(thuKyId);
    return s.size;
  })();

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="max-w-3xl mx-auto bg-white rounded border p-6 space-y-4"
    >
      <h2 className="text-xl font-semibold">Tạo cuộc họp mới</h2>

      <div>
        <label className="block text-sm font-medium mb-1">Tiêu đề *</label>
        <input
          {...register('tieu_de', { required: 'Bắt buộc nhập tiêu đề' })}
          className="w-full px-3 py-2 border rounded"
        />
        {errors.tieu_de && (
          <p className="text-xs text-red-600 mt-1">{errors.tieu_de.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Mô tả</label>
        <textarea
          {...register('mo_ta')}
          rows={3}
          className="w-full px-3 py-2 border rounded"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Khối *</label>
          <select {...register('khoi')} className="w-full px-3 py-2 border rounded">
            <option value="CHUYEN_MON">Chuyên môn</option>
            <option value="DANG">Đảng</option>
            <option value="HANH_CHINH">Hành chính</option>
            <option value="BAN_NHOM">Ban / Nhóm</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Hình thức *</label>
          <select {...register('hinh_thuc')} className="w-full px-3 py-2 border rounded">
            <option value="TRUC_TIEP">Trực tiếp</option>
            <option value="TRUC_TUYEN">Trực tuyến</option>
            <option value="HYBRID">Hybrid</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Ngày họp *</label>
          <input
            type="date"
            {...register('ngay_hop', { required: true })}
            className="w-full px-3 py-2 border rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Giờ bắt đầu *</label>
          <input
            type="time"
            {...register('gio_bat_dau', { required: true })}
            className="w-full px-3 py-2 border rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Giờ kết thúc</label>
          <input
            type="time"
            {...register('gio_ket_thuc')}
            className="w-full px-3 py-2 border rounded"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Địa điểm</label>
        <input {...register('dia_diem')} className="w-full px-3 py-2 border rounded" />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Đơn vị tổ chức *</label>
        <select
          {...register('don_vi_to_chuc_id', { required: true })}
          className="w-full px-3 py-2 border rounded"
        >
          <option value="">— Chọn đơn vị —</option>
          {donViList.map((dv) => (
            <option key={dv.id} value={dv.id}>
              {dv.ma_don_vi} — {dv.ten_don_vi}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <ScopedPickerField
          label="Chủ tọa *"
          scope={chuToaScope}
          setScope={setChuToaScope}
          donViId={donViId}
        >
          <Controller
            name="chu_toa_id"
            control={control}
            rules={{ required: true }}
            render={({ field }) => (
              <CongChucPicker
                multiple={false}
                value={field.value || null}
                onChange={(id, item) => {
                  field.onChange(id || '');
                  setChuToaDonViId(item?.don_vi_id || null);
                }}
                placeholder="Tìm chủ tọa..."
                donViId={chuToaScope === 'don_vi' ? donViId : null}
              />
            )}
          />
        </ScopedPickerField>

        <ScopedPickerField
          label="Thư ký"
          scope={thuKyScope}
          setScope={setThuKyScope}
          donViId={donViId}
        >
          <Controller
            name="thu_ky_id"
            control={control}
            render={({ field }) => (
              <CongChucPicker
                multiple={false}
                value={field.value || null}
                onChange={(id, item) => {
                  field.onChange(id || '');
                  setThuKyDonViId(item?.don_vi_id || null);
                }}
                placeholder="Tìm thư ký..."
                donViId={thuKyScope === 'don_vi' ? donViId : null}
              />
            )}
          />
        </ScopedPickerField>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium">
            <Users className="w-4 h-4 inline mr-1" />
            Thành phần tham dự
          </label>
          <button
            type="button"
            onClick={() => setShowNhomPicker(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs border border-blue-300 text-blue-700 bg-white rounded hover:bg-blue-50"
            title="Gộp thành viên từ 1+ nhóm có sẵn"
          >
            <UsersRound className="w-3.5 h-3.5" />
            Thêm từ nhóm
          </button>
        </div>

        <CongChucCheckboxList
          donViId={donViId || null}
          value={inDonViIds}
          onChange={setInDonViIds}
          chuToaId={chuToaInHomeDv}
          thuKyId={thuKyInHomeDv}
        />

        <div>
          <p className="text-xs font-medium text-gray-700 mb-1">
            Thêm CBCC từ đơn vị khác
          </p>
          <CrossUnitPicker
            donViList={donViList}
            excludeDonViId={donViId || null}
            entries={outsideEntries}
            onChange={setOutsideEntries}
          />
        </div>

        <p className="text-xs text-gray-500">
          Tổng {totalCount} thành phần · Tất cả mặc định &quot;Bắt buộc&quot;. Chủ tọa + thư ký
          luôn được tính vào thành phần khi submit.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
          {error}
        </div>
      )}

      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          type="button"
          onClick={() => router.back()}
          className="px-4 py-2 border rounded"
        >
          Hủy
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Tạo cuộc họp
        </button>
      </div>

      {showNhomPicker && (
        <ChonNhomModal
          title="Thêm thành viên từ nhóm có sẵn"
          confirmLabel="Thêm vào danh sách"
          busy={mergingNhom}
          onConfirm={handleMergeNhom}
          onClose={() => setShowNhomPicker(false)}
        />
      )}
    </form>
  );
}


// ════════════════════════════════════════════════════════════════════
// SUB-COMPONENT: Field wrapper với radio toggle scope
// ════════════════════════════════════════════════════════════════════

interface IScopedPickerFieldProps {
  label: string;
  scope: Scope;
  setScope: (s: Scope) => void;
  donViId?: string;
  children: React.ReactNode;
}

function ScopedPickerField({
  label,
  scope,
  setScope,
  donViId,
  children,
}: IScopedPickerFieldProps) {
  const disabled = !donViId;
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="block text-sm font-medium">{label}</label>
        <div className="flex gap-3 text-xs">
          <label className={`inline-flex items-center gap-1 cursor-pointer ${disabled ? 'opacity-50' : ''}`}>
            <input
              type="radio"
              checked={scope === 'don_vi'}
              onChange={() => setScope('don_vi')}
              disabled={disabled}
              className="w-3 h-3"
            />
            Trong đơn vị
          </label>
          <label className="inline-flex items-center gap-1 cursor-pointer">
            <input
              type="radio"
              checked={scope === 'toan_cc'}
              onChange={() => setScope('toan_cc')}
              className="w-3 h-3"
            />
            Toàn Chi cục
          </label>
        </div>
      </div>
      {children}
      {scope === 'don_vi' && !donViId && (
        <p className="text-xs text-amber-600 mt-1">
          Chọn đơn vị tổ chức trước để filter trong đơn vị.
        </p>
      )}
    </div>
  );
}

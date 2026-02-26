/**
 * src/app/(main)/dien-dan/tao-moi/page.tsx
 * Trang tao chu de moi trong Dien dan.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronRight, AlertCircle, Loader2 } from 'lucide-react';
import { useAuthStore } from '@/stores/useAuthStore';
import { chuyenMucApi, chuDeApi } from '@/services/forum';
import type { IChuyenMuc, IChuDeCreate, ICanCuPhapLy } from '@/types/forum';
import TagSelector from '@/components/forum/TagSelector';
import VanBanCitation from '@/components/forum/VanBanCitation';

export default function TaoMoiChuDePage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);

  const [chuyenMucs, setChuyenMucs] = useState<IChuyenMuc[]>([]);
  const [isLoadingChuyenMuc, setIsLoadingChuyenMuc] = useState(true);

  // Form state
  const [chuyenMucId, setChuyenMucId] = useState('');
  const [tieuDe, setTieuDe] = useState('');
  const [noiDung, setNoiDung] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [canCuPhapLy, setCanCuPhapLy] = useState<ICanCuPhapLy[]>([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load chuyen muc
  useEffect(() => {
    const loadChuyenMuc = async () => {
      try {
        const data = await chuyenMucApi.danhSach(true);
        setChuyenMucs(data);
      } catch (err) {
        console.error('Failed to load chuyen muc:', err);
        setError('Khong the tai danh sach chuyen muc');
      } finally {
        setIsLoadingChuyenMuc(false);
      }
    };
    loadChuyenMuc();
  }, []);

  // Flatten chuyen muc tree thanh list (de dung select dropdown)
  const flattenChuyenMuc = (items: IChuyenMuc[], level = 0): Array<IChuyenMuc & { level: number }> => {
    let result: Array<IChuyenMuc & { level: number }> = [];
    for (const item of items) {
      result.push({ ...item, level });
      if (item.children && item.children.length > 0) {
        result = result.concat(flattenChuyenMuc(item.children, level + 1));
      }
    }
    return result;
  };

  const flatChuyenMucs = flattenChuyenMuc(chuyenMucs);

  // Tim chuyen muc da chon
  const selectedChuyenMuc = flatChuyenMucs.find((cm) => cm.id === chuyenMucId);

  // Validation
  const validateForm = (): string | null => {
    if (!chuyenMucId) return 'Vui long chon chuyen muc';
    if (tieuDe.trim().length < 10) return 'Tieu de phai co it nhat 10 ky tu';
    if (tieuDe.trim().length > 500) return 'Tieu de khong duoc qua 500 ky tu';
    if (noiDung.trim().length < 30) return 'Noi dung phai co it nhat 30 ky tu';
    if (tags.length > 5) return 'Toi da 5 tags';
    return null;
  };

  // Submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload: IChuDeCreate = {
        chuyen_muc_id: chuyenMucId,
        tieu_de: tieuDe.trim(),
        noi_dung: noiDung.trim(),
        tags: tags.length > 0 ? tags : undefined,
        van_ban_lien_quan: canCuPhapLy
          .filter((c) => c.loai === 'VAN_BAN' && c.trich_dan.trim())
          .map((c) => c.id),
        sop_lien_quan: canCuPhapLy
          .filter((c) => c.loai === 'SOP' && c.trich_dan.trim())
          .map((c) => c.id),
      };

      const result = await chuDeApi.taoMoi(payload);
      router.push(`/dien-dan/chu-de/${result.id}`);
    } catch (err: any) {
      console.error('Submit error:', err);
      setError(err?.response?.data?.error?.message || 'Khong the tao chu de. Vui long thu lai.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-6">
          <button onClick={() => router.push('/dien-dan')} className="hover:text-blue-600">
            Dien dan
          </button>
          <ChevronRight className="w-4 h-4" />
          <span className="text-gray-900 font-medium">Tao chu de moi</span>
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Tao chu de moi</h1>

        {/* Error alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-900">Loi</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 space-y-6">
          {/* Chuyen muc */}
          <div>
            <label htmlFor="chuyenMuc" className="block text-sm font-medium text-gray-700 mb-2">
              Chuyen muc <span className="text-red-500">*</span>
            </label>
            {isLoadingChuyenMuc ? (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                Dang tai chuyen muc...
              </div>
            ) : (
              <select
                id="chuyenMuc"
                value={chuyenMucId}
                onChange={(e) => setChuyenMucId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">-- Chon chuyen muc --</option>
                {flatChuyenMucs.map((cm) => (
                  <option key={cm.id} value={cm.id}>
                    {'  '.repeat(cm.level) + cm.ten_chuyen_muc}
                  </option>
                ))}
              </select>
            )}

            {/* Thong bao dac biet */}
            {selectedChuyenMuc?.yeu_cau_duyet && (
              <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-yellow-800">
                  Bai viet se duoc duyet truoc khi hien thi
                </p>
              </div>
            )}
            {selectedChuyenMuc?.chi_doc && (
              <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-800">
                  Chuyen muc nay chi cho phep Chuyen gia/Dieu phoi dang bai
                </p>
              </div>
            )}
          </div>

          {/* Tieu de */}
          <div>
            <label htmlFor="tieuDe" className="block text-sm font-medium text-gray-700 mb-2">
              Tieu de <span className="text-red-500">*</span>
            </label>
            <input
              id="tieuDe"
              type="text"
              value={tieuDe}
              onChange={(e) => setTieuDe(e.target.value)}
              placeholder="Nhap tieu de (10-500 ky tu)"
              minLength={10}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <p className="text-xs text-gray-500 mt-1">{tieuDe.length} / 500 ky tu</p>
          </div>

          {/* Noi dung */}
          <div>
            <label htmlFor="noiDung" className="block text-sm font-medium text-gray-700 mb-2">
              Noi dung <span className="text-red-500">*</span>
            </label>
            <textarea
              id="noiDung"
              value={noiDung}
              onChange={(e) => setNoiDung(e.target.value)}
              placeholder="Nhap noi dung chi tiet (toi thieu 30 ky tu)..."
              rows={10}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <p className="text-xs text-gray-500 mt-1">{noiDung.length} ky tu</p>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
            <TagSelector selectedTags={tags} onChange={setTags} maxTags={5} />
          </div>

          {/* Can cu phap ly */}
          <div>
            <VanBanCitation citations={canCuPhapLy} onChange={setCanCuPhapLy} />
          </div>

          {/* Submit buttons */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={isSubmitting}
            >
              Huy
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
              {isSubmitting ? 'Dang dang...' : 'Dang bai'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

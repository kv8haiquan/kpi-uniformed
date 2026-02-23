/**
 * app/(main)/tin-tuc/quan-ly/soan-bai/page.tsx
 * ===============================================
 * Form soạn bài viết mới hoặc chỉnh sửa bài có sẵn.
 * URL: /tin-tuc/quan-ly/soan-bai          → Tạo mới
 *      /tin-tuc/quan-ly/soan-bai?id=xxx   → Chỉnh sửa
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { baiVietApi, chuyenMucApi } from '@/services/portal';
import type { IChuyenMuc } from '@/types/tin-tuc';

// =============================================================================
// FORM STATE
// =============================================================================

interface FormState {
  tieu_de: string;
  tom_tat: string;
  noi_dung: string;
  anh_dai_dien: string;
  chuyen_muc_id: string;
}

const EMPTY_FORM: FormState = {
  tieu_de: '',
  tom_tat: '',
  noi_dung: '',
  anh_dai_dien: '',
  chuyen_muc_id: '',
};

// =============================================================================
// PAGE
// =============================================================================

export default function SoanBaiPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const editId = searchParams?.get('id') ?? null;
  const isEdit = !!editId;

  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [chuyenMucList, setChuyenMucList] = useState<IChuyenMuc[]>([]);
  const [loadingEdit, setLoadingEdit] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // ---------------------------------------------------------------------------
  // Khởi tạo
  // ---------------------------------------------------------------------------

  useEffect(() => {
    // Load danh sách chuyên mục
    chuyenMucApi.danhSach().then((res) => {
      const items = res.data?.data ?? res.data;
      setChuyenMucList(Array.isArray(items) ? items : []);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!editId) return;
    const load = async () => {
      try {
        const res = await baiVietApi.chiTiet(editId);
        const data = res.data?.data ?? res.data;
        if (data) {
          setForm({
            tieu_de: data.tieu_de ?? '',
            tom_tat: data.tom_tat ?? '',
            noi_dung: data.noi_dung ?? '',
            anh_dai_dien: data.anh_dai_dien ?? '',
            chuyen_muc_id: data.chuyen_muc?.id ?? '',
          });
        }
      } catch {
        setError('Không thể tải bài viết để chỉnh sửa.');
      } finally {
        setLoadingEdit(false);
      }
    };
    load();
  }, [editId]);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (action: 'NHAP' | 'KIEM_TRA') => {
    if (!form.tieu_de.trim()) {
      setError('Vui lòng nhập tiêu đề bài viết.');
      return;
    }
    if (!form.chuyen_muc_id) {
      setError('Vui lòng chọn chuyên mục.');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      const payload = {
        tieu_de: form.tieu_de.trim(),
        tom_tat: form.tom_tat.trim() || undefined,
        noi_dung: form.noi_dung.trim() || undefined,
        anh_dai_dien: form.anh_dai_dien.trim() || undefined,
        chuyen_muc_id: form.chuyen_muc_id,
      };

      if (isEdit && editId) {
        await baiVietApi.capNhat(editId, payload);
        // Nếu action là gửi duyệt, thực hiện thêm
        if (action === 'KIEM_TRA') {
          await baiVietApi.doiTrangThai(editId, { trang_thai_moi: 'KIEM_TRA' });
        }
      } else {
        const res = await baiVietApi.taoMoi(payload);
        const data = res.data?.data ?? res.data;
        const newId = data?.id;
        // Nếu gửi duyệt luôn
        if (action === 'KIEM_TRA' && newId) {
          await baiVietApi.doiTrangThai(newId, { trang_thai_moi: 'KIEM_TRA' });
        }
      }

      router.push('/tin-tuc/quan-ly');
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e?.message ?? 'Có lỗi xảy ra. Vui lòng thử lại.');
    } finally {
      setSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------

  if (loadingEdit) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-6 sm:px-6">

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Link href="/tin-tuc/quan-ly" className="text-gray-400 hover:text-gray-700 text-lg">←</Link>
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              {isEdit ? 'Chỉnh sửa bài viết' : 'Soạn bài viết mới'}
            </h1>
          </div>
        </div>

        {/* Form */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">

          {/* Chuyên mục */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Chuyên mục <span className="text-red-500">*</span>
            </label>
            <select
              name="chuyen_muc_id"
              value={form.chuyen_muc_id}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
            >
              <option value="">— Chọn chuyên mục —</option>
              {chuyenMucList.map((cm) => (
                <option key={cm.id} value={cm.id}>{cm.ten}</option>
              ))}
            </select>
          </div>

          {/* Tiêu đề */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Tiêu đề <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="tieu_de"
              value={form.tieu_de}
              onChange={handleChange}
              placeholder="Tiêu đề bài viết..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>

          {/* Tóm tắt */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Tóm tắt</label>
            <textarea
              name="tom_tat"
              value={form.tom_tat}
              onChange={handleChange}
              rows={3}
              placeholder="Tóm tắt ngắn gọn nội dung bài viết (hiển thị trong danh sách)..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
            />
          </div>

          {/* Ảnh đại diện */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">URL ảnh đại diện</label>
            <input
              type="url"
              name="anh_dai_dien"
              value={form.anh_dai_dien}
              onChange={handleChange}
              placeholder="https://..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            {form.anh_dai_dien && (
              <div className="mt-2 rounded-lg overflow-hidden border border-gray-200 w-32 h-20">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={form.anh_dai_dien} alt="preview" className="w-full h-full object-cover" />
              </div>
            )}
          </div>

          {/* Nội dung */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Nội dung</label>
            <textarea
              name="noi_dung"
              value={form.noi_dung}
              onChange={handleChange}
              rows={16}
              placeholder="Nhập nội dung bài viết. Hỗ trợ HTML cơ bản..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-y font-mono"
            />
            <p className="text-xs text-gray-400 mt-1">
              Hỗ trợ HTML cơ bản: &lt;p&gt;, &lt;b&gt;, &lt;i&gt;, &lt;ul&gt;, &lt;ol&gt;, &lt;table&gt;, &lt;img&gt;...
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              href="/tin-tuc/quan-ly"
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50 transition-colors"
            >
              Hủy
            </Link>
            <button
              onClick={() => handleSubmit('NHAP')}
              disabled={submitting}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg text-sm hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? 'Đang lưu...' : 'Lưu nháp'}
            </button>
            <button
              onClick={() => handleSubmit('KIEM_TRA')}
              disabled={submitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? 'Đang xử lý...' : 'Gửi kiểm tra'}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}

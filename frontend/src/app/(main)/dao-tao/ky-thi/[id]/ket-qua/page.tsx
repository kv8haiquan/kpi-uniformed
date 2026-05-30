/**
 * src/app/(main)/dao-tao/ky-thi/[id]/ket-qua/page.tsx
 * =====================================================
 * Trang ket qua ca nhan — thi sinh tu xem ket qua bai thi cua minh.
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { kyThiApi } from '@/services/lms';
import type { IDgnlKetQua } from '@/types/lms';
import DgnlKetQuaDetail from '@/components/lms/DgnlKetQuaDetail';

export default function KetQuaDgnlPage() {
  const params = useParams();
  const kyThiId = params.id as string;

  const [ketQua, setKetQua] = useState<IDgnlKetQua | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await kyThiApi.ketQua(kyThiId);
        setKetQua(res.data.data);
      } catch (err: any) {
        setError(err?.response?.data?.detail?.error?.message || 'Không thể tải kết quả');
      } finally {
        setLoading(false);
      }
    };
    if (kyThiId) load();
  }, [kyThiId]);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error || !ketQua) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || 'Chưa có kết quả'}
        </div>
        <Link href="/dao-tao/ky-thi" className="mt-4 inline-block text-blue-600 hover:underline text-sm">
          Quay lại danh sách kỳ thi
        </Link>
      </div>
    );
  }

  return (
    <DgnlKetQuaDetail
      ketQua={ketQua}
      backHref="/dao-tao/ky-thi"
      title="Kết quả kỳ thi"
    />
  );
}

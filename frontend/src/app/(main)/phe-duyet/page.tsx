'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function RedirectPheDuyet() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/xep-loai?tab=cong-viec');
  }, [router]);
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
        <p className="text-gray-500">Đang chuyển hướng...</p>
      </div>
    </div>
  );
}
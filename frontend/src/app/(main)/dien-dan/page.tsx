/**
 * src/app/(main)/dien-dan/page.tsx
 * Trang chính Module Diễn đàn — Placeholder.
 */

'use client';

export default function DienDanPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center">
          <div className="w-20 h-20 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl">💬</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Module Diễn đàn
          </h1>
          <p className="text-gray-500 mb-6">
            Module Diễn đàn đang được phát triển. Vui lòng quay lại sau.
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-full text-sm font-medium">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            Đang phát triển
          </div>
        </div>
      </div>
    </div>
  );
}

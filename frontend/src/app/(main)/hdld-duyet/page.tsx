/**
 * src/app/(main)/hdld-duyet/page.tsx
 * ==================================
 * Trang cấp quản lý (TDV/PDV) duyệt đánh giá HĐLĐ 111 theo Bộ tiêu chí VB714.
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import Hdld111DuyetView from '@/components/hdld/Hdld111DuyetView';

export default function HdldDuyetPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const now = new Date();
  const [thang, setThang] = useState(now.getMonth() + 1);
  const [nam, setNam] = useState(now.getFullYear());

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  Duyệt đánh giá HĐLĐ
                  <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-amber-100 text-amber-700">
                    VB714
                  </span>
                </h1>
                <p className="text-xs text-gray-500">{user?.ho_ten} - {user?.chuc_vu || user?.vai_tro?.ten_vai_tro}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <select
                value={thang}
                onChange={(e) => setThang(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500"
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((t) => (
                  <option key={t} value={t}>Tháng {t}</option>
                ))}
              </select>
              <select
                value={nam}
                onChange={(e) => setNam(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500"
              >
                {[2025, 2026, 2027].map((n) => (
                  <option key={n} value={n}>Năm {n}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Hdld111DuyetView thang={thang} nam={nam} />
      </main>
    </div>
  );
}

/**
 * src/components/shared/ExportButton.tsx
 * =======================================
 * Component nút xuất báo cáo DOCX/PDF dùng chung.
 * 
 * Features:
 * - Dropdown chọn DOCX hoặc PDF
 * - Loading state khi đang tải
 * - Error handling với toast/alert
 * 
 * Version: 1.0.0 (02/02/2026)
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';

// =============================================================================
// TYPES
// =============================================================================

export type ExportFormat = 'docx' | 'pdf';

export interface ExportButtonProps {
  /** Callback khi user chọn format và bấm xuất */
  onExport: (format: ExportFormat) => Promise<void>;
  /** Label hiển thị trên nút */
  label?: string;
  /** CSS class bổ sung */
  className?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Chỉ cho phép 1 format (ẩn dropdown) */
  singleFormat?: ExportFormat;
  /** Size variant */
  size?: 'sm' | 'md';
}

// =============================================================================
// ICONS
// =============================================================================

const DownloadIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const SpinnerIcon = () => (
  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
  </svg>
);

const ChevronIcon = () => (
  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

// =============================================================================
// COMPONENT
// =============================================================================

export default function ExportButton({
  onExport,
  label = 'Xuất báo cáo',
  className = '',
  disabled = false,
  singleFormat,
  size = 'md',
}: ExportButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleExport = async (format: ExportFormat) => {
    setShowDropdown(false);
    setIsLoading(true);
    setError(null);

    try {
      await onExport(format);
    } catch (err: any) {
      const msg = err?.message || 'Không thể xuất báo cáo. Vui lòng thử lại.';
      setError(msg);
      // Auto-clear error sau 5s
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsLoading(false);
    }
  };

  const sizeClasses = size === 'sm'
    ? 'px-3 py-1.5 text-xs'
    : 'px-4 py-2 text-sm';

  // Nếu chỉ 1 format → button đơn giản
  if (singleFormat) {
    return (
      <div className="relative inline-block">
        <button
          onClick={() => handleExport(singleFormat)}
          disabled={disabled || isLoading}
          className={`inline-flex items-center gap-2 ${sizeClasses} font-medium text-white 
            bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors
            disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
        >
          {isLoading ? <SpinnerIcon /> : <DownloadIcon />}
          {isLoading ? 'Đang tải...' : `${label} (.${singleFormat})`}
        </button>
        {error && (
          <div className="absolute top-full left-0 mt-1 px-3 py-1.5 bg-red-50 text-red-600 text-xs rounded-lg border border-red-200 whitespace-nowrap z-50">
            {error}
          </div>
        )}
      </div>
    );
  }

  // Dropdown: chọn DOCX hoặc PDF
  return (
    <div className="relative inline-block" ref={dropdownRef}>
      <button
        onClick={() => !isLoading && setShowDropdown(!showDropdown)}
        disabled={disabled || isLoading}
        className={`inline-flex items-center gap-2 ${sizeClasses} font-medium text-white 
          bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors
          disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      >
        {isLoading ? <SpinnerIcon /> : <DownloadIcon />}
        {isLoading ? 'Đang tải...' : label}
        {!isLoading && <ChevronIcon />}
      </button>

      {/* Dropdown menu */}
      {showDropdown && !isLoading && (
        <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50 overflow-hidden">
          <button
            onClick={() => handleExport('docx')}
            className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 flex items-center gap-2 transition-colors"
          >
            <span className="text-blue-500">📄</span>
            Tải DOCX (Word)
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 flex items-center gap-2 transition-colors border-t border-gray-100"
          >
            <span className="text-red-500">📕</span>
            Tải PDF
          </button>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="absolute top-full right-0 mt-1 px-3 py-1.5 bg-red-50 text-red-600 text-xs rounded-lg border border-red-200 whitespace-nowrap z-50">
          {error}
        </div>
      )}
    </div>
  );
}
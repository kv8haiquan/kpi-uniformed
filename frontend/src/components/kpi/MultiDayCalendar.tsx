/**
 * src/components/kpi/MultiDayCalendar.tsx
 * ========================================
 * Component lịch để chọn nhiều ngày trong tháng.
 *
 * Version: 1.0.0 (25/02/2026)
 *
 * Features:
 * - Hiển thị lịch tháng dạng grid
 * - Chọn/bỏ chọn ngày bằng click
 * - Quick actions: T2-T6, Chọn tất cả, Bỏ chọn
 * - Ngày tương lai bị disable
 * - Cuối tuần có màu khác
 * - Badge hiển thị số ngày đã chọn
 */

'use client';

import { useMemo } from 'react';
import {
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  format,
  isSameDay,
  isAfter,
  getDay,
  isSaturday,
  isSunday,
  isWeekend,
  addDays,
  startOfWeek,
} from 'date-fns';
import { vi } from 'date-fns/locale';

interface MultiDayCalendarProps {
  month: number;      // 1-12
  year: number;       // e.g., 2026
  selectedDates: Date[];
  onDatesChange: (dates: Date[]) => void;
}

export default function MultiDayCalendar({
  month,
  year,
  selectedDates,
  onDatesChange,
}: MultiDayCalendarProps) {
  // Tạo Date object từ month/year (month 1-12 -> month 0-11)
  const currentMonthDate = useMemo(() => {
    return new Date(year, month - 1, 1);
  }, [month, year]);

  const today = useMemo(() => new Date(), []);

  // Lấy tất cả ngày trong tháng
  const daysInMonth = useMemo(() => {
    const start = startOfMonth(currentMonthDate);
    const end = endOfMonth(currentMonthDate);
    return eachDayOfInterval({ start, end });
  }, [currentMonthDate]);

  // Tính padding days (ngày từ tuần trước để điền đầy grid)
  const firstDayOfWeek = useMemo(() => {
    const start = startOfMonth(currentMonthDate);
    // getDay trả về 0 = Sunday, 1 = Monday, ...
    // Chuyển sang Monday = 0, Sunday = 6
    const day = getDay(start);
    return day === 0 ? 6 : day - 1;
  }, [currentMonthDate]);

  const paddingDays = useMemo(() => {
    return Array.from({ length: firstDayOfWeek }, (_, i) => {
      const paddingDate = addDays(startOfMonth(currentMonthDate), -(firstDayOfWeek - i));
      return paddingDate;
    });
  }, [firstDayOfWeek, currentMonthDate]);

  // Check nếu ngày đã được chọn
  const isDateSelected = (date: Date) => {
    return selectedDates.some((d) => isSameDay(d, date));
  };

  // Check nếu ngày là tương lai (disable)
  const isDateDisabled = (date: Date) => {
    return isAfter(date, today);
  };

  // Toggle chọn ngày
  const handleToggleDate = (date: Date) => {
    if (isDateDisabled(date)) return;

    if (isDateSelected(date)) {
      // Bỏ chọn
      onDatesChange(selectedDates.filter((d) => !isSameDay(d, date)));
    } else {
      // Chọn
      onDatesChange([...selectedDates, date]);
    }
  };

  // Quick action: Chọn T2-T6 (weekdays)
  const handleSelectWeekdays = () => {
    const weekdayDates = daysInMonth.filter((date) => {
      return !isWeekend(date) && !isDateDisabled(date);
    });
    onDatesChange(weekdayDates);
  };

  // Quick action: Chọn tất cả
  const handleSelectAll = () => {
    const allValidDates = daysInMonth.filter((date) => !isDateDisabled(date));
    onDatesChange(allValidDates);
  };

  // Quick action: Bỏ chọn tất cả
  const handleDeselectAll = () => {
    onDatesChange([]);
  };

  return (
    <div className="space-y-3">
      {/* Header: Tên tháng + Badge số ngày đã chọn */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-700">
          Chọn ngày: Tháng {month}/{year}
        </h4>
        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
          {selectedDates.length} ngày
        </span>
      </div>

      {/* Quick actions */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          onClick={handleSelectWeekdays}
          className="px-3 py-1 text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 rounded border border-blue-200 transition-colors"
        >
          T2-T6
        </button>
        <button
          type="button"
          onClick={handleSelectAll}
          className="px-3 py-1 text-xs bg-gray-50 hover:bg-gray-100 text-gray-700 rounded border border-gray-200 transition-colors"
        >
          Chọn tất cả
        </button>
        <button
          type="button"
          onClick={handleDeselectAll}
          className="px-3 py-1 text-xs bg-gray-50 hover:bg-gray-100 text-gray-700 rounded border border-gray-200 transition-colors"
        >
          Bỏ chọn
        </button>
      </div>

      {/* Calendar Grid */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        {/* Header: Tên các ngày trong tuần */}
        <div className="grid grid-cols-7 bg-gray-50 border-b border-gray-200">
          {['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map((day) => (
            <div
              key={day}
              className="text-center py-2 text-xs font-medium text-gray-600"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Body: Grid các ngày */}
        <div className="grid grid-cols-7">
          {/* Padding days từ tháng trước */}
          {paddingDays.map((date, index) => (
            <div
              key={`padding-${index}`}
              className="aspect-square p-2 border-b border-r border-gray-100"
            >
              <div className="text-xs text-gray-300 text-center">
                {format(date, 'd')}
              </div>
            </div>
          ))}

          {/* Các ngày trong tháng */}
          {daysInMonth.map((date) => {
            const isSelected = isDateSelected(date);
            const isDisabled = isDateDisabled(date);
            const isToday = isSameDay(date, today);
            const isWeekendDay = isSaturday(date) || isSunday(date);

            return (
              <button
                key={format(date, 'yyyy-MM-dd')}
                type="button"
                onClick={() => handleToggleDate(date)}
                disabled={isDisabled}
                className={`
                  aspect-square p-2 border-b border-r border-gray-100
                  transition-colors text-sm font-medium
                  ${isDisabled ? 'cursor-not-allowed' : 'cursor-pointer'}
                  ${!isDisabled && !isSelected ? 'hover:bg-gray-50' : ''}
                  ${isWeekendDay && !isSelected ? 'bg-gray-50' : ''}
                  ${isSelected ? 'bg-blue-500 text-white hover:bg-blue-600' : ''}
                  ${isDisabled ? 'text-gray-300' : isSelected ? 'text-white' : 'text-gray-700'}
                  ${isToday && !isSelected ? 'ring-2 ring-inset ring-blue-500' : ''}
                `}
              >
                {format(date, 'd')}
              </button>
            );
          })}
        </div>
      </div>

      {/* Hướng dẫn */}
      <div className="text-xs text-gray-500 space-y-1">
        <p>• Nhấn vào ngày để chọn/bỏ chọn</p>
        <p>• Ngày tương lai không thể chọn</p>
        <p>• Cuối tuần có nền màu xám nhạt</p>
      </div>
    </div>
  );
}

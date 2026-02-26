'use client';

/**
 * TagSelector.tsx
 * ===============
 * Component chon tag voi autocomplete.
 * Su dung debounce 300ms khi go de goi API goi y tag.
 */

import { useState, useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { timKiemApi } from '@/services/forum';

interface TagSelectorProps {
  selectedTags: string[];
  onChange: (tags: string[]) => void;
  maxTags?: number;
}

export default function TagSelector({
  selectedTags,
  onChange,
  maxTags = 5,
}: TagSelectorProps) {
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout>(null);

  // Debounce tim kiem tag
  useEffect(() => {
    if (!inputValue.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(async () => {
      setIsLoadingSuggestions(true);
      try {
        const results = await timKiemApi.goiYTag(inputValue.trim());
        // Loc ra nhung tag chua duoc chon
        const filtered = results.filter(
          (tag) => !selectedTags.includes(tag)
        );
        setSuggestions(filtered);
        setShowSuggestions(filtered.length > 0);
      } catch (error) {
        console.error('Tag suggestion error:', error);
        setSuggestions([]);
      } finally {
        setIsLoadingSuggestions(false);
      }
    }, 300);

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [inputValue, selectedTags]);

  // Them tag
  const addTag = (tag: string) => {
    const trimmedTag = tag.trim();
    if (!trimmedTag) return;
    if (selectedTags.includes(trimmedTag)) return;
    if (selectedTags.length >= maxTags) return;

    onChange([...selectedTags, trimmedTag]);
    setInputValue('');
    setSuggestions([]);
    setShowSuggestions(false);
  };

  // Xoa tag
  const removeTag = (tagToRemove: string) => {
    onChange(selectedTags.filter((tag) => tag !== tagToRemove));
  };

  // Xu ly phim Enter
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (suggestions.length > 0) {
        // Chon goi y dau tien
        addTag(suggestions[0]);
      } else if (inputValue.trim()) {
        // Tao tag moi
        addTag(inputValue);
      }
    } else if (e.key === 'Backspace' && !inputValue && selectedTags.length > 0) {
      // Xoa tag cuoi cung neu dang khong go gi
      removeTag(selectedTags[selectedTags.length - 1]);
    }
  };

  // Tat suggestions khi click ra ngoai
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const isMaxTagsReached = selectedTags.length >= maxTags;

  return (
    <div className="relative">
      {/* Hien thi cac tag da chon */}
      {selectedTags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selectedTags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
            >
              {tag}
              <button
                onClick={() => removeTag(tag)}
                className="hover:bg-blue-200 rounded-full p-0.5 transition-colors"
                aria-label={`Xoa tag ${tag}`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Input nhap tag */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (suggestions.length > 0) {
              setShowSuggestions(true);
            }
          }}
          placeholder={
            isMaxTagsReached
              ? `Da dat gioi han ${maxTags} tag`
              : 'Nhap tag...'
          }
          disabled={isMaxTagsReached}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
        />

        {/* Dropdown goi y */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
            {isLoadingSuggestions && (
              <div className="px-3 py-2 text-sm text-gray-500 text-center">
                Dang tai...
              </div>
            )}
            {!isLoadingSuggestions && suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => addTag(suggestion)}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Hien thi so luong tag hien tai */}
      <div className="text-xs text-gray-500 mt-1">
        {selectedTags.length} / {maxTags} tag
      </div>
    </div>
  );
}

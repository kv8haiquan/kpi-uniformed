'use client';

/**
 * VoteButton.tsx
 * ==============
 * Component nut upvote/downvote cho chu de hoac tra loi.
 * Su dung optimistic update de UX tot hon.
 */

import { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { bieuQuyetApi } from '@/services/forum';
import type { DoiTuongType } from '@/types/forum';

interface VoteButtonProps {
  doi_tuong_type: DoiTuongType;
  doi_tuong_id: string;
  so_upvote: number;
  da_upvote: boolean | null;
  onVoteChange?: (newCount: number, newState: boolean | null) => void;
}

export default function VoteButton({
  doi_tuong_type,
  doi_tuong_id,
  so_upvote,
  da_upvote,
  onVoteChange,
}: VoteButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [currentCount, setCurrentCount] = useState(so_upvote);
  const [currentState, setCurrentState] = useState<boolean | null>(da_upvote);

  const handleVote = async (loai: 'UP' | 'DOWN') => {
    if (isLoading) return;

    // Optimistic update
    const previousCount = currentCount;
    const previousState = currentState;

    let newCount = currentCount;
    let newState: boolean | null = null;

    // Logic tinh toan state moi
    if (loai === 'UP') {
      if (currentState === true) {
        // Dang upvote -> bỏ vote
        newCount -= 1;
        newState = null;
      } else if (currentState === false) {
        // Dang downvote -> chuyen sang upvote
        newCount += 1;
        newState = true;
      } else {
        // Chua vote -> upvote
        newCount += 1;
        newState = true;
      }
    } else {
      // DOWN
      if (currentState === false) {
        // Dang downvote -> bo vote
        newState = null;
      } else if (currentState === true) {
        // Dang upvote -> chuyen sang downvote
        newCount -= 1;
        newState = false;
      } else {
        // Chua vote -> downvote
        newState = false;
      }
    }

    setCurrentCount(newCount);
    setCurrentState(newState);

    if (onVoteChange) {
      onVoteChange(newCount, newState);
    }

    setIsLoading(true);

    try {
      const response = await bieuQuyetApi.vote({
        doi_tuong_type,
        doi_tuong_id,
        loai,
      });

      // Cap nhat lai voi du lieu thuc tu server
      setCurrentCount(response.so_upvote_moi);

      if (response.hanh_dong === 'TOGGLED_OFF') {
        setCurrentState(null);
        if (onVoteChange) {
          onVoteChange(response.so_upvote_moi, null);
        }
      } else {
        const finalState = response.loai === 'UP' ? true : false;
        setCurrentState(finalState);
        if (onVoteChange) {
          onVoteChange(response.so_upvote_moi, finalState);
        }
      }
    } catch (error) {
      // Rollback neu loi
      console.error('Vote error:', error);
      setCurrentCount(previousCount);
      setCurrentState(previousState);
      if (onVoteChange) {
        onVoteChange(previousCount, previousState);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-1">
      {/* Nut upvote */}
      <button
        onClick={() => handleVote('UP')}
        disabled={isLoading}
        className={`p-1 rounded hover:bg-gray-100 transition-colors disabled:opacity-50 ${
          currentState === true ? 'text-green-600' : 'text-gray-400'
        }`}
        aria-label="Upvote"
      >
        <ChevronUp className="w-5 h-5" />
      </button>

      {/* So diem */}
      <span
        className={`text-sm font-semibold ${
          currentState === true
            ? 'text-green-600'
            : currentState === false
            ? 'text-red-600'
            : 'text-gray-700'
        }`}
      >
        {currentCount}
      </span>

      {/* Nut downvote */}
      <button
        onClick={() => handleVote('DOWN')}
        disabled={isLoading}
        className={`p-1 rounded hover:bg-gray-100 transition-colors disabled:opacity-50 ${
          currentState === false ? 'text-red-600' : 'text-gray-400'
        }`}
        aria-label="Downvote"
      >
        <ChevronDown className="w-5 h-5" />
      </button>
    </div>
  );
}

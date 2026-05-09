'use client';

/**
 * useMediaQuery — match window.matchMedia với SSR-safe.
 *
 * Phase 4.1 FE_P4. Dùng để adapt UX trên mobile (PDF.js scale, layout).
 */

import { useEffect, useState } from 'react';

export function useMediaQuery(query: string, defaultValue = false): boolean {
  const [matches, setMatches] = useState<boolean>(defaultValue);

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mql = window.matchMedia(query);
    const onChange = (e: MediaQueryListEvent) => setMatches(e.matches);
    setMatches(mql.matches);
    // Modern API; fallback addListener for very old browsers
    if (mql.addEventListener) mql.addEventListener('change', onChange);
    else mql.addListener(onChange);
    return () => {
      if (mql.removeEventListener) mql.removeEventListener('change', onChange);
      else mql.removeListener(onChange);
    };
  }, [query]);

  return matches;
}

/** Tailwind md breakpoint = 768px → mobile khi < 768. */
export function useIsMobile(): boolean {
  return useMediaQuery('(max-width: 767px)');
}

export default useMediaQuery;

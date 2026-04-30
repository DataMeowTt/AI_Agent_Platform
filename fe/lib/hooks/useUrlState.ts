'use client';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';

export function useUrlState<T>(key: string, defaultValue: T): [T, (val: T) => void] {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [state, setState] = useState<T>(() => {
    const val = searchParams.get(key);
    if (val === null) return defaultValue;
    if (typeof defaultValue === 'number') return Number(val) as T;
    if (Array.isArray(defaultValue)) return val.split(',') as T;
    return val as T;
  });

  const syncToUrl = useCallback((val: T) => {
    const params = new URLSearchParams(searchParams.toString());
    const strVal = val === defaultValue || !val || (Array.isArray(val) && val.length === 0)
      ? null
      : (Array.isArray(val) ? val.join(',') : String(val));
    if (params.get(key) !== strVal) {
      if (strVal) params.set(key, strVal); else params.delete(key);
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    }
  }, [pathname, searchParams, key, defaultValue, router]);

  useEffect(() => {
    syncToUrl(state);
  }, [state, syncToUrl]);

  useEffect(() => {
    const val = searchParams.get(key);
    if (val === null) setState(defaultValue);
    else if (typeof defaultValue === 'number') setState(Number(val) as T);
    else if (Array.isArray(defaultValue)) setState(val.split(',') as T);
    else setState(val as T);
  }, [searchParams.get(key)]);

  return [state, setState];
}
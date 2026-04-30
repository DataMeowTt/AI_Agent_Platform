'use client';
import { useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  siblingsCount?: number;
}

export default function Pagination({ currentPage, totalPages, onPageChange, siblingsCount = 1 }: PaginationProps) {
  if (totalPages <= 1) return null;

  const paginationRange = useMemo(() => {
    const totalNumbers = siblingsCount * 2 + 5;
    if (totalNumbers >= totalPages) return Array.from({ length: totalPages }, (_, i) => i + 1);

    const leftSibling = Math.max(currentPage - siblingsCount, 1);
    const rightSibling = Math.min(currentPage + siblingsCount, totalPages);

    const showLeftDots = leftSibling > 2;
    const showRightDots = rightSibling < totalPages - 2;

    if (!showLeftDots && showRightDots) {
      return [...Array.from({ length: 3 + siblingsCount * 2 }, (_, i) => i + 1), '...', totalPages];
    }
    if (showLeftDots && !showRightDots) {
      return [1, '...', ...Array.from({ length: 3 + siblingsCount * 2 }, (_, i) => totalPages - 2 - siblingsCount * 2 + i + 1), totalPages];
    }
    return [1, '...', ...Array.from({ length: siblingsCount * 2 + 3 }, (_, i) => leftSibling + i), '...', totalPages];
  }, [currentPage, totalPages, siblingsCount]);

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-white border border-gray-200 rounded-md mt-6">
      <span className="text-sm text-gray-500">
        {`Hiển thị ${(currentPage - 1) * 15 + 1}–${Math.min(currentPage * 15, totalPages * 15)} / ${totalPages * 15}`}
      </span>
      <div className="flex items-center gap-2">
        <button
          disabled={currentPage === 1}
          onClick={() => onPageChange(currentPage - 1)}
          className="p-2 border rounded-md hover:bg-gray-50 disabled:opacity-50"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        {paginationRange.map((page, idx) => (
          page === '...' ? (
            <span key={`dot-${idx}`} className="px-2 text-gray-500">...</span>
          ) : (
            <button
              key={page}
              onClick={() => onPageChange(page as number)}
              className={`px-3 h-8 text-sm rounded-md border ${
                page === currentPage ? 'bg-blue-600 text-white border-blue-600' : 'hover:bg-gray-50'
              }`}
            >
              {page}
            </button>
          )
        ))}
        <button
          disabled={currentPage === totalPages}
          onClick={() => onPageChange(currentPage + 1)}
          className="p-2 border rounded-md hover:bg-gray-50 disabled:opacity-50"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
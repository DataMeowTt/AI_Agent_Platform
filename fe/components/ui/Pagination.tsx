'use client';
import { useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  siblingsCount?: number;
}

export default function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  siblingsCount = 1,
}: PaginationProps) {
  if (totalPages <= 1) return null;

  const safeCurrent = Math.min(Math.max(currentPage, 1), totalPages);

  const paginationRange = useMemo(() => {
    const totalNumbers = siblingsCount * 2 + 5;
    if (totalNumbers >= totalPages) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const leftSibling = Math.max(safeCurrent - siblingsCount, 1);
    const rightSibling = Math.min(safeCurrent + siblingsCount, totalPages);

    const showLeftDots = leftSibling > 2;
    const showRightDots = rightSibling < totalPages - 2;

    if (!showLeftDots && showRightDots) {
      const rightItemCount = 3 + siblingsCount * 2;
      return [...Array.from({ length: rightItemCount }, (_, i) => i + 1), '...', totalPages];
    }

    if (showLeftDots && !showRightDots) {
      const leftItemCount = 3 + siblingsCount * 2;
      return [1, '...', ...Array.from({ length: leftItemCount }, (_, i) => totalPages - leftItemCount + i + 1)];
    }

    return [
      1,
      '...',
      ...Array.from({ length: siblingsCount * 2 + 3 }, (_, i) => leftSibling + i),
      '...',
      totalPages,
    ];
  }, [safeCurrent, totalPages, siblingsCount]);

  const handlePageChange = (page: number | string) => {
    if (typeof page === 'number') {
      const newPage = Math.min(Math.max(page, 1), totalPages);
      onPageChange(newPage);
    }
  };

  const itemsPerPage = 8;

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-white border border-gray-200 rounded-md mt-6">
      <span className="text-sm text-gray-500">
        {`Hiển thị ${Math.min((safeCurrent - 1) * itemsPerPage + 1, totalPages * itemsPerPage)}–${Math.min(safeCurrent * itemsPerPage, totalPages * itemsPerPage)} / ${totalPages * itemsPerPage}`}
      </span>
      <div className="flex items-center gap-2">
        <button
          disabled={safeCurrent === 1}
          onClick={() => handlePageChange(safeCurrent - 1)}
          className="p-2 border rounded-md hover:bg-gray-50 disabled:opacity-50"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {paginationRange.map((page, idx) =>
          page === '...' ? (
            <span key={`dot-${idx}`} className="px-2 text-gray-500">...</span>
          ) : (
            <button
              key={`page-${page}-${idx}`}
              onClick={() => handlePageChange(page as number)}
              className={`px-3 h-8 text-sm rounded-md border ${
                page === safeCurrent
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'hover:bg-gray-50'
              }`}
            >
              {page}
            </button>
          )
        )}

        <button
          disabled={safeCurrent === totalPages}
          onClick={() => handlePageChange(safeCurrent + 1)}
          className="p-2 border rounded-md hover:bg-gray-50 disabled:opacity-50"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
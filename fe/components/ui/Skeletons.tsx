import { cn } from '@/lib/utils/cn';

export const TableSkeleton = ({ rows = 5 }: { rows?: number }) => (
  <div className="animate-pulse space-y-3 bg-white p-6 rounded-md border border-gray-200">
    <div className="flex space-x-4 mb-4">
      <div className="h-6 bg-gray-200 rounded w-24" />
      <div className="h-6 bg-gray-200 rounded w-32" />
      <div className="h-6 bg-gray-200 rounded w-20" />
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex space-x-4">
        <div className="h-12 bg-gray-100 rounded w-1/4" />
        <div className="h-12 bg-gray-100 rounded w-1/4" />
        <div className="h-12 bg-gray-100 rounded w-1/4" />
        <div className="h-12 bg-gray-100 rounded w-1/4" />
      </div>
    ))}
  </div>
);

export const CardSkeleton = ({ className }: { className?: string }) => (
  <div className={cn('h-[140px] bg-white rounded-md border border-gray-200 p-6 flex flex-col justify-between animate-pulse', className)}>
    <div className="h-4 w-24 bg-gray-200 rounded" />
    <div className="h-8 w-20 bg-gray-200 rounded" />
    <div className="h-4 w-32 bg-gray-200 rounded" />
  </div>
);

export const ChartSkeleton = () => (
  <div className="bg-white rounded-md border border-gray-200 p-6 animate-pulse">
    <div className="flex justify-between items-center mb-6">
      <div className="h-5 w-32 bg-gray-200 rounded" />
      <div className="h-8 w-16 bg-gray-200 rounded" />
    </div>
    <div className="h-[400px] bg-gray-50 rounded flex items-center justify-center border border-dashed border-gray-300">
      <div className="w-2/3 h-1/2 bg-gray-100 rounded" />
    </div>
  </div>
);
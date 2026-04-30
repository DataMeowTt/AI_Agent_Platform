'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

const routeMap: Record<string, string> = {
  '/countries': 'Quốc gia',
  '/anomalies': 'Bất thường',
  '/clusters': 'Nhóm nước',
  '/compare': 'So sánh',
  '/chat': 'AI Chat',
};

export default function Breadcrumbs({ className }: { className?: string }) {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);

  const items = [
    { label: 'Dashboard', path: '/' },
    ...segments.map((segment, idx) => {
      const path = `/${segments.slice(0, idx + 1).join('/')}`;
      return {
        label: routeMap[path] || segment.toUpperCase(),
        path,
      };
    }),
  ];

  if (items.length <= 1) return null;

  return (
    <nav className={cn('flex items-center gap-2 text-sm', className)} aria-label="Breadcrumb">
      <Link href="/" className="flex items-center gap-1 text-gray-500 hover:text-gray-900 transition-colors">
        <Home className="w-4 h-4" />
      </Link>
      {items.slice(1).map((item, idx) => {
        const isLast = idx === items.length - 2;
        return (
          <div key={item.path} className="flex items-center gap-2">
            <ChevronRight className="w-4 h-4 text-gray-400" />
            {isLast ? (
              <span className="font-medium text-gray-900">{item.label}</span>
            ) : (
              <Link href={item.path} className="text-gray-500 hover:text-gray-700 transition-colors">
                {item.label}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}
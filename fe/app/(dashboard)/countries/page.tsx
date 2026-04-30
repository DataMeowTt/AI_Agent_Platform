'use client';
import { useCountries } from '@/lib/hooks/useCountries';
import { useDataState } from '@/lib/hooks/useDataState';
import { TableSkeleton } from '@/components/ui/Skeletons';
import { Search, Globe2 } from 'lucide-react';
import { useState, useMemo } from 'react';
import Link from 'next/link';

export default function CountriesPage() {
  const { data: countries, isLoading, isError, error } = useDataState(useCountries());
  const [search, setSearch] = useState('');

  const filteredCountries = useMemo(() => {
    if (!countries) return [];
    const q = search.toLowerCase();
    return countries.filter(c =>
      c.country_name.toLowerCase().includes(q) || c.country_code.toLowerCase().includes(q)
    );
  }, [countries, search]);

  if (isError) return <div className="p-4 bg-red-50 text-red-700 rounded border border-red-200">Error: {error?.message}</div>;
  if (isLoading) return <TableSkeleton rows={8} />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Danh sách Quốc gia</h1>
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Tìm theo tên hoặc mã..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 h-10 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="bg-white rounded-md border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Mã</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Quốc gia</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Khu vực</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Thao tác</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredCountries.length > 0 ? filteredCountries.map((country) => (
              <tr key={country.country_code} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">{country.country_code}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{country.country_name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{country.region || '--'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <Link href={`/countries/${country.country_code}`} className="text-sm font-medium text-blue-600 hover:text-blue-800">
                    Xem chi tiết
                  </Link>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan={4} className="px-6 py-12 text-center text-gray-500">
                  <Globe2 className="w-8 h-8 mx-auto text-gray-300 mb-3" />
                  Không tìm thấy quốc gia phù hợp.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
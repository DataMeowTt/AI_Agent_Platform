'use client';
import { useUrlState } from '@/lib/hooks/useUrlState';
import { useAnomalies } from '@/lib/hooks/useAnomalies';
import { useCountries } from '@/lib/hooks/useCountries';
import AnomaliesTable from '@/components/tables/AnomaliesTable';
import Pagination from '@/components/ui/Pagination';
import { TableSkeleton } from '@/components/ui/Skeletons';
import { Search, Filter } from 'lucide-react';
import { useMemo, useState, useEffect, useRef } from 'react';
import { Country } from '@/lib/types';

export default function AnomaliesPage() {
  const [country, setCountry] = useUrlState<string>('country', '');
  const [rawThreshold, setRawThreshold] = useUrlState<number>('threshold', 0.75);
  const [page, setPage] = useUrlState<number>('page', 1);

  const [appliedThreshold, setAppliedThreshold] = useState(rawThreshold);
  const [countrySearch, setCountrySearch] = useState('');
  const [isCountryDropdownOpen, setIsCountryDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const ITEMS_PER_PAGE = 8;
  const offset = (page - 1) * ITEMS_PER_PAGE;

  const { data: countries, isLoading: loadingCountries } = useCountries();
  const { data, total, isLoading, isEmpty, isError, error } = useAnomalies({
    country: country || undefined,
    threshold: appliedThreshold,
    limit: ITEMS_PER_PAGE,
    offset,
  });

  const totalPages = useMemo(() => {
    const t = total ?? 0;
    return t > 0 ? Math.ceil(t / ITEMS_PER_PAGE) : 1;
  }, [total]);

  useEffect(() => {
    if (!isLoading && page > totalPages) {
      setPage(totalPages);
    }
  }, [isLoading, totalPages, page, setPage]);

  const handleApply = () => {
    setPage(1);
    setAppliedThreshold(rawThreshold);
  };

  const filteredCountries = useMemo(() => {
    const list = (countries ?? []) as Country[];
    const q = countrySearch.toLowerCase();
    return list.filter(c => c.country_name.toLowerCase().includes(q) || c.country_code.toLowerCase().includes(q));
  }, [countries, countrySearch]);

  const selectedCountryName = useMemo(() => {
    const list = (countries ?? []) as Country[];
    if (!country) return '';
    return list.find(c => c.country_code === country)?.country_name || '';
  }, [country, countries]);

  const selectCountry = (code: string, name: string) => {
    setCountry(code);
    setCountrySearch(name);
    setIsCountryDropdownOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsCountryDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (loadingCountries) return <TableSkeleton rows={1} />;
  if (isError) return <div className="p-4 bg-red-50 text-red-700 rounded border border-red-200">Lỗi: {error?.message}</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Giám sát Bất thường</h1>
        <div className="flex items-center gap-2 text-sm text-gray-500 bg-white px-3 py-1.5 rounded-full border border-gray-200 shadow-sm">
          <span className="font-medium text-gray-900">{total || 0}</span> kết quả
        </div>
      </div>

      <div className="bg-white p-6 rounded-md border border-gray-200 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          <div className="relative" ref={dropdownRef}>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Quốc gia</label>
            <div className="relative">
              <input type="text" placeholder="Chọn hoặc tìm quốc gia..." value={countrySearch || selectedCountryName}
                onChange={(e) => { setCountrySearch(e.target.value); setIsCountryDropdownOpen(true); }}
                onFocus={() => setIsCountryDropdownOpen(true)}
                className="w-full h-10 px-3 pr-8 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white" />
              {(country || countrySearch) && (
                <button onClick={() => { setCountry(''); setCountrySearch(''); }} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
              )}
            </div>
            {isCountryDropdownOpen && (
              <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto">
                <div onClick={() => selectCountry('', 'Tất cả')} className="px-3 py-2 text-sm hover:bg-gray-100 cursor-pointer border-b border-gray-100 font-medium">Tất cả</div>
                {filteredCountries.map((c: Country) => (
                  <div key={c.country_code} onClick={() => selectCountry(c.country_code, c.country_name)} className="px-3 py-2 text-sm hover:bg-gray-100 cursor-pointer">
                    {c.country_name} <span className="text-gray-400 text-xs ml-1">({c.country_code})</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="lg:col-span-2">
            <div className="flex justify-between mb-1.5">
              <label className="block text-sm font-medium text-gray-700">Ngưỡng Bất thường</label>
              <span className="text-xs font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded">{rawThreshold.toFixed(2)}</span>
            </div>
            <input type="range" min="0.5" max="1" step="0.01" value={rawThreshold}
              onChange={(e) => setRawThreshold(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600" />
            <div className="flex justify-between text-xs text-gray-400 mt-1"><span>0.5 (Thấp)</span><span>1.0 (Cao)</span></div>
          </div>

          <div className="flex gap-2">
            <button onClick={handleApply} disabled={isLoading}
              className="flex-1 h-10 px-4 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors">
              <Search className="w-4 h-4" /> Áp dụng
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <TableSkeleton rows={5} />
      ) : isEmpty ? (
        <div className="bg-white rounded-md border border-gray-200 p-12 flex flex-col items-center text-center">
          <Filter className="w-10 h-10 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Không tìm thấy bất thường</h3>
          <p className="text-sm text-gray-500 max-w-sm mb-6">Thử giảm ngưỡng xuống 0.5 hoặc bỏ lọc quốc gia để mở rộng kết quả.</p>
          <button onClick={() => { setCountry(''); setRawThreshold(0.75); handleApply(); }} className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200 transition-colors">Đặt lại bộ lọc</button>
        </div>
      ) : (
        <>
          <AnomaliesTable data={data || []} />
          <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage}/>
        </>
      )}
    </div>
  );
}
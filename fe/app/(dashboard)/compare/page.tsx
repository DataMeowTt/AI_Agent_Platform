'use client';
import { useUrlState } from '@/lib/hooks/useUrlState';
import MultiCountrySelector from '@/components/filters/MultiCountrySelector';
import IndicatorSelector from '@/components/filters/IndicatorSelector';
import dynamic from 'next/dynamic';
import { useCompare } from '@/lib/hooks/useCompare';

const CompareLineChart = dynamic(() => import('@/components/charts/CompareLineChart'), {
  ssr: false,
  loading: () => <div className="h-64 bg-gray-200 animate-pulse rounded" />
});

const INDICATOR_NAMES: Record<string, string> = {
  rGDP_growth_YoY: 'Real GDP Growth (%)',
  govdebt_GDP: 'Government Debt (% GDP)',
  REER_deviation: 'REER Deviation (%)',
  inflation_cpi: 'Inflation (CPI)',
  poverty_headcount: 'Poverty Headcount (%)',
  unemployment_total: 'Unemployment (%)',
  manuf_va_share: 'Manufacturing VA (% GDP)',
  agri_va_share: 'Agriculture VA (% GDP)',
};

export default function ComparePage() {
  const [selectedCountries, setSelectedCountries] = useUrlState<string[]>('countries', []);
  const [selectedIndicator, setSelectedIndicator] = useUrlState<string>('indicator', 'rGDP_growth_YoY');
  const { data, isLoading, error } = useCompare(selectedCountries, selectedIndicator);

  const hasData = selectedCountries.length > 0 && Object.keys(data).length > 0;
  const missingCountries = selectedCountries.filter(code => !data[code]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Compare Countries</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <label className="block font-medium mb-2">Quốc gia (tối đa 5)</label>
          <MultiCountrySelector selected={selectedCountries} onChange={setSelectedCountries} max={5} />
        </div>
        <div>
          <label className="block font-medium mb-2">Chỉ số so sánh</label>
          <IndicatorSelector selected={selectedIndicator} onChange={setSelectedIndicator} />
        </div>
      </div>

      {selectedCountries.length === 0 && (
        <div className="bg-blue-50 p-4 rounded text-blue-800 mb-4 border border-blue-200">
          Vui lòng chọn ít nhất một quốc gia để bắt đầu so sánh.
        </div>
      )}

      {missingCountries.length > 0 && (
        <div className="bg-yellow-50 p-4 rounded text-yellow-800 mb-4 border border-yellow-200 flex items-start gap-2">
          ⚠️
          <div>
            <p className="font-medium">Dữ liệu thiếu cho các quốc gia: {missingCountries.join(', ')}</p>
            <p className="text-sm opacity-80">Biểu đồ sẽ hiển thị cảnh báo tại các năm không có số liệu.</p>
          </div>
        </div>
      )}

      {error && <div className="bg-red-50 p-4 rounded text-red-800 mb-4">Lỗi: {error.message}</div>}
      
      {!isLoading && hasData && (
        <div className="bg-white p-4 rounded shadow">
          <CompareLineChart data={data} indicatorName={INDICATOR_NAMES[selectedIndicator] || selectedIndicator} />
        </div>
      )}
    </div>
  );
}
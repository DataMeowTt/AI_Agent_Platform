'use client';

import { useCountries } from '@/lib/hooks/useCountries';

export default function CountriesPage() {
  const { data: countries, isLoading, error } = useCountries();

  if (isLoading) return <div>Loading countries...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Countries</h1>
      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Country Name</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {countries?.map((country: any) => (
              <tr key={country.country_code} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{country.country_code}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{country.country_name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
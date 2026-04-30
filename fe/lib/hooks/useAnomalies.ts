import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api/endpoints';
import { anomalySchema } from '@/lib/schemas';
import { z } from 'zod';

const anomalyResponseSchema = z.object({
  items: z.array(anomalySchema),
  meta: z.object({ total_count: z.number(), limit: z.number(), offset: z.number() }),
});

export const useAnomalies = ({
  country, indicator, threshold = 0.75, limit = 15, offset = 0
}: { country?: string; indicator?: string; threshold?: number; limit?: number; offset?: number } = {}) => {
  const queryResult = useQuery({
    queryKey: ['anomalies', country, indicator, threshold, limit, offset],
    queryFn: async () => {
      const { data } = await analyticsApi.getAnomalies({ country, indicator, threshold, limit, offset });
      return anomalyResponseSchema.parse(data);
    },
    staleTime: 30 * 1000,
  });

  const { data, isLoading, isError, error } = queryResult;
  return {
    data: data?.items,
    total: data?.meta.total_count,
    isLoading,
    isError,
    error: error as Error | null,
    isEmpty: !isLoading && !isError && (!data || data.items.length === 0),
  };
};
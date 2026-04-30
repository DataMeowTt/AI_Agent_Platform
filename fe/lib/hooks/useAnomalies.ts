import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api/endpoints';
import { anomalySchema } from '@/lib/schemas';
import { AnomalyItem } from '@/lib/types';
import { z } from 'zod';

const anomalyResponseSchema = z.object({
    items: z.array(anomalySchema),
    meta: z.object({ total_count: z.number() }),
});

interface UseAnomaliesResult {
    data: AnomalyItem[] | undefined;
    total: number | undefined;
    isLoading: boolean;
    isError: boolean;
    error: Error | null;
    isEmpty: boolean;
}

export const useAnomalies = (params?: { country?: string; indicator?: string; threshold?: number; limit?: number }): UseAnomaliesResult => {
    const queryResult = useQuery({
        queryKey: ['anomalies', params],
        queryFn: async () => {
            const { data } = await analyticsApi.getAnomalies(params);
            return anomalyResponseSchema.parse(data);
        },
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
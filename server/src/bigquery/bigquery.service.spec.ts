import { ConfigService } from '@nestjs/config';
import { BigQueryService } from './bigquery.service';
import { BigQueryCacheService } from './bigquery-cache.service';

const queryMock = jest.fn();

jest.mock('@google-cloud/bigquery', () => ({
  BigQuery: jest.fn().mockImplementation(() => ({
    query: queryMock,
  })),
}));

describe('BigQueryService', () => {
  let service: BigQueryService;
  let cacheService: jest.Mocked<BigQueryCacheService>;

  beforeEach(() => {
    queryMock.mockReset();
    cacheService = {
      get: jest.fn(),
      set: jest.fn(),
    } as unknown as jest.Mocked<BigQueryCacheService>;

    const configService = {
      get: jest.fn((key: string) => {
        if (key === 'BIGQUERY_PROJECT_ID') return 'western-pivot-452008-a6';
        if (key === 'BIGQUERY_LOCATION') return 'asia-southeast1';
        if (key === 'BIGQUERY_GOLD_DATASET') return 'gov_ai_gold';
        if (key === 'BIGQUERY_ANALYTICS_DATASET') return 'gov_ai_analytics';
        if (key === 'BIGQUERY_MAX_BYTES_BILLED') return '100000000';
        if (key === 'BIGQUERY_CACHE_TTL_SECONDS') return '300';
        return undefined;
      }),
    } as unknown as ConfigService;

    service = new BigQueryService(configService, cacheService);
  });

  it('getClusters query should not include method column', async () => {
    cacheService.get.mockReturnValueOnce(undefined);
    queryMock.mockResolvedValueOnce([
      [
        {
          country_code: 'VNM',
          country: 'Viet Nam',
          year: 2020,
          cluster_id: 1,
          latest_valid_year: 2020,
        },
      ],
    ]);

    await service.getClusters(2020);

    expect(queryMock).toHaveBeenCalledTimes(1);
    const queryArg = queryMock.mock.calls[0][0].query as string;
    expect(queryArg).not.toMatch(/\bmethod\b/i);
    expect(queryArg).toContain('c.latest_valid_year AS latest_valid_year');
    expect(queryArg).toContain('c.country AS country');
    expect(queryArg).toContain('`western-pivot-452008-a6.gov_ai_analytics.analytics_clusters`');
  });

  it('getAnomalies should return empty for unsupported indicator', async () => {
    const result = await service.getAnomalies({
      indicator: 'unsupported-indicator',
      threshold: 0.75,
      limit: 15,
      offset: 3,
    });

    expect(result).toEqual({
      items: [],
      meta: { total_count: 0, limit: 15, offset: 3 },
    });
    expect(queryMock).not.toHaveBeenCalled();
  });

  it('getAnomalies without countryCode should not pass null/undefined params', async () => {
    cacheService.get.mockReturnValueOnce(undefined);
    queryMock.mockResolvedValueOnce([
      [
        {
          country_code: 'VNM',
          year: 2022,
          indicator: 'rGDP_growth_YoY',
          actual_value: 4.2,
          anomaly_score: 0.91,
          country_name: 'Viet Nam',
          total_count: 1,
        },
      ],
    ]);

    const result = await service.getAnomalies({
      threshold: 0.75,
      limit: 5,
      offset: 0,
    });

    expect(result.meta).toEqual({ total_count: 1, limit: 5, offset: 0 });
    expect(result.items).toHaveLength(1);
    expect(queryMock).toHaveBeenCalledTimes(1);

    const queryOptions = queryMock.mock.calls[0][0];
    expect(queryOptions.query).not.toContain('@countryCode IS NULL');
    expect(queryOptions.params).toEqual({
      threshold: 0.75,
      limit: 5,
      offset: 0,
    });
    expect(Object.values(queryOptions.params)).not.toContain(null);
    expect(Object.values(queryOptions.params)).not.toContain(undefined);
  });

  it('getAnomalies with countryCode should include countryCode param and filter', async () => {
    cacheService.get.mockReturnValueOnce(undefined);
    queryMock.mockResolvedValueOnce([
      [
        {
          country_code: 'VNM',
          year: 2022,
          indicator: 'govdebt_GDP',
          actual_value: 39.1,
          anomaly_score: 0.89,
          country_name: 'Viet Nam',
          total_count: 1,
        },
      ],
    ]);

    await service.getAnomalies({
      countryCode: 'vnm',
      threshold: 0.75,
      limit: 5,
      offset: 0,
    });

    expect(queryMock).toHaveBeenCalledTimes(1);
    const queryOptions = queryMock.mock.calls[0][0];
    expect(queryOptions.query).toContain('AND a.country_code = @countryCode');
    expect(queryOptions.params).toMatchObject({
      countryCode: 'VNM',
      threshold: 0.75,
      limit: 5,
      offset: 0,
    });
  });

  it('should reject unsafe queries', () => {
    expect(() =>
      (service as any).validateQuerySafety('SELECT * FROM `a.b.c`'),
    ).toThrow('Unsafe query rejected: SELECT * is not allowed.');

    expect(() =>
      (service as any).validateQuerySafety(
        'SELECT country_code FROM `western-pivot-452008-a6.gov_ai_gold.unknown_table`',
      ),
    ).toThrow('is not whitelisted');
  });
});

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


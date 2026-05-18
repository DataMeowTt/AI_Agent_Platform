import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { BigQuery } from '@google-cloud/bigquery';
import { BigQueryCacheService } from './bigquery-cache.service';
import {
  BigQueryAnomaliesParams,
  BigQueryAnomalyItem,
  BigQueryClusterItem,
  BigQueryCountryItem,
} from './bigquery.types';

const DEFAULT_PROJECT_ID = 'western-pivot-452008-a6';
const DEFAULT_LOCATION = 'asia-southeast1';
const DEFAULT_MAX_BYTES_BILLED = 100000000;
const DEFAULT_CACHE_TTL_SECONDS = 300;
const MAX_LIMIT = 100;

@Injectable()
export class BigQueryService {
  private readonly projectId: string;
  private readonly location: string;
  private readonly maximumBytesBilled: number;
  private readonly cacheTtlSeconds: number;
  private readonly client: BigQuery;

  private readonly whitelistedTables = new Set<string>([
    'western-pivot-452008-a6.gov_ai_gold.gold_growth_dynamics',
    'western-pivot-452008-a6.gov_ai_analytics.analytics_clusters',
    'western-pivot-452008-a6.gov_ai_analytics.analytics_gold_growth_dynamics',
    'western-pivot-452008-a6.gov_ai_analytics.analytics_gold_fiscal_monetary',
    'western-pivot-452008-a6.gov_ai_analytics.analytics_gold_crisis_risk',
  ]);

  constructor(
    private readonly configService: ConfigService,
    private readonly cacheService: BigQueryCacheService,
  ) {
    this.projectId =
      this.configService.get<string>('BIGQUERY_PROJECT_ID') || DEFAULT_PROJECT_ID;
    this.location =
      this.configService.get<string>('BIGQUERY_LOCATION') || DEFAULT_LOCATION;
    this.maximumBytesBilled = Number(
      this.configService.get<string>('BIGQUERY_MAX_BYTES_BILLED') ||
        DEFAULT_MAX_BYTES_BILLED,
    );
    this.cacheTtlSeconds = Number(
      this.configService.get<string>('BIGQUERY_CACHE_TTL_SECONDS') ||
        DEFAULT_CACHE_TTL_SECONDS,
    );
    this.client = new BigQuery({ projectId: this.projectId });
  }

  async listCountries(): Promise<BigQueryCountryItem[]> {
    const sql = `
      SELECT
        g.country_code AS country_code,
        g.country AS country_name,
        ANY_VALUE(g.income_group) AS region
      FROM \`western-pivot-452008-a6.gov_ai_gold.gold_growth_dynamics\` g
      GROUP BY g.country_code, g.country
      ORDER BY g.country ASC
      LIMIT @limit
    `;
    return this.executeQuery<BigQueryCountryItem>(sql, { limit: MAX_LIMIT });
  }

  async getClusters(year: number): Promise<BigQueryClusterItem[]> {
    const safeYear = Number(year);
    const sql = `
      SELECT
        c.country_code AS country_code,
        c.country AS country,
        c.year AS year,
        c.cluster_id AS cluster_id,
        c.latest_valid_year AS latest_valid_year
      FROM \`western-pivot-452008-a6.gov_ai_analytics.analytics_clusters\` c
      WHERE c.year = @year
      ORDER BY c.country_code ASC
      LIMIT @limit
    `;
    return this.executeQuery<BigQueryClusterItem>(sql, {
      year: safeYear,
      limit: MAX_LIMIT,
    });
  }

  async getAnomalies(
    params: BigQueryAnomaliesParams,
  ): Promise<{ items: BigQueryAnomalyItem[]; meta: { total_count: number; limit: number; offset: number } }> {
    const hasIndicatorFilter =
      params.indicator !== undefined &&
      params.indicator !== null &&
      params.indicator.trim() !== '';
    const normalizedIndicator = this.normalizeIndicator(params.indicator);
    const threshold = this.clampNumber(params.threshold, 0, 1, 0.75);
    const limit = this.clampNumber(params.limit, 1, MAX_LIMIT, 15);
    const offset = this.clampNumber(params.offset, 0, Number.MAX_SAFE_INTEGER, 0);

    if (hasIndicatorFilter && !normalizedIndicator) {
      return {
        items: [],
        meta: { total_count: 0, limit, offset },
      };
    }

    const anomalyBranches: string[] = [];
    if (!normalizedIndicator || normalizedIndicator === 'growth') {
      anomalyBranches.push(`
        SELECT
          a.country_code AS country_code,
          a.year AS year,
          'rGDP_growth_YoY' AS indicator,
          a.rGDP_growth_YoY_actual AS actual_value,
          a.rGDP_growth_YoY_anomaly_score AS anomaly_score,
          g.country AS country_name
        FROM \`western-pivot-452008-a6.gov_ai_analytics.analytics_gold_growth_dynamics\` a
        LEFT JOIN \`western-pivot-452008-a6.gov_ai_gold.gold_growth_dynamics\` g
          ON g.country_code = a.country_code AND g.year = a.year
        WHERE a.rGDP_growth_YoY_anomaly_score BETWEEN @threshold AND 1
          AND (@countryCode IS NULL OR a.country_code = @countryCode)
      `);
    }

    if (!normalizedIndicator || normalizedIndicator === 'govdebt') {
      anomalyBranches.push(`
        SELECT
          a.country_code AS country_code,
          a.year AS year,
          'govdebt_GDP' AS indicator,
          a.govdebt_GDP_actual AS actual_value,
          a.govdebt_GDP_anomaly_score AS anomaly_score,
          g.country AS country_name
        FROM \`western-pivot-452008-a6.gov_ai_analytics.analytics_gold_fiscal_monetary\` a
        LEFT JOIN \`western-pivot-452008-a6.gov_ai_gold.gold_growth_dynamics\` g
          ON g.country_code = a.country_code AND g.year = a.year
        WHERE a.govdebt_GDP_anomaly_score BETWEEN @threshold AND 1
          AND (@countryCode IS NULL OR a.country_code = @countryCode)
      `);
    }

    if (!normalizedIndicator || normalizedIndicator === 'reer') {
      anomalyBranches.push(`
        SELECT
          a.country_code AS country_code,
          a.year AS year,
          'REER_deviation' AS indicator,
          a.REER_deviation_actual AS actual_value,
          a.REER_deviation_anomaly_score AS anomaly_score,
          g.country AS country_name
        FROM \`western-pivot-452008-a6.gov_ai_analytics.analytics_gold_crisis_risk\` a
        LEFT JOIN \`western-pivot-452008-a6.gov_ai_gold.gold_growth_dynamics\` g
          ON g.country_code = a.country_code AND g.year = a.year
        WHERE a.REER_deviation_anomaly_score BETWEEN @threshold AND 1
          AND (@countryCode IS NULL OR a.country_code = @countryCode)
      `);
    }

    if (anomalyBranches.length === 0) {
      return {
        items: [],
        meta: { total_count: 0, limit, offset },
      };
    }

    const sql = `
      WITH anomaly_raw AS (
        ${anomalyBranches.join('\nUNION ALL\n')}
      ),
      dedup AS (
        SELECT
          country_code,
          year,
          indicator,
          actual_value,
          anomaly_score,
          country_name,
          ROW_NUMBER() OVER (
            PARTITION BY country_code, year, indicator
            ORDER BY anomaly_score DESC
          ) AS rn
        FROM anomaly_raw
      ),
      ranked AS (
        SELECT
          country_code,
          year,
          indicator,
          actual_value,
          anomaly_score,
          COALESCE(country_name, country_code) AS country_name
        FROM dedup
        WHERE rn = 1
      )
      SELECT
        country_code,
        year,
        indicator,
        actual_value,
        anomaly_score,
        country_name,
        COUNT(*) OVER() AS total_count
      FROM ranked
      ORDER BY anomaly_score DESC
      LIMIT @limit
      OFFSET @offset
    `;

    const rows = await this.executeQuery<
      BigQueryAnomalyItem & { total_count: number | string | null }
    >(sql, {
      countryCode: params.countryCode || null,
      threshold,
      limit,
      offset,
    });

    const totalCount =
      rows.length > 0 ? Number(rows[0].total_count || 0) : 0;

    return {
      items: rows.map(row => ({
        country_code: row.country_code,
        year: Number(row.year),
        indicator: row.indicator,
        actual_value: row.actual_value,
        anomaly_score: row.anomaly_score,
        country_name: row.country_name,
      })),
      meta: {
        total_count: totalCount,
        limit,
        offset,
      },
    };
  }

  private async executeQuery<T>(
    query: string,
    params: Record<string, unknown>,
  ): Promise<T[]> {
    this.validateQuerySafety(query);
    const cacheKey = `${query}::${JSON.stringify(params)}`;
    const cached = this.cacheService.get<T[]>(cacheKey);
    if (cached) {
      return cached;
    }

    const [rows] = await this.client.query({
      query,
      params,
      location: this.location,
      useLegacySql: false,
      maximumBytesBilled: String(this.maximumBytesBilled),
    });

    const typedRows = rows as T[];
    this.cacheService.set(cacheKey, typedRows, this.cacheTtlSeconds);
    return typedRows;
  }

  private validateQuerySafety(query: string): void {
    if (/\bselect\s+\*/i.test(query)) {
      throw new Error('Unsafe query rejected: SELECT * is not allowed.');
    }

    const tableRefs = Array.from(query.matchAll(/`([^`]+)`/g)).map(
      match => match[1],
    );
    if (tableRefs.length === 0) {
      throw new Error('Unsafe query rejected: missing fully-qualified tables.');
    }

    for (const tableRef of tableRefs) {
      if (!this.whitelistedTables.has(tableRef)) {
        throw new Error(
          `Unsafe query rejected: table ${tableRef} is not whitelisted.`,
        );
      }
    }
  }

  private clampNumber(
    value: number | undefined,
    min: number,
    max: number,
    fallback: number,
  ): number {
    const normalized = Number.isFinite(Number(value)) ? Number(value) : fallback;
    return Math.min(max, Math.max(min, normalized));
  }

  private normalizeIndicator(indicator?: string): 'growth' | 'govdebt' | 'reer' | undefined {
    if (!indicator) {
      return undefined;
    }

    const normalized = indicator.trim().toLowerCase();
    if (normalized === 'growth') {
      return 'growth';
    }
    if (normalized === 'govdebt') {
      return 'govdebt';
    }
    if (normalized === 'reer') {
      return 'reer';
    }
    return undefined;
  }
}

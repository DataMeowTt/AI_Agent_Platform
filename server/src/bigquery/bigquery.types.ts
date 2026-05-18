export type BackendDataSource = 'postgres' | 'bigquery';

export interface BigQueryAnomaliesParams {
  countryCode?: string;
  indicator?: string;
  threshold: number;
  limit: number;
  offset: number;
}

export interface BigQueryCountryItem {
  country_code: string;
  country_name: string;
  region: string | null;
}

export interface BigQueryClusterItem {
  country_code: string;
  country: string;
  year: number;
  cluster_id: number;
  latest_valid_year: number;
}

export interface BigQueryAnomalyItem {
  country_code: string;
  year: number;
  indicator: string;
  actual_value: number | null;
  anomaly_score: number | null;
  country_name: string;
}

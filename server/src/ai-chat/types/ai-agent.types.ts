export type AiAgentQuestionType =
  | 'OFF_TOPIC'
  | 'NEED_CLARIFICATION'
  | 'VALID_SIMPLE_QUERY'
  | 'VALID_COMPARE_QUERY'
  | 'VALID_RANKING_QUERY'
  | 'VALID_TREND_QUERY'
  | 'VALID_ANOMALY_QUERY'
  | 'VALID_COVERAGE_QUERY'
  | 'UNSUPPORTED_DATA_QUERY';

export interface AiAgentChartConfig {
  type: 'line' | 'bar' | 'scatter' | 'table' | 'none';
  title?: string;
  xKey?: string;
  yKeys?: string[];
  data?: Record<string, unknown>[];
}

export interface AiAgentChatResponse {
  answer: string;

  questionType?: AiAgentQuestionType;

  data?: Record<string, unknown>[];

  chart?: AiAgentChartConfig;

  warnings?: string[];

  metadata?: {
    source?: 'template' | 'gemini' | 'mock';
    toolsUsed?: string[];
    indicators?: string[];
    countries?: string[];
    years?: number[];
    [key: string]: unknown;
  };
}

export interface AiAgentHealthResponse {
  status: 'ok' | 'degraded' | 'error';
  service: string;
  version?: string;
}
import {
  BadGatewayException,
  Injectable,
  ServiceUnavailableException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { HttpService } from '@nestjs/axios';
import { AxiosError } from 'axios';
import { firstValueFrom } from 'rxjs';
import { AiChatRequestDto } from './dto/ai-chat.dto';
import {
  AiAgentChatResponse,
  AiAgentHealthResponse,
} from './types/ai-agent.types';

@Injectable()
export class AiChatService {
  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {}

  async chat(payload: AiChatRequestDto): Promise<AiAgentChatResponse> {
    const baseUrl = this.getAgentBaseUrl();

    try {
      const response = await firstValueFrom(
        this.httpService.post<AiAgentChatResponse>(
          `${baseUrl}/agent/chat`,
          payload,
          {
            headers: this.getInternalHeaders(),
            timeout: this.getTimeoutMs(),
          },
        ),
      );

      return response.data;
    } catch (error) {
      this.handleAgentError(error, 'AI Agent chat request failed');
    }
  }

  async health(): Promise<AiAgentHealthResponse> {
    const baseUrl = this.getAgentBaseUrl();

    try {
      const response = await firstValueFrom(
        this.httpService.get<AiAgentHealthResponse>(`${baseUrl}/health`, {
          headers: this.getInternalHeaders(),
          timeout: 5000,
        }),
      );

      return response.data;
    } catch (error) {
      this.handleAgentError(error, 'AI Agent health check failed');
    }
  }

  private getAgentBaseUrl(): string {
    const baseUrl = this.configService.get<string>('AI_AGENT_BASE_URL');

    if (!baseUrl) {
      throw new ServiceUnavailableException({
        message: 'AI_AGENT_BASE_URL is not configured',
      });
    }

    return baseUrl.replace(/\/$/, '');
  }

  private getTimeoutMs(): number {
    const timeout = this.configService.get<string>('AI_AGENT_TIMEOUT_MS');
    return timeout ? Number(timeout) : 30000;
  }

  private getInternalHeaders(): Record<string, string> {
    const internalApiKey = this.configService.get<string>(
      'AI_AGENT_INTERNAL_API_KEY',
    );

    if (!internalApiKey) {
      return {};
    }

    return {
      'x-internal-api-key': internalApiKey,
    };
  }

  private handleAgentError(error: unknown, fallbackMessage: string): never {
    const axiosError = error as AxiosError;

    if (axiosError.response) {
      throw new BadGatewayException({
        message: fallbackMessage,
        agentStatusCode: axiosError.response.status,
        agentResponse: axiosError.response.data,
      });
    }

    if (
      axiosError.code === 'ECONNABORTED' ||
      axiosError.message?.toLowerCase().includes('timeout')
    ) {
      throw new ServiceUnavailableException({
        message: 'AI Agent service timeout',
        detail: axiosError.message,
      });
    }

    throw new ServiceUnavailableException({
      message: fallbackMessage,
      detail: axiosError.message ?? 'Unknown AI Agent error',
    });
  }
}